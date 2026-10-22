from fastapi import APIRouter

from .orders import router as orders_router

main_router = APIRouter()

main_router.include_router(orders_router, prefix="/orders", tags=["orders"])
