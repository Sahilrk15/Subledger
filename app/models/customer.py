from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import utcnow
from app.models.enums import CustomerStatus


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    # Unique constraint = database-level backstop for the "email must be unique" rule.
    email = Column(String(254), nullable=False, unique=True, index=True)
    company_name = Column(String(150), nullable=True)
    status = Column(String(20), nullable=False, default=CustomerStatus.ACTIVE.value)
    created_at = Column(DateTime, nullable=False, default=utcnow)

    subscriptions = relationship("Subscription", back_populates="customer")
    ledger_entries = relationship("LedgerEntry", back_populates="customer")
