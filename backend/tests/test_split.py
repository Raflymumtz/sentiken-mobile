"""TEST FIXTURE: pengujian split data memakai label uji sintetis (bukan hasil penelitian)."""

from datetime import UTC, datetime

import pytest

from app.services.dedup import compute_fingerprint


def _make_labeled_reviews(db_session, dataset, source, labels: list[str]):
    from app.models.label import SentimentLabel
    from app.models.review import Review

    reviews = []
    for i, label in enumerate(labels):
        content = f"ulasan uji ke-{i} dengan label {label}"
        fp = compute_fingerprint(str(source.id), content, f"user{i}", None)
        review = Review(
            dataset_id=dataset.id,
            app_source_id=source.id,
            review_id=f"split-{i}",
            fingerprint=fp,
            content=content,
            fetched_at=datetime.now(UTC),
        )
        db_session.add(review)
        db_session.flush()
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
        reviews.append(review)
    db_session.commit()
    return reviews


@pytest.fixture
def dataset_and_source(client, auth_headers, db_session):
    from app.models.app_source import AppSource
    from app.models.dataset import Dataset

    source = AppSource(app_name="PLN Mobile", package_id="com.icon.pln.splittest")
    db_session.add(source)
    db_session.flush()
    dataset = Dataset(name="Dataset Split Uji", app_source_id=source.id, label_mode="binary")
    db_session.add(dataset)
    db_session.commit()
    db_session.refresh(dataset)
    return dataset, source


def test_split_success_with_balanced_classes(client, auth_headers, db_session, dataset_and_source):
    dataset, source = dataset_and_source
    _make_labeled_reviews(db_session, dataset, source, ["positive"] * 10 + ["negative"] * 10)

    resp = client.post(
        f"/api/v1/datasets/{dataset.id}/split",
        json={
            "train_size": 0.8,
            "test_size": 0.2,
            "random_state": 42,
            "stratify": True,
            "label_mode": "binary",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["train_count"] == 16
    assert body["test_count"] == 4
    assert body["class_distribution"] == {"positive": 10, "negative": 10}


def test_split_reproducible_with_same_random_state(client, auth_headers, db_session, dataset_and_source):
    dataset, source = dataset_and_source
    _make_labeled_reviews(db_session, dataset, source, ["positive"] * 10 + ["negative"] * 10)

    resp1 = client.post(
        f"/api/v1/datasets/{dataset.id}/split",
        json={
            "train_size": 0.8,
            "test_size": 0.2,
            "random_state": 42,
            "stratify": True,
            "label_mode": "binary",
        },
        headers=auth_headers,
    )
    resp2 = client.post(
        f"/api/v1/datasets/{dataset.id}/split",
        json={
            "train_size": 0.8,
            "test_size": 0.2,
            "random_state": 42,
            "stratify": True,
            "label_mode": "binary",
        },
        headers=auth_headers,
    )
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    splits_resp = client.get(f"/api/v1/datasets/{dataset.id}/splits", headers=auth_headers)
    assert len(splits_resp.json()) == 2


def test_split_fails_when_class_too_small_for_stratify(client, auth_headers, db_session, dataset_and_source):
    dataset, source = dataset_and_source
    _make_labeled_reviews(db_session, dataset, source, ["positive"] * 10 + ["negative"] * 1)

    resp = client.post(
        f"/api/v1/datasets/{dataset.id}/split",
        json={
            "train_size": 0.8,
            "test_size": 0.2,
            "random_state": 42,
            "stratify": True,
            "label_mode": "binary",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "negative" in resp.json()["error"]["message"]


def test_split_fails_with_insufficient_data(client, auth_headers, db_session, dataset_and_source):
    dataset, source = dataset_and_source
    _make_labeled_reviews(db_session, dataset, source, ["positive"])

    resp = client.post(
        f"/api/v1/datasets/{dataset.id}/split",
        json={
            "train_size": 0.8,
            "test_size": 0.2,
            "random_state": 42,
            "stratify": False,
            "label_mode": "binary",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_split_invalid_train_test_size_sum_rejected(client, auth_headers, dataset_and_source):
    dataset, source = dataset_and_source
    resp = client.post(
        f"/api/v1/datasets/{dataset.id}/split",
        json={
            "train_size": 0.9,
            "test_size": 0.3,
            "random_state": 42,
            "stratify": True,
            "label_mode": "binary",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422
