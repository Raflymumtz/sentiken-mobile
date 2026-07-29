from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import PageParams, build_pagination, get_current_user, get_db
from app.jobs.queue import submit_job
from app.models.app_source import AppSource
from app.models.dataset import Dataset
from app.models.enums import JobStatus
from app.models.job import CollectionJob
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.job import CollectionJobCreate, CollectionJobResponse
from app.services.audit import write_audit_log
from app.services.collection import run_collection_job

router = APIRouter(prefix="/collection-jobs", tags=["Pengumpulan Data"])


@router.post("", response_model=CollectionJobResponse, status_code=status.HTTP_201_CREATED)
def create_collection_job(
    payload: CollectionJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_source = (
        db.query(AppSource)
        .filter(AppSource.id == str(payload.app_source_id), AppSource.deleted_at.is_(None))
        .first()
    )
    if app_source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sumber aplikasi tidak ditemukan.")

    dataset = (
        db.query(Dataset).filter(Dataset.id == str(payload.dataset_id), Dataset.deleted_at.is_(None)).first()
    )
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset tidak ditemukan.")

    if str(dataset.app_source_id) != str(app_source.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset yang dipilih tidak terhubung dengan sumber aplikasi ini.",
        )

    job = CollectionJob(
        app_source_id=str(payload.app_source_id),
        dataset_id=str(payload.dataset_id),
        period_start=payload.period_start,
        period_end=payload.period_end,
        max_reviews=payload.max_reviews,
        language=payload.language,
        country=payload.country,
        sort_order=payload.sort_order,
        method=payload.method,
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
        entity_type="collection_job",
        entity_id=str(job.id),
        detail={"dataset_id": str(dataset.id)},
    )

    submit_job(run_collection_job, str(job.id))

    return job


@router.get("", response_model=PaginatedResponse[CollectionJobResponse])
def list_collection_jobs(
    dataset_id: str | None = None,
    status_filter: str | None = None,
    page_params: PageParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(CollectionJob)
    if dataset_id:
        query = query.filter(CollectionJob.dataset_id == dataset_id)
    if status_filter:
        query = query.filter(CollectionJob.status == status_filter)

    total = query.count()
    items = (
        query.order_by(CollectionJob.created_at.desc())
        .offset(page_params.offset)
        .limit(page_params.page_size)
        .all()
    )
    return PaginatedResponse(items=items, pagination=build_pagination(page_params, total))


@router.get("/{job_id}", response_model=CollectionJobResponse)
def get_collection_job(
    job_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    job = db.get(CollectionJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job tidak ditemukan.")
    return job


@router.post("/{job_id}/cancel", response_model=CollectionJobResponse)
def cancel_collection_job(
    job_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    job = db.get(CollectionJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job tidak ditemukan.")
    if job.status in (JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job sudah selesai dan tidak dapat dibatalkan.",
        )
    job.cancel_requested = True
    if job.status == JobStatus.QUEUED.value:
        job.status = JobStatus.CANCELLED.value
    db.commit()
    db.refresh(job)
    write_audit_log(
        db, user_id=current_user.id, action="cancel", entity_type="collection_job", entity_id=str(job.id)
    )
    return job
