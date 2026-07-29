from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings

settings = get_settings()

if settings.database_url == "sqlite:///:memory:":
    # StaticPool + satu koneksi bersama diperlukan agar DB in-memory tidak
    # hilang antar koneksi. CATATAN: mode ini hanya aman untuk skenario
    # single-thread (mis. test unit murni) karena satu koneksi sqlite3 mentah
    # tidak thread-safe untuk akses bersamaan sungguhan -- lihat cabang file
    # sqlite di bawah untuk pengujian yang melibatkan background job/thread.
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
elif settings.is_sqlite:
    # SQLite berbasis file (termasuk untuk test suite yang menjalankan
    # background job pada thread terpisah): setiap sesi mendapat koneksi
    # sendiri dari pool sehingga akses multi-thread aman, dengan busy
    # timeout agar penulis yang bersamaan menunggu alih-alih langsung gagal
    # dengan "database is locked".
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False, "timeout": 30},
        future=True,
    )
else:
    engine = create_engine(settings.database_url, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
