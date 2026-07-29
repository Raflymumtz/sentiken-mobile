from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.dataset import Dataset


class AppSource(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "app_sources"

    app_name: Mapped[str] = mapped_column(String(255), nullable=False)
    package_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    play_store_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="id", nullable=False)
    country: Mapped[str] = mapped_column(String(10), default="id", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    datasets: Mapped[list["Dataset"]] = relationship(back_populates="app_source")
