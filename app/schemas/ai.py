from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class AIChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # Frontend-generated UUID per chat session


class AIChatResponse(BaseModel):
    reply: str
    tools_used: Optional[List[str]] = []
    session_id: Optional[str] = None


class ChatLogResponse(BaseModel):
    id: str
    session_id: str
    user_id: Optional[str] = None
    question: str
    response: str
    tools_used: List[str] = []
    ip_address: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    device: Optional[str] = None
    is_authenticated: bool = False
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}
