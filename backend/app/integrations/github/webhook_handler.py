from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.logger import get_logger

logger = get_logger(__name__)


async def handle_github_event(event: str, payload: dict, db: AsyncSession) -> None:
    """Route GitHub webhook events to appropriate handlers."""
    logger.info(f"GitHub event received: {event}")

    handlers = {
        "issues": _handle_issues,
        "pull_request": _handle_pull_request,
        "push": _handle_push,
    }

    handler = handlers.get(event)
    if handler:
        await handler(payload, db)
    else:
        logger.debug(f"No handler for GitHub event: {event}")


async def _handle_issues(payload: dict, db: AsyncSession) -> None:
    action = payload.get("action")
    issue = payload.get("issue", {})
    logger.info(f"Issue {action}: #{issue.get('number')} - {issue.get('title')}")
    # TODO: Sync GitHub issue with Task model


async def _handle_pull_request(payload: dict, db: AsyncSession) -> None:
    action = payload.get("action")
    pr = payload.get("pull_request", {})
    logger.info(f"PR {action}: #{pr.get('number')} - {pr.get('title')}")
    # TODO: Update task status when PR is merged


async def _handle_push(payload: dict, db: AsyncSession) -> None:
    ref = payload.get("ref", "")
    commits = payload.get("commits", [])
    logger.info(f"Push to {ref}: {len(commits)} commits")
    # TODO: Parse commit messages for task references (#task-id)
