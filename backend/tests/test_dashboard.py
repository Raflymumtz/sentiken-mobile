"""TEST FIXTURE: pengujian endpoint dashboard dengan data uji sintetis kecil."""

from datetime import UTC, date, datetime

import pytest

from app.services.dedup import compute_fingerprint


def test_dashboard_summary_empty_state_has_no_fake_metrics(client, auth_headers):
    resp = client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["has_data"] is False
    assert body["total_reviews"] == 0
    assert body["total_datasets"] == 0
    assert body["active_model_version"] is None
    assert body["active_metrics"] is None
    assert body["sentiment_counts"] == {"positive": 0, "negative": 0, "neutral": 0}


@pytest.fixture
def populated_dashboard(client, auth_headers, db_session):
    from app.models.app_source import AppSource
    from app.models.dataset import Dataset
    from app.models.label import SentimentLabel
    from app.models.review import PreprocessingResult, Review

    pln = AppSource(app_name="PLN Mobile", package_id="com.icon.pln.dashtest")
    mypertamina = AppSource(app_name="MyPertamina", package_id="com.pertamina.mp.dashtest")
    db_session.add_all([pln, mypertamina])
    db_session.flush()

    dataset_pln = Dataset(name="Dataset PLN Dash", app_source_id=pln.id, label_mode="binary")
    dataset_mp = Dataset(name="Dataset MyPertamina Dash", app_source_id=mypertamina.id, label_mode="binary")
    db_session.add_all([dataset_pln, dataset_mp])
    db_session.flush()

    samples = [
        (pln, dataset_pln, "bagus mantap sekali", "positive", 5, date(2026, 1, 10)),
        (pln, dataset_pln, "jelek lambat parah", "negative", 1, date(2026, 2, 10)),
        (mypertamina, dataset_mp, "cepat dan mudah", "positive", 4, date(2026, 1, 15)),
    ]
    for i, (source, dataset, text, label, score, review_date) in enumerate(samples):
        fp = compute_fingerprint(str(source.id), text, f"user{i}", review_date)
        review = Review(
            dataset_id=dataset.id,
            app_source_id=source.id,
            review_id=f"dash-{i}",
            fingerprint=fp,
            content=text,
            score=score,
            review_date=review_date,
            fetched_at=datetime.now(UTC),
        )
        db_session.add(review)
        db_session.flush()
        db_session.add(
            PreprocessingResult(
                review_id=review.id,
                case_folded_text=text,
                cleaned_text=text,
                normalized_text=text,
                tokens=text.split(),
                tokens_no_stopword=text.split(),
                stemmed_text=text,
                final_text=text,
                processed_at=datetime.now(UTC),
            )
        )
        db_session.add(
            SentimentLabel(
                review_id=review.id,
                dataset_id=dataset.id,
                label_mode="binary",
                positive_score=1.0 if label == "positive" else 0.0,
                negative_score=1.0 if label == "negative" else 0.0,
                sentiment_score=1.0 if label == "positive" else -1.0,
                label=label,
                is_excluded_from_training=False,
                labeled_at=datetime.now(UTC),
            )
        )
    db_session.commit()
    return pln, mypertamina


def test_dashboard_summary_reflects_real_counts(client, auth_headers, populated_dashboard):
    resp = client.get("/api/v1/dashboard/summary", headers=auth_headers)
    body = resp.json()
    assert body["has_data"] is True
    assert body["total_reviews"] == 3
    assert body["total_reviews_pln_mobile"] == 2
    assert body["total_reviews_mypertamina"] == 1
    assert body["sentiment_counts"]["positive"] == 2
    assert body["sentiment_counts"]["negative"] == 1


def test_sentiment_comparison_per_app(client, auth_headers, populated_dashboard):
    resp = client.get("/api/v1/dashboard/sentiment-comparison", headers=auth_headers)
    assert resp.status_code == 200
    items = {item["app_name"]: item for item in resp.json()["items"]}
    assert items["PLN Mobile"]["total_reviews"] == 2
    assert items["PLN Mobile"]["positive_count"] == 1
    assert items["PLN Mobile"]["negative_count"] == 1
    assert items["MyPertamina"]["total_reviews"] == 1


def test_sentiment_trend_grouped_by_month(client, auth_headers, populated_dashboard):
    resp = client.get("/api/v1/dashboard/sentiment-trend?granularity=month", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["granularity"] == "month"
    assert len(body["points"]) >= 2


def test_rating_distribution_per_app(client, auth_headers, populated_dashboard):
    resp = client.get("/api/v1/dashboard/rating-distribution", headers=auth_headers)
    assert resp.status_code == 200
    items = {item["app_name"]: item for item in resp.json()["items"]}
    assert items["PLN Mobile"]["distribution"]["5"] == 1
    assert items["PLN Mobile"]["distribution"]["1"] == 1


def test_frequent_terms_reflects_actual_dataset_words(client, auth_headers, populated_dashboard):
    resp = client.get("/api/v1/dashboard/frequent-terms", headers=auth_headers)
    assert resp.status_code == 200
    terms = [item["term"] for item in resp.json()["terms"]]
    assert "mantap" in terms or "bagus" in terms
