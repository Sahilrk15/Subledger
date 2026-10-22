from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_ledger_service
from app.models.enums import LedgerEntryType
from app.schemas.ledger import LedgerEntryOut
from app.services.ledger_service import LedgerService

router = APIRouter(prefix="/customers", tags=["Ledger"])


@router.get("/{customer_id}/ledger", response_model=List[LedgerEntryOut], summary="Fetch customer ledger history")
def get_customer_ledger(
    customer_id: int,
    entry_type: Optional[LedgerEntryType] = None,
    invoice_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: LedgerService = Depends(get_ledger_service),
):
    return service.get_customer_ledger(
        customer_id,
        entry_type=entry_type.value if entry_type else None,
        invoice_id=invoice_id,
        skip=skip,
        limit=limit,
    )
