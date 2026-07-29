from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.jobs.queue import submit_job
from app.models.dataset import Dataset
from app.models.review import PreprocessingResult, Review
from app.models.user import User
from app.schemas.review import PreprocessingResultResponse
from app.services.audit import write_audit_log
from app.services.preprocessing_job import run_preprocessing_job

router = APIRouter(tags=["Preprocessing"])


class PreprocessingStatusResponse(BaseModel):
    dataset_id: str
    status: str
    total_reviews: int
    processed_reviews: int
    remaining_reviews: int
    progress_percent: float


class MessageResponse(BaseModel):
    message: str


def _get_dataset_or_404(db: Session, dataset_id: str) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.deleted_at.is_(None)).first()
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset tidak ditemukan.")
    return dataset


@router.post("/datasets/{dataset_id}/preprocess", response_model=MessageResponse)
def start_preprocessing(
    dataset_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    dataset = _get_dataset_or_404(db, dataset_id)

    total_reviews = db.query(Review).filter(Review.dataset_id == dataset.id).count()
    if total_reviews == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset belum memiliki ulasan. Kumpulkan atau impor data terlebih dahulu.",
        )

    write_audit_log(
        db,
        user_id=current_user.id,
        action="start_preprocessing",
        entity_type="dataset",
        entity_id=str(dataset.id),
    )
    submit_job(run_preprocessing_job, str(dataset.id))
    return MessageResponse(message="Proses preprocessing dimulai di latar belakang.")


@router.get("/datasets/{dataset_id}/preprocessing-status", response_model=PreprocessingStatusResponse)
def get_preprocessing_status(
    dataset_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    dataset = _get_dataset_or_404(db, dataset_id)

    total_reviews = db.query(Review).filter(Review.dataset_id == dataset.id).count()
    processed_reviews = (
        db.query(Review)
        .join(PreprocessingResult, PreprocessingResult.review_id == Review.id)
        .filter(Review.dataset_id == dataset.id)
        .count()
    )
    progress = round((processed_reviews / total_reviews) * 100, 2) if total_reviews else 0.0

    return PreprocessingStatusResponse(
        dataset_id=str(dataset.id),
        status=dataset.preprocessing_status,
        total_reviews=total_reviews,
        processed_reviews=processed_reviews,
        remaining_reviews=total_reviews - processed_reviews,
        progress_percent=progress,
    )


@router.get("/reviews/{review_id}/preprocessing", response_model=PreprocessingResultResponse)
def get_review_preprocessing(
    review_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    review = db.get(Review, review_id)
    if review is None or review.preprocessing_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hasil preprocessing untuk ulasan ini belum tersedia.",
        )
    return review.preprocessing_result
