from sqlalchemy import CheckConstraint, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import utcnow
from app.models.enums import PlanStatus


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (
        # Business rule "plan price > 0", enforced again at the database level.
        CheckConstraint("price > 0", name="ck_plans_price_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    billing_cycle = Column(String(20), nullable=False)  # monthly | quarterly | yearly | custom
    # Added field: length of a 'custom' cycle in days (NULL for the standard cycles).
    billing_cycle_days = Column(Integer, nullable=True)
    price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    status = Column(String(20), nullable=False, default=PlanStatus.ACTIVE.value, index=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    updated_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    subscriptions = relationship("Subscription", back_populates="plan")
