from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.core.dependencies import require_customer
from app.models.user import UserModel
from app.schemas.order import OrderResponse
from app.services.order_service import order_service

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/create-from-cart", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order_from_cart(current_user: UserModel = Depends(require_customer)):
    """
    Create a new order from the user's active cart. Backend snapshots prices and calculates totals.
    """
    return await order_service.create_order_from_cart(current_user.id)

@router.get("", response_model=List[OrderResponse])
async def get_my_orders(current_user: UserModel = Depends(require_customer)):
    """
    Retrieve all orders placed by the authenticated customer.
    """
    return await order_service.get_user_orders(current_user.id)

@router.get("/{order_id}", response_model=OrderResponse)
async def get_my_order_details(
    order_id: str,
    current_user: UserModel = Depends(require_customer)
):
    """
    Retrieve details for a specific order. Enforces user ownership.
    """
    order = await order_service.get_order_by_id_for_user(order_id, current_user.id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or access denied"
        )
    return order
