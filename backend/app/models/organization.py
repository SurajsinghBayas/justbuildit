import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id:         Mapped[str]           = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    name:       Mapped[str]           = mapped_column(String(255), nullable=False)
    slug:       Mapped[str]           = mapped_column(String(100), unique=True, nullable=False, index=True)
    logo_url:   Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id:   Mapped[str]           = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    is_deleted: Mapped[bool]          = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime]      = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    owner:       Mapped["User"]  = relationship("User", back_populates="organizations", foreign_keys=[owner_id])
    memberships: Mapped[list]    = relationship("Membership", back_populates="organization")
    projects:    Mapped[list]    = relationship("Project", back_populates="organization")
