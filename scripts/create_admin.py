"""
create_admin.py — Create a superuser account.
Usage: python scripts/create_admin.py --email admin@example.com --password secret123
"""
import asyncio
import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app.db.session import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.core.security import hash_password


async def create_admin(email: str, password: str, name: str):
    async with AsyncSessionLocal() as db:
        user = User(
            name=name,
            email=email,
            hashed_password=hash_password(password),
            is_superuser=True,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"✅ Superuser created: {user.email} (id={user.id})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a superuser account")
    parser.add_argument("--email", required=True, help="Admin email")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument("--name", default="Admin", help="Admin display name")
    args = parser.parse_args()

    asyncio.run(create_admin(args.email, args.password, args.name))
