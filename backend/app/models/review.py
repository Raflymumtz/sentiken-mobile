from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ReviewSource
from app.models.types import GUID

if TYPE_CHECKING:
    from app.models.dataset import Dataset
    from app.models.label import SentimentLabel


class Review(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("app_source_id", "review_id", name="uq_review_app_source_review_id"),)

    dataset_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    app_source_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("app_sources.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    review_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    thumbs_up_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    review_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    app_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reply_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    reply_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    source: Mapped[str] = mapped_column(String(20), default=ReviewSource.SCRAPED.value, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    dataset: Mapped["Dataset"] = relationship(back_populates="reviews")
    preprocessing_result: Mapped["PreprocessingResult | None"] = relationship(
        back_populates="review", cascade="all, delete-orphan", uselist=False
    )
    sentiment_labels: Mapped[list["SentimentLabel"]] = relationship(
        back_populates="review", cascade="all, delete-orphan"
    )


class PreprocessingResult(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "preprocessing_results"

    review_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("reviews.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    case_folded_text: Mapped[str] = mapped_column(Text, nullable=False)
    cleaned_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    tokens: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    tokens_no_stopword: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    stemmed_text: Mapped[str] = mapped_column(Text, nullable=False)
    final_text: Mapped[str] = mapped_column(Text, nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    review: Mapped["Review"] = relationship(back_populates="preprocessing_result")
