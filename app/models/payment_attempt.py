from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import utcnow


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"
    __table_args__ = (CheckConstraint("amount > 0", name="ck_payment_attempts_amount_positive"),)

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(String(20), nullable=False)  # success | failed
    # Unique when present: protects against the same provider transaction being recorded twice.
    provider_reference = Column(String(100), nullable=True, unique=True)
    failure_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)

    invoice = relationship("Invoice", back_populates="payment_attempts")
