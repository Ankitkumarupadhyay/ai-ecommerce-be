from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from fastapi import HTTPException, status
from app.db.mongodb import get_database
from app.schemas.cart import CartResponse, CartItemResponse, AddCartItemRequest, UpdateCartItemRequest

class CartService:
    @staticmethod
    async def get_or_create_cart(user_id: str) -> dict:
        db = get_database()
        cart = await db.carts.find_one({"user_id": user_id})
        if not cart:
            new_cart = {
                "user_id": user_id,
                "items": [],
                "updated_at": datetime.now(timezone.utc)
            }
            result = await db.carts.insert_one(new_cart)
            new_cart["_id"] = result.inserted_id
            return new_cart
        return cart

    @staticmethod
    async def get_user_cart(user_id: str) -> CartResponse:
        cart = await CartService.get_or_create_cart(user_id)
        db = get_database()
        
        enriched_items = []
        total_amount = 0.0
        
        for item in cart.get("items", []):
            product_id = item["product_id"]
            quantity = item["quantity"]
            
            if not ObjectId.is_valid(product_id):
                continue
                
            product = await db.products.find_one({"_id": ObjectId(product_id), "is_active": True})
            if not product:
                continue
                
            line_total = round(product["price"] * quantity, 2)
            total_amount += line_total
            
            enriched_items.append(CartItemResponse(
                product_id=str(product["_id"]),
                name=product["name"],
                price=product["price"],
                image_url=product.get("image_url", ""),
                quantity=quantity,
                stock=product.get("stock", 0),
                line_total=line_total
            ))
            
        return CartResponse(
            id=str(cart["_id"]),
            user_id=user_id,
            items=enriched_items,
            total_amount=round(total_amount, 2)
        )

    @staticmethod
    async def add_item_to_cart(user_id: str, item_in: AddCartItemRequest) -> CartResponse:
        db = get_database()
        if not ObjectId.is_valid(item_in.product_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product ID format")
            
        product = await db.products.find_one({"_id": ObjectId(item_in.product_id), "is_active": True})
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found or inactive")
            
        cart = await CartService.get_or_create_cart(user_id)
        items = cart.get("items", [])
        
        # Check existing quantity in cart
        existing_item = next((i for i in items if i["product_id"] == item_in.product_id), None)
        new_quantity = item_in.quantity
        if existing_item:
            new_quantity += existing_item["quantity"]
            
        if new_quantity > product["stock"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requested quantity ({new_quantity}) exceeds available stock ({product['stock']})"
            )
            
        if existing_item:
            existing_item["quantity"] = new_quantity
        else:
            items.append({"product_id": item_in.product_id, "quantity": item_in.quantity})
            
        await db.carts.update_one(
            {"_id": cart["_id"]},
            {"$set": {"items": items, "updated_at": datetime.now(timezone.utc)}}
        )
        
        return await CartService.get_user_cart(user_id)

    @staticmethod
    async def update_item_quantity(user_id: str, product_id: str, item_in: UpdateCartItemRequest) -> CartResponse:
        db = get_database()
        if not ObjectId.is_valid(product_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product ID format")
            
        product = await db.products.find_one({"_id": ObjectId(product_id), "is_active": True})
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found or inactive")
            
        if item_in.quantity > product["stock"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requested quantity ({item_in.quantity}) exceeds available stock ({product['stock']})"
            )
            
        cart = await CartService.get_or_create_cart(user_id)
        items = cart.get("items", [])
        
        item_found = False
        for item in items:
            if item["product_id"] == product_id:
                item["quantity"] = item_in.quantity
                item_found = True
                break
                
        if not item_found:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not in cart")
            
        await db.carts.update_one(
            {"_id": cart["_id"]},
            {"$set": {"items": items, "updated_at": datetime.now(timezone.utc)}}
        )
        
        return await CartService.get_user_cart(user_id)

    @staticmethod
    async def remove_item_from_cart(user_id: str, product_id: str) -> CartResponse:
        db = get_database()
        cart = await CartService.get_or_create_cart(user_id)
        items = [i for i in cart.get("items", []) if i["product_id"] != product_id]
        
        await db.carts.update_one(
            {"_id": cart["_id"]},
            {"$set": {"items": items, "updated_at": datetime.now(timezone.utc)}}
        )
        
        return await CartService.get_user_cart(user_id)

    @staticmethod
    async def clear_cart(user_id: str):
        db = get_database()
        await db.carts.update_one(
            {"user_id": user_id},
            {"$set": {"items": [], "updated_at": datetime.now(timezone.utc)}}
        )

cart_service = CartService()
