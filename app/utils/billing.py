"""Pure helpers for billing-period maths (no database, easy to unit test)."""
import calendar
from datetime import date, timedelta
from typing import Optional

CYCLE_MONTHS = {"monthly": 1, "quarterly": 3, "yearly": 12}


def add_months(d: date, months: int) -> date:
    """Add calendar months, clamping the day (31 Jan + 1 month = 28/29 Feb)."""
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def compute_period_end(start: date, billing_cycle: str, billing_cycle_days: Optional[int] = None) -> date:
    """End of the billing period that begins on ``start`` (the end date is exclusive).

    monthly / quarterly / yearly use calendar months; 'custom' uses ``billing_cycle_days``.
    """
    if billing_cycle in CYCLE_MONTHS:
        return add_months(start, CYCLE_MONTHS[billing_cycle])
    if billing_cycle == "custom":
        if not billing_cycle_days or billing_cycle_days <= 0:
            raise ValueError("billing_cycle_days must be a positive number for a custom cycle")
        return start + timedelta(days=billing_cycle_days)
    raise ValueError(f"Unknown billing cycle: {billing_cycle}")
