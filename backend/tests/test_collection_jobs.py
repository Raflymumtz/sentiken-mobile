"""TEST FIXTURE: pengujian alur job pengumpulan data. Panggilan nyata ke Google
Play Store DI-MOCK dengan data rekaan kecil (bukan data ulasan penelitian
sungguhan) agar test cepat, deterministik, dan tidak bergantung jaringan."""

from datetime import datetime

import pytest

from app.services.scraping import ScrapingNotFoundError
from tests.conftest import wait_for_job_status

FAKE_REVIEWS = [
    {
        "reviewId": "fake-1",
        "userName": "Tester Satu",
        "userImage": None,
        "content": "Ulasan uji pertama, aplikasi lancar",
        "score": 5,
        "thumbsUpCount": 2,
        "at": datetime(2026, 3, 1, 8, 0, 0),
        "replyContent": None,
        "repliedAt": None,
        "appVersion": "1.0.0",
    },
    {
        "reviewId": "fake-2",
        "userName": "Tester Dua",
        "userImage": None,
        "content": "Ulasan uji kedua, agak lambat",
        "score": 3,
        "thumbsUpCount": 0,
        "at": datetime(2026, 3, 2, 9, 0, 0),
        "replyContent": None,
        "repliedAt": None,
        "appVersion": "1.0.0",
    },
]


@pytest.fixture
def app_source_and_dataset(client, auth_headers):
    source_resp = client.post(
        "/api/v1/app-sources",
        json={"app_name": "PLN Mobile", "package_id": "com.icon.pln.collecttest"},
        headers=auth_headers,
    )
    source = source_resp.json()
    dataset_resp = client.post(
        "/api/v1/datasets",
        json={"name": "Dataset Koleksi Uji", "app_source_id": source["id"]},
        headers=auth_headers,
    )
    return source, dataset_resp.json()


def test_collection_job_completes_and_stores_reviews(
    client, auth_headers, app_source_and_dataset, monkeypatch
):
    source, dataset = app_source_and_dataset

    def fake_fetch_reviews(package_id, **kwargs):
        return list(FAKE_REVIEWS), []

    monkeypatch.setattr("app.services.collection.fetch_reviews", fake_fetch_reviews)

    resp = client.post(
        "/api/v1/collection-jobs",
        json={
            "app_source_id": source["id"],
            "dataset_id": dataset["id"],
            "max_reviews": 100,
            "language": "id",
            "country": "id",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    job_id = resp.json()["id"]

    job = wait_for_job_status(
        client, auth_headers, f"/api/v1/collection-jobs/{job_id}", {"completed", "failed"}
    )
    assert job["status"] == "completed", job
    assert job["found_count"] == 2
    assert job["new_count"] == 2
    assert job["duplicate_count"] == 0

    reviews_resp = client.get(f"/api/v1/datasets/{dataset['id']}/reviews", headers=auth_headers)
    assert reviews_resp.json()["pagination"]["total_items"] == 2


def test_collection_job_deduplicates_on_second_run(client, auth_headers, app_source_and_dataset, monkeypatch):
    source, dataset = app_source_and_dataset
    monkeypatch.setattr(
        "app.services.collection.fetch_reviews", lambda package_id, **kw: (list(FAKE_REVIEWS), [])
    )

    for _ in range(2):
        resp = client.post(
            "/api/v1/collection-jobs",
            json={"app_source_id": source["id"], "dataset_id": dataset["id"], "max_reviews": 100},
            headers=auth_headers,
        )
        job_id = resp.json()["id"]
        job = wait_for_job_status(
            client, auth_headers, f"/api/v1/collection-jobs/{job_id}", {"completed", "failed"}
        )

    assert job["new_count"] == 0
    assert job["duplicate_count"] == 2

    reviews_resp = client.get(f"/api/v1/datasets/{dataset['id']}/reviews", headers=auth_headers)
    assert reviews_resp.json()["pagination"]["total_items"] == 2


def test_collection_job_fails_when_package_not_found(
    client, auth_headers, app_source_and_dataset, monkeypatch
):
    source, dataset = app_source_and_dataset

    def raise_not_found(package_id, **kwargs):
        raise ScrapingNotFoundError(f"Package ID '{package_id}' tidak ditemukan.")

    monkeypatch.setattr("app.services.collection.fetch_reviews", raise_not_found)

    resp = client.post(
        "/api/v1/collection-jobs",
        json={"app_source_id": source["id"], "dataset_id": dataset["id"], "max_reviews": 50},
        headers=auth_headers,
    )
    job_id = resp.json()["id"]
    job = wait_for_job_status(
        client, auth_headers, f"/api/v1/collection-jobs/{job_id}", {"completed", "failed"}
    )
    assert job["status"] == "failed"
    assert "tidak ditemukan" in job["error_message"]


def test_collection_job_invalid_dataset_app_source_mismatch(client, auth_headers, app_source_and_dataset):
    source, dataset = app_source_and_dataset
    other_source_resp = client.post(
        "/api/v1/app-sources",
        json={"app_name": "MyPertamina", "package_id": "com.pertamina.mypertamina.test"},
        headers=auth_headers,
    )
    other_source = other_source_resp.json()

    resp = client.post(
        "/api/v1/collection-jobs",
        json={"app_source_id": other_source["id"], "dataset_id": dataset["id"], "max_reviews": 50},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_cancel_queued_collection_job(client, auth_headers, app_source_and_dataset, monkeypatch):
    source, dataset = app_source_and_dataset

    # fetch_reviews lambat agar job masih "running" saat dibatalkan.
    def slow_fetch(package_id, should_cancel=None, **kwargs):
        import time

        for _ in range(20):
            if should_cancel and should_cancel():
                return [], []
            time.sleep(0.05)
        return list(FAKE_REVIEWS), []

    monkeypatch.setattr("app.services.collection.fetch_reviews", slow_fetch)

    resp = client.post(
        "/api/v1/collection-jobs",
        json={"app_source_id": source["id"], "dataset_id": dataset["id"], "max_reviews": 50},
        headers=auth_headers,
    )
    job_id = resp.json()["id"]

    cancel_resp = client.post(f"/api/v1/collection-jobs/{job_id}/cancel", headers=auth_headers)
    assert cancel_resp.status_code == 200

    job = wait_for_job_status(
        client, auth_headers, f"/api/v1/collection-jobs/{job_id}", {"completed", "failed", "cancelled"}
    )
    assert job["status"] == "cancelled"
