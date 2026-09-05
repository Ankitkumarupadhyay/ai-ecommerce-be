from datetime import datetime, timezone
from bson import ObjectId
from app.db.mongodb import get_database
from app.core.security import verify_google_token, create_access_token
from app.models.user import UserModel, UserRole
from app.schemas.auth import TokenResponse, UserResponse

class AuthService:
    @staticmethod
    async def authenticate_google_user(credential: str) -> TokenResponse:
        google_user_info = verify_google_token(credential)
        
        db = get_database()
        user_dict = await db.users.find_one({
            "$or": [
                {"google_id": google_user_info["sub"]},
                {"email": google_user_info["email"]}
            ]
        })
        
        now = datetime.now(timezone.utc)
        if not user_dict:
            new_user = {
                "google_id": google_user_info["sub"],
                "email": google_user_info["email"],
                "name": google_user_info["name"],
                "picture": google_user_info.get("picture", ""),
                "role": UserRole.CUSTOMER.value,
                "created_at": now,
                "updated_at": now
            }
            result = await db.users.insert_one(new_user)
            user_id = str(result.inserted_id)
            role = UserRole.CUSTOMER.value
            email = google_user_info["email"]
            name = google_user_info["name"]
            picture = google_user_info.get("picture", "")
        else:
            user_id = str(user_dict["_id"])
            role = user_dict.get("role", UserRole.CUSTOMER.value)
            email = user_dict["email"]
            name = user_dict["name"]
            picture = user_dict.get("picture", "")
            
            # Update user info if google details updated
            await db.users.update_one(
                {"_id": user_dict["_id"]},
                {"$set": {
                    "google_id": google_user_info["sub"],
                    "name": google_user_info["name"],
                    "picture": google_user_info.get("picture", ""),
                    "updated_at": now
                }}
            )
            
        access_token = create_access_token(data={"sub": user_id, "role": role, "email": email})
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user_id,
                email=email,
                name=name,
                picture=picture,
                role=role
            )
        )

auth_service = AuthService()
