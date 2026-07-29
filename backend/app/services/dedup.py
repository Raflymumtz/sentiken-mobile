import hashlib

from sqlalchemy.orm import Session

from app.models.review import Review


def compute_fingerprint(app_source_id: str, content: str, username: str | None, review_date) -> str:
    """Fingerprint deterministik dipakai saat review_id kosong (mis. sebagian data CSV).

    Kombinasi: app_source_id + content + username + review_date.
    """
    normalized_username = (username or "").strip().lower()
    normalized_content = (content or "").strip()
    normalized_date = review_date.isoformat() if hasattr(review_date, "isoformat") else str(review_date or "")
    raw = f"{app_source_id}|{normalized_content}|{normalized_username}|{normalized_date}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def find_existing_review(
    db: Session, *, app_source_id: str, review_id: str | None, fingerprint: str
) -> Review | None:
    """Cek duplikat: prioritaskan review_id (kolom unik bersama app_source_id di DB),
    lalu fallback ke fingerprint (dipakai saat review_id kosong/tidak ada di sumber data)."""
    if review_id:
        existing = (
            db.query(Review)
            .filter(Review.app_source_id == app_source_id, Review.review_id == review_id)
            .first()
        )
        if existing:
            return existing

    return (
        db.query(Review)
        .filter(Review.app_source_id == app_source_id, Review.fingerprint == fingerprint)
        .first()
    )
