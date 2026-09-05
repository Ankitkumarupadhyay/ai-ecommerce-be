from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from app.core.security import decode_access_token
from app.db.mongodb import get_database
from app.models.user import UserModel, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/google")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    db = get_database()
    if not ObjectId.is_valid(user_id):
        raise credentials_exception

    user_dict = await db.users.find_one({"_id": ObjectId(user_id)})
    if user_dict is None:
        raise credentials_exception
    
    user_dict["_id"] = str(user_dict["_id"])
    return UserModel(**user_dict)

async def require_customer(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    # Any authenticated user (customer or admin) is allowed as customer
    return current_user

async def require_admin(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    if current_user.role != UserRole.ADMIN and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Admin access required"
        )
    return current_user
