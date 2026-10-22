from decimal import Decimal
from typing import List, Optional

from app.exceptions import NotFoundError
from app.models.enums import LedgerEntryType, PaymentStatus
from app.models.invoice import Invoice
from app.models.ledger_entry import LedgerEntry
from app.models.payment_attempt import PaymentAttempt
from app.repositories.customer_repository import CustomerRepository
from app.repositories.ledger_repository import LedgerRepository


class LedgerService:
    """Creates append-only ledger entries and reads a customer's ledger history.

    reference_id convention (makes every entry traceable to its source row):
      invoice_created  -> "INV-<invoice id>"
      payment_success  -> "PAY-<payment attempt id>"
      payment_failure  -> "PAY-<payment attempt id>"
    """

    def __init__(self, ledger_repo: LedgerRepository, customer_repo: CustomerRepository):
        self.ledger_repo = ledger_repo
        self.customer_repo = customer_repo

    def record_invoice_created(self, invoice: Invoice) -> LedgerEntry:
        entry = LedgerEntry(
            customer_id=invoice.customer_id,
            invoice_id=invoice.id,
            entry_type=LedgerEntryType.INVOICE_CREATED.value,
            amount=Decimal(invoice.amount_due),
            currency=invoice.currency,
            reference_id=f"INV-{invoice.id}",
            description=f"Invoice {invoice.id} issued for {invoice.period_start} to {invoice.period_end}",
        )
        return self.ledger_repo.add(entry)

    def record_payment(self, attempt: PaymentAttempt, invoice: Invoice) -> LedgerEntry:
        succeeded = attempt.status == PaymentStatus.SUCCESS.value
        entry_type = LedgerEntryType.PAYMENT_SUCCESS if succeeded else LedgerEntryType.PAYMENT_FAILURE
        if succeeded:
            description = f"Payment of {attempt.amount} received for invoice {invoice.id}"
        else:
            description = f"Payment of {attempt.amount} failed for invoice {invoice.id}: {attempt.failure_reason}"
        entry = LedgerEntry(
            customer_id=invoice.customer_id,
            invoice_id=invoice.id,
            entry_type=entry_type.value,
            amount=Decimal(attempt.amount),
            currency=attempt.currency,
            reference_id=f"PAY-{attempt.id}",
            description=description,
        )
        return self.ledger_repo.add(entry)

    def get_customer_ledger(
        self,
        customer_id: int,
        entry_type: Optional[str] = None,
        invoice_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[LedgerEntry]:
        if self.customer_repo.get(customer_id) is None:
            raise NotFoundError(f"Customer {customer_id} not found")
        return self.ledger_repo.list_by_customer(
            customer_id, entry_type=entry_type, invoice_id=invoice_id, skip=skip, limit=limit
        )
