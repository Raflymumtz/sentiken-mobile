from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.ml import Prediction
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewDetailResponse

router = APIRouter(prefix="/reviews", tags=["Ulasan"])


@router.get("/{review_id}", response_model=ReviewDetailResponse)
def get_review_detail(
    review_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ulasan tidak ditemukan.")

    latest_prediction = (
        db.query(Prediction)
        .filter(Prediction.review_id == review.id)
        .order_by(Prediction.created_at.desc())
        .first()
    )

    response = ReviewDetailResponse.model_validate(review)
    if latest_prediction:
        response.predicted_label = latest_prediction.predicted_label
        response.prediction_confidence = latest_prediction.confidence
        response.nearest_neighbors = latest_prediction.neighbors
    return response
