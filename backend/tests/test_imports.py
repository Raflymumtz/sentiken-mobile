"""TEST FIXTURE: pengujian alur import CSV memakai tests/fixtures/sample_reviews.csv
(data rekaan untuk pengujian, BUKAN data ulasan penelitian sungguhan)."""

from pathlib import Path

import pytest

from tests.conftest import wait_for_job_status

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_reviews.csv"


@pytest.fixture
def dataset(client, auth_headers):
    source_resp = client.post(
        "/api/v1/app-sources",
        json={"app_name": "PLN Mobile", "package_id": "com.icon.pln.importtest"},
        headers=auth_headers,
    )
    assert source_resp.status_code == 201
    source_id = source_resp.json()["id"]

    dataset_resp = client.post(
        "/api/v1/datasets",
        json={"name": "Dataset Import Uji", "app_source_id": source_id},
        headers=auth_headers,
    )
    assert dataset_resp.status_code == 201
    return dataset_resp.json()


def test_preview_import_reports_valid_and_invalid_rows(client, auth_headers, dataset):
    with open(FIXTURE_PATH, "rb") as f:
        response = client.post(
            f"/api/v1/datasets/{dataset['id']}/imports/preview",
            files={"file": ("sample_reviews.csv", f, "text/csv")},
            headers=auth_headers,
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total_rows"] == 6
    assert body["valid_rows"] == 3
    assert body["invalid_rows"] == 3
    assert "content" in body["detected_columns"] or "content" in [c.lower() for c in body["detected_columns"]]
    assert body["missing_required_columns"] == []
    assert body["upload_token"]


def test_execute_import_persists_valid_rows_and_dedups_on_rerun(client, auth_headers, dataset):
    with open(FIXTURE_PATH, "rb") as f:
        preview_resp = client.post(
            f"/api/v1/datasets/{dataset['id']}/imports/preview",
            files={"file": ("sample_reviews.csv", f, "text/csv")},
            headers=auth_headers,
        )
    token = preview_resp.json()["upload_token"]

    exec_resp = client.post(
        f"/api/v1/datasets/{dataset['id']}/imports/execute",
        json={"upload_token": token},
        headers=auth_headers,
    )
    assert exec_resp.status_code == 201, exec_resp.text
    job_id = exec_resp.json()["id"]

    job = wait_for_job_status(client, auth_headers, f"/api/v1/import-jobs/{job_id}", {"completed", "failed"})
    assert job["status"] == "completed", job
    assert job["new_count"] == 3
    assert job["duplicate_count"] == 0
    assert job["invalid_rows"] == 3

    reviews_resp = client.get(f"/api/v1/datasets/{dataset['id']}/reviews", headers=auth_headers)
    assert reviews_resp.status_code == 200
    assert reviews_resp.json()["pagination"]["total_items"] == 3

    # Import ulang file yang sama -> seluruh baris valid terdeteksi sebagai duplikat.
    with open(FIXTURE_PATH, "rb") as f:
        preview_resp2 = client.post(
            f"/api/v1/datasets/{dataset['id']}/imports/preview",
            files={"file": ("sample_reviews.csv", f, "text/csv")},
            headers=auth_headers,
        )
    token2 = preview_resp2.json()["upload_token"]
    exec_resp2 = client.post(
        f"/api/v1/datasets/{dataset['id']}/imports/execute",
        json={"upload_token": token2},
        headers=auth_headers,
    )
    job_id2 = exec_resp2.json()["id"]
    job2 = wait_for_job_status(
        client, auth_headers, f"/api/v1/import-jobs/{job_id2}", {"completed", "failed"}
    )
    assert job2["status"] == "completed"
    assert job2["new_count"] == 0
    assert job2["duplicate_count"] == 3

    reviews_resp2 = client.get(f"/api/v1/datasets/{dataset['id']}/reviews", headers=auth_headers)
    assert reviews_resp2.json()["pagination"]["total_items"] == 3


def test_preview_rejects_corrupted_csv(client, auth_headers, dataset):
    # Byte non-UTF-8 yang tidak valid -> pandas gagal membaca file sama sekali.
    garbage = b"\xff\xfe\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\xfe\xff\x80\x81"
    response = client.post(
        f"/api/v1/datasets/{dataset['id']}/imports/preview",
        files={"file": ("rusak.csv", garbage, "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code in (400, 422)


def test_preview_rejects_missing_content_column(client, auth_headers, dataset):
    csv_bytes = b"reviewId,userName,score\nr1,user,5\n"
    response = client.post(
        f"/api/v1/datasets/{dataset['id']}/imports/preview",
        files={"file": ("tanpa_content.csv", csv_bytes, "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert "content" in body["missing_required_columns"]


def test_execute_import_rejects_invalid_token(client, auth_headers, dataset):
    response = client.post(
        f"/api/v1/datasets/{dataset['id']}/imports/execute",
        json={"upload_token": "token-tidak-ada"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_preview_rejects_oversized_extension(client, auth_headers, dataset):
    response = client.post(
        f"/api/v1/datasets/{dataset['id']}/imports/preview",
        files={"file": ("data.txt", b"content\nhalo", "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 400
