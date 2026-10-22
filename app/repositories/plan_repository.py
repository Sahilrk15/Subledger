from typing import List, Optional

from sqlalchemy import select

from app.models.plan import Plan
from app.repositories.base import BaseRepository


class PlanRepository(BaseRepository[Plan]):
    model = Plan

    def list(self, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Plan]:
        stmt = select(Plan).order_by(Plan.id)
        if status:
            stmt = stmt.where(Plan.status == status)
        return list(self.db.scalars(stmt.offset(skip).limit(limit)))
