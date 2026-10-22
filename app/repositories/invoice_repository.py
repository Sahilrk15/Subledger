from datetime import date
from typing import Optional

from sqlalchemy import select

from app.models.invoice import Invoice
from app.repositories.base import BaseRepository


class InvoiceRepository(BaseRepository[Invoice]):
    model = Invoice

    def get_by_subscription_and_period(
        self, subscription_id: int, period_start: date, period_end: date
    ) -> Optional[Invoice]:
        stmt = select(Invoice).where(
            Invoice.subscription_id == subscription_id,
            Invoice.period_start == period_start,
            Invoice.period_end == period_end,
        )
        return self.db.scalar(stmt)
