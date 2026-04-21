import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.logger import get_logger
from app.models.github_integration import GitHubIntegration, GitHubEvent
from app.models.task import Task
from app.models.project import Project

logger = get_logger(__name__)


async def _get_integration(payload: dict, db: AsyncSession):
    repo_name = payload.get("repository", {}).get("full_name")
    if not repo_name:
        return None
    # Case-insensitive match to handle GitHub casing differences
    from sqlalchemy import func
    result = await db.execute(
        select(GitHubIntegration).where(
            func.lower(GitHubIntegration.repo_name) == repo_name.lower()
        )
    )
    integrations = result.scalars().all()
    if not integrations:
        return None
    # Prefer the one with an access token (active integration)
    for i in integrations:
        if i.access_token:
            return i
    return integrations[0]


async def handle_github_event(event: str, payload: dict, db: AsyncSession) -> None:
    """Route GitHub webhook events to appropriate handlers."""
    logger.info(f"GitHub event received: {event}")

    integration = await _get_integration(payload, db)
    if not integration:
        logger.debug(f"No integration found for repo in event: {event}")
        return

    handlers = {
        "issues": _handle_issues,
        "pull_request": _handle_pull_request,
        "push": _handle_push,
    }

    handler = handlers.get(event)
    if handler:
        await handler(payload, integration, db)
    else:
        logger.debug(f"No handler for GitHub event: {event}")


async def _handle_issues(payload: dict, integration: GitHubIntegration, db: AsyncSession) -> None:
    action = payload.get("action")
    issue = payload.get("issue", {})
    issue_number = issue.get("number")
    title = issue.get("title", "")[:512]
    body = issue.get("body") or ""
    author = issue.get("user", {}).get("login", "")
    
    logger.info(f"Issue {action}: #{issue_number} - {title}")

    github_event = GitHubEvent(
        integration_id=integration.id,
        organization_id=integration.organization_id,
        event_type="issues",
        payload=payload,
        author=author,
    )
    db.add(github_event)

    result = await db.execute(
        select(Task).where(
            Task.project_id == integration.project_id,
            Task.github_issue_number == issue_number
        )
    )
    task = result.scalar_one_or_none()

    if action == "opened" and not task:
        project_res = await db.execute(select(Project).where(Project.id == integration.project_id))
        project = project_res.scalar_one_or_none()
        if not project:
            return

        new_task = Task(
            project_id=integration.project_id,
            organization_id=integration.organization_id,
            created_by=project.created_by,
            title=title,
            description=body,
            status="TODO",
            github_issue_number=issue_number,
        )
        db.add(new_task)
        await db.commit()
        logger.info(f"Created task from issue #{issue_number}")

    elif action == "closed" and task:
        task.status = "DONE"
        db.add(task)
        await db.commit()
        logger.info(f"Closed task from issue #{issue_number}")

    elif action == "reopened" and task:
        task.status = "TODO"
        db.add(task)
        await db.commit()
        logger.info(f"Reopened task from issue #{issue_number}")


async def _handle_pull_request(payload: dict, integration: GitHubIntegration, db: AsyncSession) -> None:
    action = payload.get("action")
    pr = payload.get("pull_request", {})
    pr_number = pr.get("number")
    title = pr.get("title", "")
    author = pr.get("user", {}).get("login", "")
    branch = pr.get("head", {}).get("ref", "")

    logger.info(f"PR {action}: #{pr_number} - {title}")

    github_event = GitHubEvent(
        integration_id=integration.id,
        organization_id=integration.organization_id,
        event_type="pull_request",
        payload=payload,
        pr_number=pr_number,
        author=author,
        branch=branch,
    )
    db.add(github_event)
    await db.commit()

    body = pr.get("body") or ""
    text_to_search = f"{title} {body}"
    issue_numbers = _extract_issue_numbers(text_to_search)

    if not issue_numbers:
        return

    for num in issue_numbers:
        result = await db.execute(
            select(Task).where(
                Task.project_id == integration.project_id,
                Task.github_issue_number == num
            )
        )
        task = result.scalar_one_or_none()
        if task:
            if action in ("opened", "reopened", "synchronize"):
                task.status = "IN_REVIEW"
                logger.info(f"Updated task #{num} to IN_REVIEW due to PR #{pr_number}")
            elif action == "closed" and pr.get("merged"):
                task.status = "DONE"
                logger.info(f"Updated task #{num} to DONE due to merged PR #{pr_number}")
            
            db.add(task)
    
    await db.commit()


async def _handle_push(payload: dict, integration: GitHubIntegration, db: AsyncSession) -> None:
    ref = payload.get("ref", "")
    commits = payload.get("commits", [])
    author = payload.get("pusher", {}).get("name", "")

    logger.info(f"Push to {ref}: {len(commits)} commits")

    for commit in commits:
        message = commit.get("message", "")
        sha = commit.get("id", "")
        
        github_event = GitHubEvent(
            integration_id=integration.id,
            organization_id=integration.organization_id,
            event_type="push",
            payload=commit,
            sha=sha,
            author=author,
            message=message,
        )
        db.add(github_event)

        closing_numbers = _extract_closing_issue_numbers(message)
        issue_numbers = _extract_issue_numbers(message)
        
        all_nums = set(closing_numbers + issue_numbers)

        for num in all_nums:
            result = await db.execute(
                select(Task).where(
                    Task.project_id == integration.project_id,
                    Task.github_issue_number == num
                )
            )
            task = result.scalar_one_or_none()
            if task and task.status not in ["DONE"]:
                if num in closing_numbers:
                    task.status = "DONE"
                    logger.info(f"Updated task #{num} to DONE due to closing keyword in commit {sha[:7]}")
                else:
                    task.status = "IN_PROGRESS"
                    logger.info(f"Updated task #{num} to IN_PROGRESS due to commit {sha[:7]}")
                db.add(task)

    await db.commit()


def _extract_issue_numbers(text: str) -> list[int]:
    """Extract all issue numbers formatted like #123."""
    matches = re.findall(r'#(\d+)', text)
    return [int(m) for m in set(matches)]

def _extract_closing_issue_numbers(text: str) -> list[int]:
    """Extract issue numbers formatted with closing keywords like 'fixes #123'."""
    pattern = r'(?i)(?:close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)[:\s]+#(\d+)'
    matches = re.findall(pattern, text)
    return [int(m) for m in set(matches)]
