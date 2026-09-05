from pydantic import BaseModel
from typing import List, Optional

class AIChatRequest(BaseModel):
    message: str

class AIChatResponse(BaseModel):
    reply: str
    tools_used: Optional[List[str]] = []
