"""TEST FIXTURE: pengujian CRUD dataset menggunakan data uji, bukan data penelitian."""

import pytest


@pytest.fixture
def app_source(client, auth_headers):
    resp = client.post(
        "/api/v1/app-sources",
        json={"app_name": "PLN Mobile", "package_id": "com.icon.pln789"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()


def test_create_dataset(client, auth_headers, app_source):
    response = client.post(
        "/api/v1/datasets",
        json={
            "name": "Dataset PLN Mobile Uji",
            "app_source_id": app_source["id"],
            "description": "Dataset pengujian",
            "label_mode": "binary",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == "Dataset PLN Mobile Uji"
    assert body["review_count"] == 0
    assert body["app_source"]["app_name"] == "PLN Mobile"


def test_create_dataset_unknown_app_source(client, auth_headers):
    response = client.post(
        "/api/v1/datasets",
        json={"name": "Dataset X", "app_source_id": "00000000-0000-0000-0000-000000000000"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_dataset_summary_empty(client, auth_headers, app_source):
    create_resp = client.post(
        "/api/v1/datasets",
        json={"name": "Dataset Kosong", "app_source_id": app_source["id"]},
        headers=auth_headers,
    )
    dataset_id = create_resp.json()["id"]

    summary_resp = client.get(f"/api/v1/datasets/{dataset_id}/summary", headers=auth_headers)
    assert summary_resp.status_code == 200
    body = summary_resp.json()
    assert body["total_reviews"] == 0
    assert body["active_training_run_id"] is None


def test_delete_dataset_soft_delete(client, auth_headers, app_source, db_session):
    create_resp = client.post(
        "/api/v1/datasets",
        json={"name": "Dataset Hapus", "app_source_id": app_source["id"]},
        headers=auth_headers,
    )
    dataset_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/v1/datasets/{dataset_id}", headers=auth_headers)
    assert delete_resp.status_code == 200

    get_resp = client.get(f"/api/v1/datasets/{dataset_id}", headers=auth_headers)
    assert get_resp.status_code == 404
