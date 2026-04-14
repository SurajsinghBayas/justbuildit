from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.project import Project


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_summary(self, user_id: str, project_id: Optional[str] = None):
        q = select(Task)
        if project_id:
            q = q.where(Task.project_id == project_id)

        result = await self.db.execute(q)
        tasks = result.scalars().all()

        return {
            "total_tasks": len(tasks),
            "completed_tasks": sum(1 for t in tasks if t.status == "done"),
            "in_progress_tasks": sum(1 for t in tasks if t.status == "in_progress"),
            "blocked_tasks": sum(1 for t in tasks if t.status == "blocked"),
            "todo_tasks": sum(1 for t in tasks if t.status == "todo"),
        }

    async def get_velocity(self, user_id: str, weeks: int = 7) -> dict:
        # Stub: return placeholder velocity data
        return {"weeks": list(range(1, weeks + 1)), "completed": [5, 8, 6, 10, 12, 9, 14]}
