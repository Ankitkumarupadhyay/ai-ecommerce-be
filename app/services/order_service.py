from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId
from fastapi import HTTPException, status
from app.db.mongodb import get_database
from app.models.order import PaymentStatus, OrderStatus
from app.schemas.order import OrderResponse, OrderItemResponse
from app.services.cart_service import cart_service

class OrderService:
    @staticmethod
    async def create_order_from_cart(user_id: str) -> OrderResponse:
        cart_response = await cart_service.get_user_cart(user_id)
        if not cart_response.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create an order from an empty cart"
            )

        db = get_database()
        order_items = []
        subtotal = 0.0

        for cart_item in cart_response.items:
            product = await db.products.find_one({
                "_id": ObjectId(cart_item.product_id),
                "is_active": True
            })
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product {cart_item.name} is no longer available"
                )

            if cart_item.quantity > product.get("stock", 0):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for product {product['name']}. Available: {product.get('stock', 0)}"
                )

            price_snapshot = float(product["price"])
            line_subtotal = round(price_snapshot * cart_item.quantity, 2)
            subtotal += line_subtotal

            order_items.append({
                "product_id": str(product["_id"]),
                "product_name": product["name"],
                "price": price_snapshot,
                "quantity": cart_item.quantity
            })

        subtotal = round(subtotal, 2)
        now = datetime.now(timezone.utc)

        order_doc = {
            "user_id": user_id,
            "items": order_items,
            "subtotal": subtotal,
            "total": subtotal,
            "currency": "usd",
            "payment_status": PaymentStatus.PENDING.value,
            "order_status": OrderStatus.PENDING.value,
            "stripe_checkout_session_id": None,
            "stripe_payment_intent_id": None,
            "created_at": now,
            "updated_at": now
        }

        result = await db.orders.insert_one(order_doc)
        order_doc["id"] = str(result.inserted_id)

        # Clear cart upon order placement
        await cart_service.clear_cart(user_id)

        return OrderResponse(**order_doc)

    @staticmethod
    async def get_user_orders(user_id: str) -> List[OrderResponse]:
        db = get_database()
        cursor = db.orders.find({"user_id": user_id}).sort("created_at", -1)
        orders = []
        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            orders.append(OrderResponse(**doc))
        return orders

    @staticmethod
    async def get_order_by_id_for_user(order_id: str, user_id: str) -> Optional[OrderResponse]:
        if not ObjectId.is_valid(order_id):
            return None
        db = get_database()
        doc = await db.orders.find_one({"_id": ObjectId(order_id), "user_id": user_id})
        if not doc:
            return None
        doc["id"] = str(doc["_id"])
        return OrderResponse(**doc)

    @staticmethod
    async def get_all_orders_admin() -> List[OrderResponse]:
        db = get_database()
        cursor = db.orders.find({}).sort("created_at", -1)
        orders = []
        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            orders.append(OrderResponse(**doc))
        return orders

    @staticmethod
    async def get_order_by_id_admin(order_id: str) -> Optional[OrderResponse]:
        if not ObjectId.is_valid(order_id):
            return None
        db = get_database()
        doc = await db.orders.find_one({"_id": ObjectId(order_id)})
        if not doc:
            return None
        doc["id"] = str(doc["_id"])
        return OrderResponse(**doc)

    @staticmethod
    async def update_order_status_admin(order_id: str, new_status: OrderStatus) -> Optional[OrderResponse]:
        if not ObjectId.is_valid(order_id):
            return None
        db = get_database()
        now = datetime.now(timezone.utc)
        result = await db.orders.find_one_and_update(
            {"_id": ObjectId(order_id)},
            {"$set": {"order_status": new_status.value, "updated_at": now}},
            return_document=True
        )
        if not result:
            return None
        result["id"] = str(result["_id"])
        return OrderResponse(**result)

order_service = OrderService()
