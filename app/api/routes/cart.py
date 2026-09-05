from fastapi import APIRouter, Depends, status
from app.core.dependencies import require_customer
from app.models.user import UserModel
from app.schemas.cart import CartResponse, AddCartItemRequest, UpdateCartItemRequest
from app.services.cart_service import cart_service

router = APIRouter(prefix="/cart", tags=["Cart"])

@router.get("", response_model=CartResponse)
async def get_cart(current_user: UserModel = Depends(require_customer)):
    """
    Get the authenticated user's current shopping cart.
    """
    return await cart_service.get_user_cart(current_user.id)

@router.post("/items", response_model=CartResponse)
async def add_item_to_cart(
    item_in: AddCartItemRequest,
    current_user: UserModel = Depends(require_customer)
):
    """
    Add a product to the user's shopping cart.
    """
    return await cart_service.add_item_to_cart(current_user.id, item_in)

@router.put("/items/{product_id}", response_model=CartResponse)
async def update_cart_item(
    product_id: str,
    item_in: UpdateCartItemRequest,
    current_user: UserModel = Depends(require_customer)
):
    """
    Update quantity for a product in the user's shopping cart.
    """
    return await cart_service.update_item_quantity(current_user.id, product_id, item_in)

@router.delete("/items/{product_id}", response_model=CartResponse)
async def remove_cart_item(
    product_id: str,
    current_user: UserModel = Depends(require_customer)
):
    """
    Remove a product from the user's shopping cart.
    """
    return await cart_service.remove_item_from_cart(current_user.id, product_id)
