from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, project_id: Optional[str] = None) -> List[Task]:
        q = select(Task)
        if project_id:
            q = q.where(Task.project_id == project_id)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get(self, task_id: str) -> Optional[Task]:
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    async def create(self, payload: TaskCreate) -> Task:
        task = Task(**payload.model_dump())
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def update(self, task_id: str, payload: TaskUpdate) -> Task:
        task = await self.get(task_id)
        if not task:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Task not found")
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(task, field, value)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def update_status(self, task_id: str, status: str) -> Task:
        return await self.update(task_id, TaskUpdate(status=status))

    async def delete(self, task_id: str) -> None:
        task = await self.get(task_id)
        if task:
            await self.db.delete(task)
            await self.db.commit()
