# Models package — import all to ensure Alembic and SQLAlchemy discover them
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.project import Project
from app.models.task import Task
from app.models.comment import Comment
from app.models.activity_log import ActivityLog
from app.models.github_integration import GitHubIntegration, GitHubEvent
from app.models.analytics import AnalyticsSnapshot, AIPrediction

__all__ = [
    "User",
    "Organization",
    "Membership",
    "Project",
    "Task",
    "Comment",
    "ActivityLog",
    "GitHubIntegration",
    "GitHubEvent",
    "AnalyticsSnapshot",
    "AIPrediction",
]
