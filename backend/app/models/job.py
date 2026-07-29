from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import CollectionMethod, JobStatus
from app.models.types import GUID


class CollectionJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "collection_jobs"

    app_source_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("app_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dataset_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )

    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    max_reviews: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    language: Mapped[str] = mapped_column(String(10), default="id", nullable=False)
    country: Mapped[str] = mapped_column(String(10), default="id", nullable=False)
    sort_order: Mapped[str] = mapped_column(String(20), default="newest", nullable=False)
    method: Mapped[str] = mapped_column(
        String(30), default=CollectionMethod.GOOGLE_PLAY_SCRAPER.value, nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20), default=JobStatus.QUEUED.value, nullable=False, index=True
    )
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    found_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_log: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    requested_by: Mapped[str | None] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class ImportJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "import_jobs"

    dataset_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[str] = mapped_column(
        String(20), default=JobStatus.QUEUED.value, nullable=False, index=True
    )
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    invalid_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_report: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    requested_by: Mapped[str | None] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
