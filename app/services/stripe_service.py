import logging
from datetime import datetime, timezone
import stripe
from bson import ObjectId
from fastapi import HTTPException, status
from app.core.config import settings
from app.db.mongodb import get_database
from app.models.order import PaymentStatus, OrderStatus
from app.schemas.payment import CheckoutSessionResponse

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    @staticmethod
    async def create_checkout_session(order_id: str, user_id: str) -> CheckoutSessionResponse:
        if not ObjectId.is_valid(order_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order ID format")

        db = get_database()
        order = await db.orders.find_one({"_id": ObjectId(order_id), "user_id": user_id})
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found or access denied")

        if order["payment_status"] == PaymentStatus.PAID.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order is already paid")

        line_items = []
        for item in order["items"]:
            line_items.append({
                "price_data": {
                    "currency": order.get("currency", "usd").lower(),
                    "product_data": {
                        "name": item["product_name"],
                    },
                    "unit_amount": int(round(item["price"] * 100)),
                },
                "quantity": item["quantity"],
            })

        success_url = f"{settings.FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{settings.FRONTEND_URL}/payment/cancel"

        try:
            if settings.STRIPE_SECRET_KEY.startswith("sk_test_your_stripe"):
                # Developer test mock session ID when real secret key isn't populated
                session_id = f"cs_test_mock_{order_id}"
                checkout_url = f"{settings.FRONTEND_URL}/payment/success?session_id={session_id}&mock=true"
            else:
                session = stripe.checkout.Session.create(
                    payment_method_types=["card"],
                    line_items=line_items,
                    mode="payment",
                    success_url=success_url,
                    cancel_url=cancel_url,
                    client_reference_id=order_id,
                    metadata={"order_id": order_id, "user_id": user_id}
                )
                session_id = session.id
                checkout_url = session.url

            # Save session ID to order
            await db.orders.update_one(
                {"_id": ObjectId(order_id)},
                {"$set": {
                    "stripe_checkout_session_id": session_id,
                    "updated_at": datetime.now(timezone.utc)
                }}
            )

            return CheckoutSessionResponse(checkout_url=checkout_url, session_id=session_id)

        except Exception as e:
            logger.error(f"Stripe session creation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Stripe session creation failed: {str(e)}"
            )

    @staticmethod
    async def process_webhook_event(payload: bytes, sig_header: str) -> dict:
        db = get_database()
        
        try:
            if settings.STRIPE_WEBHOOK_SECRET.startswith("whsec_your_webhook"):
                # Mock event parsing for dev testing without secret
                import json
                event_data = json.loads(payload)
                event = event_data
            else:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
                )
        except Exception as e:
            logger.error(f"Webhook verification failed: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Webhook signature error: {str(e)}")

        event_id = event.get("id")
        event_type = event.get("type")

        # Idempotency check using webhook_events collection
        if event_id:
            existing_event = await db.webhook_events.find_one({"event_id": event_id})
            if existing_event:
                logger.info(f"Webhook event {event_id} already processed. Skipping.")
                return {"status": "already_processed"}

            await db.webhook_events.insert_one({
                "event_id": event_id,
                "type": event_type,
                "processed_at": datetime.now(timezone.utc)
            })

        if event_type == "checkout.session.completed":
            session = event["data"]["object"]
            order_id = session.get("client_reference_id") or session.get("metadata", {}).get("order_id")
            payment_intent = session.get("payment_intent", "pi_mock_success")

            if order_id and ObjectId.is_valid(order_id):
                order = await db.orders.find_one({"_id": ObjectId(order_id)})
                if order and order.get("payment_status") != PaymentStatus.PAID.value:
                    now = datetime.now(timezone.utc)
                    # Update payment and order status
                    await db.orders.update_one(
                        {"_id": ObjectId(order_id)},
                        {"$set": {
                            "payment_status": PaymentStatus.PAID.value,
                            "order_status": OrderStatus.CONFIRMED.value,
                            "stripe_payment_intent_id": payment_intent,
                            "updated_at": now
                        }}
                    )

                    # Deduct product stock safely and idempotently
                    for item in order.get("items", []):
                        prod_id = item.get("product_id")
                        qty = item.get("quantity", 0)
                        if prod_id and ObjectId.is_valid(prod_id):
                            await db.products.update_one(
                                {"_id": ObjectId(prod_id)},
                                {"$inc": {"stock": -qty}}
                            )

        elif event_type in ["payment_intent.payment_failed", "checkout.session.expired"]:
            session = event["data"]["object"]
            order_id = session.get("client_reference_id") or session.get("metadata", {}).get("order_id")
            if order_id and ObjectId.is_valid(order_id):
                now = datetime.now(timezone.utc)
                await db.orders.update_one(
                    {"_id": ObjectId(order_id)},
                    {"$set": {
                        "payment_status": PaymentStatus.FAILED.value,
                        "updated_at": now
                    }}
                )

        return {"status": "success", "event": event_type}

    @staticmethod
    async def simulate_mock_payment_success(session_id: str, user_id: str) -> dict:
        """
        Helper endpoint for demo/local testing when clicking Stripe mock success.
        Updates the pending order associated with session_id to paid.
        """
        db = get_database()
        order = await db.orders.find_one({"stripe_checkout_session_id": session_id, "user_id": user_id})
        if not order:
            # Fallback to finding latest pending order for user if session_id is generic
            order = await db.orders.find_one({"user_id": user_id, "payment_status": PaymentStatus.PENDING.value})
            
        if not order:
            return {"message": "No pending order found to process"}

        if order.get("payment_status") == PaymentStatus.PAID.value:
            return {"message": "Order already marked as paid", "order_id": str(order["_id"])}

        now = datetime.now(timezone.utc)
        await db.orders.update_one(
            {"_id": order["_id"]},
            {"$set": {
                "payment_status": PaymentStatus.PAID.value,
                "order_status": OrderStatus.CONFIRMED.value,
                "stripe_payment_intent_id": f"pi_mock_{order['_id']}",
                "updated_at": now
            }}
        )

        for item in order.get("items", []):
            prod_id = item.get("product_id")
            qty = item.get("quantity", 0)
            if prod_id and ObjectId.is_valid(prod_id):
                await db.products.update_one(
                    {"_id": ObjectId(prod_id)},
                    {"$inc": {"stock": -qty}}
                )

        return {"message": "Payment verified and order confirmed successfully", "order_id": str(order["_id"])}

stripe_service = StripeService()
