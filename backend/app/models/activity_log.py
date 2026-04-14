import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id:              Mapped[str]           = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str]           = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id:         Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action:          Mapped[str]           = mapped_column(String(255), nullable=False)  # e.g. "task.status_changed"
    entity_type:     Mapped[str]           = mapped_column(String(50), nullable=False)   # TASK|PROJECT|COMMENT|MEMBER|INTEGRATION
    entity_id:       Mapped[str]           = mapped_column(UUID(as_uuid=False), nullable=False)
    metadata_:       Mapped[dict]          = mapped_column("metadata", JSONB, default=dict, nullable=False, server_default="{}")
    created_at:      Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    actor: Mapped[Optional["User"]] = relationship("User")
