"""TEST FIXTURE: pengujian unique constraint pada level database dengan data uji sintetis."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.services.dedup import compute_fingerprint


def test_review_unique_constraint_app_source_and_review_id(db_session):
    from app.models.app_source import AppSource
    from app.models.dataset import Dataset
    from app.models.review import Review

    source = AppSource(app_name="PLN Mobile", package_id="com.icon.pln.uniquetest")
    db_session.add(source)
    db_session.flush()
    dataset = Dataset(name="Dataset Unique Uji", app_source_id=source.id)
    db_session.add(dataset)
    db_session.flush()

    fp1 = compute_fingerprint(str(source.id), "konten pertama", "user1", None)
    review1 = Review(
        dataset_id=dataset.id,
        app_source_id=source.id,
        review_id="dup-review-id",
        fingerprint=fp1,
        content="konten pertama",
        fetched_at=datetime.now(UTC),
    )
    db_session.add(review1)
    db_session.commit()

    fp2 = compute_fingerprint(str(source.id), "konten berbeda", "user2", None)
    review2 = Review(
        dataset_id=dataset.id,
        app_source_id=source.id,
        review_id="dup-review-id",
        fingerprint=fp2,
        content="konten berbeda",
        fetched_at=datetime.now(UTC),
    )
    db_session.add(review2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_app_source_package_id_unique_constraint(db_session):
    from app.models.app_source import AppSource

    db_session.add(AppSource(app_name="PLN Mobile", package_id="com.icon.pln.dupcheck"))
    db_session.commit()

    db_session.add(AppSource(app_name="PLN Mobile Duplikat", package_id="com.icon.pln.dupcheck"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_email_unique_constraint(db_session):
    from app.models.user import User
    from app.security import hash_password

    db_session.add(
        User(
            email="unik@sentiken.local",
            password_hash=hash_password("Password123!"),
            full_name="Unik Satu",
            role="admin",
            is_active=True,
        )
    )
    db_session.commit()

    db_session.add(
        User(
            email="unik@sentiken.local",
            password_hash=hash_password("Password456!"),
            full_name="Unik Dua",
            role="admin",
            is_active=True,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
