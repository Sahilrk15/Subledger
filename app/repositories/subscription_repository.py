from typing import List, Optional

from sqlalchemy import select

from app.models.enums import SubscriptionStatus
from app.models.subscription import Subscription
from app.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    model = Subscription

    def get_active_for_customer_and_plan(self, customer_id: int, plan_id: int) -> Optional[Subscription]:
        stmt = select(Subscription).where(
            Subscription.customer_id == customer_id,
            Subscription.plan_id == plan_id,
            Subscription.status == SubscriptionStatus.ACTIVE.value,
        )
        return self.db.scalar(stmt)

    def list(
        self,
        customer_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Subscription]:
        stmt = select(Subscription).order_by(Subscription.id)
        if customer_id is not None:
            stmt = stmt.where(Subscription.customer_id == customer_id)
        if status:
            stmt = stmt.where(Subscription.status == status)
        return list(self.db.scalars(stmt.offset(skip).limit(limit)))
