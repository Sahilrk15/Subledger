from typing import List, Optional

from sqlalchemy import select

from app.models.customer import Customer
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    model = Customer

    def get_by_email(self, email: str) -> Optional[Customer]:
        return self.db.scalar(select(Customer).where(Customer.email == email))

    def list(self, skip: int = 0, limit: int = 100) -> List[Customer]:
        stmt = select(Customer).order_by(Customer.id).offset(skip).limit(limit)
        return list(self.db.scalars(stmt))
