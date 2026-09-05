from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from app.core.dependencies import require_admin
from app.models.user import UserModel
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.schemas.order import OrderResponse, UpdateOrderStatusRequest
from app.services.product_service import product_service
from app.services.order_service import order_service

router = APIRouter(prefix="/admin", tags=["Admin"])

# Admin Product Management
@router.get("/products", response_model=List[ProductResponse])
async def admin_list_products(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    admin: UserModel = Depends(require_admin)
):
    """
    Admin endpoint to view all products (including inactive ones).
    """
    return await product_service.get_products(search=search, category=category, include_inactive=True)

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_product(
    product_in: ProductCreate,
    admin: UserModel = Depends(require_admin)
):
    """
    Admin endpoint to create a new product.
    """
    return await product_service.create_product(product_in)

@router.put("/products/{product_id}", response_model=ProductResponse)
async def admin_update_product(
    product_id: str,
    product_in: ProductUpdate,
    admin: UserModel = Depends(require_admin)
):
    """
    Admin endpoint to update product details or stock.
    """
    updated = await product_service.update_product(product_id, product_in)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return updated

@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_product(
    product_id: str,
    admin: UserModel = Depends(require_admin)
):
    """
    Admin endpoint to delete a product.
    """
    deleted = await product_service.delete_product(product_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return None

# Admin Order Management
@router.get("/orders", response_model=List[OrderResponse])
async def admin_list_orders(admin: UserModel = Depends(require_admin)):
    """
    Admin endpoint to view all customer orders across the platform.
    """
    return await order_service.get_all_orders_admin()

@router.get("/orders/{order_id}", response_model=OrderResponse)
async def admin_get_order(order_id: str, admin: UserModel = Depends(require_admin)):
    """
    Admin endpoint to view details for any order.
    """
    order = await order_service.get_order_by_id_admin(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order

@router.put("/orders/{order_id}/status", response_model=OrderResponse)
async def admin_update_order_status(
    order_id: str,
    status_in: UpdateOrderStatusRequest,
    admin: UserModel = Depends(require_admin)
):
    """
    Admin endpoint to update an order's status (e.g., confirmed, shipped, delivered).
    """
    updated_order = await order_service.update_order_status_admin(order_id, status_in.order_status)
    if not updated_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return updated_order
