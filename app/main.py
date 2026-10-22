from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db import init_db
from app.exceptions import DomainError
from app.routes import customers, invoices, ledger, payments, plans, subscriptions

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # create tables on startup
    yield


app = FastAPI(
    title=f"{settings.app_name} - SaaS Subscription & Billing API",
    description="Simplified billing backend: plans, customers, subscriptions, invoices, payments and an append-only ledger.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


app.include_router(plans.router)
app.include_router(customers.router)
app.include_router(ledger.router)
app.include_router(subscriptions.router)
app.include_router(invoices.router)
app.include_router(payments.router)


@app.get("/health", tags=["Health"], summary="Health check")
def health():
    return {"status": "ok", "service": settings.app_name}
