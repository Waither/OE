from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.chart_artifact import ChartArtifact


class RunRecord(Base):
    __tablename__ = "run_records"
    __table_args__ = (
        CheckConstraint(
            "project_key IN ('p1', 'p2', 'p3', 'p4')",
            name="ck_run_records_project_key",
        ),
        Index("ix_run_records_project_created", "project_key", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_key: Mapped[str] = mapped_column(String(2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(64), nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    result_data: Mapped[Any] = mapped_column(JSON, nullable=False)

    chart_artifacts: Mapped[list["ChartArtifact"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
