from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.db.session import engine

# Import all models so Alembic picks them up
from app.models import user, organization, project, task, membership  # noqa: F401


async def init_db() -> None:
    """Create all tables. Use Alembic migrations in production."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """Drop all tables. Use only in tests."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
