from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import PageParams, build_pagination, get_current_user, get_db
from app.models.ml import EvaluationMetric, Prediction, TrainingRun
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.ml import ConfusionMatrixResponse, EvaluationMetricResponse

router = APIRouter(prefix="/training-runs", tags=["Evaluasi"])


def _get_metric_or_404(db: Session, run_id: str) -> EvaluationMetric:
    metric = (
        db.query(EvaluationMetric)
        .filter(EvaluationMetric.training_run_id == run_id)
        .order_by(EvaluationMetric.created_at.desc())
        .first()
    )
    if metric is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hasil evaluasi belum tersedia untuk training run ini.",
        )
    return metric


def _to_response(metric: EvaluationMetric) -> EvaluationMetricResponse:
    return EvaluationMetricResponse(
        training_run_id=metric.training_run_id,
        accuracy=metric.accuracy,
        precision_macro=metric.precision_macro,
        recall_macro=metric.recall_macro,
        f1_macro=metric.f1_macro,
        precision_weighted=metric.precision_weighted,
        recall_weighted=metric.recall_weighted,
        f1_weighted=metric.f1_weighted,
        support=metric.support,
        confusion_matrix=ConfusionMatrixResponse(**metric.confusion_matrix),
        classification_report=metric.classification_report,
        warnings=metric.warnings,
        created_at=metric.created_at,
    )


@router.get("/{run_id}/metrics", response_model=EvaluationMetricResponse)
def get_metrics(run_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    metric = _get_metric_or_404(db, run_id)
    return _to_response(metric)


@router.get("/{run_id}/confusion-matrix", response_model=ConfusionMatrixResponse)
def get_confusion_matrix(
    run_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    metric = _get_metric_or_404(db, run_id)
    return ConfusionMatrixResponse(**metric.confusion_matrix)


@router.get("/{run_id}/classification-report")
def get_classification_report(
    run_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    metric = _get_metric_or_404(db, run_id)
    return metric.classification_report


@router.get("/{run_id}/predictions", response_model=PaginatedResponse[dict])
def list_run_predictions(
    run_id: str,
    page_params: PageParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = db.get(TrainingRun, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training run tidak ditemukan.")

    query = db.query(Prediction).filter(Prediction.training_run_id == run_id)
    total = query.count()
    items = (
        query.order_by(Prediction.created_at.asc())
        .offset(page_params.offset)
        .limit(page_params.page_size)
        .all()
    )
    payload = [
        {
            "id": str(p.id),
            "review_id": str(p.review_id) if p.review_id else None,
            "input_text": p.input_text,
            "actual_label": p.actual_label,
            "predicted_label": p.predicted_label,
            "is_correct": p.actual_label == p.predicted_label,
            "confidence": p.confidence,
            "k_used": p.k_used,
            "neighbors": p.neighbors,
            "prediction_time_ms": p.prediction_time_ms,
        }
        for p in items
    ]
    return PaginatedResponse(items=payload, pagination=build_pagination(page_params, total))
