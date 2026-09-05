from pydantic import BaseModel, Field
from typing import List

class AddCartItemRequest(BaseModel):
    product_id: str
    quantity: int = Field(..., ge=1, description="Quantity must be at least 1")

class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(..., ge=1, description="Quantity must be at least 1")

class CartItemResponse(BaseModel):
    product_id: str
    name: str
    price: float
    image_url: str
    quantity: int
    stock: int
    line_total: float

class CartResponse(BaseModel):
    id: str
    user_id: str
    items: List[CartItemResponse]
    total_amount: float
