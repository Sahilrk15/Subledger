from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, event
from sqlalchemy.orm import relationship

from app.db import Base
from app.exceptions import LedgerImmutableError
from app.models.base import utcnow


class LedgerEntry(Base):
    """One row per billing event. Append-only: it can be inserted and read, never changed."""

    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False, index=True)
    entry_type = Column(String(30), nullable=False, index=True)  # invoice_created | payment_success | payment_failure
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    # Traceability key, e.g. "INV-12" for an invoice or "PAY-7" for a payment attempt.
    reference_id = Column(String(50), nullable=False, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)

    customer = relationship("Customer", back_populates="ledger_entries")
    invoice = relationship("Invoice", back_populates="ledger_entries")


@event.listens_for(LedgerEntry, "before_update")
def _block_ledger_update(mapper, connection, target):
    raise LedgerImmutableError("Ledger entries are append-only and cannot be updated")


@event.listens_for(LedgerEntry, "before_delete")
def _block_ledger_delete(mapper, connection, target):
    raise LedgerImmutableError("Ledger entries are append-only and cannot be deleted")
