"""TEST FIXTURE: pengujian prediksi satu teks memakai model yang dilatih dari data uji kecil."""

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
def active_model_setup(client, auth_headers, db_session):
    from app.models.app_source import AppSource
    from app.models.dataset import Dataset
    from app.models.label import SentimentLabel
    from app.models.review import PreprocessingResult, Review

    source = AppSource(app_name="PLN Mobile", package_id="com.icon.pln.predicttest")
    db_session.add(source)
    db_session.flush()
    dataset = Dataset(name="Dataset Prediksi Uji", app_source_id=source.id, label_mode="binary")
    db_session.add(dataset)
    db_session.flush()

    all_texts = [(t, "positive") for t in POSITIVE_TEXTS] + [(t, "negative") for t in NEGATIVE_TEXTS]
    for i, (text, label) in enumerate(all_texts):
        fp = compute_fingerprint(str(source.id), text, f"user{i}", None)
        review = Review(
            dataset_id=dataset.id,
            app_source_id=source.id,
            review_id=f"pred-{i}",
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
        status_resp = client.get(f"/api/v1/training-runs/{run_id}", headers=auth_headers)
        if status_resp.json()["status"] == "completed":
            break
        time.sleep(0.05)

    return dataset, run_id


def test_predict_single_text_with_active_model(client, auth_headers, active_model_setup):
    dataset, run_id = active_model_setup

    resp = client.post(
        "/api/v1/predictions/single",
        json={"text": "aplikasi ini sangat bagus dan mantap"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["predicted_label"] in ("positive", "negative")
    assert body["k_used"] == 3
    assert len(body["neighbors"]) == 3
    assert body["final_text"] != ""
    assert body["training_run_id"] == run_id


def test_predict_single_text_with_explicit_run(client, auth_headers, active_model_setup):
    dataset, run_id = active_model_setup
    resp = client.post(
        "/api/v1/predictions/single",
        json={"text": "pelayanan cepat dan mantap", "training_run_id": run_id},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["training_run_id"] == run_id


def test_predict_without_trained_model_returns_clear_message(client, auth_headers, db_session):
    # Hapus training run aktif dari fixture lain dengan memakai admin baru (DB kosong per test).
    resp = client.post(
        "/api/v1/predictions/single", json={"text": "belum ada model sama sekali"}, headers=auth_headers
    )
    assert resp.status_code == 400
    assert "belum dilatih" in resp.json()["error"]["message"]


def test_prediction_history_records_single_predictions(client, auth_headers, active_model_setup):
    dataset, run_id = active_model_setup
    client.post("/api/v1/predictions/single", json={"text": "bagus mantap sekali"}, headers=auth_headers)
    client.post("/api/v1/predictions/single", json={"text": "jelek parah error"}, headers=auth_headers)

    history_resp = client.get("/api/v1/predictions/history", headers=auth_headers)
    assert history_resp.status_code == 200
    assert history_resp.json()["pagination"]["total_items"] == 2
