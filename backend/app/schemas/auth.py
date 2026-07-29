import re
import uuid

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel

# Regex email longgar (bukan pydantic.EmailStr) karena EmailStr menolak TLD
# reserved seperti ".local"/".internal" yang lazim dipakai untuk admin akun
# single-user pada deployment lokal/riset ini.
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        value = value.strip().lower()
        if not _EMAIL_PATTERN.match(value):
            raise ValueError("Format email tidak valid.")
        return value


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserResponse(ORMModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
