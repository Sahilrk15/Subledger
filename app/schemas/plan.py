from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import Field, field_validator, model_validator

from app.models.enums import BillingCycle, PlanStatus
from app.schemas.base import ORMModel


def _normalise_currency(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    value = value.strip().upper()
    if len(value) != 3 or not value.isalpha():
        raise ValueError("currency must be a 3-letter code such as INR or USD")
    return value


class PlanCreate(ORMModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    billing_cycle: BillingCycle
    billing_cycle_days: Optional[int] = Field(default=None, gt=0)
    # Rule: price must be greater than 0 (checked here, again in PlanService, and by a DB constraint).
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = "INR"
    status: PlanStatus = PlanStatus.ACTIVE.value

    _currency = field_validator("currency")(_normalise_currency)

    @model_validator(mode="after")
    def _check_cycle(self):
        if self.billing_cycle == BillingCycle.CUSTOM and not self.billing_cycle_days:
            raise ValueError("billing_cycle_days is required when billing_cycle is 'custom'")
        if self.billing_cycle != BillingCycle.CUSTOM and self.billing_cycle_days is not None:
            raise ValueError("billing_cycle_days is only allowed when billing_cycle is 'custom'")
        return self


class PlanUpdate(ORMModel):
    """Partial update. Setting status to 'inactive' deactivates the plan."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    billing_cycle: Optional[BillingCycle] = None
    billing_cycle_days: Optional[int] = Field(default=None, gt=0)
    price: Optional[Decimal] = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: Optional[str] = None
    status: Optional[PlanStatus] = None

    _currency = field_validator("currency")(_normalise_currency)


class PlanOut(ORMModel):
    id: int
    name: str
    description: Optional[str]
    billing_cycle: BillingCycle
    billing_cycle_days: Optional[int]
    price: Decimal
    currency: str
    status: PlanStatus
    created_at: datetime
    updated_at: datetime
