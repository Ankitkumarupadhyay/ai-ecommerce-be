import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List
import httpx
from user_agents import parse as parse_ua
from fastapi import Request
from app.db.mongodb import get_database

logger = logging.getLogger(__name__)

_GEO_CACHE: dict[str, dict] = {}


async def _get_location(ip_address: Optional[str]) -> dict:
    """Lookup city and country for an IP address."""
    if not ip_address or ip_address in ("127.0.0.1", "::1", "localhost", "unknown"):
        return {"city": None, "country": None}

    if ip_address in _GEO_CACHE:
        return _GEO_CACHE[ip_address]

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"http://ip-api.com/json/{ip_address}?fields=status,country,city")
            if resp.status_code == 200:
                geo = resp.json()
                if geo.get("status") == "success":
                    location = {
                        "city": geo.get("city") or None,
                        "country": geo.get("country") or None,
                    }
                    if len(_GEO_CACHE) > 1000:
                        _GEO_CACHE.clear()
                    _GEO_CACHE[ip_address] = location
                    return location
    except Exception as e:
        logger.debug(f"Geo IP lookup error for {ip_address}: {e}")

    return {"city": None, "country": None}


def _get_client_ip(request: Request) -> str:
    """Extract real client IP, respecting proxy headers."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


def _parse_user_agent(ua_string: Optional[str]) -> dict:
    """Parse browser, OS, and device from User-Agent string."""
    if not ua_string:
        return {"browser": "Unknown", "os": "Unknown", "device": "Desktop"}
    try:
        ua = parse_ua(ua_string)
        device = "Mobile" if ua.is_mobile else ("Tablet" if ua.is_tablet else "Desktop")
        return {
            "browser": f"{ua.browser.family} {ua.browser.version_string}".strip(),
            "os": f"{ua.os.family} {ua.os.version_string}".strip(),
            "device": device,
        }
    except Exception:
        return {"browser": "Unknown", "os": "Unknown", "device": "Unknown"}


class ChatLogService:
    @staticmethod
    async def log_chat(
        *,
        question: str,
        response: str,
        tools_used: List[str],
        session_id: Optional[str],
        user_id: Optional[str],
        request: Request,
    ) -> str:
        """Persist a chat exchange to the ai_chat_logs collection."""
        db = get_database()
        session_id = session_id or str(uuid.uuid4())
        ip = _get_client_ip(request)
        ua_info = _parse_user_agent(request.headers.get("User-Agent"))
        location = await _get_location(ip)

        doc = {
            "session_id": session_id,
            "user_id": user_id,
            "is_authenticated": bool(user_id),
            "question": question,
            "response": response,
            "tools_used": tools_used,
            "ip_address": ip,
            "country": location["country"],
            "city": location["city"],
            "browser": ua_info["browser"],
            "os": ua_info["os"],
            "device": ua_info["device"],
            "created_at": datetime.now(timezone.utc),
        }

        try:
            await db.ai_chat_logs.insert_one(doc)
        except Exception as e:
            logger.warning(f"Failed to log AI chat: {e}")

        return session_id

    @staticmethod
    async def get_logs(limit: int = 100, skip: int = 0) -> List[dict]:
        db = get_database()
        cursor = db.ai_chat_logs.find({}).sort("created_at", -1).skip(skip).limit(limit)
        logs = []
        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            logs.append(doc)
        return logs

    @staticmethod
    async def get_logs_by_user(user_id: str) -> List[dict]:
        db = get_database()
        cursor = db.ai_chat_logs.find({"user_id": user_id}).sort("created_at", -1)
        logs = []
        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            logs.append(doc)
        return logs


chat_log_service = ChatLogService()
