from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)
from app.security import (
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.services.audit import write_audit_log

router = APIRouter(prefix="/auth", tags=["Autentikasi"])

# Refresh token yang sudah di-revoke (logout). Disimpan in-memory karena
# skala penelitian ini single-instance; untuk produksi ganti dengan Redis set.
_revoked_refresh_jti: set[str] = set()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email atau kata sandi salah.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Akun tidak aktif.")

    user.last_login_at = datetime.now(UTC)
    db.commit()

    write_audit_log(db, user_id=user.id, action="login", entity_type="user", entity_id=str(user.id))

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        token_payload = decode_token(payload.refresh_token, expected_type="refresh")
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    if token_payload["jti"] in _revoked_refresh_jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token sudah tidak berlaku."
        )

    user = db.get(User, token_payload["sub"])
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Pengguna tidak valid.")

    # Rotasi refresh token: token lama langsung dicabut setelah dipakai.
    _revoked_refresh_jti.add(token_payload["jti"])

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/logout")
def logout(payload: LogoutRequest, current_user: User = Depends(get_current_user)):
    try:
        token_payload = decode_token(payload.refresh_token, expected_type="refresh")
        _revoked_refresh_jti.add(token_payload["jti"])
    except InvalidTokenError:
        pass
    return {"message": "Berhasil keluar."}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
