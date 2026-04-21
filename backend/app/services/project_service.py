from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.membership import Membership
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_user(self, user_id: str) -> List[Project]:
        """Return all projects in orgs the user belongs to (member or owner)."""
        # Get org IDs the user is a member of
        org_result = await self.db.execute(
            select(Membership.organization_id).where(Membership.user_id == user_id)
        )
        org_ids = [row[0] for row in org_result.fetchall()]
        if not org_ids:
            return []
        result = await self.db.execute(
            select(Project)
            .where(Project.organization_id.in_(org_ids))
            .where(Project.is_deleted == False)
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, project_id: str) -> Optional[Project]:
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def create(self, payload: ProjectCreate, owner_id: str) -> Project:
        project = Project(
            name=payload.name,
            description=payload.description,
            status=payload.status,
            organization_id=payload.organization_id,
            created_by=owner_id,
        )
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
            project.is_deleted = True
            await self.db.commit()
