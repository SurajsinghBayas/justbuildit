"""
seed_db.py — Populate database with sample data for local development.
Usage: python scripts/seed_db.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.models.organization import Organization
from backend.app.models.project import Project
from backend.app.models.task import Task
from backend.app.core.security import hash_password


async def seed():
    async with AsyncSessionLocal() as db:
        # Create test user
        user = User(
            name="Alice Dev",
            email="alice@justbuildit.dev",
            hashed_password=hash_password("password123"),
        )
        db.add(user)
        await db.flush()

        # Create organization
        org = Organization(name="justbuildit HQ", slug="justbuildit-hq", owner_id=user.id)
        db.add(org)
        await db.flush()

        # Create projects
        projects = [
            Project(name="Project Alpha", description="Main product", organization_id=org.id, owner_id=user.id),
            Project(name="Project Beta", description="Side project", organization_id=org.id, owner_id=user.id),
        ]
        for p in projects:
            db.add(p)
        await db.flush()

        # Create tasks
        task_data = [
            ("Implement login flow", "todo", "high", projects[0].id),
            ("Build Kanban board", "in_progress", "high", projects[0].id),
            ("Write API tests", "todo", "medium", projects[0].id),
            ("Deploy to staging", "done", "critical", projects[0].id),
            ("Set up CI/CD", "in_review", "medium", projects[1].id),
        ]
        for title, status, priority, project_id in task_data:
            db.add(Task(title=title, status=status, priority=priority, project_id=project_id, assignee_id=user.id))

        await db.commit()
        print("✅ Database seeded successfully!")
        print(f"   User: alice@justbuildit.dev / password123")
        print(f"   Organization: justbuildit HQ")
        print(f"   Projects: {[p.name for p in projects]}")


if __name__ == "__main__":
    asyncio.run(seed())
