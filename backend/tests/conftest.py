import os
import tempfile
import time
import uuid
from pathlib import Path

# SQLite berbasis file (bukan ":memory:") dipakai untuk test suite karena
# beberapa alur (collection job, import job) menjalankan pekerjaan pada
# thread background sungguhan. Satu koneksi sqlite3 mentah tidak thread-safe
# untuk dipakai bersamaan oleh >1 thread walau check_same_thread=False --
# itu hanya mematikan pengecekan, bukan membuatnya benar-benar aman -- dan
# sempat menyebabkan hang saat dipakai bersama StaticPool. File DB di
# direktori temp memberi tiap sesi koneksi sendiri sehingga aman dipakai
# bersamaan oleh test client dan job background.
_TEST_DB_PATH = Path(tempfile.gettempdir()) / "sentiken_test.db"
_TEST_DB_PATH.unlink(missing_ok=True)
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TEST_DB_PATH.as_posix()}")
os.environ.setdefault("JOB_EXECUTION_MODE", "inline")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("ADMIN_EMAIL", "admin@sentiken.local")
os.environ.setdefault("ADMIN_PASSWORD", "TestAdmin123!")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "100000")

# Model joblib (TF-IDF/K-NN) hasil training pada test suite disimpan di
# direktori temp terpisah, bukan ke backend/storage/models sungguhan.
_TEST_MODEL_DIR = Path(tempfile.gettempdir()) / "sentiken_test_models"
os.environ.setdefault("ML_MODEL_STORAGE_DIR", str(_TEST_MODEL_DIR))

import pytest
from fastapi.testclient import TestClient

import app.models  # noqa: F401  (registers all ORM models)
from app.database import Base, SessionLocal, engine
from app.main import app as fastapi_app
from app.models.user import User
from app.security import hash_password

# PENTING: fixture di bawah ini SENGAJA memakai `app.database.engine` /
# `SessionLocal` yang sama dengan yang dipakai runtime aplikasi (termasuk
# background job thread pada JOB_EXECUTION_MODE=inline), bukan engine test
# terpisah, sehingga job background yang membuka sesi DB sendiri tetap
# membaca/menulis file SQLite yang sama dengan yang dipakai request test.


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    with TestClient(fastapi_app) as test_client:
        yield test_client


@pytest.fixture
def admin_user(db_session):
    user = User(
        id=uuid.uuid4(),
        email="admin@sentiken.local",
        password_hash=hash_password("TestAdmin123!"),
        full_name="Administrator Test",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, admin_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "TestAdmin123!"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def wait_for_job_status(client, headers, url: str, terminal_statuses, timeout: float = 5.0) -> dict:
    """Job background (inline thread) berjalan async terhadap request test; polling
    singkat ini menunggu status job mencapai salah satu status terminal."""
    deadline = time.monotonic() + timeout
    body = {}
    while time.monotonic() < deadline:
        resp = client.get(url, headers=headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        if body["status"] in terminal_statuses:
            return body
        time.sleep(0.05)
    raise TimeoutError(f"Job pada {url} belum mencapai status terminal dalam {timeout}s: {body}")
