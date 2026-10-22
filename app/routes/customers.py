from typing import List

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_customer_service
from app.schemas.customer import CustomerCreate, CustomerOut
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("", response_model=CustomerOut, status_code=201, summary="Create a customer")
def create_customer(payload: CustomerCreate, service: CustomerService = Depends(get_customer_service)):
    return service.create_customer(payload)


@router.get("", response_model=List[CustomerOut], summary="List customers")
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: CustomerService = Depends(get_customer_service),
):
    return service.list_customers(skip=skip, limit=limit)


@router.get("/{customer_id}", response_model=CustomerOut, summary="Fetch customer details")
def get_customer(customer_id: int, service: CustomerService = Depends(get_customer_service)):
    return service.get_customer(customer_id)
