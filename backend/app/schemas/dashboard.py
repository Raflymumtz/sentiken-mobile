import uuid

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    has_data: bool
    total_datasets: int
    total_reviews: int
    total_reviews_by_app: dict[str, int]
    total_reviews_pln_mobile: int
    total_reviews_mypertamina: int
    sentiment_counts: dict[str, int]
    sentiment_percentage: dict[str, float]
    active_model_version: str | None
    active_k: int | None
    active_metrics: dict[str, float] | None
    latest_job_status: str | None
    latest_job_type: str | None


class SentimentComparisonItem(BaseModel):
    app_source_id: uuid.UUID
    app_name: str
    total_reviews: int
    positive_count: int
    negative_count: int
    neutral_count: int
    positive_percentage: float
    negative_percentage: float
    neutral_percentage: float
    average_rating: float | None
    rating_distribution: dict[str, int]


class SentimentComparisonResponse(BaseModel):
    items: list[SentimentComparisonItem]


class SentimentTrendPoint(BaseModel):
    period: str
    app_source_id: uuid.UUID
    app_name: str
    positive_count: int
    negative_count: int
    neutral_count: int
    total_count: int


class SentimentTrendResponse(BaseModel):
    granularity: str
    points: list[SentimentTrendPoint]


class RatingDistributionItem(BaseModel):
    app_source_id: uuid.UUID
    app_name: str
    distribution: dict[str, int]


class RatingDistributionResponse(BaseModel):
    items: list[RatingDistributionItem]


class FrequentTermItem(BaseModel):
    term: str
    frequency: int


class FrequentTermsResponse(BaseModel):
    app_source_id: uuid.UUID | None
    label: str | None
    terms: list[FrequentTermItem]


class AspectSentimentItem(BaseModel):
    aspect: str
    total_mentions: int
    positive_count: int
    negative_count: int
    neutral_count: int
    positive_percentage: float
    negative_percentage: float
    neutral_percentage: float


class AppAspectComparisonItem(BaseModel):
    app_source_id: uuid.UUID
    app_name: str
    aspects: list[AspectSentimentItem]


class AspectComparisonResponse(BaseModel):
    items: list[AppAspectComparisonItem]
