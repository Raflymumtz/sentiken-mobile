from sqlalchemy import exists
from sqlalchemy.orm import Query, Session

from app.models.label import SentimentLabel
from app.models.ml import Prediction
from app.models.review import PreprocessingResult, Review
from app.schemas.review import ReviewFilterParams


def apply_review_filters(db: Session, query: Query, filters: ReviewFilterParams) -> Query:
    if filters.app_source_id:
        query = query.filter(Review.app_source_id == str(filters.app_source_id))
    if filters.score is not None:
        query = query.filter(Review.score == filters.score)
    if filters.date_from:
        query = query.filter(Review.review_date >= filters.date_from)
    if filters.date_to:
        query = query.filter(Review.review_date <= filters.date_to)
    if filters.search:
        query = query.filter(Review.content.ilike(f"%{filters.search}%"))
    if filters.label:
        query = query.filter(
            exists().where(SentimentLabel.review_id == Review.id, SentimentLabel.label == filters.label)
        )
    if filters.preprocessing_status == "processed":
        query = query.filter(exists().where(PreprocessingResult.review_id == Review.id))
    elif filters.preprocessing_status == "not_processed":
        query = query.filter(~exists().where(PreprocessingResult.review_id == Review.id))
    if filters.prediction_status == "predicted":
        query = query.filter(exists().where(Prediction.review_id == Review.id))
    elif filters.prediction_status == "not_predicted":
        query = query.filter(~exists().where(Prediction.review_id == Review.id))
    return query
