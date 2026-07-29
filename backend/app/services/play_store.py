import logging
from dataclasses import dataclass

from google_play_scraper import app as gplay_app
from google_play_scraper.exceptions import NotFoundError

logger = logging.getLogger("sentiken")


@dataclass
class PlayStoreCheckResult:
    is_valid: bool
    exists: bool
    detail: str
    app_name: str | None = None


def check_package_on_play_store(
    package_id: str, country: str = "id", lang: str = "id"
) -> PlayStoreCheckResult:
    """Memeriksa apakah package_id benar-benar terdaftar di Google Play Store.

    Hanya melakukan pembacaan metadata publik (tanpa login/otentikasi/CAPTCHA).
    """
    try:
        result = gplay_app(package_id, lang=lang, country=country)
        return PlayStoreCheckResult(
            is_valid=True,
            exists=True,
            detail="Package ID ditemukan di Google Play Store.",
            app_name=result.get("title"),
        )
    except NotFoundError:
        return PlayStoreCheckResult(
            is_valid=False,
            exists=False,
            detail="Package ID tidak ditemukan di Google Play Store.",
        )
    except Exception as exc:  # noqa: BLE001 - Play Store bisa gagal karena banyak sebab jaringan
        logger.warning("Gagal memvalidasi package_id=%s: %s", package_id, exc)
        return PlayStoreCheckResult(
            is_valid=False,
            exists=False,
            detail=f"Tidak dapat memvalidasi saat ini (kemungkinan gangguan jaringan): {exc}",
        )
