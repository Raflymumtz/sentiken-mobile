import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.app_source import AppSourceResponse
from app.schemas.common import ORMModel


class DatasetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    app_source_id: uuid.UUID
    description: str | None = Field(default=None, max_length=1000)
    period_start: date | None = None
    period_end: date | None = None
    label_mode: str = Field(default="binary", pattern="^(binary|ternary)$")


class DatasetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    period_start: date | None = None
    period_end: date | None = None
    label_mode: str | None = Field(default=None, pattern="^(binary|ternary)$")


class DatasetResponse(ORMModel):
    id: uuid.UUID
    name: str
    app_source_id: uuid.UUID
    description: str | None
    period_start: date | None
    period_end: date | None
    preprocessing_status: str
    labeling_status: str
    label_mode: str
    training_status: str
    created_at: datetime
    updated_at: datetime
    review_count: int = 0
    app_source: AppSourceResponse | None = None


class DatasetSummaryResponse(BaseModel):
    dataset_id: uuid.UUID
    total_reviews: int
    rating_distribution: dict[str, int]
    label_distribution: dict[str, int]
    preprocessing_status: str
    labeling_status: str
    training_status: str
    active_training_run_id: uuid.UUID | None = None
