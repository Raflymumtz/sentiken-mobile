from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPrimaryKeyMixin
from app.models.enums import LabelMode
from app.models.types import GUID

if TYPE_CHECKING:
    from app.models.review import Review


class SentimentLabel(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "sentiment_labels"

    review_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dataset_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label_mode: Mapped[str] = mapped_column(String(10), default=LabelMode.BINARY.value, nullable=False)

    positive_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    negative_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    label: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    is_excluded_from_training: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    labeled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    review: Mapped["Review"] = relationship(back_populates="sentiment_labels")
