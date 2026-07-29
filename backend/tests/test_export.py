"""TEST FIXTURE: pengujian fitur ekspor (CSV, PNG confusion matrix, PDF ringkasan)."""

import time
from datetime import UTC, datetime

import pytest

from app.services.dedup import compute_fingerprint

POSITIVE_TEXTS = [
    "aplikasi bagus mantap cepat",
    "pelayanan mantap sangat membantu",
    "top sekali bagus responsif",
    "mantap cepat dan mudah dipakai",
    "bagus banget sangat puas",
    "aplikasi mantap top rekomendasi",
]
NEGATIVE_TEXTS = [
    "aplikasi jelek lambat error",
    "parah sekali sering gagal",
    "buruk lambat tidak jelas",
    "error terus jelek banget",
    "lambat parah mengecewakan sekali",
    "jelek error tidak bisa dipakai",
]


@pytest.fixture
def completed_run(client, auth_headers, db_session):
    from app.models.app_source import AppSource
    from app.models.dataset import Dataset
    from app.models.label import SentimentLabel
    from app.models.review import PreprocessingResult, Review

    source = AppSource(app_name="PLN Mobile", package_id="com.icon.pln.exporttest")
    db_session.add(source)
    db_session.flush()
    dataset = Dataset(name="Dataset Export Uji", app_source_id=source.id, label_mode="binary")
    db_session.add(dataset)
    db_session.flush()

    all_texts = [(t, "positive") for t in POSITIVE_TEXTS] + [(t, "negative") for t in NEGATIVE_TEXTS]
    for i, (text, label) in enumerate(all_texts):
        fp = compute_fingerprint(str(source.id), text, f"user{i}", None)
        review = Review(
            dataset_id=dataset.id,
            app_source_id=source.id,
            review_id=f"exp-{i}",
            fingerprint=fp,
            content=text,
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

    split_resp = client.post(
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
    split_id = split_resp.json()["id"]

    train_resp = client.post(
        f"/api/v1/datasets/{dataset.id}/train",
        json={"data_split_id": split_id, "knn_config": {"n_neighbors": 3}},
        headers=auth_headers,
    )
    run_id = train_resp.json()["id"]

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if (
            client.get(f"/api/v1/training-runs/{run_id}", headers=auth_headers).json()["status"]
            == "completed"
        ):
            break
        time.sleep(0.05)

    return dataset, split_id, run_id


def test_export_raw_reviews_csv(client, auth_headers, completed_run):
    dataset, split_id, run_id = completed_run
    resp = client.get(f"/api/v1/datasets/{dataset.id}/export?kind=raw", headers=auth_headers)
    assert resp.status_code == 200
    assert "review_id" in resp.text


def test_export_train_and_test_csv(client, auth_headers, completed_run):
    dataset, split_id, run_id = completed_run
    train_resp = client.get(
        f"/api/v1/datasets/{dataset.id}/splits/{split_id}/export/train", headers=auth_headers
    )
    assert train_resp.status_code == 200
    assert "final_text" in train_resp.text

    test_resp = client.get(
        f"/api/v1/datasets/{dataset.id}/splits/{split_id}/export/test", headers=auth_headers
    )
    assert test_resp.status_code == 200


def test_export_predictions_and_metrics_csv(client, auth_headers, completed_run):
    dataset, split_id, run_id = completed_run
    pred_resp = client.get(f"/api/v1/training-runs/{run_id}/export/predictions", headers=auth_headers)
    assert pred_resp.status_code == 200
    assert "predicted_label" in pred_resp.text

    metrics_resp = client.get(f"/api/v1/training-runs/{run_id}/export/metrics", headers=auth_headers)
    assert metrics_resp.status_code == 200
    assert "accuracy" in metrics_resp.text


def test_export_classification_report_csv(client, auth_headers, completed_run):
    dataset, split_id, run_id = completed_run
    resp = client.get(f"/api/v1/training-runs/{run_id}/export/classification-report", headers=auth_headers)
    assert resp.status_code == 200


def test_export_confusion_matrix_png(client, auth_headers, completed_run):
    dataset, split_id, run_id = completed_run
    resp = client.get(f"/api/v1/training-runs/{run_id}/export/confusion-matrix.png", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert resp.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_export_summary_pdf(client, auth_headers, completed_run):
    dataset, split_id, run_id = completed_run
    resp = client.get(f"/api/v1/training-runs/{run_id}/export/summary.pdf", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:4] == b"%PDF"
