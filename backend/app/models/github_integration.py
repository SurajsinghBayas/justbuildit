import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GitHubIntegration(Base):
    __tablename__ = "github_integrations"

    id:              Mapped[str]            = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id:      Mapped[str]            = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), unique=True, nullable=False)
    organization_id: Mapped[str]            = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    repo_name:       Mapped[str]            = mapped_column(String(255), nullable=False)
    repo_url:        Mapped[str]            = mapped_column(Text, nullable=False)
    access_token:    Mapped[Optional[str]]  = mapped_column(Text, nullable=True)     # encrypted at app layer
    webhook_secret:  Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    github_app_id:   Mapped[Optional[str]]  = mapped_column(String(100), nullable=True)
    installation_id: Mapped[Optional[int]]  = mapped_column(BigInteger, nullable=True)
    is_active:       Mapped[bool]           = mapped_column(Boolean, default=True, nullable=False)
    created_at:      Mapped[datetime]       = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at:      Mapped[datetime]       = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="github_integration")
    events:  Mapped[list]      = relationship("GitHubEvent", back_populates="integration")


class GitHubEvent(Base):
    __tablename__ = "github_events"

    id:              Mapped[str]            = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    integration_id:  Mapped[str]            = mapped_column(ForeignKey("github_integrations.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id: Mapped[str]            = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type:      Mapped[str]            = mapped_column(String(100), nullable=False)   # 'push', 'pull_request', 'issues'
    payload:         Mapped[dict]           = mapped_column(JSONB, default=dict, nullable=False, server_default="{}")
    sha:             Mapped[Optional[str]]  = mapped_column(String(100), nullable=True)
    pr_number:       Mapped[Optional[int]]  = mapped_column(Integer, nullable=True)
    branch:          Mapped[Optional[str]]  = mapped_column(String(255), nullable=True)
    author:          Mapped[Optional[str]]  = mapped_column(String(255), nullable=True)
    message:         Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    created_at:      Mapped[datetime]       = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    integration: Mapped["GitHubIntegration"] = relationship("GitHubIntegration", back_populates="events")
