"""Rules: invoice amount from plan price, overpayment, paid / partially_paid, failed payment."""
from decimal import Decimal


def pay(client, invoice_id, amount, status="success", currency="INR", **extra):
    return client.post(
        "/payments/record",
        json={"invoice_id": invoice_id, "amount": amount, "currency": currency, "status": status, **extra},
    )


def test_invoice_amount_due_comes_from_plan_price_at_generation_time(client, make_plan, make_customer, make_subscription, make_invoice):
    plan = make_plan(price="499.00")
    customer = make_customer()
    subscription = make_subscription(customer["id"], plan["id"], start_date="2026-01-01")

    first = make_invoice(subscription["id"])
    assert Decimal(first["amount_due"]) == Decimal("499.00")
    assert Decimal(first["amount_paid"]) == Decimal("0")
    assert first["status"] == "issued"
    assert first["currency"] == "INR"

    client.patch(f"/plans/{plan['id']}", json={"price": "999.00"})

    # the existing invoice keeps the old price ...
    assert Decimal(client.get(f"/invoices/{first['id']}").json()["amount_due"]) == Decimal("499.00")
    # ... and a new invoice picks up the new price
    second = make_invoice(subscription["id"], period_start="2026-02-01", period_end="2026-03-01")
    assert Decimal(second["amount_due"]) == Decimal("999.00")


def test_invoice_only_for_active_subscription(client, make_plan, make_customer, make_subscription):
    plan = make_plan()
    customer = make_customer()
    subscription = make_subscription(customer["id"], plan["id"])
    client.patch(f"/subscriptions/{subscription['id']}/cancel")

    assert client.post("/invoices/generate", json={"subscription_id": subscription["id"]}).status_code == 400
    assert client.post("/invoices/generate", json={"subscription_id": 999}).status_code == 404


def test_cannot_generate_two_invoices_for_same_period(client, make_plan, make_customer, make_subscription, make_invoice):
    subscription = make_subscription(make_customer()["id"], make_plan()["id"])
    make_invoice(subscription["id"])
    assert client.post("/invoices/generate", json={"subscription_id": subscription["id"]}).status_code == 409


def test_invoice_period_validation(client, make_plan, make_customer, make_subscription):
    subscription = make_subscription(make_customer()["id"], make_plan()["id"])
    only_start = client.post("/invoices/generate", json={"subscription_id": subscription["id"], "period_start": "2026-01-01"})
    assert only_start.status_code == 400
    backwards = client.post(
        "/invoices/generate",
        json={"subscription_id": subscription["id"], "period_start": "2026-02-01", "period_end": "2026-01-01"},
    )
    assert backwards.status_code == 400


def test_successful_payment_cannot_exceed_remaining_amount(client, issued_invoice):
    invoice_id = issued_invoice["invoice"]["id"]
    response = pay(client, invoice_id, "500.00")
    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"]

    invoice = client.get(f"/invoices/{invoice_id}").json()
    assert Decimal(invoice["amount_paid"]) == Decimal("0")
    assert invoice["status"] == "issued"

    # nothing was recorded in the ledger for the rejected payment either
    ledger = client.get(f"/customers/{issued_invoice['customer']['id']}/ledger").json()
    assert [e["entry_type"] for e in ledger] == ["invoice_created"]


def test_partial_then_full_payment_updates_status(client, issued_invoice):
    invoice_id = issued_invoice["invoice"]["id"]

    partial = pay(client, invoice_id, "200.00", provider_reference="txn-1")
    assert partial.status_code == 201
    body = partial.json()
    assert body["payment_attempt"]["status"] == "success"
    assert body["invoice"]["status"] == "partially_paid"
    assert Decimal(body["invoice"]["amount_paid"]) == Decimal("200.00")
    assert Decimal(body["invoice"]["amount_remaining"]) == Decimal("299.00")

    # remaining is now 299.00, so 300.00 is too much
    assert pay(client, invoice_id, "300.00").status_code == 400

    final = pay(client, invoice_id, "299.00", provider_reference="txn-2")
    assert final.status_code == 201
    assert final.json()["invoice"]["status"] == "paid"
    assert Decimal(final.json()["invoice"]["amount_paid"]) == Decimal("499.00")

    # a paid invoice accepts no more payments
    assert pay(client, invoice_id, "1.00").status_code == 409


def test_failed_payment_does_not_increase_amount_paid(client, issued_invoice):
    invoice_id = issued_invoice["invoice"]["id"]
    response = pay(client, invoice_id, "499.00", status="failed", failure_reason="Card declined", provider_reference="txn-f1")
    assert response.status_code == 201
    body = response.json()
    assert body["payment_attempt"]["status"] == "failed"
    assert body["payment_attempt"]["failure_reason"] == "Card declined"
    assert Decimal(body["invoice"]["amount_paid"]) == Decimal("0")
    assert body["invoice"]["status"] == "issued"

    # the customer can still pay afterwards
    assert pay(client, invoice_id, "499.00").json()["invoice"]["status"] == "paid"


def test_payment_currency_must_match_invoice(client, issued_invoice):
    assert pay(client, issued_invoice["invoice"]["id"], "100.00", currency="USD").status_code == 400


def test_duplicate_provider_reference_is_rejected(client, issued_invoice):
    invoice_id = issued_invoice["invoice"]["id"]
    assert pay(client, invoice_id, "100.00", provider_reference="txn-same").status_code == 201
    assert pay(client, invoice_id, "100.00", provider_reference="txn-same").status_code == 409


def test_payment_for_unknown_invoice_and_invalid_amount(client, issued_invoice):
    assert pay(client, 999, "10.00").status_code == 404
    assert pay(client, issued_invoice["invoice"]["id"], "0").status_code == 422
    assert pay(client, issued_invoice["invoice"]["id"], "-5").status_code == 422
