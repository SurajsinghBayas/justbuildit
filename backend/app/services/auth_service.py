from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, name: str, email: str, password: str) -> User:
        existing = await self.get_by_email(email)
        if existing:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Email already registered")
        user = User(name=name, email=email, password_hash=hash_password(password))
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        user = await self.get_by_email(email)
        if not user or not user.password_hash:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def update_profile(self, user_id: str, name: Optional[str] = None, email: Optional[str] = None, password: Optional[str] = None) -> User:
        user = await self.get_by_id(user_id)
        if not user:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="User not found")
        
        if name:
            user.name = name
        if email and email != user.email:
            existing = await self.get_by_email(email)
            if existing:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="Email already in use")
            user.email = email
        if password:
            user.password_hash = hash_password(password)
            
        await self.db.commit()
        await self.db.refresh(user)
        return user
