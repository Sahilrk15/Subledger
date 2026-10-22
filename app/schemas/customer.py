from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field

from app.models.enums import CustomerStatus
from app.schemas.base import ORMModel


class CustomerCreate(ORMModel):
    name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    company_name: Optional[str] = Field(default=None, max_length=150)


class CustomerOut(ORMModel):
    id: int
    name: str
    email: str
    company_name: Optional[str]
    status: CustomerStatus
    created_at: datetime
