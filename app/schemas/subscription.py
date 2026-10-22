from datetime import date, datetime
from typing import Optional

from app.models.enums import SubscriptionStatus
from app.schemas.base import ORMModel


class SubscriptionCreate(ORMModel):
    customer_id: int
    plan_id: int
    start_date: Optional[date] = None  # defaults to today
    activate: bool = True  # False creates a 'pending' subscription to be activated later


class SubscriptionOut(ORMModel):
    id: int
    customer_id: int
    plan_id: int
    status: SubscriptionStatus
    start_date: date
    current_period_start: date
    current_period_end: date
    cancelled_at: Optional[datetime]
    created_at: datetime
