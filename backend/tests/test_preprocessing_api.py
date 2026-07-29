"""TEST FIXTURE: pengujian endpoint preprocessing end-to-end dengan ulasan uji sintetis."""

from datetime import UTC, datetime

import pytest


@pytest.fixture
def dataset_with_reviews(client, auth_headers, db_session):
    from app.models.app_source import AppSource
    from app.models.dataset import Dataset
    from app.models.review import Review
    from app.services.dedup import compute_fingerprint

    source = AppSource(app_name="PLN Mobile", package_id="com.icon.pln.preproctest")
    db_session.add(source)
    db_session.flush()
    dataset = Dataset(name="Dataset Preprocessing Uji", app_source_id=source.id)
    db_session.add(dataset)
    db_session.flush()

    contents = [
        "Aplikasi ini gak bisa dibuka, parah bgt!!",
        "Pelayanannya mempermudah pembayaran, mantap sekali",
    ]
    reviews = []
    for i, content in enumerate(contents):
        fp = compute_fingerprint(str(source.id), content, f"user{i}", None)
        review = Review(
            dataset_id=dataset.id,
            app_source_id=source.id,
            review_id=f"preproc-{i}",
            fingerprint=fp,
            content=content,
            fetched_at=datetime.now(UTC),
        )
        db_session.add(review)
        reviews.append(review)
    db_session.commit()
    for r in reviews:
        db_session.refresh(r)
    return dataset, reviews


def test_preprocess_endpoint_processes_all_reviews(client, auth_headers, dataset_with_reviews):
    dataset, reviews = dataset_with_reviews

    # Tambahkan entri normalisasi agar "gak"/"bgt" ternormalisasi seperti pipeline unit test.
    client.post(
        "/api/v1/dictionaries/normalization",
        json={"informal_word": "gak", "formal_word": "tidak"},
        headers=auth_headers,
    )
    client.post(
        "/api/v1/dictionaries/normalization",
        json={"informal_word": "bgt", "formal_word": "banget"},
        headers=auth_headers,
    )

    start_resp = client.post(f"/api/v1/datasets/{dataset.id}/preprocess", headers=auth_headers)
    assert start_resp.status_code == 200

    deadline_status = None
    import time

    for _ in range(100):
        status_resp = client.get(f"/api/v1/datasets/{dataset.id}/preprocessing-status", headers=auth_headers)
        deadline_status = status_resp.json()
        if deadline_status["status"] == "completed":
            break
        time.sleep(0.05)

    assert deadline_status["status"] == "completed"
    assert deadline_status["processed_reviews"] == 2
    assert deadline_status["remaining_reviews"] == 0

    detail_resp = client.get(f"/api/v1/reviews/{reviews[0].id}/preprocessing", headers=auth_headers)
    assert detail_resp.status_code == 200
    body = detail_resp.json()
    assert "tidak" in body["normalized_text"]
    assert body["final_text"] != ""


def test_preprocess_empty_dataset_returns_400(client, auth_headers):
    source_resp = client.post(
        "/api/v1/app-sources",
        json={"app_name": "MyPertamina", "package_id": "com.pertamina.mypertamina.empty"},
        headers=auth_headers,
    )
    dataset_resp = client.post(
        "/api/v1/datasets",
        json={"name": "Dataset Kosong Preproc", "app_source_id": source_resp.json()["id"]},
        headers=auth_headers,
    )
    resp = client.post(f"/api/v1/datasets/{dataset_resp.json()['id']}/preprocess", headers=auth_headers)
    assert resp.status_code == 400


def test_review_detail_endpoint(client, auth_headers, dataset_with_reviews):
    dataset, reviews = dataset_with_reviews
    resp = client.get(f"/api/v1/reviews/{reviews[0].id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["content"] == reviews[0].content
