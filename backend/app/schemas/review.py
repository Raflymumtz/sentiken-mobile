import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class PreprocessingResultResponse(ORMModel):
    case_folded_text: str
    cleaned_text: str
    normalized_text: str
    tokens: list[str]
    tokens_no_stopword: list[str]
    stemmed_text: str
    final_text: str
    processed_at: datetime


class SentimentLabelResponse(ORMModel):
    label_mode: str
    positive_score: float
    negative_score: float
    sentiment_score: float
    label: str
    is_excluded_from_training: bool
    labeled_at: datetime


class ReviewResponse(ORMModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    app_source_id: uuid.UUID
    review_id: str | None
    username: str | None
    user_image: str | None
    content: str
    score: int | None
    thumbs_up_count: int
    review_date: date | None
    app_version: str | None
    reply_content: str | None
    reply_date: date | None
    source: str
    fetched_at: datetime
    created_at: datetime
    preprocessing_result: PreprocessingResultResponse | None = None
    sentiment_labels: list[SentimentLabelResponse] = []


class ReviewDetailResponse(ReviewResponse):
    predicted_label: str | None = None
    prediction_confidence: float | None = None
    nearest_neighbors: list[dict] = []


class ReviewFilterParams(BaseModel):
    app_source_id: uuid.UUID | None = None
    label: str | None = None
    score: int | None = None
    date_from: date | None = None
    date_to: date | None = None
    search: str | None = None
    preprocessing_status: str | None = None
    prediction_status: str | None = None
