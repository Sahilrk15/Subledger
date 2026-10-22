from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from app.models.enums import InvoiceStatus
from app.schemas.base import ORMModel


class InvoiceGenerateRequest(ORMModel):
    subscription_id: int
    # Optional billing period; if omitted the subscription's current period is used.
    # Provide both or neither.
    period_start: Optional[date] = None
    period_end: Optional[date] = None


class InvoiceOut(ORMModel):
    id: int
    subscription_id: int
    customer_id: int
    amount_due: Decimal
    amount_paid: Decimal
    amount_remaining: Decimal
    currency: str
    status: InvoiceStatus
    period_start: date
    period_end: date
    due_date: date
    created_at: datetime
