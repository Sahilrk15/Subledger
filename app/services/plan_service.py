from decimal import Decimal
from typing import List, Optional

from app.exceptions import BusinessRuleError, NotFoundError
from app.models.enums import BillingCycle, PlanStatus, enum_value
from app.models.plan import Plan
from app.repositories.plan_repository import PlanRepository
from app.schemas.plan import PlanCreate, PlanUpdate


class PlanService:
    """Owns plan rules: price > 0, valid billing cycle, plan status changes."""

    def __init__(self, plan_repo: PlanRepository):
        self.plan_repo = plan_repo

    def create_plan(self, data: PlanCreate) -> Plan:
        self._validate_price(data.price)
        self._validate_cycle(data.billing_cycle, data.billing_cycle_days)
        plan = Plan(
            name=data.name,
            description=data.description,
            billing_cycle=enum_value(data.billing_cycle),
            billing_cycle_days=data.billing_cycle_days,
            price=data.price,
            currency=data.currency,
            status=enum_value(data.status),
        )
        return self.plan_repo.add(plan)

    def get_plan(self, plan_id: int) -> Plan:
        plan = self.plan_repo.get(plan_id)
        if plan is None:
            raise NotFoundError(f"Plan {plan_id} not found")
        return plan

    def list_plans(self, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Plan]:
        return self.plan_repo.list(status=status, skip=skip, limit=limit)

    def update_plan(self, plan_id: int, data: PlanUpdate) -> Plan:
        plan = self.get_plan(plan_id)
        # Ignore explicit nulls: every column except description is NOT NULL.
        changes = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None or k == "description"}

        if "price" in changes:
            self._validate_price(changes["price"])

        new_cycle = changes.get("billing_cycle", plan.billing_cycle)
        if "billing_cycle" in changes and enum_value(new_cycle) != BillingCycle.CUSTOM.value:
            changes.setdefault("billing_cycle_days", None)  # leaving 'custom' clears the day count
        new_days = changes.get("billing_cycle_days", plan.billing_cycle_days)
        self._validate_cycle(new_cycle, new_days)

        for field, value in changes.items():
            setattr(plan, field, enum_value(value))
        return self.plan_repo.save(plan)

    def deactivate_plan(self, plan_id: int) -> Plan:
        plan = self.get_plan(plan_id)
        plan.status = PlanStatus.INACTIVE.value
        return self.plan_repo.save(plan)

    @staticmethod
    def _validate_price(price) -> None:
        if price is None or Decimal(price) <= 0:
            raise BusinessRuleError("Plan price must be greater than 0")

    @staticmethod
    def _validate_cycle(billing_cycle, billing_cycle_days) -> None:
        cycle = enum_value(billing_cycle)
        if cycle == BillingCycle.CUSTOM.value:
            if not billing_cycle_days or billing_cycle_days <= 0:
                raise BusinessRuleError("billing_cycle_days is required for a custom billing cycle")
        elif billing_cycle_days is not None:
            raise BusinessRuleError("billing_cycle_days is only allowed for a custom billing cycle")
