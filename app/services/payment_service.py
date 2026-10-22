from decimal import Decimal
from typing import Optional, Tuple

from sqlalchemy.exc import IntegrityError

from app.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.enums import InvoiceStatus, PaymentStatus, enum_value
from app.models.invoice import Invoice
from app.models.payment_attempt import PaymentAttempt
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.payment_attempt_repository import PaymentAttemptRepository
from app.schemas.payment import PaymentRecordRequest
from app.services.invoice_service import InvoiceService
from app.services.ledger_service import LedgerService

PAYABLE_STATUSES = {
    InvoiceStatus.ISSUED.value,
    InvoiceStatus.PARTIALLY_PAID.value,
    InvoiceStatus.OVERDUE.value,
}


class PaymentService:
    """Owns payment rules: valid amount, no overpayment, failed payments never touch amount_paid.

    Compared with the assignment skeleton it also receives InvoiceService, because the
    ownership table says InvoiceService updates the invoice status after a payment.
    """

    def __init__(
        self,
        invoice_repo: InvoiceRepository,
        payment_attempt_repo: PaymentAttemptRepository,
        ledger_service: LedgerService,
        invoice_service: InvoiceService,
    ):
        self.invoice_repo = invoice_repo
        self.payment_attempt_repo = payment_attempt_repo
        self.ledger_service = ledger_service
        self.invoice_service = invoice_service

    def record_payment(self, data: PaymentRecordRequest) -> Tuple[PaymentAttempt, Invoice]:
        invoice = self.invoice_repo.get(data.invoice_id)
        if invoice is None:
            raise NotFoundError(f"Invoice {data.invoice_id} not found")

        amount = Decimal(data.amount)
        if amount <= 0:
            raise BusinessRuleError("Payment amount must be greater than 0")
        if data.currency.strip().upper() != invoice.currency:
            raise BusinessRuleError(f"Payment currency must match the invoice currency ({invoice.currency})")
        if invoice.status not in PAYABLE_STATUSES:
            raise ConflictError(f"Invoice is '{invoice.status}' and cannot accept payments")
        if data.provider_reference and self.payment_attempt_repo.get_by_provider_reference(data.provider_reference):
            raise ConflictError("A payment with this provider_reference has already been recorded")

        succeeded = enum_value(data.status) == PaymentStatus.SUCCESS.value
        if succeeded and amount > invoice.amount_remaining:
            raise BusinessRuleError(
                f"Payment of {amount} exceeds the remaining unpaid amount of {invoice.amount_remaining}"
            )

        attempt = PaymentAttempt(
            invoice_id=invoice.id,
            amount=amount,
            currency=invoice.currency,
            status=enum_value(data.status),
            provider_reference=data.provider_reference,
            failure_reason=None if succeeded else (data.failure_reason or "Payment failed"),
        )
        try:
            attempt = self.payment_attempt_repo.add(attempt)
        except IntegrityError:
            raise ConflictError("A payment with this provider_reference has already been recorded")

        if succeeded:
            self.invoice_service.apply_successful_payment(invoice, amount)
        # A failed attempt is stored and logged but deliberately leaves the invoice untouched.

        self.ledger_service.record_payment(attempt, invoice)
        return attempt, invoice
