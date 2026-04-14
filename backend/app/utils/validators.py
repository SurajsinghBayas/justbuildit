import re
from fastapi import HTTPException, status

VALID_STATUSES = {"todo", "in_progress", "in_review", "done", "blocked"}
VALID_PRIORITIES = {"low", "medium", "high", "critical"}
EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_task_status(status: str) -> str:
    if status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{status}'. Must be one of: {sorted(VALID_STATUSES)}",
        )
    return status


def validate_task_priority(priority: str) -> str:
    if priority not in VALID_PRIORITIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid priority '{priority}'. Must be one of: {sorted(VALID_PRIORITIES)}",
        )
    return priority


def validate_email(email: str) -> str:
    if not EMAIL_RE.match(email):
        raise ValueError(f"Invalid email address: {email}")
    return email.lower()
