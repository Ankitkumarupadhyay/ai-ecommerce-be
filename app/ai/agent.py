import json
import logging
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from app.core.config import settings
from app.ai.prompts import SYSTEM_PROMPT, OFF_TOPIC_SIGNALS, OFF_TOPIC_REPLY
from app.ai.tools import (
    get_available_products_tool,
    search_products_tool,
    get_product_details_tool,
    get_my_orders_tool,
    get_my_order_status_tool,
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

        logger.info(f"🤖 [AI AGENT] Processing Chat Message: '{message}' | User ID: '{user_id or 'Anonymous'}'")

        # ── Guardrail: off-topic detection (fast-path, no LLM cost) ────────
        if any(signal in msg_lower for signal in OFF_TOPIC_SIGNALS):
            logger.info(f"🛡️ [AI AGENT GUARDRAIL] Message flagged as off-topic: '{message}'")
            return {"reply": OFF_TOPIC_REPLY, "tools_used": []}

        if self.use_openai:
            try:
                llm = ChatOpenAI(
                    model=settings.OPENAI_MODEL,
                    api_key=settings.OPENAI_API_KEY,
                    temperature=0.2
                )

                tools = [
                    get_available_products_tool,
                    search_products_tool,
                    get_product_details_tool,
                    get_my_orders_tool,
                    get_my_order_status_tool
                ]
                tool_map = {t.name: t for t in tools}
                llm_with_tools = llm.bind_tools(tools)

                context_str = f"\nUser Security Context: Authenticated User ID = '{user_id or 'Anonymous'}'."
                messages = [
                    SystemMessage(content=SYSTEM_PROMPT + context_str),
                    HumanMessage(content=message)
                ]

                logger.info(f"🚀 [SENDING USER QUERY TO LLM] Sending query: '{message}' to OpenAI ({settings.OPENAI_MODEL})...")
                response = await llm_with_tools.ainvoke(messages)

                tool_calls = getattr(response, "tool_calls", None)
                if tool_calls:
                    messages.append(response)
                    for tool_call in tool_calls:
                        t_name = tool_call["name"]
                        t_args = tool_call.get("args", {})
                        t_id = tool_call.get("id", "")

                        tools_used.append(t_name)
                        logger.info(f"⚡ [LLM DECIDED TOOL CALL] LLM autonomously selected tool: '{t_name}' with args: {t_args}")

                        # Inject user_id for order tools if missing
                        if t_name in ["get_my_orders_tool", "get_my_order_status_tool"]:
                            if not t_args.get("user_id"):
                                t_args["user_id"] = user_id or ""

                        if t_name in tool_map:
                            target_tool = tool_map[t_name]
                            tool_result = await target_tool.ainvoke(t_args)
                        else:
                            tool_result = f"Error: Tool '{t_name}' not found."

                        logger.info(f"📦 [TOOL EXECUTED RESULT] Tool '{t_name}' completed. Result preview: '{str(tool_result)[:120]}...'")
                        logger.info(f"📤 [SENDING TOOL RESP TO LLM] Appending ToolMessage (id={t_id}) back to LLM context...")
                        messages.append(ToolMessage(content=str(tool_result), tool_call_id=t_id))

                    logger.info(f"🚀 [SENDING TOOL RESULTS TO LLM] Querying OpenAI for final response with tool outputs...")
                    final_response = await llm.ainvoke(messages)
                    reply_text = str(final_response.content)
                    logger.info(f"✨ [FINAL LLM RESPONSE GENERATED] Reply length={len(reply_text)} chars.")
                    return {
                        "reply": reply_text,
                        "tools_used": tools_used
                    }
                else:
                    reply_text = str(response.content)
                    logger.info(f"✨ [DIRECT LLM RESPONSE GENERATED] Reply length={len(reply_text)} chars.")
                    return {
                        "reply": reply_text,
                        "tools_used": []
                    }
            except Exception as e:
                logger.warning(f"⚠️ [AI AGENT OPENAI ERROR] OpenAI API call failed or unavailable ({e}), using fallback engine.", exc_info=True)

        # Real-Data Fallback Engine using exact DB tools
        logger.info("🔄 [AI AGENT FALLBACK ENGINE] Executing fallback logic...")
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
            return {
                "reply": (
                    "Hi! I'm AuraBot, your AuraStore shopping assistant. "
                    "I can help you with:\n"
                    "• 🛍️ Product availability, prices & stock\n"
                    "• 📦 Your order history & shipping status\n\n"
                    "What can I help you find today?"
                ),
                "tools_used": []
            }


ai_assistant = AIAssistant()
