import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id:            Mapped[str]            = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    email:         Mapped[str]            = mapped_column(String(320), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]]  = mapped_column(Text, nullable=True)         # None = OAuth-only
    name:          Mapped[str]            = mapped_column(String(255), nullable=False)
    avatar_url:    Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    google_id:     Mapped[Optional[str]]  = mapped_column(String(255), unique=True, nullable=True, index=True)
    github_id:     Mapped[Optional[str]]  = mapped_column(String(255), unique=True, nullable=True)
    is_active:     Mapped[bool]           = mapped_column(Boolean, default=True, nullable=False)
    is_superuser:  Mapped[bool]           = mapped_column(Boolean, default=False, nullable=False)
    is_deleted:    Mapped[bool]           = mapped_column(Boolean, default=False, nullable=False)
    created_at:    Mapped[datetime]       = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at:    Mapped[datetime]       = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    organizations: Mapped[list] = relationship("Organization", back_populates="owner", foreign_keys="Organization.owner_id")
    memberships:   Mapped[list] = relationship("Membership", back_populates="user")
