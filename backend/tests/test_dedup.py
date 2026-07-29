"""TEST FIXTURE: pengujian logika deduplikasi review dengan data uji sintetis."""

from datetime import UTC, date

from app.services.dedup import compute_fingerprint, find_existing_review


def test_fingerprint_is_deterministic():
    fp1 = compute_fingerprint("source-1", "Aplikasi bagus", "budi", date(2026, 1, 1))
    fp2 = compute_fingerprint("source-1", "Aplikasi bagus", "budi", date(2026, 1, 1))
    assert fp1 == fp2


def test_fingerprint_differs_for_different_content():
    fp1 = compute_fingerprint("source-1", "Aplikasi bagus", "budi", date(2026, 1, 1))
    fp2 = compute_fingerprint("source-1", "Aplikasi jelek", "budi", date(2026, 1, 1))
    assert fp1 != fp2


def test_fingerprint_case_insensitive_username():
    fp1 = compute_fingerprint("source-1", "Sama saja", "Budi", date(2026, 1, 1))
    fp2 = compute_fingerprint("source-1", "Sama saja", "budi", date(2026, 1, 1))
    assert fp1 == fp2


def test_find_existing_review_by_review_id(db_session):
    from datetime import datetime

    from app.models.app_source import AppSource
    from app.models.dataset import Dataset
    from app.models.review import Review

    source = AppSource(app_name="Uji", package_id="com.uji.dedup")
    db_session.add(source)
    db_session.flush()
    dataset = Dataset(name="Dataset Uji", app_source_id=source.id)
    db_session.add(dataset)
    db_session.flush()

    fingerprint = compute_fingerprint(str(source.id), "konten", "user1", date(2026, 1, 1))
    review = Review(
        dataset_id=dataset.id,
        app_source_id=source.id,
        review_id="rev-123",
        fingerprint=fingerprint,
        content="konten",
        username="user1",
        review_date=date(2026, 1, 1),
        fetched_at=datetime.now(UTC),
    )
    db_session.add(review)
    db_session.commit()

    found = find_existing_review(
        db_session, app_source_id=str(source.id), review_id="rev-123", fingerprint="beda"
    )
    assert found is not None
    assert found.id == review.id

    found_by_fp = find_existing_review(
        db_session, app_source_id=str(source.id), review_id=None, fingerprint=fingerprint
    )
    assert found_by_fp is not None
    assert found_by_fp.id == review.id

    not_found = find_existing_review(
        db_session, app_source_id=str(source.id), review_id="rev-lain", fingerprint="lain-lagi"
    )
    assert not_found is None
