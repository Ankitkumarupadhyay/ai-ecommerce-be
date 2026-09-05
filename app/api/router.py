from fastapi import APIRouter
from app.api.routes import auth, products, cart, orders, payments, admin, ai

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(products.router)
api_router.include_router(cart.router)
api_router.include_router(orders.router)
api_router.include_router(payments.router)
api_router.include_router(admin.router)
api_router.include_router(ai.router)
