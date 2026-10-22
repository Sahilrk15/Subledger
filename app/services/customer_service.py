from typing import List

from sqlalchemy.exc import IntegrityError

from app.exceptions import ConflictError, NotFoundError
from app.models.customer import Customer
from app.models.enums import CustomerStatus
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerCreate


class CustomerService:
    """Owns customer rules: unique email, fetching the customer profile."""

    def __init__(self, customer_repo: CustomerRepository):
        self.customer_repo = customer_repo

    def create_customer(self, data: CustomerCreate) -> Customer:
        email = str(data.email).strip().lower()
        if self.customer_repo.get_by_email(email) is not None:
            raise ConflictError(f"A customer with email '{email}' already exists")
        customer = Customer(
            name=data.name,
            email=email,
            company_name=data.company_name,
            status=CustomerStatus.ACTIVE.value,
        )
        try:
            return self.customer_repo.add(customer)
        except IntegrityError:  # lost a race with a concurrent request; the DB constraint caught it
            raise ConflictError(f"A customer with email '{email}' already exists")

    def get_customer(self, customer_id: int) -> Customer:
        customer = self.customer_repo.get(customer_id)
        if customer is None:
            raise NotFoundError(f"Customer {customer_id} not found")
        return customer

    def list_customers(self, skip: int = 0, limit: int = 100) -> List[Customer]:
        return self.customer_repo.list(skip=skip, limit=limit)
