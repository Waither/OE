from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Index, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class ChartComparison(Base):
    __tablename__ = "chart_comparisons"
    __table_args__ = (Index("ix_chart_comparisons_project_created", "project_key", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_key: Mapped[str] = mapped_column(String(2), nullable=False)
    run_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    metric: Mapped[str] = mapped_column(String(32), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
