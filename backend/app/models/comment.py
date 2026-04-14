import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Comment(Base):
    __tablename__ = "comments"

    id:              Mapped[str]       = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id:         Mapped[str]       = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id: Mapped[str]       = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id:         Mapped[str]       = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content:         Mapped[str]       = mapped_column(Text, nullable=False)
    is_deleted:      Mapped[bool]      = mapped_column(Boolean, default=False, nullable=False)
    created_at:      Mapped[datetime]  = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at:      Mapped[datetime]  = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    task:   Mapped["Task"] = relationship("Task", back_populates="comments")
    author: Mapped["User"] = relationship("User")
