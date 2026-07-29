from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import PageParams, build_pagination, get_current_user, get_db
from app.jobs.queue import submit_job
from app.models.dataset import Dataset
from app.models.enums import ProcessingStatus
from app.models.ml import DataSplit, TrainingRun
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.ml import (
    ActivateRunRequest,
    ExperimentKRequest,
    TrainingRunResponse,
    TrainRequest,
)
from app.services.audit import write_audit_log
from app.services.training_service import run_experiment_k_job, run_training_job

router = APIRouter(tags=["Training"])


def _get_dataset_or_404(db: Session, dataset_id: str) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.deleted_at.is_(None)).first()
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset tidak ditemukan.")
    return dataset


def _get_split_or_404(db: Session, dataset_id: str, split_id: str) -> DataSplit:
    split = db.query(DataSplit).filter(DataSplit.id == split_id, DataSplit.dataset_id == dataset_id).first()
    if split is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data split tidak ditemukan.")
    return split


@router.post(
    "/datasets/{dataset_id}/train", response_model=TrainingRunResponse, status_code=status.HTTP_201_CREATED
)
def train_model(
    dataset_id: str,
    payload: TrainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = _get_dataset_or_404(db, dataset_id)
    split = _get_split_or_404(db, dataset_id, str(payload.data_split_id))

    run = TrainingRun(
        dataset_id=dataset.id,
        data_split_id=split.id,
        label_mode=split.label_mode,
        run_type="single",
        tfidf_config=payload.tfidf_config.model_dump(),
        knn_config=payload.knn_config.model_dump(),
        status=ProcessingStatus.PENDING.value,
    )
    db.add(run)
    dataset.training_status = ProcessingStatus.RUNNING.value
    db.commit()
    db.refresh(run)

    write_audit_log(
        db,
        user_id=current_user.id,
        action="start_training",
        entity_type="dataset",
        entity_id=str(dataset.id),
        detail={"training_run_id": str(run.id)},
    )
    submit_job(run_training_job, str(run.id))
    return run


@router.post(
    "/datasets/{dataset_id}/experiment-k",
    response_model=TrainingRunResponse,
    status_code=status.HTTP_201_CREATED,
)
def experiment_k(
    dataset_id: str,
    payload: ExperimentKRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = _get_dataset_or_404(db, dataset_id)
    split = _get_split_or_404(db, dataset_id, str(payload.data_split_id))

    run = TrainingRun(
        dataset_id=dataset.id,
        data_split_id=split.id,
        label_mode=split.label_mode,
        run_type="experiment",
        tfidf_config=payload.tfidf_config.model_dump(),
        knn_config={"metric": payload.metric, "weights": payload.weights},
        selection_metric=payload.selection_metric,
        status=ProcessingStatus.PENDING.value,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    write_audit_log(
        db,
        user_id=current_user.id,
        action="start_experiment_k",
        entity_type="dataset",
        entity_id=str(dataset.id),
        detail={"training_run_id": str(run.id), "k_values": payload.k_values},
    )
    submit_job(run_experiment_k_job, str(run.id), payload.k_values)
    return run


@router.get("/training-runs", response_model=PaginatedResponse[TrainingRunResponse])
def list_training_runs(
    dataset_id: str | None = None,
    run_type: str | None = None,
    page_params: PageParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(TrainingRun)
    if dataset_id:
        query = query.filter(TrainingRun.dataset_id == dataset_id)
    if run_type:
        query = query.filter(TrainingRun.run_type == run_type)

    total = query.count()
    items = (
        query.order_by(TrainingRun.created_at.desc())
        .offset(page_params.offset)
        .limit(page_params.page_size)
        .all()
    )
    return PaginatedResponse(items=items, pagination=build_pagination(page_params, total))


@router.get("/training-runs/{run_id}", response_model=TrainingRunResponse)
def get_training_run(
    run_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    run = db.get(TrainingRun, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training run tidak ditemukan.")
    return run


@router.post("/training-runs/{run_id}/activate", response_model=TrainingRunResponse)
def activate_training_run(
    run_id: str,
    payload: ActivateRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = db.get(TrainingRun, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training run tidak ditemukan.")
    if run.run_type != "single" or run.status != ProcessingStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hanya training run tunggal yang sudah selesai yang dapat diaktifkan.",
        )
    if not payload.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Konfirmasi diperlukan (confirm=true) untuk mengganti model aktif.",
        )

    db.query(TrainingRun).filter(
        TrainingRun.dataset_id == run.dataset_id, TrainingRun.is_active.is_(True)
    ).update({"is_active": False})

    run.is_active = True
    run.activated_at = datetime.now(UTC)
    db.commit()
    db.refresh(run)

    write_audit_log(
        db,
        user_id=current_user.id,
        action="activate_training_run",
        entity_type="training_run",
        entity_id=str(run.id),
    )
    return run
