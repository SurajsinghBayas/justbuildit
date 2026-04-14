import asyncio
import hashlib
import hmac
import json
import uuid

import httpx
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.project import Project
from app.models.github_integration import GitHubIntegration
from app.models.task import Task
from app.core.config import settings
from app.core.security import hash_password

WEBHOOK_SECRET = "change-me"
REPO_NAME = "surajbayas/justbuildit"


async def setup_test_data():
    async with AsyncSessionLocal() as session:
        # Create user
        user = User(
            id=str(uuid.uuid4()),
            name="Test User",
            email=f"test{uuid.uuid4().hex[:4]}@example.com",
            password_hash=hash_password("password123")
        )
        session.add(user)
        
        # Create organization
        org = Organization(
            id=str(uuid.uuid4()),
            name="Test Org",
            slug=f"test-org-{uuid.uuid4().hex[:4]}",
            owner_id=user.id
        )
        session.add(org)
        
        # Create project
        project = Project(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            name="Test Project",
            created_by=user.id
        )
        session.add(project)

        # Create GitHub Integration
        integration = GitHubIntegration(
            id=str(uuid.uuid4()),
            project_id=project.id,
            organization_id=org.id,
            repo_name=REPO_NAME,
            repo_url=f"https://github.com/{REPO_NAME}",
            webhook_secret=WEBHOOK_SECRET,
            is_active=True
        )
        session.add(integration)

        await session.commit()
        return user, org, project, integration

async def send_webhook(event_type: str, payload_dict: dict):
    payload_bytes = json.dumps(payload_dict).encode("utf-8")
    mac = hmac.new(WEBHOOK_SECRET.encode("utf-8"), payload_bytes, hashlib.sha256)
    signature = "sha256=" + mac.hexdigest()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/github/webhook",
            content=payload_bytes,
            headers={
                "X-GitHub-Event": event_type,
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json"
            }
        )
        print(f"Webhook response status: {response.status_code}")
        print(f"Webhook response body: {response.text}")

async def test_all():
    print("Setting up DB test data...")
    user, org, proj, integration = await setup_test_data()
    print(f"Created integration for {integration.repo_name} mapped to project {proj.id}")

    # 1. Test Issue Opened
    issue_payload = {
        "action": "opened",
        "issue": {
            "number": 101,
            "title": "Fix the network error API",
            "body": "It returns a 500.",
            "user": {"login": "surajbayas"}
        },
        "repository": {"full_name": REPO_NAME}
    }
    print("\n--- Testing Issue Opened ---")
    await send_webhook("issues", issue_payload)
    
    # 2. Test Push (mentioning issue 101)
    push_payload = {
        "ref": "refs/heads/main",
        "commits": [
            {
                "id": "abc123456",
                "message": "working on the fix #101",
            }
        ],
        "pusher": {"name": "surajbayas"},
        "repository": {"full_name": REPO_NAME}
    }
    print("\n--- Testing Push (Task #101) ---")
    await send_webhook("push", push_payload)

    # 3. Test Pull Request Closed (Merging) mentions #101
    pr_payload = {
        "action": "closed",
        "pull_request": {
            "number": 42,
            "title": "Fix issue",
            "body": "Closes #101",
            "user": {"login": "surajbayas"},
            "head": {"ref": "fix-101"},
            "merged": True
        },
        "repository": {"full_name": REPO_NAME}
    }
    print("\n--- Testing PR Merged (Task #101) ---")
    await send_webhook("pull_request", pr_payload)

    # Validate Task mapping
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Task).where(Task.project_id == proj.id, Task.github_issue_number == 101)
        )
        task = result.scalar_one_or_none()
        print("\n--- Final Task State ---")
        if task:
            print(f"Task found: ID={task.id}, Status={task.status}, Title={task.title}")
            assert task.status == "DONE", f"Expected DONE, got {task.status}"
            print("=> Verification Passed!")
        else:
            print("Task not found!")

if __name__ == "__main__":
    asyncio.run(test_all())
