"""Database setup: engine, session factory, declarative Base and the per-request session.

Transaction model (unit of work per request)
--------------------------------------------
Repositories only ``add`` / ``flush``; they never commit. ``get_db`` commits once
when the request finishes successfully and rolls everything back if any
exception escapes. That makes each API call atomic, e.g. recording a payment
updates the invoice, the payment attempt and the ledger together or not at all.
"""
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base()


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Create tables if they do not exist (no migrations in this simplified version)."""
    import app.models  # noqa: F401  (registers all models on Base.metadata)

    Base.metadata.create_all(bind=engine)
