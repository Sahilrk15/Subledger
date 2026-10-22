from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import utcnow
from app.models.enums import SubscriptionStatus


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        # One ACTIVE subscription per (customer, plan). Partial unique index = DB backstop
        # for the duplicate-subscription rule; cancelled/pending rows are not restricted.
        Index(
            "uq_active_subscription_per_customer_plan",
            "customer_id",
            "plan_id",
            unique=True,
            sqlite_where=text("status = 'active'"),
            postgresql_where=text("status = 'active'"),
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default=SubscriptionStatus.ACTIVE.value, index=True)
    start_date = Column(Date, nullable=False)
    current_period_start = Column(Date, nullable=False)
    current_period_end = Column(Date, nullable=False)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)

    customer = relationship("Customer", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    invoices = relationship("Invoice", back_populates="subscription")
