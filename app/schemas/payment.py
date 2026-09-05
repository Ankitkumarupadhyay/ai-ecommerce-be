from pydantic import BaseModel
from typing import Optional

class CreateCheckoutSessionRequest(BaseModel):
    order_id: str

class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str
