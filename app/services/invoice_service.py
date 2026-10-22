from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.exc import IntegrityError

from app.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.enums import InvoiceStatus, SubscriptionStatus
from app.models.invoice import Invoice
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.schemas.invoice import InvoiceGenerateRequest
from app.services.ledger_service import LedgerService


class InvoiceService:
    """Owns invoice rules: generate for active subscriptions, amount_due from the plan price at
    generation time, and invoice status transitions after a successful payment."""

    def __init__(
        self,
        subscription_repo: SubscriptionRepository,
        plan_repo: PlanRepository,
        invoice_repo: InvoiceRepository,
        ledger_service: LedgerService,
        invoice_due_days: int = 7,
    ):
        self.subscription_repo = subscription_repo
        self.plan_repo = plan_repo
        self.invoice_repo = invoice_repo
        self.ledger_service = ledger_service
        self.invoice_due_days = invoice_due_days

    def generate_invoice(self, data: InvoiceGenerateRequest) -> Invoice:
        subscription = self.subscription_repo.get(data.subscription_id)
        if subscription is None:
            raise NotFoundError(f"Subscription {data.subscription_id} not found")
        if subscription.status != SubscriptionStatus.ACTIVE.value:
            raise BusinessRuleError("Invoices can only be generated for active subscriptions")

        plan = self.plan_repo.get(subscription.plan_id)
        if plan is None:  # should be impossible (foreign key) but keep the service honest
            raise NotFoundError(f"Plan {subscription.plan_id} not found")

        period_start, period_end = self._resolve_period(data, subscription)
        if self.invoice_repo.get_by_subscription_and_period(subscription.id, period_start, period_end):
            raise ConflictError("An invoice already exists for this subscription and billing period")

        invoice = Invoice(
            subscription_id=subscription.id,
            customer_id=subscription.customer_id,
            amount_due=plan.price,  # snapshot of the plan price at generation time
            amount_paid=Decimal("0.00"),
            currency=plan.currency,
            status=InvoiceStatus.ISSUED.value,
            period_start=period_start,
            period_end=period_end,
            due_date=date.today() + timedelta(days=self.invoice_due_days),
        )
        try:
            invoice = self.invoice_repo.add(invoice)
        except IntegrityError:
            raise ConflictError("An invoice already exists for this subscription and billing period")

        self.ledger_service.record_invoice_created(invoice)
        return invoice

    def get_invoice(self, invoice_id: int) -> Invoice:
        invoice = self.invoice_repo.get(invoice_id)
        if invoice is None:
            raise NotFoundError(f"Invoice {invoice_id} not found")
        return invoice

    def apply_successful_payment(self, invoice: Invoice, amount: Decimal) -> Invoice:
        """Add a successful payment to the invoice and move its status.

        Only ever called by PaymentService after it has validated the amount.
        """
        invoice.amount_paid = Decimal(invoice.amount_paid) + Decimal(amount)
        if Decimal(invoice.amount_paid) == Decimal(invoice.amount_due):
            invoice.status = InvoiceStatus.PAID.value
        else:
            invoice.status = InvoiceStatus.PARTIALLY_PAID.value
        return self.invoice_repo.save(invoice)

    @staticmethod
    def _resolve_period(data: InvoiceGenerateRequest, subscription):
        if (data.period_start is None) != (data.period_end is None):
            raise BusinessRuleError("Provide both period_start and period_end, or neither")
        if data.period_start is None:
            return subscription.current_period_start, subscription.current_period_end
        if data.period_end <= data.period_start:
            raise BusinessRuleError("period_end must be after period_start")
        return data.period_start, data.period_end
