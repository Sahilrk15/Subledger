from decimal import Decimal

from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import utcnow
from app.models.enums import InvoiceStatus


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        CheckConstraint("amount_due >= 0", name="ck_invoices_amount_due_non_negative"),
        CheckConstraint("amount_paid >= 0", name="ck_invoices_amount_paid_non_negative"),
        CheckConstraint("amount_paid <= amount_due", name="ck_invoices_not_overpaid"),
        # Added rule: only one invoice per subscription per billing period.
        UniqueConstraint("subscription_id", "period_start", "period_end", name="uq_invoice_subscription_period"),
    )

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    amount_due = Column(Numeric(12, 2), nullable=False)
    amount_paid = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    currency = Column(String(3), nullable=False)
    status = Column(String(20), nullable=False, default=InvoiceStatus.ISSUED.value, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utcnow)

    subscription = relationship("Subscription", back_populates="invoices")
    payment_attempts = relationship("PaymentAttempt", back_populates="invoice")
    ledger_entries = relationship("LedgerEntry", back_populates="invoice")

    @property
    def amount_remaining(self) -> Decimal:
        return Decimal(self.amount_due) - Decimal(self.amount_paid or 0)
