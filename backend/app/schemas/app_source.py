import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel


class AppSourceBase(BaseModel):
    app_name: str = Field(min_length=1, max_length=255)
    package_id: str = Field(min_length=3, max_length=255)
    play_store_url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=1000)
    language: str = Field(default="id", min_length=2, max_length=10)
    country: str = Field(default="id", min_length=2, max_length=10)
    is_active: bool = True

    @field_validator("package_id")
    @classmethod
    def validate_package_id(cls, value: str) -> str:
        value = value.strip()
        parts = value.split(".")
        if len(parts) < 2 or not all(parts):
            raise ValueError("Package ID harus berformat seperti 'com.contoh.aplikasi' (minimal dua segmen).")
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._")
        if not set(value) <= allowed:
            raise ValueError("Package ID hanya boleh berisi huruf, angka, titik, dan garis bawah.")
        return value


class AppSourceCreate(AppSourceBase):
    pass


class AppSourceUpdate(BaseModel):
    app_name: str | None = Field(default=None, min_length=1, max_length=255)
    package_id: str | None = Field(default=None, min_length=3, max_length=255)
    play_store_url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=1000)
    language: str | None = Field(default=None, min_length=2, max_length=10)
    country: str | None = Field(default=None, min_length=2, max_length=10)
    is_active: bool | None = None


class AppSourceResponse(ORMModel, AppSourceBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class AppSourceValidationResult(BaseModel):
    package_id: str
    is_valid: bool
    exists_on_play_store: bool
    checked_at: datetime
    detail: str
    play_store_app_name: str | None = None
