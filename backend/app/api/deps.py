from collections.abc import Generator
from math import ceil

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.schemas.common import Pagination
from app.security import InvalidTokenError, decode_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token akses tidak ditemukan. Silakan login kembali.",
        )
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = db.get(User, payload["sub"])
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Pengguna tidak ditemukan atau tidak aktif.",
        )
    return user


class PageParams:
    def __init__(
        self,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=200),
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size


def build_pagination(page_params: PageParams, total_items: int) -> Pagination:
    total_pages = ceil(total_items / page_params.page_size) if total_items else 0
    return Pagination(
        page=page_params.page,
        page_size=page_params.page_size,
        total_items=total_items,
        total_pages=total_pages,
    )
