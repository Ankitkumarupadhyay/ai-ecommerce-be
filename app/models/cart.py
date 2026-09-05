from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.common import PyObjectId

class CartItemModel(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, description="Quantity must be at least 1")

class CartModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: str
    items: List[CartItemModel] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
