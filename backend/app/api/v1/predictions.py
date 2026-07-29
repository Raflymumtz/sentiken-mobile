from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import PageParams, build_pagination, get_current_user, get_db
from app.models.ml import Prediction
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.ml import NeighborInfo, SinglePredictionRequest, SinglePredictionResponse
from app.services.audit import write_audit_log
from app.services.prediction_service import PredictionError, predict_single_text

router = APIRouter(prefix="/predictions", tags=["Prediksi"])


@router.post("/single", response_model=SinglePredictionResponse)
def predict_single(
    payload: SinglePredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run_id = str(payload.training_run_id) if payload.training_run_id else None
    try:
        result = predict_single_text(db, payload.text, run_id, current_user.id)
    except PredictionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    write_audit_log(
        db,
        user_id=current_user.id,
        action="predict_single",
        entity_type="prediction",
        detail={"predicted_label": result["predicted_label"]},
    )

    return SinglePredictionResponse(
        original_text=result["original_text"],
        final_text=result["final_text"],
        predicted_label=result["predicted_label"],
        confidence=result["confidence"],
        k_used=result["k_used"],
        neighbors=[NeighborInfo(**n) for n in result["neighbors"]],
        model_version=result["model_version"],
        training_run_id=result["training_run_id"],
        prediction_time_ms=result["prediction_time_ms"],
    )


@router.get("/history", response_model=PaginatedResponse[dict])
def prediction_history(
    training_run_id: str | None = None,
    page_params: PageParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Prediction).filter(Prediction.source == "single")
    if training_run_id:
        query = query.filter(Prediction.training_run_id == training_run_id)

    total = query.count()
    items = (
        query.order_by(Prediction.created_at.desc())
        .offset(page_params.offset)
        .limit(page_params.page_size)
        .all()
    )
    payload = [
        {
            "id": str(p.id),
            "input_text": p.input_text,
            "final_text": p.final_text,
            "predicted_label": p.predicted_label,
            "confidence": p.confidence,
            "k_used": p.k_used,
            "training_run_id": str(p.training_run_id),
            "created_at": p.created_at.isoformat(),
        }
        for p in items
    ]
    return PaginatedResponse(items=payload, pagination=build_pagination(page_params, total))
