from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.audit import AuditLog

_SENSITIVE_KEYS = {"password", "password_hash", "token", "access_token", "refresh_token"}


def _sanitize(detail: dict | None) -> dict:
    if not detail:
        return {}
    return {k: v for k, v in detail.items() if k.lower() not in _SENSITIVE_KEYS}


def write_audit_log(
    db: Session,
    *,
    user_id=None,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    detail: dict | None = None,
    ip_address: str | None = None,
) -> None:
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=_sanitize(detail),
        ip_address=ip_address,
        created_at=datetime.now(UTC),
    )
    db.add(log)
    db.commit()
