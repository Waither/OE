from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_key: str
    created_at: datetime
    seed: int
    algorithm_version: str
    parameters: dict[str, Any]
    result_data: Any


class ChartArtifactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    name: str
    media_type: str
    created_at: datetime


class ChartComparisonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_key: str
    run_ids: list[str]
    metric: str
    created_at: datetime


class RunListQuery(BaseModel):
    project_key: str | None = Field(default=None, pattern=r"^p[1-4]$")
    limit: int = Field(default=50, ge=1, le=200)
