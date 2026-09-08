import logging
from fastapi import APIRouter, Header, Request
from typing import Optional
from app.core.security import decode_access_token
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.ai.agent import ai_assistant
from app.services.chat_log_service import chat_log_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/chat", response_model=AIChatResponse)
async def ai_chat(
    body: AIChatRequest,
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """
    AI Support Agent endpoint.
    - Resolves user identity from JWT (if present)
    - Captures IP, browser, OS, device from request
    - Persists every Q&A pair to ai_chat_logs collection
    """
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get("sub")

    logger.info(
        f"📥 [AI CHAT ROUTE] Received User Request | "
        f"Message: '{body.message}' | User ID: {user_id or 'Anonymous'} | Session ID: {body.session_id}"
    )

    result = await ai_assistant.process_chat(body.message, user_id=user_id)

    logger.info(
        f"📤 [AI CHAT ROUTE] Returning Response to User | "
        f"Tools Used: {result.get('tools_used', [])} | Reply Snippet: '{result['reply'][:100]}...'"
    )

    # Persist chat log asynchronously (non-blocking to caller)
    session_id = await chat_log_service.log_chat(
        question=body.message,
        response=result["reply"],
        tools_used=result.get("tools_used", []),
        session_id=body.session_id,
        user_id=user_id,
        request=request,
    )

    return AIChatResponse(
        reply=result["reply"],
        tools_used=result.get("tools_used", []),
        session_id=session_id,
    )

