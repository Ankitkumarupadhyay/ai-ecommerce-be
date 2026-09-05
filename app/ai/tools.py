import json
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from app.services.product_service import product_service
from app.services.order_service import order_service

@tool
async def get_available_products_tool(query: str = "") -> str:
    """
    Retrieves all available active products in the store with their prices, categories, and stock.
    """
    products = await product_service.get_products(search=query if query else None, include_inactive=False)
    if not products:
        return "No active products currently available matching the query."
    
    result = []
    for p in products:
        result.append({
            "name": p.name,
            "category": p.category,
            "price": f"${p.price:.2f} {p.currency.upper()}",
            "stock": p.stock,
            "description": p.description
        })
    return json.dumps(result, indent=2)

@tool
async def search_products_tool(search_term: str) -> str:
    """
    Searches products by keyword in name, description, or category.
    """
    products = await product_service.get_products(search=search_term, include_inactive=False)
    if not products:
        return f"No products found matching search term '{search_term}'."
    
    result = []
    for p in products:
        result.append({
            "name": p.name,
            "category": p.category,
            "price": f"${p.price:.2f}",
            "stock": p.stock,
            "description": p.description
        })
    return json.dumps(result, indent=2)

@tool
async def get_product_details_tool(product_name: str) -> str:
    """
    Gets detailed information for a specific product by name.
    """
    products = await product_service.get_products(search=product_name, include_inactive=False)
    if not products:
        return f"Product '{product_name}' not found."
    
    # Exact or best match
    p = products[0]
    return json.dumps({
        "name": p.name,
        "price": f"${p.price:.2f}",
        "category": p.category,
        "stock": p.stock,
        "description": p.description,
        "available": p.stock > 0
    }, indent=2)

async def get_my_orders_backend(user_id: str) -> str:
    """
    Backend implementation to fetch orders belonging strictly to user_id.
    """
    if not user_id:
        return "User not authenticated. Cannot access order history."
        
    orders = await order_service.get_user_orders(user_id)
    if not orders:
        return "You have placed no orders yet."
        
    result = []
    for o in orders:
        items_summary = [f"{i.product_name} (x{i.quantity})" for i in o.items]
        result.append({
            "order_id": o.id,
            "date": o.created_at.strftime("%Y-%m-%d %H:%M"),
            "items": items_summary,
            "total": f"${o.total:.2f}",
            "payment_status": o.payment_status,
            "order_status": o.order_status
        })
    return json.dumps(result, indent=2)

async def get_my_order_status_backend(user_id: str, order_id: str) -> str:
    """
    Backend implementation to fetch order status strictly for user_id.
    """
    if not user_id:
        return "User not authenticated."
        
    order = await order_service.get_order_by_id_for_user(order_id, user_id)
    if not order:
        return f"Order '{order_id}' was not found in your order history."
        
    return json.dumps({
        "order_id": order.id,
        "date": order.created_at.strftime("%Y-%m-%d %H:%M"),
        "total": f"${order.total:.2f}",
        "payment_status": order.payment_status,
        "order_status": order.order_status
    }, indent=2)
