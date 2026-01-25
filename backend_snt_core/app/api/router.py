from fastapi import APIRouter

from app.api.routers import (
    charge_items,
    documents_accruals,
    documents_payments,
    owners,
    plots,
    reports,
    snts,
)

api_router = APIRouter()

api_router.include_router(snts.router, tags=["snt"])
api_router.include_router(plots.router, tags=["plots"])
api_router.include_router(owners.router, tags=["owners"])
api_router.include_router(charge_items.router, tags=["charge_items"])
api_router.include_router(documents_accruals.router, tags=["doc_accrual"])
api_router.include_router(documents_payments.router, tags=["doc_payment"])
api_router.include_router(reports.router, tags=["reports"])

