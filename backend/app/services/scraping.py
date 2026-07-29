import logging
import time
from collections.abc import Callable
from datetime import date, datetime

from google_play_scraper import Sort
from google_play_scraper import reviews as gplay_reviews
from google_play_scraper.exceptions import NotFoundError
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_exponential

from app.config import get_settings

logger = logging.getLogger("sentiken")

SORT_MAP = {"newest": Sort.NEWEST, "rating": Sort.RATING, "relevance": Sort.MOST_RELEVANT}


class ScrapingNotFoundError(Exception):
    """Package ID tidak ditemukan di Google Play Store."""


def fetch_reviews(
    package_id: str,
    *,
    lang: str = "id",
    country: str = "id",
    sort_order: str = "newest",
    max_reviews: int = 1000,
    period_start: date | None = None,
    period_end: date | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
    page_size: int = 200,
) -> tuple[list[dict], list[str]]:
    """Mengambil ulasan dari Google Play Store.

    Menerapkan jeda antar-permintaan, retry dengan backoff, pagination via
    continuation token, filter periode, dan dukungan pembatalan job. Tidak
    melewati mekanisme autentikasi/CAPTCHA apa pun -- hanya membaca data
    ulasan publik yang memang disediakan Google Play Store.

    Mengembalikan (list_review_dict, list_pesan_error).
    """
    settings = get_settings()
    sort = SORT_MAP.get(sort_order, Sort.NEWEST)
    collected: list[dict] = []
    errors: list[str] = []
    token = None

    @retry(
        reraise=True,
        stop=stop_after_attempt(max(1, settings.scrape_max_retries)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_not_exception_type(NotFoundError),
    )
    def _fetch_page(continuation_token, count):
        return gplay_reviews(
            package_id,
            lang=lang,
            country=country,
            sort=sort,
            count=count,
            continuation_token=continuation_token,
        )

    while len(collected) < max_reviews:
        if should_cancel and should_cancel():
            logger.info("Job pengumpulan %s dibatalkan oleh pengguna.", package_id)
            break

        remaining = max_reviews - len(collected)
        try:
            items, token = _fetch_page(token, min(page_size, remaining))
        except NotFoundError as exc:
            raise ScrapingNotFoundError(
                f"Package ID '{package_id}' tidak ditemukan di Google Play Store."
            ) from exc
        except Exception as exc:  # noqa: BLE001
            logger.exception("Gagal mengambil ulasan untuk %s: %s", package_id, exc)
            errors.append(f"Gagal mengambil halaman ulasan: {exc}")
            break

        if not items:
            break

        stop_due_to_date = False
        for item in items:
            review_date = item.get("at")
            if isinstance(review_date, datetime):
                review_date = review_date.date()

            if sort_order == "newest" and period_start and review_date and review_date < period_start:
                stop_due_to_date = True
                break
            if period_end and review_date and review_date > period_end:
                continue
            if period_start and review_date and review_date < period_start:
                continue

            collected.append(item)
            if len(collected) >= max_reviews:
                break

        if progress_callback:
            progress_callback(len(collected), max_reviews)

        if stop_due_to_date or token is None or len(collected) >= max_reviews:
            break

        time.sleep(settings.scrape_request_delay_seconds)

    return collected, errors
