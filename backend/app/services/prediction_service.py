import time
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.dictionary import NormalizationDictionary, Stopword
from app.models.enums import PredictionSource
from app.models.ml import DataSplit, KnnModel, Prediction, TfidfModel, TrainingRun
from app.services.model_storage import load_model
from app.services.preprocessing import run_pipeline
from app.services.training_service import gather_texts_labels


class PredictionError(Exception):
    pass


def resolve_prediction_run(db: Session, training_run_id: str | None) -> TrainingRun:
    if training_run_id:
        run = db.get(TrainingRun, training_run_id)
        if run is None:
            raise PredictionError("Training run tidak ditemukan.")
        return run

    # Tidak ada dataset eksplisit pada endpoint prediksi satu teks, sehingga model
    # aktif yang dipakai adalah training run YANG PALING TERAKHIR diaktifkan secara
    # global (lihat docs/assumptions.md untuk penjelasan keputusan ini).
    run = (
        db.query(TrainingRun)
        .filter(TrainingRun.is_active.is_(True))
        .order_by(TrainingRun.activated_at.desc())
        .first()
    )
    if run is None:
        raise PredictionError("Model belum dilatih. Latih model terlebih dahulu sebelum melakukan prediksi.")
    return run


def predict_single_text(
    db: Session, text: str, training_run_id: str | None, user_id: uuid.UUID | None
) -> dict:
    run = resolve_prediction_run(db, training_run_id)

    tfidf_model = db.query(TfidfModel).filter(TfidfModel.training_run_id == run.id).first()
    knn_model = db.query(KnnModel).filter(KnnModel.training_run_id == run.id).first()
    if tfidf_model is None or knn_model is None:
        raise PredictionError("Model untuk training run ini belum tersedia (training belum selesai).")

    vectorizer = load_model(tfidf_model.model_file_path)
    classifier = load_model(knn_model.model_file_path)

    normalization_map = {
        row.informal_word: row.formal_word for row in db.query(NormalizationDictionary).all()
    }
    stopword_set = {row.word for row in db.query(Stopword).all()}
    pipeline_result = run_pipeline(text, normalization_map, stopword_set)

    t0 = time.perf_counter()
    vector = vectorizer.transform([pipeline_result.final_text])
    predicted_label = str(classifier.predict(vector)[0])

    k = classifier.n_neighbors
    split = db.get(DataSplit, run.data_split_id) if run.data_split_id else None
    train_ids, train_texts, train_labels = (
        gather_texts_labels(db, split.train_review_ids, run.label_mode) if split else ([], [], [])
    )

    neighbors_payload = []
    if train_ids:
        n_neighbors = min(k, len(train_ids))
        distances, indices = classifier.kneighbors(vector, n_neighbors=n_neighbors)
        for pos, idx in enumerate(indices[0]):
            neighbors_payload.append(
                {
                    "review_id": train_ids[idx],
                    "distance": float(distances[0][pos]),
                    "label": train_labels[idx],
                    "text": train_texts[idx][:300],
                }
            )
    prediction_time_ms = (time.perf_counter() - t0) * 1000

    neighbor_labels = [n["label"] for n in neighbors_payload]
    confidence = neighbor_labels.count(predicted_label) / len(neighbor_labels) if neighbor_labels else 0.0

    now = datetime.now(UTC)
    prediction = Prediction(
        training_run_id=run.id,
        review_id=None,
        source=PredictionSource.SINGLE.value,
        input_text=text,
        final_text=pipeline_result.final_text,
        actual_label=None,
        predicted_label=predicted_label,
        confidence=confidence,
        k_used=k,
        neighbors=neighbors_payload,
        prediction_time_ms=prediction_time_ms,
        created_by=user_id,
        created_at=now,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    return {
        "original_text": text,
        "final_text": pipeline_result.final_text,
        "predicted_label": predicted_label,
        "confidence": confidence,
        "k_used": k,
        "neighbors": neighbors_payload,
        "model_version": run.model_version,
        "training_run_id": run.id,
        "prediction_time_ms": prediction_time_ms,
    }
