from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_subscription_service
from app.models.enums import SubscriptionStatus
from app.schemas.subscription import SubscriptionCreate, SubscriptionOut
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.post("", response_model=SubscriptionOut, status_code=201, summary="Create a subscription")
def create_subscription(
    payload: SubscriptionCreate, service: SubscriptionService = Depends(get_subscription_service)
):
    return service.create_subscription(payload)


@router.get("", response_model=List[SubscriptionOut], summary="List subscriptions")
def list_subscriptions(
    customer_id: Optional[int] = None,
    status: Optional[SubscriptionStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: SubscriptionService = Depends(get_subscription_service),
):
    return service.list_subscriptions(
        customer_id=customer_id, status=status.value if status else None, skip=skip, limit=limit
    )


@router.get("/{subscription_id}", response_model=SubscriptionOut, summary="Fetch one subscription")
def get_subscription(subscription_id: int, service: SubscriptionService = Depends(get_subscription_service)):
    return service.get_subscription(subscription_id)


@router.patch("/{subscription_id}/activate", response_model=SubscriptionOut, summary="Activate a pending subscription")
def activate_subscription(subscription_id: int, service: SubscriptionService = Depends(get_subscription_service)):
    return service.activate_subscription(subscription_id)


@router.patch("/{subscription_id}/cancel", response_model=SubscriptionOut, summary="Cancel a subscription")
def cancel_subscription(subscription_id: int, service: SubscriptionService = Depends(get_subscription_service)):
    return service.cancel_subscription(subscription_id)
