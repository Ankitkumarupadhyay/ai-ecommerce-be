import json
import logging
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.config import settings
from app.ai.prompts import SYSTEM_PROMPT
from app.ai.tools import (
    get_available_products_tool,
    search_products_tool,
    get_product_details_tool,
    get_my_orders_backend,
    get_my_order_status_backend
)

logger = logging.getLogger(__name__)

class AIAssistant:
    def __init__(self):
        self.use_openai = (
            bool(settings.OPENAI_API_KEY) and 
            not settings.OPENAI_API_KEY.startswith("your_openai_api")
        )

    async def process_chat(self, message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        msg_lower = message.lower().strip()
        tools_used = []

        if self.use_openai:
            try:
                llm = ChatOpenAI(
                    model=settings.OPENAI_MODEL,
                    api_key=settings.OPENAI_API_KEY,
                    temperature=0.2
                )
                
                # Context enrichment for order queries
                context_str = f"\nUser Security Context: Authenticated User ID = '{user_id or 'Anonymous'}'."
                
                # Tool calling logic via LangChain
                messages = [
                    SystemMessage(content=SYSTEM_PROMPT + context_str),
                    HumanMessage(content=message)
                ]
                
                # Simple tool selection check
                if any(w in msg_lower for w in ["order", "purchase", "bought", "history", "status"]):
                    tools_used.append("get_my_orders")
                    order_data = await get_my_orders_backend(user_id or "")
                    messages.append(SystemMessage(content=f"Authorized Customer Order Data from DB:\n{order_data}"))
                elif any(w in msg_lower for w in ["product", "price", "stock", "available", "cost", "buy", "item", "catalog"]):
                    tools_used.append("search_products")
                    prod_data = await get_available_products_tool.ainvoke({"query": message})
                    messages.append(SystemMessage(content=f"Current Store Product Data from DB:\n{prod_data}"))
                
                response = await llm.ainvoke(messages)
                return {
                    "reply": str(response.content),
                    "tools_used": tools_used
                }
            except Exception as e:
                logger.warning(f"OpenAI API call failed or unavailable ({e}), using fallback engine.")

        # Real-Data Fallback Engine using exact DB tools
        if any(w in msg_lower for w in ["order", "purchase", "bought", "history", "status", "ship"]):
            tools_used.append("get_my_orders")
            if not user_id:
                return {
                    "reply": "Please sign in to view your personalized order history and tracking status.",
                    "tools_used": tools_used
                }
            order_json_str = await get_my_orders_backend(user_id)
            orders_data = json.loads(order_json_str) if order_json_str.startswith("[") else []
            
            if not orders_data:
                return {
                    "reply": "You have no order history yet. Browse our products and place your first order!",
                    "tools_used": tools_used
                }
                
            reply_lines = ["Here is your authorized order history:"]
            for o in orders_data:
                reply_lines.append(
                    f"• Order #{o['order_id'][:8]}... placed on {o['date']}: Total {o['total']} | Payment: {o['payment_status'].upper()} | Status: {o['order_status'].upper()} (Items: {', '.join(o['items'])})"
                )
            return {"reply": "\n".join(reply_lines), "tools_used": tools_used}

        elif any(w in msg_lower for w in ["product", "available", "catalog", "item", "list", "what do you sell"]):
            tools_used.append("get_available_products")
            prods_json_str = await get_available_products_tool.ainvoke({"query": ""})
            prods_data = json.loads(prods_json_str) if prods_json_str.startswith("[") else []
            
            if not prods_data:
                return {"reply": "No products are currently available in the catalog.", "tools_used": tools_used}
                
            reply_lines = ["Here are our currently available products:"]
            for p in prods_data:
                reply_lines.append(f"• **{p['name']}** ({p['category']}) - {p['price']} (Stock: {p['stock']}) - {p['description']}")
            return {"reply": "\n\n".join(reply_lines), "tools_used": tools_used}

        elif "price" in msg_lower or "how much" in msg_lower or "cost" in msg_lower:
            tools_used.append("search_products")
            prods_json_str = await search_products_tool.ainvoke({"search_term": message.replace("price", "").replace("of", "").replace("what is the", "").strip()})
            
            if "No products found" in prods_json_str:
                # Get all products as backup
                prods_json_str = await get_available_products_tool.ainvoke({"query": ""})
                
            prods_data = json.loads(prods_json_str) if prods_json_str.startswith("[") else []
            if not prods_data:
                return {"reply": "Sorry, I couldn't find matching product prices in our inventory.", "tools_used": tools_used}
                
            reply_lines = ["Product pricing information:"]
            for p in prods_data:
                reply_lines.append(f"• **{p['name']}**: {p['price']} (Stock: {p['stock']} available)")
            return {"reply": "\n".join(reply_lines), "tools_used": tools_used}

        else:
            tools_used.append("get_available_products")
            prods_json_str = await get_available_products_tool.ainvoke({"query": ""})
            return {
                "reply": "I am your AI E-Commerce Assistant. You can ask me about product pricing, stock availability, or check your personal order status!",
                "tools_used": tools_used
            }

ai_assistant = AIAssistant()
