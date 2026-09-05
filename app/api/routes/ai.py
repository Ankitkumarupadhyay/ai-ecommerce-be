from fastapi import APIRouter, Depends, Header, HTTPException, status
from typing import Optional
from app.core.security import decode_access_token
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.ai.agent import ai_assistant

router = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/chat", response_model=AIChatResponse)
async def ai_chat(
    request: AIChatRequest,
    authorization: Optional[str] = Header(None)
):
    """
    AI Support Agent endpoint. Resolves context and securely enforces user order isolation.
    """
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get("sub")
            
    result = await ai_assistant.process_chat(request.message, user_id=user_id)
    return AIChatResponse(
        reply=result["reply"],
        tools_used=result.get("tools_used", [])
    )
