import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class DictionaryWordCreate(BaseModel):
    word: str = Field(min_length=1, max_length=255)
    weight: float = Field(default=1.0, gt=0)


class DictionaryWordUpdate(BaseModel):
    word: str | None = Field(default=None, min_length=1, max_length=255)
    weight: float | None = Field(default=None, gt=0)


class DictionaryWordResponse(ORMModel):
    id: uuid.UUID
    word: str
    weight: float
    created_at: datetime
    updated_at: datetime


class NormalizationEntryCreate(BaseModel):
    informal_word: str = Field(min_length=1, max_length=255)
    formal_word: str = Field(min_length=1, max_length=255)


class NormalizationEntryUpdate(BaseModel):
    informal_word: str | None = Field(default=None, min_length=1, max_length=255)
    formal_word: str | None = Field(default=None, min_length=1, max_length=255)


class NormalizationEntryResponse(ORMModel):
    id: uuid.UUID
    informal_word: str
    formal_word: str
    created_at: datetime
    updated_at: datetime


class StopwordCreate(BaseModel):
    word: str = Field(min_length=1, max_length=255)


class StopwordResponse(ORMModel):
    id: uuid.UUID
    word: str
    created_at: datetime
    updated_at: datetime


class DictionaryImportReport(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    inserted: int
    duplicates_skipped: int
    errors: list[str]
