from collections import Counter
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.app_source import AppSource
from app.models.dataset import Dataset
from app.models.job import CollectionJob, ImportJob
from app.models.label import SentimentLabel
from app.models.ml import EvaluationMetric, KnnModel, TrainingRun
from app.models.review import PreprocessingResult, Review


def _dataset_label_mode_map(db: Session) -> dict[str, str]:
    return {str(d.id): d.label_mode for d in db.query(Dataset.id, Dataset.label_mode).all()}


def get_summary(db: Session) -> dict:
    total_datasets = db.query(Dataset).filter(Dataset.deleted_at.is_(None)).count()
    total_reviews = db.query(Review).count()

    by_app_rows = (
        db.query(AppSource.app_name, func.count(Review.id))
        .join(Review, Review.app_source_id == AppSource.id)
        .group_by(AppSource.app_name)
        .all()
    )
    total_reviews_by_app = {name: count for name, count in by_app_rows}

    label_rows = (
        db.query(SentimentLabel.label, func.count(SentimentLabel.id))
        .join(Dataset, Dataset.id == SentimentLabel.dataset_id)
        .filter(SentimentLabel.label_mode == Dataset.label_mode)
        .group_by(SentimentLabel.label)
        .all()
    )
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    for label, count in label_rows:
        sentiment_counts[label] = count
    total_labeled = sum(sentiment_counts.values())
    sentiment_percentage = (
        {k: round((v / total_labeled) * 100, 2) for k, v in sentiment_counts.items()}
        if total_labeled
        else {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
    )

    active_run = (
        db.query(TrainingRun)
        .filter(TrainingRun.is_active.is_(True))
        .order_by(TrainingRun.activated_at.desc())
        .first()
    )
    active_model_version = None
    active_k = None
    active_metrics = None
    if active_run:
        active_model_version = active_run.model_version
        knn_model = db.query(KnnModel).filter(KnnModel.training_run_id == active_run.id).first()
        if knn_model:
            active_k = knn_model.n_neighbors
        metric = (
            db.query(EvaluationMetric)
            .filter(EvaluationMetric.training_run_id == active_run.id)
            .order_by(EvaluationMetric.created_at.desc())
            .first()
        )
        if metric:
            active_metrics = {
                "accuracy": metric.accuracy,
                "precision": metric.precision_weighted,
                "recall": metric.recall_weighted,
                "f1_score": metric.f1_weighted,
            }

    latest_collection = db.query(CollectionJob).order_by(CollectionJob.created_at.desc()).first()
    latest_import = db.query(ImportJob).order_by(ImportJob.created_at.desc()).first()
    latest_job_status, latest_job_type = None, None
    candidates = []
    if latest_collection:
        candidates.append(("collection", latest_collection.status, latest_collection.created_at))
    if latest_import:
        candidates.append(("import", latest_import.status, latest_import.created_at))
    if candidates:
        candidates.sort(key=lambda c: c[2], reverse=True)
        latest_job_type, latest_job_status, _ = candidates[0]

    pln_count = total_reviews_by_app.get("PLN Mobile", 0)
    mypertamina_count = total_reviews_by_app.get("MyPertamina", 0)

    return {
        "has_data": total_reviews > 0,
        "total_datasets": total_datasets,
        "total_reviews": total_reviews,
        "total_reviews_by_app": total_reviews_by_app,
        "total_reviews_pln_mobile": pln_count,
        "total_reviews_mypertamina": mypertamina_count,
        "sentiment_counts": sentiment_counts,
        "sentiment_percentage": sentiment_percentage,
        "active_model_version": active_model_version,
        "active_k": active_k,
        "active_metrics": active_metrics,
        "latest_job_status": latest_job_status,
        "latest_job_type": latest_job_type,
    }


def get_sentiment_comparison(db: Session) -> list[dict]:
    sources = db.query(AppSource).filter(AppSource.deleted_at.is_(None)).all()
    label_mode_map = _dataset_label_mode_map(db)
    results = []

    for source in sources:
        reviews = db.query(Review).filter(Review.app_source_id == source.id).all()
        total = len(reviews)
        rating_distribution = {str(i): 0 for i in range(1, 6)}
        rating_sum, rating_count = 0, 0
        for review in reviews:
            if review.score and 1 <= review.score <= 5:
                rating_distribution[str(review.score)] += 1
                rating_sum += review.score
                rating_count += 1

        labels = (
            db.query(SentimentLabel)
            .join(Review, Review.id == SentimentLabel.review_id)
            .filter(Review.app_source_id == source.id)
            .all()
        )
        counts = {"positive": 0, "negative": 0, "neutral": 0}
        for label in labels:
            dataset_mode = label_mode_map.get(str(label.dataset_id))
            if dataset_mode and label.label_mode == dataset_mode and label.label in counts:
                counts[label.label] += 1
        total_labeled = sum(counts.values())

        def _pct(count: int, denom: int = total_labeled) -> float:
            return round((count / denom) * 100, 2) if denom else 0.0

        results.append(
            {
                "app_source_id": source.id,
                "app_name": source.app_name,
                "total_reviews": total,
                "positive_count": counts["positive"],
                "negative_count": counts["negative"],
                "neutral_count": counts["neutral"],
                "positive_percentage": _pct(counts["positive"]),
                "negative_percentage": _pct(counts["negative"]),
                "neutral_percentage": _pct(counts["neutral"]),
                "average_rating": round(rating_sum / rating_count, 2) if rating_count else None,
                "rating_distribution": rating_distribution,
            }
        )
    return results


def get_sentiment_trend(db: Session, granularity: str = "month") -> list[dict]:
    label_mode_map = _dataset_label_mode_map(db)
    rows = (
        db.query(
            Review.app_source_id,
            AppSource.app_name,
            Review.review_date,
            SentimentLabel.label,
            SentimentLabel.dataset_id,
            SentimentLabel.label_mode,
        )
        .join(SentimentLabel, SentimentLabel.review_id == Review.id)
        .join(AppSource, AppSource.id == Review.app_source_id)
        .filter(Review.review_date.is_not(None))
        .all()
    )

    buckets: dict[tuple, Counter] = {}
    for app_source_id, app_name, review_date, label, dataset_id, label_mode in rows:
        if label_mode_map.get(str(dataset_id)) != label_mode:
            continue
        period = _format_period(review_date, granularity)
        key = (period, str(app_source_id), app_name)
        buckets.setdefault(key, Counter())[label] += 1

    points = []
    for (period, app_source_id, app_name), counter in sorted(buckets.items()):
        points.append(
            {
                "period": period,
                "app_source_id": app_source_id,
                "app_name": app_name,
                "positive_count": counter.get("positive", 0),
                "negative_count": counter.get("negative", 0),
                "neutral_count": counter.get("neutral", 0),
                "total_count": sum(counter.values()),
            }
        )
    return points


def _format_period(d: date, granularity: str) -> str:
    if granularity == "week":
        iso = d.isocalendar()
        return f"{iso[0]}-W{iso[1]:02d}"
    if granularity == "day":
        return d.isoformat()
    return f"{d.year}-{d.month:02d}"


def get_rating_distribution(db: Session) -> list[dict]:
    sources = db.query(AppSource).filter(AppSource.deleted_at.is_(None)).all()
    results = []
    for source in sources:
        distribution = {str(i): 0 for i in range(1, 6)}
        reviews = db.query(Review.score).filter(Review.app_source_id == source.id).all()
        for (score,) in reviews:
            if score and 1 <= score <= 5:
                distribution[str(score)] += 1
        results.append(
            {
                "app_source_id": source.id,
                "app_name": source.app_name,
                "distribution": distribution,
            }
        )
    return results


# Kata akar (hasil stemming Sastrawi, lihat app/services/preprocessing.py)
# yang menandakan ulasan sedang membahas aspek kecepatan/kemudahan aplikasi.
# Mencakup bentuk positif maupun negatif dari aspek yang sama (mis. "cepat"
# dan "lambat" sama-sama tentang aspek kecepatan) -- polaritasnya diambil
# dari label sentimen ulasan tersebut, bukan dari kata itu sendiri. Daftar
# kata diambil dari app/data/seed_dictionary.py agar konsisten dengan kamus
# yang sudah dipakai untuk pelabelan.
ASPECT_KEYWORDS: dict[str, set[str]] = {
    "kecepatan": {"cepat", "lambat", "lemot", "lelet", "lag"},
    "kemudahan": {"mudah", "gampang", "susah", "sulit", "ribet", "rumit"},
}

_STOP_TERMS = {"yang", "dan", "di", "ke", "ini", "itu", "untuk", "dengan", "nya"}


def get_frequent_terms(
    db: Session, app_source_id: str | None = None, label: str | None = None, top_n: int = 30
) -> list[dict]:
    query = db.query(PreprocessingResult.final_text).join(Review, Review.id == PreprocessingResult.review_id)
    if app_source_id:
        query = query.filter(Review.app_source_id == app_source_id)
    if label:
        query = query.join(SentimentLabel, SentimentLabel.review_id == Review.id).filter(
            SentimentLabel.label == label
        )

    counter: Counter = Counter()
    for (final_text,) in query.all():
        if not final_text:
            continue
        for token in final_text.split():
            if len(token) > 2 and token not in _STOP_TERMS:
                counter[token] += 1

    return [{"term": term, "frequency": freq} for term, freq in counter.most_common(top_n)]


def get_aspect_comparison(db: Session) -> list[dict]:
    """Membandingkan sentimen ulasan per aspek (kecepatan, kemudahan) antar aplikasi.

    Ulasan yang teks hasil preprocessing-nya memuat salah satu kata pada
    ASPECT_KEYWORDS untuk suatu aspek dihitung sebagai "menyebut" aspek itu;
    polaritasnya diambil dari label sentimen ulasan (hasil pelabelan kamus
    yang sudah ada), bukan dianalisis ulang di sini.
    """
    sources = db.query(AppSource).filter(AppSource.deleted_at.is_(None)).all()
    label_mode_map = _dataset_label_mode_map(db)
    results = []

    for source in sources:
        rows = (
            db.query(
                PreprocessingResult.final_text,
                SentimentLabel.label,
                SentimentLabel.label_mode,
                SentimentLabel.dataset_id,
            )
            .join(Review, Review.id == PreprocessingResult.review_id)
            .join(SentimentLabel, SentimentLabel.review_id == Review.id)
            .filter(Review.app_source_id == source.id)
            .all()
        )

        aspect_counts = {name: {"positive": 0, "negative": 0, "neutral": 0} for name in ASPECT_KEYWORDS}

        for final_text, label, label_mode, dataset_id in rows:
            if label_mode_map.get(str(dataset_id)) != label_mode:
                continue
            if not final_text or label not in ("positive", "negative", "neutral"):
                continue
            tokens = set(final_text.split())
            for aspect_name, keywords in ASPECT_KEYWORDS.items():
                if tokens & keywords:
                    aspect_counts[aspect_name][label] += 1

        aspects_out = []
        for aspect_name, counts in aspect_counts.items():
            total = sum(counts.values())

            def _pct(count: int, denom: int = total) -> float:
                return round((count / denom) * 100, 2) if denom else 0.0

            aspects_out.append(
                {
                    "aspect": aspect_name,
                    "total_mentions": total,
                    "positive_count": counts["positive"],
                    "negative_count": counts["negative"],
                    "neutral_count": counts["neutral"],
                    "positive_percentage": _pct(counts["positive"]),
                    "negative_percentage": _pct(counts["negative"]),
                    "neutral_percentage": _pct(counts["neutral"]),
                }
            )

        results.append(
            {
                "app_source_id": source.id,
                "app_name": source.app_name,
                "aspects": aspects_out,
            }
        )

    return results
