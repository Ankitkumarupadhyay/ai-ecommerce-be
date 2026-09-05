from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.auth import GoogleAuthRequest, TokenResponse, UserResponse
from app.services.auth_service import auth_service
from app.core.dependencies import get_current_user
from app.models.user import UserModel

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/google", response_model=TokenResponse)
async def google_auth(request: GoogleAuthRequest):
    try:
        token_response = await auth_service.authenticate_google_user(request.credential)
        return token_response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Authentication failed: {str(e)}")

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserModel = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture,
        role=current_user.role
    )
