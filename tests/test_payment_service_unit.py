"""Unit tests for PaymentService with in-memory fakes: no database, no HTTP.

They show the payoff of dependency injection and the repository pattern: the business
rules can be tested by handing the service fake repositories.
"""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.exceptions import BusinessRuleError
from app.models.invoice import Invoice
from app.schemas.payment import PaymentRecordRequest
from app.services.invoice_service import InvoiceService
from app.services.payment_service import PaymentService


class FakeInvoiceRepo:
    def __init__(self, invoice):
        self.invoice = invoice

    def get(self, invoice_id):
        return self.invoice if invoice_id == self.invoice.id else None

    def save(self, invoice):
        return invoice


class FakeAttemptRepo:
    def __init__(self):
        self.items = []

    def get_by_provider_reference(self, reference):
        return next((a for a in self.items if a.provider_reference == reference), None)

    def add(self, attempt):
        attempt.id = len(self.items) + 1
        self.items.append(attempt)
        return attempt


class FakeLedgerService:
    def __init__(self):
        self.recorded = []

    def record_payment(self, attempt, invoice):
        self.recorded.append((attempt.status, attempt.amount))


def build_service(amount_due="100.00", amount_paid="0.00", status="issued"):
    invoice = Invoice(
        id=1,
        subscription_id=1,
        customer_id=1,
        amount_due=Decimal(amount_due),
        amount_paid=Decimal(amount_paid),
        currency="INR",
        status=status,
        period_start=date(2026, 1, 1),
        period_end=date(2026, 2, 1),
        due_date=date(2026, 1, 8),
    )
    invoice_repo, attempt_repo, ledger = FakeInvoiceRepo(invoice), FakeAttemptRepo(), FakeLedgerService()
    invoice_service = InvoiceService(SimpleNamespace(), SimpleNamespace(), invoice_repo, ledger)
    service = PaymentService(invoice_repo, attempt_repo, ledger, invoice_service)
    return service, invoice, attempt_repo, ledger


def request(amount, status="success", **extra):
    return PaymentRecordRequest(invoice_id=1, amount=amount, currency="INR", status=status, **extra)


def test_overpayment_is_rejected_and_nothing_is_stored():
    service, invoice, attempts, ledger = build_service(amount_due="100.00", amount_paid="60.00", status="partially_paid")
    with pytest.raises(BusinessRuleError):
        service.record_payment(request("40.01"))
    assert attempts.items == [] and ledger.recorded == []
    assert invoice.amount_paid == Decimal("60.00")


def test_exact_remaining_amount_marks_invoice_paid():
    service, invoice, _, ledger = build_service(amount_due="100.00", amount_paid="60.00", status="partially_paid")
    service.record_payment(request("40.00"))
    assert invoice.status == "paid"
    assert invoice.amount_paid == Decimal("100.00")
    assert ledger.recorded == [("success", Decimal("40.00"))]


def test_failed_payment_is_stored_but_leaves_invoice_unchanged():
    service, invoice, attempts, ledger = build_service()
    attempt, _ = service.record_payment(request("100.00", status="failed", failure_reason="Declined"))
    assert attempt.failure_reason == "Declined"
    assert invoice.amount_paid == Decimal("0.00") and invoice.status == "issued"
    assert ledger.recorded == [("failed", Decimal("100.00"))]
