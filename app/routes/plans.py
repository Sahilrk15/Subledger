from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_plan_service
from app.models.enums import PlanStatus
from app.schemas.plan import PlanCreate, PlanOut, PlanUpdate
from app.services.plan_service import PlanService

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.post("", response_model=PlanOut, status_code=201, summary="Create a subscription plan")
def create_plan(payload: PlanCreate, service: PlanService = Depends(get_plan_service)):
    return service.create_plan(payload)


@router.get("", response_model=List[PlanOut], summary="List plans")
def list_plans(
    status: Optional[PlanStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: PlanService = Depends(get_plan_service),
):
    return service.list_plans(status=status.value if status else None, skip=skip, limit=limit)


@router.get("/{plan_id}", response_model=PlanOut, summary="Get one plan")
def get_plan(plan_id: int, service: PlanService = Depends(get_plan_service)):
    return service.get_plan(plan_id)


@router.patch("/{plan_id}", response_model=PlanOut, summary="Update or deactivate a plan")
def update_plan(plan_id: int, payload: PlanUpdate, service: PlanService = Depends(get_plan_service)):
    return service.update_plan(plan_id, payload)
