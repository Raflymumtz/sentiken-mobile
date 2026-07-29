"""TEST FIXTURE: pengujian CRUD sumber aplikasi menggunakan data uji, bukan data penelitian."""


def test_create_app_source(client, auth_headers):
    response = client.post(
        "/api/v1/app-sources",
        json={
            "app_name": "PLN Mobile",
            "package_id": "com.icon.pln123",
            "play_store_url": "https://play.google.com/store/apps/details?id=com.icon.pln123",
            "description": "Aplikasi kelistrikan PLN",
            "language": "id",
            "country": "id",
            "is_active": True,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["app_name"] == "PLN Mobile"
    assert body["package_id"] == "com.icon.pln123"


def test_create_app_source_invalid_package_id(client, auth_headers):
    response = client.post(
        "/api/v1/app-sources",
        json={"app_name": "Contoh", "package_id": "invalidpackageid"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_create_app_source_duplicate_package_id(client, auth_headers):
    payload = {"app_name": "MyPertamina", "package_id": "com.pertamina.mypertamina"}
    first = client.post("/api/v1/app-sources", json=payload, headers=auth_headers)
    assert first.status_code == 201
    second = client.post("/api/v1/app-sources", json=payload, headers=auth_headers)
    assert second.status_code == 409


def test_list_app_sources_requires_auth(client):
    response = client.get("/api/v1/app-sources")
    assert response.status_code == 401


def test_update_app_source(client, auth_headers):
    create_resp = client.post(
        "/api/v1/app-sources",
        json={"app_name": "PLN Mobile", "package_id": "com.icon.pln456"},
        headers=auth_headers,
    )
    source_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/api/v1/app-sources/{source_id}",
        json={"is_active": False, "description": "Dinonaktifkan sementara"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["is_active"] is False


def test_delete_app_source_is_soft_delete(client, auth_headers, db_session):
    create_resp = client.post(
        "/api/v1/app-sources",
        json={"app_name": "Aplikasi Uji", "package_id": "com.contoh.ujicoba"},
        headers=auth_headers,
    )
    source_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/v1/app-sources/{source_id}", headers=auth_headers)
    assert delete_resp.status_code == 200

    get_resp = client.get(f"/api/v1/app-sources/{source_id}", headers=auth_headers)
    assert get_resp.status_code == 404

    from app.models.app_source import AppSource

    still_in_db = db_session.query(AppSource).filter(AppSource.id == source_id).first()
    assert still_in_db is not None
    assert still_in_db.deleted_at is not None
