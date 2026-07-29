import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import ORMModel


class CollectionJobCreate(BaseModel):
    app_source_id: uuid.UUID
    dataset_id: uuid.UUID
    period_start: date | None = None
    period_end: date | None = None
    max_reviews: int = Field(default=1000, gt=0, le=20000)
    language: str = Field(default="id", min_length=2, max_length=10)
    country: str = Field(default="id", min_length=2, max_length=10)
    sort_order: str = Field(default="newest", pattern="^(newest|rating|relevance)$")
    method: str = Field(default="google_play_scraper")

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_start and self.period_end and self.period_start > self.period_end:
            raise ValueError("Tanggal awal tidak boleh setelah tanggal akhir.")
        return self


class CollectionJobResponse(ORMModel):
    id: uuid.UUID
    app_source_id: uuid.UUID
    dataset_id: uuid.UUID
    period_start: date | None
    period_end: date | None
    max_reviews: int
    language: str
    country: str
    sort_order: str
    method: str
    status: str
    progress_percent: float
    found_count: int
    new_count: int
    duplicate_count: int
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ImportPreviewRequest(BaseModel):
    delimiter: str = ","


class ImportPreviewRow(BaseModel):
    row_number: int
    data: dict[str, str | None]
    is_valid: bool
    errors: list[str]


class ImportPreviewResponse(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    detected_columns: list[str]
    missing_required_columns: list[str]
    sample_rows: list[ImportPreviewRow]
    upload_token: str


class ImportExecuteRequest(BaseModel):
    upload_token: str


class ImportJobResponse(ORMModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    filename: str
    status: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    new_count: int
    duplicate_count: int
    error_message: str | None
    validation_report: dict
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
