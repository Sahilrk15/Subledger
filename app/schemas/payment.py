from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import Field

from app.models.enums import PaymentStatus
from app.schemas.base import ORMModel
from app.schemas.invoice import InvoiceOut


class PaymentRecordRequest(ORMModel):
    invoice_id: int
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    status: PaymentStatus
    provider_reference: Optional[str] = Field(default=None, max_length=100)
    failure_reason: Optional[str] = Field(default=None, max_length=255)  # used when status == 'failed'


class PaymentAttemptOut(ORMModel):
    id: int
    invoice_id: int
    amount: Decimal
    currency: str
    status: PaymentStatus
    provider_reference: Optional[str]
    failure_reason: Optional[str]
    created_at: datetime


class PaymentRecordResponse(ORMModel):
    payment_attempt: PaymentAttemptOut
    invoice: InvoiceOut
