import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id:                  Mapped[str]            = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id:          Mapped[str]            = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id:     Mapped[str]            = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    tasks_total:         Mapped[int]            = mapped_column(default=0, nullable=False)
    tasks_completed:     Mapped[int]            = mapped_column(default=0, nullable=False)
    tasks_pending:       Mapped[int]            = mapped_column(default=0, nullable=False)
    tasks_blocked:       Mapped[int]            = mapped_column(default=0, nullable=False)
    velocity_score:      Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    avg_completion_time: Mapped[Optional[float]] = mapped_column(Numeric(8, 4), nullable=True)
    on_time_rate:        Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    recorded_at:         Mapped[datetime]        = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="analytics")


class AIPrediction(Base):
    __tablename__ = "ai_predictions"

    id:                Mapped[str]            = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id:           Mapped[str]            = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id:   Mapped[str]            = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    predicted_delay:   Mapped[bool]           = mapped_column(Boolean, nullable=False)
    confidence_score:  Mapped[float]          = mapped_column(Numeric(5, 4), nullable=False)
    model_version:     Mapped[Optional[str]]  = mapped_column(String(50), nullable=True)
    features_snapshot: Mapped[dict]           = mapped_column(JSONB, default=dict, nullable=False, server_default="{}")
    created_at:        Mapped[datetime]       = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="predictions")
