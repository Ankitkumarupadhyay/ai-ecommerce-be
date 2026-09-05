from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from app.models.common import PyObjectId

class ProductModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str
    description: str
    price: float = Field(gt=0, description="Price must be strictly positive")
    currency: str = "usd"
    image_url: str
    stock: int = Field(ge=0, description="Stock cannot be negative")
    category: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
