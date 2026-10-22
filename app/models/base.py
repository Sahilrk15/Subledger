from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC timestamp (stored without tzinfo so SQLite and PostgreSQL behave the same)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
