from datetime import datetime, timezone
from typing import Optional, List
from bson import ObjectId


class ChatLog:
    """
    Represents a single AI chat exchange stored in the `ai_chat_logs` collection.

    Fields
    ------
    session_id      : UUID generated per browser chat session (groups messages together)
    user_id         : MongoDB ObjectId string of the logged-in user, or None for guests
    is_authenticated: True if a valid JWT was present on the request
    question        : The message sent by the user
    response        : The AI assistant reply
    tools_used      : List of LangChain tool names invoked to answer the question
    ip_address      : Client IP (X-Forwarded-For aware)
    country         : Geo-resolved country (optional enrichment)
    city            : Geo-resolved city (optional enrichment)
    browser         : Parsed browser family + version from User-Agent
    os              : Parsed OS family + version from User-Agent
    device          : "Mobile" | "Tablet" | "Desktop"
    created_at      : UTC timestamp of the exchange
    """

    def __init__(
        self,
        session_id: str,
        question: str,
        response: str,
        tools_used: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        is_authenticated: bool = False,
        ip_address: Optional[str] = None,
        country: Optional[str] = None,
        city: Optional[str] = None,
        browser: Optional[str] = None,
        os: Optional[str] = None,
        device: Optional[str] = None,
    ):
        self._id: Optional[ObjectId] = None
        self.session_id = session_id
        self.user_id = user_id
        self.is_authenticated = is_authenticated
        self.question = question
        self.response = response
        self.tools_used: List[str] = tools_used or []
        self.ip_address = ip_address
        self.country = country
        self.city = city
        self.browser = browser
        self.os = os
        self.device = device
        self.created_at: datetime = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "is_authenticated": self.is_authenticated,
            "question": self.question,
            "response": self.response,
            "tools_used": self.tools_used,
            "ip_address": self.ip_address,
            "country": self.country,
            "city": self.city,
            "browser": self.browser,
            "os": self.os,
            "device": self.device,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "ChatLog":
        log = ChatLog(
            session_id=data.get("session_id", ""),
            question=data.get("question", ""),
            response=data.get("response", ""),
            tools_used=data.get("tools_used", []),
            user_id=data.get("user_id"),
            is_authenticated=data.get("is_authenticated", False),
            ip_address=data.get("ip_address"),
            country=data.get("country"),
            city=data.get("city"),
            browser=data.get("browser"),
            os=data.get("os"),
            device=data.get("device"),
        )
        log._id = data.get("_id")
        if "created_at" in data:
            log.created_at = data["created_at"]
        return log

    @property
    def id(self) -> Optional[str]:
        return str(self._id) if self._id else None
