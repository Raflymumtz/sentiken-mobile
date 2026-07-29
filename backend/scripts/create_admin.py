"""Membuat atau memperbarui akun admin tunggal dari environment variable.

Jalankan dari direktori backend/:
    python -m scripts.create_admin

Kredensial admin dibaca dari ADMIN_EMAIL, ADMIN_PASSWORD, dan ADMIN_FULL_NAME
(lihat .env.example). Skrip ini idempoten: bila admin dengan email tersebut
sudah ada, kata sandi dan nama akan disinkronkan ke nilai environment saat ini.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.security import hash_password  # noqa: E402


def create_or_update_admin() -> None:
    settings = get_settings()
    email = settings.admin_email.strip().lower()

    if not email or not settings.admin_password:
        print("ADMIN_EMAIL dan ADMIN_PASSWORD wajib diisi pada environment.")
        sys.exit(1)

    if len(settings.admin_password) < 8:
        print("ADMIN_PASSWORD sebaiknya minimal 8 karakter.")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(
                email=email,
                password_hash=hash_password(settings.admin_password),
                full_name=settings.admin_full_name,
                role="admin",
                is_active=True,
            )
            db.add(user)
            db.commit()
            print(f"Admin baru dibuat: {email}")
        else:
            user.password_hash = hash_password(settings.admin_password)
            user.full_name = settings.admin_full_name
            user.is_active = True
            db.commit()
            print(f"Admin diperbarui: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    create_or_update_admin()
