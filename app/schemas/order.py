from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.order import PaymentStatus, OrderStatus

class OrderItemResponse(BaseModel):
    product_id: str
    product_name: str
    price: float
    quantity: int

class OrderResponse(BaseModel):
    id: str
    user_id: str
    items: List[OrderItemResponse]
    subtotal: float
    total: float
    currency: str
    payment_status: PaymentStatus
    order_status: OrderStatus
    stripe_checkout_session_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "use_enum_values": True
    }

class UpdateOrderStatusRequest(BaseModel):
    order_status: OrderStatus
