from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user_id
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/summary")
async def analytics_summary(
    project_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    svc = AnalyticsService(db)
    return await svc.get_summary(user_id=user_id, project_id=project_id)


@router.get("/velocity")
async def velocity(
    weeks: int = 7,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    svc = AnalyticsService(db)
    return await svc.get_velocity(user_id=user_id, weeks=weeks)
