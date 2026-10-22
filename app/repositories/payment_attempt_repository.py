from typing import List, Optional

from sqlalchemy import select

from app.models.payment_attempt import PaymentAttempt
from app.repositories.base import BaseRepository


class PaymentAttemptRepository(BaseRepository[PaymentAttempt]):
    model = PaymentAttempt

    def get_by_provider_reference(self, provider_reference: str) -> Optional[PaymentAttempt]:
        return self.db.scalar(select(PaymentAttempt).where(PaymentAttempt.provider_reference == provider_reference))

    def list_by_invoice(self, invoice_id: int) -> List[PaymentAttempt]:
        stmt = select(PaymentAttempt).where(PaymentAttempt.invoice_id == invoice_id).order_by(PaymentAttempt.id)
        return list(self.db.scalars(stmt))
