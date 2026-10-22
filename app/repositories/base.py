from typing import Generic, Optional, TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Shared persistence helpers. Repositories flush but never commit (see app/db.py)."""

    model: type

    def __init__(self, db: Session):
        self.db = db

    def add(self, obj: T) -> T:
        self.db.add(obj)
        self.db.flush()  # assigns the primary key and surfaces constraint violations early
        return obj

    def get(self, obj_id: int) -> Optional[T]:
        return self.db.get(self.model, obj_id)

    def save(self, obj: T) -> T:
        self.db.add(obj)
        self.db.flush()
        return obj
