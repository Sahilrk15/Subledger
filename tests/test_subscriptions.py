"""Rules: inactive plan cannot be subscribed to, no duplicate active subscription, lifecycle."""


def test_cannot_subscribe_to_inactive_plan(client, make_plan, make_customer):
    plan = make_plan()
    customer = make_customer()
    client.patch(f"/plans/{plan['id']}", json={"status": "inactive"})

    response = client.post("/subscriptions", json={"customer_id": customer["id"], "plan_id": plan["id"]})
    assert response.status_code == 400
    assert "inactive plan" in response.json()["detail"]


def test_no_duplicate_active_subscription_to_same_plan(client, make_plan, make_customer, make_subscription):
    plan = make_plan()
    customer = make_customer()
    make_subscription(customer["id"], plan["id"])

    duplicate = client.post("/subscriptions", json={"customer_id": customer["id"], "plan_id": plan["id"]})
    assert duplicate.status_code == 409

    # a different plan is fine, and so is the same plan for another customer
    other_plan = make_plan(name="Other")
    assert client.post("/subscriptions", json={"customer_id": customer["id"], "plan_id": other_plan["id"]}).status_code == 201
    other_customer = make_customer(email="ravi@example.com")
    assert client.post("/subscriptions", json={"customer_id": other_customer["id"], "plan_id": plan["id"]}).status_code == 201


def test_cancel_then_resubscribe_is_allowed(client, make_plan, make_customer, make_subscription):
    plan = make_plan()
    customer = make_customer()
    subscription = make_subscription(customer["id"], plan["id"])

    cancelled = client.patch(f"/subscriptions/{subscription['id']}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["cancelled_at"] is not None
    assert client.patch(f"/subscriptions/{subscription['id']}/cancel").status_code == 409  # already cancelled

    assert client.post("/subscriptions", json={"customer_id": customer["id"], "plan_id": plan["id"]}).status_code == 201


def test_pending_subscription_can_be_activated_once(client, make_plan, make_customer, make_subscription):
    plan = make_plan()
    customer = make_customer()
    pending = make_subscription(customer["id"], plan["id"], activate=False)
    assert pending["status"] == "pending"

    activated = client.patch(f"/subscriptions/{pending['id']}/activate")
    assert activated.status_code == 200
    assert activated.json()["status"] == "active"
    assert client.patch(f"/subscriptions/{pending['id']}/activate").status_code == 409


def test_subscription_period_follows_billing_cycle(client, make_plan, make_customer, make_subscription):
    customer = make_customer()
    monthly = make_subscription(customer["id"], make_plan(name="M", billing_cycle="monthly")["id"], start_date="2026-01-31")
    assert monthly["current_period_end"] == "2026-02-28"  # day clamped to the end of February

    quarterly = make_subscription(customer["id"], make_plan(name="Q", billing_cycle="quarterly")["id"], start_date="2026-01-15")
    assert quarterly["current_period_end"] == "2026-04-15"

    custom = make_subscription(
        customer["id"], make_plan(name="C", billing_cycle="custom", billing_cycle_days=10)["id"], start_date="2026-03-01"
    )
    assert custom["current_period_end"] == "2026-03-11"


def test_unknown_customer_or_plan_returns_404(client, make_plan, make_customer):
    plan = make_plan()
    customer = make_customer()
    assert client.post("/subscriptions", json={"customer_id": 999, "plan_id": plan["id"]}).status_code == 404
    assert client.post("/subscriptions", json={"customer_id": customer["id"], "plan_id": 999}).status_code == 404
    assert client.get("/subscriptions/999").status_code == 404
