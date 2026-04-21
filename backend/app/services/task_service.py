from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.project import Project
from app.models.membership import Membership
from app.models.github_integration import GitHubIntegration
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.github_service import GitHubService


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, user_id: str, project_id: Optional[str] = None) -> List[Task]:
        """Return tasks scoped to the user's org memberships."""
        if project_id:
            # Return all tasks for this project
            result = await self.db.execute(
                select(Task)
                .where(Task.project_id == project_id, Task.is_deleted == False)
                .order_by(Task.created_at.desc())
            )
            return list(result.scalars().all())

        # No project_id → return tasks from all projects in user's orgs
        org_result = await self.db.execute(
            select(Membership.organization_id).where(Membership.user_id == user_id)
        )
        org_ids = [row[0] for row in org_result.fetchall()]
        if not org_ids:
            return []
        proj_result = await self.db.execute(
            select(Project.id)
            .where(Project.organization_id.in_(org_ids), Project.is_deleted == False)
        )
        proj_ids = [row[0] for row in proj_result.fetchall()]
        if not proj_ids:
            return []
        result = await self.db.execute(
            select(Task)
            .where(Task.project_id.in_(proj_ids), Task.is_deleted == False)
            .order_by(Task.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, task_id: str) -> Optional[Task]:
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    async def create(self, payload: TaskCreate) -> Task:
        task = Task(**payload.model_dump())
        
        # Check if project has a GitHub integration
        int_result = await self.db.execute(
            select(GitHubIntegration).where(GitHubIntegration.project_id == payload.project_id)
        )
        integration = int_result.scalar_one_or_none()
        
        if integration and integration.access_token:
            try:
                gh = GitHubService(integration.access_token)
                owner, repo = integration.repo_name.split("/")
                gh_body = payload.description or ""
                gh_body += "\n\n*(Exported via JustBuildIt)*"
                issue_data = await gh.create_issue(owner, repo, payload.title, gh_body)
                task.github_issue_number = issue_data.get("number")
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to create GitHub issue for task: {e}")

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
            task.is_deleted = True
            await self.db.commit()
