from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from app.models.common import PyObjectId

class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"

class UserModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    google_id: str
    email: EmailStr
    name: str
    picture: Optional[str] = ""
    role: UserRole = UserRole.CUSTOMER
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "use_enum_values": True,
    }
