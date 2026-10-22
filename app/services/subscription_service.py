from datetime import date, datetime
from typing import List, Optional

from sqlalchemy.exc import IntegrityError

from app.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.base import utcnow
from app.models.enums import CustomerStatus, PlanStatus, SubscriptionStatus
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.repositories.customer_repository import CustomerRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.schemas.subscription import SubscriptionCreate
from app.utils.billing import compute_period_end


class SubscriptionService:
    """Owns subscription lifecycle rules: active plan only, no duplicate active subscription."""

    def __init__(
        self,
        subscription_repo: SubscriptionRepository,
        customer_repo: CustomerRepository,
        plan_repo: PlanRepository,
    ):
        self.subscription_repo = subscription_repo
        self.customer_repo = customer_repo
        self.plan_repo = plan_repo

    def create_subscription(self, data: SubscriptionCreate) -> Subscription:
        customer = self.customer_repo.get(data.customer_id)
        if customer is None:
            raise NotFoundError(f"Customer {data.customer_id} not found")
        if customer.status != CustomerStatus.ACTIVE.value:
            raise BusinessRuleError("Cannot create a subscription for an inactive customer")

        plan = self._get_active_plan(data.plan_id)
        if data.activate:
            self._ensure_no_active_duplicate(customer.id, plan.id)

        start = data.start_date or date.today()
        subscription = Subscription(
            customer_id=customer.id,
            plan_id=plan.id,
            status=SubscriptionStatus.ACTIVE.value if data.activate else SubscriptionStatus.PENDING.value,
            start_date=start,
            current_period_start=start,
            current_period_end=compute_period_end(start, plan.billing_cycle, plan.billing_cycle_days),
        )
        return self._save_new(subscription)

    def activate_subscription(self, subscription_id: int) -> Subscription:
        subscription = self.get_subscription(subscription_id)
        if subscription.status != SubscriptionStatus.PENDING.value:
            raise ConflictError(f"Only a pending subscription can be activated (current status: {subscription.status})")
        plan = self._get_active_plan(subscription.plan_id)
        self._ensure_no_active_duplicate(subscription.customer_id, plan.id)
        subscription.status = SubscriptionStatus.ACTIVE.value
        try:
            return self.subscription_repo.save(subscription)
        except IntegrityError:
            raise ConflictError("Customer already has an active subscription to this plan")

    def cancel_subscription(self, subscription_id: int) -> Subscription:
        subscription = self.get_subscription(subscription_id)
        if subscription.status == SubscriptionStatus.CANCELLED.value:
            raise ConflictError("Subscription is already cancelled")
        subscription.status = SubscriptionStatus.CANCELLED.value
        subscription.cancelled_at = utcnow()
        return self.subscription_repo.save(subscription)

    def get_subscription(self, subscription_id: int) -> Subscription:
        subscription = self.subscription_repo.get(subscription_id)
        if subscription is None:
            raise NotFoundError(f"Subscription {subscription_id} not found")
        return subscription

    def list_subscriptions(
        self,
        customer_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Subscription]:
        return self.subscription_repo.list(customer_id=customer_id, status=status, skip=skip, limit=limit)

    # -- helpers ------------------------------------------------------------------------------

    def _get_active_plan(self, plan_id: int) -> Plan:
        plan = self.plan_repo.get(plan_id)
        if plan is None:
            raise NotFoundError(f"Plan {plan_id} not found")
        if plan.status != PlanStatus.ACTIVE.value:
            raise BusinessRuleError("Cannot subscribe to an inactive plan")
        return plan

    def _ensure_no_active_duplicate(self, customer_id: int, plan_id: int) -> None:
        if self.subscription_repo.get_active_for_customer_and_plan(customer_id, plan_id) is not None:
            raise ConflictError("Customer already has an active subscription to this plan")

    def _save_new(self, subscription: Subscription) -> Subscription:
        try:
            return self.subscription_repo.add(subscription)
        except IntegrityError:  # partial unique index caught a concurrent duplicate
            raise ConflictError("Customer already has an active subscription to this plan")
