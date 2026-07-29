import logging
from datetime import UTC, datetime

from app.database import SessionLocal
from app.models.dataset import Dataset
from app.models.dictionary import NormalizationDictionary, Stopword
from app.models.enums import ProcessingStatus
from app.models.review import PreprocessingResult, Review
from app.services.preprocessing import run_pipeline

logger = logging.getLogger("sentiken")


def run_preprocessing_job(dataset_id: str) -> None:
    """Dijalankan di background. Memproses seluruh review pada dataset yang
    belum memiliki hasil preprocessing (idempoten -- aman dijalankan ulang)."""
    db = SessionLocal()
    try:
        dataset = db.get(Dataset, dataset_id)
        if dataset is None:
            logger.error("Dataset %s tidak ditemukan untuk preprocessing.", dataset_id)
            return

        dataset.preprocessing_status = ProcessingStatus.RUNNING.value
        db.commit()

        normalization_map = {
            row.informal_word: row.formal_word for row in db.query(NormalizationDictionary).all()
        }
        stopword_set = {row.word for row in db.query(Stopword).all()}

        reviews = (
            db.query(Review)
            .filter(Review.dataset_id == dataset_id)
            .outerjoin(PreprocessingResult, PreprocessingResult.review_id == Review.id)
            .filter(PreprocessingResult.id.is_(None))
            .all()
        )

        for review in reviews:
            result = run_pipeline(review.content, normalization_map, stopword_set)
            db.add(
                PreprocessingResult(
                    review_id=review.id,
                    case_folded_text=result.case_folded_text,
                    cleaned_text=result.cleaned_text,
                    normalized_text=result.normalized_text,
                    tokens=result.tokens,
                    tokens_no_stopword=result.tokens_no_stopword,
                    stemmed_text=result.stemmed_text,
                    final_text=result.final_text,
                    processed_at=datetime.now(UTC),
                )
            )
            db.flush()

        dataset.preprocessing_status = ProcessingStatus.COMPLETED.value
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Preprocessing dataset %s gagal: %s", dataset_id, exc)
        db.rollback()
        dataset = db.get(Dataset, dataset_id)
        if dataset:
            dataset.preprocessing_status = ProcessingStatus.FAILED.value
            db.commit()
    finally:
        db.close()
