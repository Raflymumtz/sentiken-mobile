from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import LabelMode, ProcessingStatus
from app.models.types import GUID

if TYPE_CHECKING:
    from app.models.app_source import AppSource
    from app.models.review import Review


class Dataset(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "datasets"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    app_source_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("app_sources.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)

    preprocessing_status: Mapped[str] = mapped_column(
        String(20), default=ProcessingStatus.PENDING.value, nullable=False
    )
    labeling_status: Mapped[str] = mapped_column(
        String(20), default=ProcessingStatus.PENDING.value, nullable=False
    )
    label_mode: Mapped[str] = mapped_column(String(10), default=LabelMode.BINARY.value, nullable=False)
    training_status: Mapped[str] = mapped_column(
        String(20), default=ProcessingStatus.PENDING.value, nullable=False
    )

    app_source: Mapped["AppSource"] = relationship(back_populates="datasets")
    reviews: Mapped[list["Review"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")
