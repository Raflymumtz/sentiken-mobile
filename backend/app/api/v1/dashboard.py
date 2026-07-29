from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.dashboard import (
    AspectComparisonResponse,
    DashboardSummary,
    FrequentTermsResponse,
    RatingDistributionResponse,
    SentimentComparisonResponse,
    SentimentTrendResponse,
)
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return dashboard_service.get_summary(db)


@router.get("/sentiment-comparison", response_model=SentimentComparisonResponse)
def sentiment_comparison(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return SentimentComparisonResponse(items=dashboard_service.get_sentiment_comparison(db))


@router.get("/sentiment-trend", response_model=SentimentTrendResponse)
def sentiment_trend(
    granularity: str = "month",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    granularity = granularity if granularity in ("day", "week", "month") else "month"
    points = dashboard_service.get_sentiment_trend(db, granularity)
    return SentimentTrendResponse(granularity=granularity, points=points)


@router.get("/rating-distribution", response_model=RatingDistributionResponse)
def rating_distribution(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return RatingDistributionResponse(items=dashboard_service.get_rating_distribution(db))


@router.get("/frequent-terms", response_model=FrequentTermsResponse)
def frequent_terms(
    app_source_id: str | None = None,
    label: str | None = None,
    top_n: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    terms = dashboard_service.get_frequent_terms(db, app_source_id, label, top_n)
    return FrequentTermsResponse(app_source_id=app_source_id, label=label, terms=terms)


@router.get("/aspect-comparison", response_model=AspectComparisonResponse)
def aspect_comparison(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return AspectComparisonResponse(items=dashboard_service.get_aspect_comparison(db))
