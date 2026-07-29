import re

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.config import get_settings
from app.jobs.queue import submit_job
from app.models.dataset import Dataset
from app.models.enums import JobStatus
from app.models.job import ImportJob
from app.models.user import User
from app.schemas.job import (
    ImportExecuteRequest,
    ImportJobResponse,
    ImportPreviewResponse,
    ImportPreviewRow,
)
from app.services.audit import write_audit_log
from app.services.csv_import import CsvFormatError, parse_csv_bytes
from app.services.import_execution import run_import_job
from app.services.upload_cache import pop, put

router = APIRouter(tags=["Import CSV"])

ALLOWED_CONTENT_TYPES = {"text/csv", "application/vnd.ms-excel", "application/octet-stream", "text/plain"}


def _sanitize_filename(filename: str) -> str:
    base = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    return base[:255] or "upload.csv"


def _get_dataset_or_404(db: Session, dataset_id: str) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.deleted_at.is_(None)).first()
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset tidak ditemukan.")
    return dataset


@router.post("/datasets/{dataset_id}/imports/preview", response_model=ImportPreviewResponse)
async def preview_import(
    dataset_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    settings = get_settings()
    dataset = _get_dataset_or_404(db, dataset_id)

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipe berkas '{file.content_type}' tidak didukung. Unggah berkas CSV.",
        )

    filename = _sanitize_filename(file.filename or "upload.csv")
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Berkas harus berekstensi .csv")

    raw = await file.read()
    max_bytes = settings.max_csv_upload_size_mb * 1024 * 1024
    if len(raw) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Ukuran berkas melebihi batas {settings.max_csv_upload_size_mb} MB.",
        )
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Berkas CSV kosong.")

    try:
        parsed = parse_csv_bytes(raw)
    except CsvFormatError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    token = put(dataset_id=str(dataset.id), filename=filename, raw=raw)

    sample = [
        ImportPreviewRow(
            row_number=row.row_number,
            data={k: (str(v) if v is not None else None) for k, v in row.data.items()},
            is_valid=row.is_valid,
            errors=row.errors,
        )
        for row in parsed.rows[:20]
    ]

    return ImportPreviewResponse(
        total_rows=parsed.total_rows,
        valid_rows=parsed.valid_rows,
        invalid_rows=parsed.invalid_rows,
        detected_columns=parsed.detected_columns,
        missing_required_columns=parsed.missing_required_columns,
        sample_rows=sample,
        upload_token=token,
    )


@router.post(
    "/datasets/{dataset_id}/imports/execute",
    response_model=ImportJobResponse,
    status_code=status.HTTP_201_CREATED,
)
def execute_import(
    dataset_id: str,
    payload: ImportExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = _get_dataset_or_404(db, dataset_id)

    cached = pop(payload.upload_token)
    if cached is None or cached.dataset_id != str(dataset.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token unggahan tidak valid atau sudah kedaluwarsa. Silakan unggah ulang berkas.",
        )

    job = ImportJob(
        dataset_id=dataset.id,
        filename=cached.filename,
        status=JobStatus.QUEUED.value,
        requested_by=current_user.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    write_audit_log(
        db,
        user_id=current_user.id,
        action="create",
        entity_type="import_job",
        entity_id=str(job.id),
        detail={"filename": cached.filename},
    )

    submit_job(run_import_job, str(job.id), cached.raw)

    return job


@router.get("/import-jobs/{job_id}", response_model=ImportJobResponse)
def get_import_job(
    job_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    job = db.get(ImportJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job impor tidak ditemukan.")
    return job
