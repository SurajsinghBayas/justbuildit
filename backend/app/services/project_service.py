from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_user(self, user_id: str) -> List[Project]:
        result = await self.db.execute(select(Project).where(Project.created_by == user_id))
        return list(result.scalars().all())

    async def get(self, project_id: str) -> Optional[Project]:
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def create(self, payload: ProjectCreate, owner_id: str) -> Project:
        project = Project(**payload.model_dump(), created_by=owner_id)
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def update(self, project_id: str, payload: ProjectUpdate) -> Project:
        project = await self.get(project_id)
        if not project:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Project not found")
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(project, field, value)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete(self, project_id: str) -> None:
        project = await self.get(project_id)
        if project:
            await self.db.delete(project)
            await self.db.commit()
