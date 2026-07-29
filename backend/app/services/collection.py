import logging
from datetime import UTC, datetime

from app.database import SessionLocal
from app.models.app_source import AppSource
from app.models.enums import JobStatus, ReviewSource
from app.models.job import CollectionJob
from app.models.review import Review
from app.services.dedup import compute_fingerprint, find_existing_review
from app.services.scraping import ScrapingNotFoundError, fetch_reviews

logger = logging.getLogger("sentiken")


def _review_dict_to_kwargs(item: dict) -> dict:
    at = item.get("at")
    review_date = at.date() if isinstance(at, datetime) else None
    replied_at = item.get("repliedAt")
    reply_date = replied_at.date() if isinstance(replied_at, datetime) else None

    return {
        "review_id": item.get("reviewId"),
        "username": item.get("userName"),
        "user_image": item.get("userImage"),
        "content": item.get("content") or "",
        "score": item.get("score"),
        "thumbs_up_count": item.get("thumbsUpCount") or 0,
        "review_date": review_date,
        "app_version": item.get("appVersion") or item.get("reviewCreatedVersion"),
        "reply_content": item.get("replyContent"),
        "reply_date": reply_date,
    }


def run_collection_job(job_id: str) -> None:
    """Dijalankan di background (thread lokal atau worker RQ). Membuka sesi DB sendiri."""
    db = SessionLocal()
    try:
        job = db.get(CollectionJob, job_id)
        if job is None:
            logger.error("Collection job %s tidak ditemukan.", job_id)
            return

        app_source = db.get(AppSource, job.app_source_id)
        if app_source is None:
            job.status = JobStatus.FAILED.value
            job.error_message = "Sumber aplikasi tidak ditemukan."
            job.finished_at = datetime.now(UTC)
            db.commit()
            return

        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.now(UTC)
        db.commit()

        def progress_callback(found: int, target: int) -> None:
            job.found_count = found
            job.progress_percent = round(min(found / target, 1.0) * 100, 2) if target else 0.0
            db.commit()

        def should_cancel() -> bool:
            db.refresh(job)
            return bool(job.cancel_requested)

        try:
            items, errors = fetch_reviews(
                app_source.package_id,
                lang=job.language,
                country=job.country,
                sort_order=job.sort_order,
                max_reviews=job.max_reviews,
                period_start=job.period_start,
                period_end=job.period_end,
                progress_callback=progress_callback,
                should_cancel=should_cancel,
            )
        except ScrapingNotFoundError as exc:
            job.status = JobStatus.FAILED.value
            job.error_message = str(exc)
            job.error_log = [str(exc)]
            job.finished_at = datetime.now(UTC)
            db.commit()
            return

        new_count = 0
        duplicate_count = 0
        for item in items:
            kwargs = _review_dict_to_kwargs(item)
            fingerprint = compute_fingerprint(
                str(job.app_source_id), kwargs["content"], kwargs["username"], kwargs["review_date"]
            )
            existing = find_existing_review(
                db,
                app_source_id=str(job.app_source_id),
                review_id=kwargs["review_id"],
                fingerprint=fingerprint,
            )
            if existing:
                duplicate_count += 1
                continue

            review = Review(
                dataset_id=job.dataset_id,
                app_source_id=job.app_source_id,
                fingerprint=fingerprint,
                source=ReviewSource.SCRAPED.value,
                fetched_at=datetime.now(UTC),
                **kwargs,
            )
            db.add(review)
            try:
                db.flush()
            except Exception as exc:  # noqa: BLE001 - unique constraint race, dedup fallback
                logger.warning("Insert review gagal (kemungkinan duplikat): %s", exc)
                db.rollback()
                duplicate_count += 1
                continue
            new_count += 1

        job.found_count = len(items)
        job.new_count = new_count
        job.duplicate_count = duplicate_count
        job.progress_percent = 100.0
        job.error_log = errors
        if job.cancel_requested:
            job.status = JobStatus.CANCELLED.value
        elif errors and not items:
            job.status = JobStatus.FAILED.value
            job.error_message = "; ".join(errors)
        else:
            job.status = JobStatus.COMPLETED.value
            if errors:
                job.error_message = "Selesai dengan sebagian error: " + "; ".join(errors)
        job.finished_at = datetime.now(UTC)
        db.commit()

    except Exception as exc:  # noqa: BLE001
        logger.exception("Collection job %s gagal tak terduga: %s", job_id, exc)
        db.rollback()
        job = db.get(CollectionJob, job_id)
        if job:
            job.status = JobStatus.FAILED.value
            job.error_message = f"Kesalahan tak terduga: {exc}"
            job.finished_at = datetime.now(UTC)
            db.commit()
    finally:
        db.close()
