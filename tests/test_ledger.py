"""Rules: ledger entries are append-only and traceable through reference_id."""
from decimal import Decimal

import pytest

from app.exceptions import LedgerImmutableError
from app.models.ledger_entry import LedgerEntry


def pay(client, invoice_id, amount, status="success", **extra):
    return client.post(
        "/payments/record",
        json={"invoice_id": invoice_id, "amount": amount, "currency": "INR", "status": status, **extra},
    )


def test_ledger_records_every_event_with_traceable_reference_ids(client, issued_invoice):
    invoice_id = issued_invoice["invoice"]["id"]
    customer_id = issued_invoice["customer"]["id"]

    failed = pay(client, invoice_id, "499.00", status="failed", failure_reason="Bank timeout").json()
    success = pay(client, invoice_id, "499.00").json()

    ledger = client.get(f"/customers/{customer_id}/ledger").json()
    assert [e["entry_type"] for e in ledger] == ["invoice_created", "payment_failure", "payment_success"]
    assert [e["reference_id"] for e in ledger] == [
        f"INV-{invoice_id}",
        f"PAY-{failed['payment_attempt']['id']}",
        f"PAY-{success['payment_attempt']['id']}",
    ]
    assert all(e["invoice_id"] == invoice_id and e["customer_id"] == customer_id for e in ledger)
    assert all(Decimal(e["amount"]) == Decimal("499.00") for e in ledger)
    assert "Bank timeout" in ledger[1]["description"]


def test_ledger_can_be_filtered_by_type(client, issued_invoice):
    invoice_id = issued_invoice["invoice"]["id"]
    customer_id = issued_invoice["customer"]["id"]
    pay(client, invoice_id, "100.00")
    only_payments = client.get(f"/customers/{customer_id}/ledger", params={"entry_type": "payment_success"}).json()
    assert [e["entry_type"] for e in only_payments] == ["payment_success"]


def test_ledger_is_per_customer_and_404_for_unknown_customer(client, issued_invoice, make_customer):
    other = make_customer(email="other@example.com")
    assert client.get(f"/customers/{other['id']}/ledger").json() == []
    assert client.get("/customers/9999/ledger").status_code == 404


def test_ledger_entries_cannot_be_updated_or_deleted(client, issued_invoice, session_factory):
    with session_factory() as db:
        entry = db.query(LedgerEntry).first()

        entry.description = "tampered"
        with pytest.raises(LedgerImmutableError):
            db.flush()
        db.rollback()

        entry = db.query(LedgerEntry).first()
        db.delete(entry)
        with pytest.raises(LedgerImmutableError):
            db.flush()
        db.rollback()

        assert db.query(LedgerEntry).count() == 1
        assert db.query(LedgerEntry).first().description != "tampered"


def test_failed_request_rolls_back_everything(client, issued_invoice):
    """Atomicity: a rejected payment leaves no payment attempt and no ledger entry behind."""
    invoice_id = issued_invoice["invoice"]["id"]
    customer_id = issued_invoice["customer"]["id"]
    assert pay(client, invoice_id, "1000.00").status_code == 400
    ledger = client.get(f"/customers/{customer_id}/ledger").json()
    assert len(ledger) == 1 and ledger[0]["entry_type"] == "invoice_created"
