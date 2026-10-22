from fastapi import APIRouter, Depends

from app.dependencies import get_payment_service
from app.schemas.payment import PaymentRecordRequest, PaymentRecordResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/record", response_model=PaymentRecordResponse, status_code=201, summary="Record a payment attempt")
def record_payment(payload: PaymentRecordRequest, service: PaymentService = Depends(get_payment_service)):
    attempt, invoice = service.record_payment(payload)
    return PaymentRecordResponse(payment_attempt=attempt, invoice=invoice)
