from fastapi import APIRouter, Depends, Request, Header, HTTPException, status
from app.core.dependencies import require_customer
from app.models.user import UserModel
from app.schemas.payment import CreateCheckoutSessionRequest, CheckoutSessionResponse
from app.services.stripe_service import stripe_service

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CreateCheckoutSessionRequest,
    current_user: UserModel = Depends(require_customer)
):
    """
    Create a Stripe Checkout session for an existing pending order.
    """
    return await stripe_service.create_checkout_session(request.order_id, current_user.id)

@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None, alias="Stripe-Signature")):
    """
    Stripe Webhook endpoint for async payment verification and order state updates.
    """
    payload = await request.body()
    return await stripe_service.process_webhook_event(payload, stripe_signature or "")

@router.post("/verify-session")
async def verify_session(
    session_id: str,
    current_user: UserModel = Depends(require_customer)
):
    """
    Frontend payment verification endpoint called when returning from Stripe Checkout.
    """
    return await stripe_service.simulate_mock_payment_success(session_id, current_user.id)
