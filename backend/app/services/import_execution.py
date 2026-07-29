import logging
from datetime import UTC, datetime

from app.database import SessionLocal
from app.models.dataset import Dataset
from app.models.enums import JobStatus, ReviewSource
from app.models.job import ImportJob
from app.models.review import Review
from app.services.csv_import import CsvFormatError, parse_csv_bytes
from app.services.dedup import compute_fingerprint, find_existing_review

logger = logging.getLogger("sentiken")


def run_import_job(job_id: str, raw_csv: bytes) -> None:
    db = SessionLocal()
    try:
        job = db.get(ImportJob, job_id)
        if job is None:
            logger.error("Import job %s tidak ditemukan.", job_id)
            return

        dataset = db.get(Dataset, job.dataset_id)
        if dataset is None:
            job.status = JobStatus.FAILED.value
            job.error_message = "Dataset tidak ditemukan."
            job.finished_at = datetime.now(UTC)
            db.commit()
            return

        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.now(UTC)
        db.commit()

        try:
            parsed = parse_csv_bytes(raw_csv)
        except CsvFormatError as exc:
            job.status = JobStatus.FAILED.value
            job.error_message = str(exc)
            job.finished_at = datetime.now(UTC)
            db.commit()
            return

        if parsed.missing_required_columns:
            job.status = JobStatus.FAILED.value
            job.error_message = "Kolom wajib tidak ditemukan: " + ", ".join(parsed.missing_required_columns)
            job.finished_at = datetime.now(UTC)
            db.commit()
            return

        new_count = 0
        duplicate_count = 0
        row_errors: list[str] = []

        try:
            for row in parsed.rows:
                if not row.is_valid:
                    row_errors.append(f"Baris {row.row_number}: {'; '.join(row.errors)}")
                    continue

                fingerprint = compute_fingerprint(
                    str(dataset.app_source_id),
                    row.data["content"],
                    row.data["username"],
                    row.data["review_date"],
                )
                existing = find_existing_review(
                    db,
                    app_source_id=str(dataset.app_source_id),
                    review_id=row.data["review_id"],
                    fingerprint=fingerprint,
                )
                if existing:
                    duplicate_count += 1
                    continue

                review = Review(
                    dataset_id=dataset.id,
                    app_source_id=dataset.app_source_id,
                    fingerprint=fingerprint,
                    source=ReviewSource.CSV_IMPORT.value,
                    fetched_at=datetime.now(UTC),
                    **row.data,
                )
                db.add(review)
                db.flush()
                new_count += 1

            job.total_rows = parsed.total_rows
            job.valid_rows = parsed.valid_rows
            job.invalid_rows = parsed.invalid_rows
            job.new_count = new_count
            job.duplicate_count = duplicate_count
            job.validation_report = {"row_errors": row_errors[:500]}
            job.status = JobStatus.COMPLETED.value
            job.finished_at = datetime.now(UTC)
            db.commit()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Import job %s gagal, rollback transaksi: %s", job_id, exc)
            db.rollback()
            job = db.get(ImportJob, job_id)
            job.status = JobStatus.FAILED.value
            job.error_message = f"Import dibatalkan karena kesalahan fatal: {exc}"
            job.finished_at = datetime.now(UTC)
            db.commit()
    finally:
        db.close()
