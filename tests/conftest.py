"""Test fixtures: every test gets a fresh in-memory SQLite database and a TestClient."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (register models on Base.metadata)
from app.db import Base, get_db
from app.main import app


@pytest.fixture
def engine():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
def client(session_factory):
    def override_get_db():  # same commit / rollback behaviour as app.db.get_db
        db = session_factory()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # No `with` block on purpose: it would run the app lifespan and create tables in the real DB.
    yield TestClient(app)
    app.dependency_overrides.clear()


# -- small factories that call the real API --------------------------------------------------
@pytest.fixture
def make_plan(client):
    def _make(name="Pro", price="499.00", billing_cycle="monthly", currency="INR", **extra):
        body = {"name": name, "price": price, "billing_cycle": billing_cycle, "currency": currency, **extra}
        response = client.post("/plans", json=body)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def make_customer(client):
    def _make(email="asha@example.com", name="Asha", company_name="Acme Pvt Ltd"):
        response = client.post("/customers", json={"name": name, "email": email, "company_name": company_name})
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def make_subscription(client):
    def _make(customer_id, plan_id, **extra):
        response = client.post("/subscriptions", json={"customer_id": customer_id, "plan_id": plan_id, **extra})
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def make_invoice(client):
    def _make(subscription_id, **extra):
        response = client.post("/invoices/generate", json={"subscription_id": subscription_id, **extra})
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def issued_invoice(make_plan, make_customer, make_subscription, make_invoice):
    """A customer with an active subscription and one issued invoice of 499.00 INR."""
    plan = make_plan(price="499.00")
    customer = make_customer()
    subscription = make_subscription(customer["id"], plan["id"])
    invoice = make_invoice(subscription["id"])
    return {"plan": plan, "customer": customer, "subscription": subscription, "invoice": invoice}
