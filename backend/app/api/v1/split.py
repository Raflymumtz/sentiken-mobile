from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.dataset import Dataset
from app.models.label import SentimentLabel
from app.models.ml import DataSplit
from app.models.user import User
from app.schemas.ml import SplitRequest, SplitResponse
from app.services.audit import write_audit_log
from app.services.splitting import EligibleItem, SplitValidationError, validate_and_split

router = APIRouter(tags=["Split Data"])


def _get_dataset_or_404(db: Session, dataset_id: str) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.deleted_at.is_(None)).first()
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset tidak ditemukan.")
    return dataset


def _to_response(split: DataSplit) -> SplitResponse:
    return SplitResponse(
        id=split.id,
        dataset_id=split.dataset_id,
        label_mode=split.label_mode,
        train_size=split.train_size,
        test_size=split.test_size,
        random_state=split.random_state,
        stratify=split.stratify,
        train_count=len(split.train_review_ids),
        test_count=len(split.test_review_ids),
        class_distribution=split.class_distribution,
        created_at=split.created_at,
    )


@router.post(
    "/datasets/{dataset_id}/split", response_model=SplitResponse, status_code=status.HTTP_201_CREATED
)
def create_split(
    dataset_id: str,
    payload: SplitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = _get_dataset_or_404(db, dataset_id)

    labels = (
        db.query(SentimentLabel)
        .filter(
            SentimentLabel.dataset_id == dataset.id,
            SentimentLabel.label_mode == payload.label_mode,
            SentimentLabel.is_excluded_from_training.is_(False),
        )
        .all()
    )
    items = [EligibleItem(review_id=str(label.review_id), label=label.label, text="") for label in labels]

    try:
        result = validate_and_split(
            items,
            train_size=payload.train_size,
            test_size=payload.test_size,
            random_state=payload.random_state,
            stratify=payload.stratify,
        )
    except SplitValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    split = DataSplit(
        dataset_id=dataset.id,
        label_mode=payload.label_mode,
        train_size=payload.train_size,
        test_size=payload.test_size,
        random_state=payload.random_state,
        stratify=payload.stratify,
        train_review_ids=result.train_ids,
        test_review_ids=result.test_ids,
        class_distribution=result.class_distribution,
        created_at=datetime.now(UTC),
    )
    db.add(split)
    db.commit()
    db.refresh(split)

    write_audit_log(
        db,
        user_id=current_user.id,
        action="create_split",
        entity_type="dataset",
        entity_id=str(dataset.id),
        detail={"train_count": len(result.train_ids), "test_count": len(result.test_ids)},
    )
    return _to_response(split)


@router.get("/datasets/{dataset_id}/splits", response_model=list[SplitResponse])
def list_splits(
    dataset_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    _get_dataset_or_404(db, dataset_id)
    splits = (
        db.query(DataSplit)
        .filter(DataSplit.dataset_id == dataset_id)
        .order_by(DataSplit.created_at.desc())
        .all()
    )
    return [_to_response(s) for s in splits]
