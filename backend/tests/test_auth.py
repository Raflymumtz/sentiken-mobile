"""TEST FIXTURE: pengujian autentikasi menggunakan akun admin sintetis untuk testing,
bukan data penelitian."""


def test_login_success(client, admin_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "TestAdmin123!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body


def test_login_wrong_password(client, admin_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "salah"},
    )
    assert response.status_code == 401


def test_login_unknown_email(client, db_session):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "tidakada@sentiken.local", "password": "apasaja"},
    )
    assert response.status_code == 401


def test_me_requires_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_with_valid_token(client, auth_headers):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "admin@sentiken.local"


def test_refresh_token_flow(client, admin_user):
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "TestAdmin123!"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()

    # Token lama sudah dirotasi, tidak boleh dipakai lagi.
    reused_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert reused_resp.status_code == 401


def test_logout_revokes_refresh_token(client, admin_user, auth_headers):
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "TestAdmin123!"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    logout_resp = client.post(
        "/api/v1/auth/logout", json={"refresh_token": refresh_token}, headers=auth_headers
    )
    assert logout_resp.status_code == 200

    refresh_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 401


def test_inactive_user_cannot_login(client, db_session):
    from app.models.user import User
    from app.security import hash_password

    user = User(
        email="nonaktif@sentiken.local",
        password_hash=hash_password("Password123!"),
        full_name="User Nonaktif",
        role="admin",
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonaktif@sentiken.local", "password": "Password123!"},
    )
    assert response.status_code == 403
