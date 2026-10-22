from fastapi import APIRouter, Depends

from app.dependencies import get_invoice_service
from app.schemas.invoice import InvoiceGenerateRequest, InvoiceOut
from app.services.invoice_service import InvoiceService

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.post("/generate", response_model=InvoiceOut, status_code=201, summary="Generate an invoice for a subscription")
def generate_invoice(payload: InvoiceGenerateRequest, service: InvoiceService = Depends(get_invoice_service)):
    return service.generate_invoice(payload)


@router.get("/{invoice_id}", response_model=InvoiceOut, summary="Fetch invoice details")
def get_invoice(invoice_id: int, service: InvoiceService = Depends(get_invoice_service)):
    return service.get_invoice(invoice_id)
