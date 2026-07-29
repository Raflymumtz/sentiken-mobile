from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class DictionaryPositive(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "dictionary_positive"

    word: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)


class DictionaryNegative(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "dictionary_negative"

    word: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)


class NormalizationDictionary(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "normalization_dictionary"

    informal_word: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    formal_word: Mapped[str] = mapped_column(String(255), nullable=False)


class Stopword(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "stopwords"

    word: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
