from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.core.config import settings

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def verify_google_token(token: str) -> Dict[str, Any]:
    """
    Verifies Google ID Token. In development mode with dummy tokens, supports dev bypass.
    """
    if settings.ENVIRONMENT == "development" and token.startswith("mock_google_token_"):
        # Helper for local testing / demo without live Google Client ID
        role = "admin" if "admin" in token else "customer"
        return {
            "sub": f"google_{token}",
            "email": f"{role}@example.com",
            "name": f"Demo {role.capitalize()} User",
            "picture": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150"
        }

    try:
        request = google_requests.Request()
        id_info = id_token.verify_oauth2_token(
            token, request, settings.GOOGLE_CLIENT_ID
        )
        return {
            "sub": id_info.get("sub"),
            "email": id_info.get("email"),
            "name": id_info.get("name", id_info.get("email").split("@")[0]),
            "picture": id_info.get("picture", "")
        }
    except Exception as e:
        raise ValueError(f"Invalid Google token: {str(e)}")
