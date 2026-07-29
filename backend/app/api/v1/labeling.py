from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.jobs.queue import submit_job
from app.models.dataset import Dataset
from app.models.label import SentimentLabel
from app.models.review import PreprocessingResult, Review
from app.models.user import User
from app.services.audit import write_audit_log
from app.services.labeling_job import run_labeling_job

router = APIRouter(tags=["Labelisasi"])


class LabelRequest(BaseModel):
    label_mode: str = Field(default="binary", pattern="^(binary|ternary)$")


class MessageResponse(BaseModel):
    message: str


class LabelSummaryResponse(BaseModel):
    dataset_id: str
    label_mode: str
    status: str
    total_labeled: int
    positive_count: int
    negative_count: int
    neutral_count: int
    excluded_from_training: int


def _get_dataset_or_404(db: Session, dataset_id: str) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.deleted_at.is_(None)).first()
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset tidak ditemukan.")
    return dataset


@router.post("/datasets/{dataset_id}/label", response_model=MessageResponse)
def start_labeling(
    dataset_id: str,
    payload: LabelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = _get_dataset_or_404(db, dataset_id)

    processed_count = (
        db.query(Review)
        .join(PreprocessingResult, PreprocessingResult.review_id == Review.id)
        .filter(Review.dataset_id == dataset.id)
        .count()
    )
    if processed_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Belum ada ulasan yang diproses (preprocessing). Jalankan preprocessing terlebih dahulu.",
        )

    write_audit_log(
        db,
        user_id=current_user.id,
        action="start_labeling",
        entity_type="dataset",
        entity_id=str(dataset.id),
        detail={"label_mode": payload.label_mode},
    )
    submit_job(run_labeling_job, str(dataset.id), payload.label_mode)
    return MessageResponse(message="Proses labelisasi kamus sentimen dimulai di latar belakang.")


@router.get("/datasets/{dataset_id}/label-summary", response_model=LabelSummaryResponse)
def get_label_summary(
    dataset_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    dataset = _get_dataset_or_404(db, dataset_id)

    labels = (
        db.query(SentimentLabel)
        .filter(SentimentLabel.dataset_id == dataset.id, SentimentLabel.label_mode == dataset.label_mode)
        .all()
    )
    positive = sum(1 for label in labels if label.label == "positive")
    negative = sum(1 for label in labels if label.label == "negative")
    neutral = sum(1 for label in labels if label.label == "neutral")
    excluded = sum(1 for label in labels if label.is_excluded_from_training)

    return LabelSummaryResponse(
        dataset_id=str(dataset.id),
        label_mode=dataset.label_mode,
        status=dataset.labeling_status,
        total_labeled=len(labels),
        positive_count=positive,
        negative_count=negative,
        neutral_count=neutral,
        excluded_from_training=excluded,
    )
