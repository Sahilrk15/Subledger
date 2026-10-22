from datetime import date

import pytest

from app.utils.billing import add_months, compute_period_end


def test_add_months_clamps_to_end_of_month():
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2028, 1, 31), 1) == date(2028, 2, 29)  # leap year
    assert add_months(date(2026, 11, 15), 3) == date(2027, 2, 15)  # crosses the year end


@pytest.mark.parametrize(
    "cycle, days, expected",
    [
        ("monthly", None, date(2026, 2, 10)),
        ("quarterly", None, date(2026, 4, 10)),
        ("yearly", None, date(2027, 1, 10)),
        ("custom", 45, date(2026, 2, 24)),
    ],
)
def test_compute_period_end(cycle, days, expected):
    assert compute_period_end(date(2026, 1, 10), cycle, days) == expected


def test_custom_cycle_needs_positive_days_and_unknown_cycle_fails():
    with pytest.raises(ValueError):
        compute_period_end(date(2026, 1, 1), "custom", None)
    with pytest.raises(ValueError):
        compute_period_end(date(2026, 1, 1), "weekly")
