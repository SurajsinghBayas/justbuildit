import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id:                   Mapped[str]           = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id:           Mapped[str]           = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id:      Mapped[str]           = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_to:          Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by:           Mapped[str]           = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    title:                Mapped[str]           = mapped_column(String(512), nullable=False)
    description:          Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status:               Mapped[str]           = mapped_column(String(50), nullable=False, default="TODO", index=True)
    priority:             Mapped[str]           = mapped_column(String(50), nullable=False, default="MEDIUM")
    deadline:             Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_time:       Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)  # hours
    actual_time:          Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)  # hours
    tags:                 Mapped[list]           = mapped_column(ARRAY(String), default=list, nullable=False, server_default="{}")
    github_issue_number:  Mapped[Optional[int]]  = mapped_column(Integer, nullable=True)
    is_deleted:           Mapped[bool]           = mapped_column(Boolean, default=False, nullable=False)
    created_at:           Mapped[datetime]       = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at:           Mapped[datetime]       = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    project:     Mapped["Project"]    = relationship("Project", back_populates="tasks")
    assignee:    Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to])
    creator:     Mapped["User"]       = relationship("User", foreign_keys=[created_by])
    comments:    Mapped[list]         = relationship("Comment", back_populates="task")
    predictions: Mapped[list]         = relationship("AIPrediction", back_populates="task")
