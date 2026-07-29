"""TEST FIXTURE: pengujian labelisasi kamus sentimen dengan data & kamus uji sintetis."""

from datetime import UTC, datetime

import pytest

from app.services.labeling import score_text


def test_score_text_positive():
    result = score_text("bagus mantap", {"bagus": 1.0, "mantap": 1.0}, {})
    assert result.positive_score == 2.0
    assert result.negative_score == 0.0
    assert result.sentiment_score == 2.0
    assert result.label == "positive"


def test_score_text_negative():
    result = score_text("jelek parah", {}, {"jelek": 1.0, "parah": 1.0})
    assert result.negative_score == 2.0
    assert result.sentiment_score == -2.0
    assert result.label == "negative"


def test_score_text_neutral_when_balanced():
    result = score_text("bagus jelek", {"bagus": 1.0}, {"jelek": 1.0})
    assert result.sentiment_score == 0.0
    assert result.label == "neutral"


def test_score_text_neutral_when_no_match():
    result = score_text("kata acak tanpa makna sentimen", {"bagus": 1.0}, {"jelek": 1.0})
    assert result.sentiment_score == 0.0
    assert result.label == "neutral"


def test_score_text_word_boundary_no_partial_match():
    # "bagus" tidak boleh cocok pada substring "bagusnyaaa" (sudah beda token setelah stemming
    # sehingga kasus ini jarang terjadi, tapi word-boundary tetap harus dijaga).
    result = score_text("baguskan sesuatu", {"bagus": 1.0}, {})
    assert result.positive_score == 0.0


@pytest.fixture
def labeled_dataset_setup(client, auth_headers, db_session):
    from app.models.app_source import AppSource
    from app.models.dataset import Dataset
    from app.models.review import PreprocessingResult, Review
    from app.services.dedup import compute_fingerprint

    source = AppSource(app_name="PLN Mobile", package_id="com.icon.pln.labeltest")
    db_session.add(source)
    db_session.flush()
    dataset = Dataset(name="Dataset Label Uji", app_source_id=source.id)
    db_session.add(dataset)
    db_session.flush()

    # final_text sudah disiapkan manual (melewati tahap preprocessing) agar deterministik.
    samples = [
        ("bagus mantap sekali", "positive"),
        ("jelek parah sekali", "negative"),
        ("aplikasi biasa saja", "neutral"),
    ]
    reviews = []
    for i, (final_text, _) in enumerate(samples):
        fp = compute_fingerprint(str(source.id), final_text, f"user{i}", None)
        review = Review(
            dataset_id=dataset.id,
            app_source_id=source.id,
            review_id=f"label-{i}",
            fingerprint=fp,
            content=final_text,
            fetched_at=datetime.now(UTC),
        )
        db_session.add(review)
        db_session.flush()
        db_session.add(
            PreprocessingResult(
                review_id=review.id,
                case_folded_text=final_text,
                cleaned_text=final_text,
                normalized_text=final_text,
                tokens=final_text.split(),
                tokens_no_stopword=final_text.split(),
                stemmed_text=final_text,
                final_text=final_text,
                processed_at=datetime.now(UTC),
            )
        )
        reviews.append(review)
    db_session.commit()

    # Kamus uji: kata-kata di atas didaftarkan sebagai kamus positif/negatif.
    client.post("/api/v1/dictionaries/positive", json={"word": "bagus", "weight": 1.0}, headers=auth_headers)
    client.post("/api/v1/dictionaries/positive", json={"word": "mantap", "weight": 1.0}, headers=auth_headers)
    client.post("/api/v1/dictionaries/negative", json={"word": "jelek", "weight": 1.0}, headers=auth_headers)
    client.post("/api/v1/dictionaries/negative", json={"word": "parah", "weight": 1.0}, headers=auth_headers)

    return dataset, reviews


def test_binary_labeling_excludes_neutral_from_training(client, auth_headers, labeled_dataset_setup):
    dataset, reviews = labeled_dataset_setup

    resp = client.post(
        f"/api/v1/datasets/{dataset.id}/label", json={"label_mode": "binary"}, headers=auth_headers
    )
    assert resp.status_code == 200

    summary = None
    for _ in range(100):
        summary_resp = client.get(f"/api/v1/datasets/{dataset.id}/label-summary", headers=auth_headers)
        summary = summary_resp.json()
        if summary["status"] == "completed":
            break
        import time

        time.sleep(0.05)

    assert summary["status"] == "completed"
    assert summary["positive_count"] == 1
    assert summary["negative_count"] == 1
    assert summary["neutral_count"] == 1
    assert summary["excluded_from_training"] == 1  # netral dikeluarkan pada mode binary


def test_ternary_labeling_includes_neutral(client, auth_headers, labeled_dataset_setup):
    dataset, reviews = labeled_dataset_setup

    client.post(f"/api/v1/datasets/{dataset.id}/label", json={"label_mode": "ternary"}, headers=auth_headers)

    summary = None
    for _ in range(100):
        summary_resp = client.get(f"/api/v1/datasets/{dataset.id}/label-summary", headers=auth_headers)
        summary = summary_resp.json()
        if summary["status"] == "completed":
            break
        import time

        time.sleep(0.05)

    assert summary["excluded_from_training"] == 0
    assert summary["neutral_count"] == 1


def test_labeling_without_preprocessing_returns_400(client, auth_headers):
    source_resp = client.post(
        "/api/v1/app-sources",
        json={"app_name": "PLN Mobile", "package_id": "com.icon.pln.nolabel"},
        headers=auth_headers,
    )
    dataset_resp = client.post(
        "/api/v1/datasets",
        json={"name": "Dataset Belum Preprocess", "app_source_id": source_resp.json()["id"]},
        headers=auth_headers,
    )
    resp = client.post(
        f"/api/v1/datasets/{dataset_resp.json()['id']}/label",
        json={"label_mode": "binary"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
