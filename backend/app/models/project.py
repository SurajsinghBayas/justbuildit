import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id:              Mapped[str]           = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str]           = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name:            Mapped[str]           = mapped_column(String(255), nullable=False)
    description:     Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status:          Mapped[str]           = mapped_column(String(50), nullable=False, default="ACTIVE")  # ACTIVE|COMPLETED|ON_HOLD|ARCHIVED
    created_by:      Mapped[str]           = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    is_deleted:      Mapped[bool]          = mapped_column(Boolean, default=False, nullable=False)
    created_at:      Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at:      Mapped[datetime]      = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    organization:       Mapped["Organization"]    = relationship("Organization", back_populates="projects")
    creator:            Mapped["User"]            = relationship("User", foreign_keys=[created_by])
    tasks:              Mapped[list]              = relationship("Task", back_populates="project")
    github_integration: Mapped[Optional[object]]  = relationship("GitHubIntegration", back_populates="project", uselist=False)
    analytics:          Mapped[list]              = relationship("AnalyticsSnapshot", back_populates="project")
