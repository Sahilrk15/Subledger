from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.models.enums import LedgerEntryType
from app.schemas.base import ORMModel


class LedgerEntryOut(ORMModel):
    id: int
    customer_id: int
    invoice_id: int
    entry_type: LedgerEntryType
    amount: Decimal
    currency: str
    reference_id: str
    description: Optional[str]
    created_at: datetime
