import json
import logging
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from app.services.product_service import product_service
from app.services.order_service import order_service

logger = logging.getLogger(__name__)


def _clean_search_query(raw_query: Optional[str]) -> Optional[str]:
    """Strips question stopwords so natural language queries don't break regex matching."""
    if not raw_query or not raw_query.strip():
        return None
    q = raw_query.strip().lower()

    general_phrases = [
        "what products", "show products", "list products", "available products",
        "all products", "what do you sell", "what is available", "show me",
        "what products are available", "tell me what you have", "catalog", "inventory"
    ]
    if any(p in q for p in general_phrases):
        return None

    words = [w.strip("?,!.") for w in q.split()]
    stopwords = {
        "what", "is", "are", "the", "for", "in", "of", "a", "an", "do", "you",
        "have", "show", "me", "list", "available", "products", "product", "store",
        "shop", "item", "items", "can", "i", "get", "buy", "tell"
    }
    filtered = [w for w in words if w and w not in stopwords]
    if not filtered:
        return None
    return " ".join(filtered)


@tool
async def get_available_products_tool(query: str = "") -> str:
    """
    Retrieves all available active products in the store with their prices, categories, and stock.
    """
    search_term = _clean_search_query(query)
    logger.info(f"🛠️ [LLM REQUESTED TOOL] get_available_products | Raw query: '{query}' -> Clean search term: '{search_term}'")

    products = await product_service.get_products(search=search_term, include_inactive=False)
    logger.info(f"📦 [TOOL DB RESPONSE] get_available_products | Fetched {len(products)} products from DB.")

    if not products:
        msg = f"No active products currently available matching '{search_term}'." if search_term else "No active products currently available in store."
        logger.info(f"📤 [SENDING TOOL RESP TO LLM] get_available_products -> '{msg}'")
        return msg

    result = []
    for p in products:
        result.append({
            "name": p.name,
            "category": p.category,
            "price": f"${p.price:.2f} {p.currency.upper()}",
            "stock": p.stock,
            "description": p.description
        })
    json_res = json.dumps(result, indent=2)
    logger.info(f"📤 [SENDING TOOL RESP TO LLM] get_available_products -> Returned JSON array with {len(result)} items")
    return json_res


@tool
async def search_products_tool(search_term: str) -> str:
    """
    Searches products by keyword in name, description, or category.
    """
    clean_term = _clean_search_query(search_term)
    logger.info(f"🛠️ [LLM REQUESTED TOOL] search_products | Raw search_term: '{search_term}' -> Clean term: '{clean_term}'")

    products = await product_service.get_products(search=clean_term, include_inactive=False)
    logger.info(f"📦 [TOOL DB RESPONSE] search_products | Fetched {len(products)} matching products from DB.")

    if not products:
        all_products = await product_service.get_products(search=None, include_inactive=False)
        if all_products:
            logger.info(f"📦 [TOOL FALLBACK] search_products | Returning all {len(all_products)} products as fallback.")
            result = []
            for p in all_products:
                result.append({
                    "name": p.name,
                    "category": p.category,
                    "price": f"${p.price:.2f}",
                    "stock": p.stock,
                    "description": p.description
                })
            json_res = json.dumps(result, indent=2)
            logger.info(f"📤 [SENDING TOOL RESP TO LLM] search_products -> Fallback returned {len(result)} items")
            return json_res

        msg = f"No products found matching search term '{search_term}'."
        logger.info(f"📤 [SENDING TOOL RESP TO LLM] search_products -> '{msg}'")
        return msg

    result = []
    for p in products:
        result.append({
            "name": p.name,
            "category": p.category,
            "price": f"${p.price:.2f}",
            "stock": p.stock,
            "description": p.description
        })
    json_res = json.dumps(result, indent=2)
    logger.info(f"📤 [SENDING TOOL RESP TO LLM] search_products -> Returned JSON array with {len(result)} items")
    return json_res


@tool
async def get_product_details_tool(product_name: str) -> str:
    """
    Gets detailed information for a specific product by name.
    """
    clean_name = _clean_search_query(product_name) or product_name
    logger.info(f"🛠️ [LLM REQUESTED TOOL] get_product_details | Product name: '{product_name}'")

    products = await product_service.get_products(search=clean_name, include_inactive=False)
    if not products:
        msg = f"Product '{product_name}' not found."
        logger.info(f"📤 [SENDING TOOL RESP TO LLM] get_product_details -> '{msg}'")
        return msg

    p = products[0]
    json_res = json.dumps({
        "name": p.name,
        "price": f"${p.price:.2f}",
        "category": p.category,
        "stock": p.stock,
        "description": p.description,
        "available": p.stock > 0
    }, indent=2)
    logger.info(f"📤 [SENDING TOOL RESP TO LLM] get_product_details -> Details for '{p.name}'")
    return json_res


@tool
async def get_my_orders_tool(user_id: str = "") -> str:
    """
    Retrieves the authenticated user's past order history, items purchased, totals, and order status.
    """
    return await get_my_orders_backend(user_id)


@tool
async def get_my_order_status_tool(order_id: str = "", user_id: str = "") -> str:
    """
    Retrieves detailed shipping, payment, and status for a specific order using order_id.
    """
    return await get_my_order_status_backend(user_id, order_id)


async def get_my_orders_backend(user_id: str) -> str:
    """
    Backend implementation to fetch orders belonging strictly to user_id.
    """
    logger.info(f"🛠️ [LLM REQUESTED TOOL] get_my_orders | Target User ID: '{user_id}'")
    if not user_id:
        msg = "User not authenticated. Cannot access order history."
        logger.info(f"📤 [SENDING TOOL RESP TO LLM] get_my_orders -> '{msg}'")
        return msg

    orders = await order_service.get_user_orders(user_id)
    logger.info(f"📦 [TOOL DB RESPONSE] get_my_orders | Fetched {len(orders)} orders for user '{user_id}'.")
    if not orders:
        msg = "You have placed no orders yet."
        logger.info(f"📤 [SENDING TOOL RESP TO LLM] get_my_orders -> '{msg}'")
        return msg

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
    json_res = json.dumps(result, indent=2)
    logger.info(f"📤 [SENDING TOOL RESP TO LLM] get_my_orders -> {len(result)} orders returned")
    return json_res


async def get_my_order_status_backend(user_id: str, order_id: str) -> str:
    """
    Backend implementation to fetch order status strictly for user_id.
    """
    logger.info(f"🛠️ [LLM REQUESTED TOOL] get_my_order_status | User ID: '{user_id}' | Order ID: '{order_id}'")
    if not user_id:
        msg = "User not authenticated."
        logger.info(f"📤 [SENDING TOOL RESP TO LLM] get_my_order_status -> '{msg}'")
        return msg

    order = await order_service.get_order_by_id_for_user(order_id, user_id)
    if not order:
        msg = f"Order '{order_id}' was not found in your order history."
        logger.info(f"📤 [SENDING TOOL RESP TO LLM] get_my_order_status -> '{msg}'")
        return msg

    json_res = json.dumps({
        "order_id": order.id,
        "date": order.created_at.strftime("%Y-%m-%d %H:%M"),
        "total": f"${order.total:.2f}",
        "payment_status": order.payment_status,
        "order_status": order.order_status
    }, indent=2)
    logger.info(f"📤 [SENDING TOOL RESP TO LLM] get_my_order_status -> Status for '{order_id}'")
    return json_res


