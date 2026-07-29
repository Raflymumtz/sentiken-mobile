"""TEST FIXTURE: pengujian pipeline TF-IDF + K-NN memakai data & label uji sintetis kecil
(BUKAN dataset penelitian). Bertujuan memverifikasi mekanisme training/evaluasi bekerja
benar secara end-to-end, bukan untuk mengklaim akurasi penelitian tertentu."""

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
    "sangat bagus dan cepat prosesnya",
    "mantap sekali membantu pengguna",
    "puas dengan aplikasi bagus ini",
    "cepat mantap bagus sekali rasanya",
]
NEGATIVE_TEXTS = [
    "aplikasi jelek lambat error",
    "parah sekali sering gagal",
    "buruk lambat tidak jelas",
    "error terus jelek banget",
    "lambat parah mengecewakan sekali",
    "jelek error tidak bisa dipakai",
    "buruk sekali sering error terus",
    "parah lambat mengecewakan pengguna",
    "sangat jelek dan buruk pelayanan",
    "error parah lambat sekali rasanya",
]


@pytest.fixture
def trained_split_setup(client, auth_headers, db_session):
    from app.models.app_source import AppSource
    from app.models.dataset import Dataset
    from app.models.label import SentimentLabel
    from app.models.review import PreprocessingResult, Review

    source = AppSource(app_name="PLN Mobile", package_id="com.icon.pln.traintest")
    db_session.add(source)
    db_session.flush()
    dataset = Dataset(name="Dataset Training Uji", app_source_id=source.id, label_mode="binary")
    db_session.add(dataset)
    db_session.flush()

    all_texts = [(t, "positive") for t in POSITIVE_TEXTS] + [(t, "negative") for t in NEGATIVE_TEXTS]
    for i, (text, label) in enumerate(all_texts):
        fp = compute_fingerprint(str(source.id), text, f"user{i}", None)
        review = Review(
            dataset_id=dataset.id,
            app_source_id=source.id,
            review_id=f"train-{i}",
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
    assert split_resp.status_code == 201, split_resp.text
    return dataset, split_resp.json()


def _wait_run_terminal(client, headers, run_id, timeout=10.0):
    deadline = time.monotonic() + timeout
    body = {}
    while time.monotonic() < deadline:
        resp = client.get(f"/api/v1/training-runs/{run_id}", headers=headers)
        body = resp.json()
        if body["status"] in ("completed", "failed"):
            return body
        time.sleep(0.05)
    raise TimeoutError(f"Training run {run_id} belum selesai: {body}")


def test_train_single_model_completes_and_activates(client, auth_headers, trained_split_setup):
    dataset, split = trained_split_setup

    resp = client.post(
        f"/api/v1/datasets/{dataset.id}/train",
        json={"data_split_id": split["id"], "knn_config": {"n_neighbors": 3}},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    run = _wait_run_terminal(client, auth_headers, resp.json()["id"])
    assert run["status"] == "completed", run
    assert run["is_active"] is True  # training run pertama otomatis aktif

    metrics_resp = client.get(f"/api/v1/training-runs/{run['id']}/metrics", headers=auth_headers)
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert set(metrics["confusion_matrix"]["labels"]) == {"positive", "negative"}
    assert len(metrics["confusion_matrix"]["matrix"]) == 2

    cm_resp = client.get(f"/api/v1/training-runs/{run['id']}/confusion-matrix", headers=auth_headers)
    assert cm_resp.status_code == 200

    report_resp = client.get(f"/api/v1/training-runs/{run['id']}/classification-report", headers=auth_headers)
    assert report_resp.status_code == 200

    predictions_resp = client.get(f"/api/v1/training-runs/{run['id']}/predictions", headers=auth_headers)
    assert predictions_resp.status_code == 200
    assert predictions_resp.json()["pagination"]["total_items"] == 4  # 20 data * 0.2 test_size


def test_second_training_run_does_not_auto_activate(client, auth_headers, trained_split_setup):
    dataset, split = trained_split_setup

    resp1 = client.post(
        f"/api/v1/datasets/{dataset.id}/train",
        json={"data_split_id": split["id"], "knn_config": {"n_neighbors": 3}},
        headers=auth_headers,
    )
    run1 = _wait_run_terminal(client, auth_headers, resp1.json()["id"])
    assert run1["is_active"] is True

    resp2 = client.post(
        f"/api/v1/datasets/{dataset.id}/train",
        json={"data_split_id": split["id"], "knn_config": {"n_neighbors": 5}},
        headers=auth_headers,
    )
    run2 = _wait_run_terminal(client, auth_headers, resp2.json()["id"])
    assert run2["is_active"] is False  # tidak menimpa model aktif tanpa konfirmasi

    # Konfirmasi eksplisit untuk mengaktifkan run kedua.
    activate_resp = client.post(
        f"/api/v1/training-runs/{run2['id']}/activate", json={"confirm": True}, headers=auth_headers
    )
    assert activate_resp.status_code == 200
    assert activate_resp.json()["is_active"] is True

    run1_check = client.get(f"/api/v1/training-runs/{run1['id']}", headers=auth_headers).json()
    assert run1_check["is_active"] is False  # otomatis dinonaktifkan


def test_activate_without_confirm_rejected(client, auth_headers, trained_split_setup):
    dataset, split = trained_split_setup
    resp = client.post(
        f"/api/v1/datasets/{dataset.id}/train",
        json={"data_split_id": split["id"], "knn_config": {"n_neighbors": 3}},
        headers=auth_headers,
    )
    run = _wait_run_terminal(client, auth_headers, resp.json()["id"])

    activate_resp = client.post(
        f"/api/v1/training-runs/{run['id']}/activate", json={"confirm": False}, headers=auth_headers
    )
    assert activate_resp.status_code == 400


def test_experiment_k_selects_best_k(client, auth_headers, trained_split_setup):
    dataset, split = trained_split_setup

    resp = client.post(
        f"/api/v1/datasets/{dataset.id}/experiment-k",
        json={"data_split_id": split["id"], "k_values": [1, 3, 5]},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    run = _wait_run_terminal(client, auth_headers, resp.json()["id"])
    assert run["status"] == "completed", run
    assert len(run["items"]) == 3

    selected = [item for item in run["items"] if item["is_selected"]]
    assert len(selected) == 1
    for item in run["items"]:
        assert item["k_value"] in (1, 3, 5)
        assert 0.0 <= item["f1_weighted"] <= 1.0


def test_train_fails_when_k_larger_than_train_size(client, auth_headers, trained_split_setup):
    dataset, split = trained_split_setup

    resp = client.post(
        f"/api/v1/datasets/{dataset.id}/train",
        json={"data_split_id": split["id"], "knn_config": {"n_neighbors": 999}},
        headers=auth_headers,
    )
    run = _wait_run_terminal(client, auth_headers, resp.json()["id"])
    assert run["status"] == "failed"
    assert "lebih besar" in run["error_message"]
