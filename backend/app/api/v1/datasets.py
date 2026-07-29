import csv
import io
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import PageParams, build_pagination, get_current_user, get_db
from app.models.app_source import AppSource
from app.models.dataset import Dataset
from app.models.label import SentimentLabel
from app.models.review import Review
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.dataset import (
    DatasetCreate,
    DatasetResponse,
    DatasetSummaryResponse,
    DatasetUpdate,
)
from app.schemas.review import ReviewFilterParams, ReviewResponse
from app.services.audit import write_audit_log
from app.services.review_query import apply_review_filters

router = APIRouter(prefix="/datasets", tags=["Dataset"])


def _to_response(db: Session, dataset: Dataset) -> DatasetResponse:
    review_count = db.query(Review).filter(Review.dataset_id == dataset.id).count()
    response = DatasetResponse.model_validate(dataset)
    return response.model_copy(update={"review_count": review_count})


@router.get("", response_model=PaginatedResponse[DatasetResponse])
def list_datasets(
    app_source_id: str | None = None,
    page_params: PageParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Dataset).filter(Dataset.deleted_at.is_(None))
    if app_source_id:
        query = query.filter(Dataset.app_source_id == app_source_id)

    total = query.count()
    items = (
        query.order_by(Dataset.created_at.desc())
        .offset(page_params.offset)
        .limit(page_params.page_size)
        .all()
    )
    return PaginatedResponse(
        items=[_to_response(db, ds) for ds in items],
        pagination=build_pagination(page_params, total),
    )


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
def create_dataset(
    payload: DatasetCreate,
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

    dataset = Dataset(
        name=payload.name,
        app_source_id=str(payload.app_source_id),
        description=payload.description,
        period_start=payload.period_start,
        period_end=payload.period_end,
        label_mode=payload.label_mode,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    write_audit_log(
        db,
        user_id=current_user.id,
        action="create",
        entity_type="dataset",
        entity_id=str(dataset.id),
        detail={"name": dataset.name},
    )
    return _to_response(db, dataset)


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    dataset = _get_or_404(db, dataset_id)
    return _to_response(db, dataset)


@router.put("/{dataset_id}", response_model=DatasetResponse)
def update_dataset(
    dataset_id: str,
    payload: DatasetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = _get_or_404(db, dataset_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dataset, field, value)
    db.commit()
    db.refresh(dataset)
    write_audit_log(
        db,
        user_id=current_user.id,
        action="update",
        entity_type="dataset",
        entity_id=str(dataset.id),
        detail=update_data,
    )
    return _to_response(db, dataset)


@router.delete("/{dataset_id}", response_model=MessageResponse)
def delete_dataset(
    dataset_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    dataset = _get_or_404(db, dataset_id)
    dataset.deleted_at = datetime.now(UTC)
    db.commit()
    write_audit_log(
        db, user_id=current_user.id, action="delete", entity_type="dataset", entity_id=str(dataset.id)
    )
    return MessageResponse(message="Dataset berhasil dihapus.")


@router.get("/{dataset_id}/summary", response_model=DatasetSummaryResponse)
def dataset_summary(
    dataset_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    dataset = _get_or_404(db, dataset_id)

    reviews = db.query(Review).filter(Review.dataset_id == dataset.id).all()
    rating_distribution: dict[str, int] = {str(i): 0 for i in range(1, 6)}
    for review in reviews:
        if review.score and 1 <= review.score <= 5:
            rating_distribution[str(review.score)] += 1

    label_distribution = {"positive": 0, "negative": 0, "neutral": 0}
    labels = (
        db.query(SentimentLabel)
        .filter(SentimentLabel.dataset_id == dataset.id, SentimentLabel.label_mode == dataset.label_mode)
        .all()
    )
    for label in labels:
        if label.label in label_distribution:
            label_distribution[label.label] += 1

    from app.models.ml import TrainingRun

    active_run = (
        db.query(TrainingRun)
        .filter(TrainingRun.dataset_id == dataset.id, TrainingRun.is_active.is_(True))
        .first()
    )

    return DatasetSummaryResponse(
        dataset_id=dataset.id,
        total_reviews=len(reviews),
        rating_distribution=rating_distribution,
        label_distribution=label_distribution,
        preprocessing_status=dataset.preprocessing_status,
        labeling_status=dataset.labeling_status,
        training_status=dataset.training_status,
        active_training_run_id=active_run.id if active_run else None,
    )


@router.get("/{dataset_id}/reviews", response_model=PaginatedResponse[ReviewResponse])
def list_dataset_reviews(
    dataset_id: str,
    filters: ReviewFilterParams = Depends(),
    page_params: PageParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_or_404(db, dataset_id)
    query = db.query(Review).filter(Review.dataset_id == dataset_id)
    query = apply_review_filters(db, query, filters)

    total = query.count()
    items = (
        query.order_by(Review.review_date.desc().nullslast(), Review.created_at.desc())
        .offset(page_params.offset)
        .limit(page_params.page_size)
        .all()
    )
    return PaginatedResponse(items=items, pagination=build_pagination(page_params, total))


@router.get("/{dataset_id}/export")
def export_dataset(
    dataset_id: str,
    kind: str = "raw",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = _get_or_404(db, dataset_id)
    reviews = (
        db.query(Review)
        .filter(Review.dataset_id == dataset.id)
        .order_by(Review.review_date.desc().nullslast())
        .all()
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)

    if kind == "preprocessing":
        writer.writerow(
            ["review_id", "content", "case_folded", "cleaned", "normalized", "stemmed", "final_text"]
        )
        for review in reviews:
            pr = review.preprocessing_result
            writer.writerow(
                [
                    review.review_id or str(review.id),
                    review.content,
                    pr.case_folded_text if pr else "",
                    pr.cleaned_text if pr else "",
                    pr.normalized_text if pr else "",
                    pr.stemmed_text if pr else "",
                    pr.final_text if pr else "",
                ]
            )
        filename = f"preprocessing_{dataset.id}.csv"
    elif kind == "labeling":
        writer.writerow(
            ["review_id", "content", "positive_score", "negative_score", "sentiment_score", "label"]
        )
        for review in reviews:
            label = next((sl for sl in review.sentiment_labels if sl.label_mode == dataset.label_mode), None)
            writer.writerow(
                [
                    review.review_id or str(review.id),
                    review.content,
                    label.positive_score if label else "",
                    label.negative_score if label else "",
                    label.sentiment_score if label else "",
                    label.label if label else "",
                ]
            )
        filename = f"labeling_{dataset.id}.csv"
    else:
        writer.writerow(
            [
                "review_id",
                "username",
                "content",
                "score",
                "thumbs_up_count",
                "review_date",
                "app_version",
                "reply_content",
                "reply_date",
                "source",
            ]
        )
        for review in reviews:
            writer.writerow(
                [
                    review.review_id or "",
                    review.username or "",
                    review.content,
                    review.score or "",
                    review.thumbs_up_count,
                    review.review_date.isoformat() if review.review_date else "",
                    review.app_version or "",
                    review.reply_content or "",
                    review.reply_date.isoformat() if review.reply_date else "",
                    review.source,
                ]
            )
        filename = f"raw_reviews_{dataset.id}.csv"

    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _get_or_404(db: Session, dataset_id: str) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.deleted_at.is_(None)).first()
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset tidak ditemukan.")
    return dataset
