from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from app.schemas.product import ProductResponse
from app.services.product_service import product_service

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("", response_model=List[ProductResponse])
async def list_products(
    search: Optional[str] = Query(None, description="Search by name, description, or category"),
    category: Optional[str] = Query(None, description="Filter by category name")
):
    """
    Retrieve active customer-facing products with optional search and category filters.
    """
    return await product_service.get_products(search=search, category=category, include_inactive=False)

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product_details(product_id: str):
    """
    Get detailed product information for a given product_id.
    """
    product = await product_service.get_product_by_id(product_id, include_inactive=False)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product
