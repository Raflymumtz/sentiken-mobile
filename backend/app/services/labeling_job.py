import logging
from datetime import UTC, datetime

from app.database import SessionLocal
from app.models.dataset import Dataset
from app.models.dictionary import DictionaryNegative, DictionaryPositive
from app.models.enums import LabelMode, ProcessingStatus
from app.models.label import SentimentLabel
from app.models.review import PreprocessingResult, Review
from app.services.labeling import score_text

logger = logging.getLogger("sentiken")


def run_labeling_job(dataset_id: str, label_mode: str) -> None:
    db = SessionLocal()
    try:
        dataset = db.get(Dataset, dataset_id)
        if dataset is None:
            logger.error("Dataset %s tidak ditemukan untuk labelisasi.", dataset_id)
            return

        dataset.labeling_status = ProcessingStatus.RUNNING.value
        dataset.label_mode = label_mode
        db.commit()

        positive_lexicon = {row.word: row.weight for row in db.query(DictionaryPositive).all()}
        negative_lexicon = {row.word: row.weight for row in db.query(DictionaryNegative).all()}

        reviews = (
            db.query(Review)
            .join(PreprocessingResult, PreprocessingResult.review_id == Review.id)
            .filter(Review.dataset_id == dataset_id)
            .all()
        )

        for review in reviews:
            final_text = review.preprocessing_result.final_text if review.preprocessing_result else ""
            result = score_text(final_text, positive_lexicon, negative_lexicon)

            is_excluded = label_mode == LabelMode.BINARY.value and result.label == "neutral"

            existing = (
                db.query(SentimentLabel)
                .filter(SentimentLabel.review_id == review.id, SentimentLabel.label_mode == label_mode)
                .first()
            )
            if existing is None:
                existing = SentimentLabel(review_id=review.id, dataset_id=dataset_id, label_mode=label_mode)
                db.add(existing)

            existing.positive_score = result.positive_score
            existing.negative_score = result.negative_score
            existing.sentiment_score = result.sentiment_score
            existing.label = result.label
            existing.is_excluded_from_training = is_excluded
            existing.labeled_at = datetime.now(UTC)
            db.flush()

        dataset.labeling_status = ProcessingStatus.COMPLETED.value
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Labelisasi dataset %s gagal: %s", dataset_id, exc)
        db.rollback()
        dataset = db.get(Dataset, dataset_id)
        if dataset:
            dataset.labeling_status = ProcessingStatus.FAILED.value
            db.commit()
    finally:
        db.close()
