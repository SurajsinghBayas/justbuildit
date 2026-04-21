from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user_id
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, RefreshRequest, ProfileUpdate
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    user = await svc.register(payload.name, payload.email, payload.password)
    return {"id": user.id, "email": user.email, "message": "Account created successfully"}


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    user = await svc.authenticate(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest):
    try:
        data = decode_token(payload.refresh_token)
        if data.get("type") != "refresh":
            raise ValueError("Not a refresh token")
        user_id = data["sub"]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.get("/me")
async def me(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    user = await svc.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "name": user.name, "email": user.email, "avatar_url": user.avatar_url}

@router.patch("/me")
async def update_me(payload: ProfileUpdate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    user = await svc.update_profile(
        user_id=user_id, 
        name=payload.name, 
        email=payload.email, 
        password=payload.password
    )
    return {"id": user.id, "name": user.name, "email": user.email, "message": "Profile updated successfully"}


@router.post("/logout")
async def logout():
    return {"message": "Logged out"}
