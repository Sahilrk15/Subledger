"""Rules: plan price > 0, customer email unique, plan update / deactivate."""
from decimal import Decimal


def test_plan_price_must_be_greater_than_zero(client):
    for bad_price in ("0", "0.00", "-10"):
        response = client.post("/plans", json={"name": "Bad", "price": bad_price, "billing_cycle": "monthly"})
        assert response.status_code == 422, bad_price
    assert client.get("/plans").json() == []


def test_create_and_list_plans(client, make_plan):
    plan = make_plan(name="Starter", price="199.50")
    assert plan["status"] == "active"
    assert Decimal(plan["price"]) == Decimal("199.50")
    listed = client.get("/plans").json()
    assert [p["id"] for p in listed] == [plan["id"]]


def test_custom_billing_cycle_requires_days(client):
    missing = client.post("/plans", json={"name": "X", "price": "10", "billing_cycle": "custom"})
    assert missing.status_code == 422
    ok = client.post(
        "/plans", json={"name": "X", "price": "10", "billing_cycle": "custom", "billing_cycle_days": 14}
    )
    assert ok.status_code == 201
    assert ok.json()["billing_cycle_days"] == 14


def test_patch_plan_price_must_stay_positive_and_can_deactivate(client, make_plan):
    plan = make_plan()
    assert client.patch(f"/plans/{plan['id']}", json={"price": "0"}).status_code == 422

    updated = client.patch(f"/plans/{plan['id']}", json={"price": "599.00"}).json()
    assert Decimal(updated["price"]) == Decimal("599.00")

    deactivated = client.patch(f"/plans/{plan['id']}", json={"status": "inactive"}).json()
    assert deactivated["status"] == "inactive"
    assert [p["id"] for p in client.get("/plans", params={"status": "active"}).json()] == []


def test_customer_email_must_be_unique(client, make_customer):
    make_customer(email="asha@example.com")
    duplicate = client.post("/customers", json={"name": "Other", "email": "asha@example.com"})
    assert duplicate.status_code == 409
    # emails are normalised, so a different casing is still a duplicate
    shouting = client.post("/customers", json={"name": "Other", "email": "ASHA@Example.com"})
    assert shouting.status_code == 409
    assert len(client.get("/customers").json()) == 1


def test_customer_fetch_and_not_found(client, make_customer):
    customer = make_customer()
    assert client.get(f"/customers/{customer['id']}").json()["email"] == "asha@example.com"
    assert client.get("/customers/9999").status_code == 404
