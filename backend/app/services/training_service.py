import logging
import time
from datetime import UTC, datetime

from app.database import SessionLocal
from app.models.dataset import Dataset
from app.models.enums import PredictionSource, ProcessingStatus
from app.models.label import SentimentLabel
from app.models.ml import (
    DataSplit,
    EvaluationMetric,
    KnnModel,
    Prediction,
    TfidfModel,
    TrainingRun,
    TrainingRunItem,
)
from app.models.review import PreprocessingResult, Review
from app.services.evaluation_service import compute_metrics
from app.services.knn_service import build_classifier
from app.services.model_storage import save_model
from app.services.tfidf_service import build_vectorizer

logger = logging.getLogger("sentiken")

SELECTABLE_METRICS = ("accuracy", "precision_weighted", "recall_weighted", "f1_weighted")


def gather_texts_labels(db, review_ids: list[str], label_mode: str):
    if not review_ids:
        return [], [], []
    rows = (
        db.query(Review.id, PreprocessingResult.final_text, SentimentLabel.label)
        .join(PreprocessingResult, PreprocessingResult.review_id == Review.id)
        .join(
            SentimentLabel,
            (SentimentLabel.review_id == Review.id) & (SentimentLabel.label_mode == label_mode),
        )
        .filter(Review.id.in_(review_ids))
        .all()
    )
    by_id = {str(review_id): (text, label) for review_id, text, label in rows}

    ids, texts, labels = [], [], []
    for rid in review_ids:
        found = by_id.get(rid)
        if found is None:
            continue
        text, label = found
        ids.append(rid)
        texts.append(text)
        labels.append(label)
    return ids, texts, labels


def run_training_job(training_run_id: str) -> None:
    db = SessionLocal()
    try:
        run = db.get(TrainingRun, training_run_id)
        if run is None:
            logger.error("TrainingRun %s tidak ditemukan.", training_run_id)
            return

        run.status = ProcessingStatus.RUNNING.value
        db.commit()

        split = db.get(DataSplit, run.data_split_id)
        if split is None:
            _fail(db, run, "Data split tidak ditemukan.")
            return

        train_ids, train_texts, train_labels = gather_texts_labels(db, split.train_review_ids, run.label_mode)
        test_ids, test_texts, test_labels = gather_texts_labels(db, split.test_review_ids, run.label_mode)

        if not train_texts or not test_texts:
            _fail(db, run, "Data training/testing kosong (preprocessing/labelisasi mungkin belum lengkap).")
            return

        n_neighbors = int(run.knn_config.get("n_neighbors", 3))
        if n_neighbors > len(train_ids):
            _fail(
                db,
                run,
                f"Nilai K ({n_neighbors}) lebih besar dari jumlah data training ({len(train_ids)}).",
            )
            return

        vectorizer = build_vectorizer(run.tfidf_config)
        t0 = time.perf_counter()
        x_train = vectorizer.fit_transform(train_texts)
        classifier = build_classifier(run.knn_config)
        classifier.fit(x_train, train_labels)
        training_time = time.perf_counter() - t0

        x_test = vectorizer.transform(test_texts)
        t1 = time.perf_counter()
        y_pred = list(classifier.predict(x_test))
        prediction_time = time.perf_counter() - t1

        labels_sorted = sorted(set(train_labels) | set(test_labels))
        metrics = compute_metrics(test_labels, y_pred, labels_sorted)

        now = datetime.now(UTC)
        model_version = f"{str(run.dataset_id)[:8]}-{now:%Y%m%d%H%M%S}-k{classifier.n_neighbors}"

        tfidf_path = save_model(vectorizer, f"tfidf_{run.id}.joblib")
        knn_path = save_model(classifier, f"knn_{run.id}.joblib")

        db.add(
            TfidfModel(
                training_run_id=run.id,
                config=run.tfidf_config,
                vocabulary_size=len(vectorizer.vocabulary_),
                feature_names=list(vectorizer.get_feature_names_out()),
                idf_values=[float(v) for v in vectorizer.idf_],
                model_file_path=tfidf_path,
                created_at=now,
            )
        )
        db.add(
            KnnModel(
                training_run_id=run.id,
                n_neighbors=classifier.n_neighbors,
                metric=classifier.metric,
                algorithm=classifier.algorithm,
                weights=classifier.weights,
                leaf_size=classifier.leaf_size,
                model_file_path=knn_path,
                created_at=now,
            )
        )
        db.add(
            EvaluationMetric(
                training_run_id=run.id,
                accuracy=metrics["accuracy"],
                precision_macro=metrics["precision_macro"],
                recall_macro=metrics["recall_macro"],
                f1_macro=metrics["f1_macro"],
                precision_weighted=metrics["precision_weighted"],
                recall_weighted=metrics["recall_weighted"],
                f1_weighted=metrics["f1_weighted"],
                support=metrics["support"],
                confusion_matrix=metrics["confusion_matrix"],
                classification_report=metrics["classification_report"],
                warnings=metrics["warnings"],
                created_at=now,
            )
        )

        k = classifier.n_neighbors
        distances, indices = classifier.kneighbors(x_test, n_neighbors=k)
        per_item_prediction_ms = (prediction_time / len(test_ids)) * 1000 if test_ids else 0.0
        for i, review_id in enumerate(test_ids):
            neighbor_labels = [train_labels[idx] for idx in indices[i]]
            majority_share = (
                neighbor_labels.count(y_pred[i]) / len(neighbor_labels) if neighbor_labels else 0.0
            )
            neighbors_payload = [
                {
                    "review_id": train_ids[idx],
                    "distance": float(distances[i][pos]),
                    "label": train_labels[idx],
                    "text": train_texts[idx][:300],
                }
                for pos, idx in enumerate(indices[i])
            ]
            db.add(
                Prediction(
                    training_run_id=run.id,
                    review_id=review_id,
                    source=PredictionSource.EVALUATION.value,
                    input_text=test_texts[i],
                    final_text=test_texts[i],
                    actual_label=test_labels[i],
                    predicted_label=str(y_pred[i]),
                    confidence=majority_share,
                    k_used=k,
                    neighbors=neighbors_payload,
                    prediction_time_ms=per_item_prediction_ms,
                    created_at=now,
                )
            )

        run.status = ProcessingStatus.COMPLETED.value
        run.model_version = model_version
        run.training_time_seconds = training_time
        run.prediction_time_seconds = prediction_time
        db.commit()

        _maybe_auto_activate(db, run)

        dataset = db.get(Dataset, run.dataset_id)
        if dataset:
            dataset.training_status = ProcessingStatus.COMPLETED.value
            db.commit()

    except Exception as exc:  # noqa: BLE001
        logger.exception("Training run %s gagal: %s", training_run_id, exc)
        db.rollback()
        run = db.get(TrainingRun, training_run_id)
        if run:
            _fail(db, run, f"Kesalahan tak terduga: {exc}")
    finally:
        db.close()


def run_experiment_k_job(training_run_id: str, k_values: list[int]) -> None:
    db = SessionLocal()
    try:
        run = db.get(TrainingRun, training_run_id)
        if run is None:
            logger.error("TrainingRun (experiment) %s tidak ditemukan.", training_run_id)
            return

        run.status = ProcessingStatus.RUNNING.value
        db.commit()

        split = db.get(DataSplit, run.data_split_id)
        if split is None:
            _fail(db, run, "Data split tidak ditemukan.")
            return

        train_ids, train_texts, train_labels = gather_texts_labels(db, split.train_review_ids, run.label_mode)
        test_ids, test_texts, test_labels = gather_texts_labels(db, split.test_review_ids, run.label_mode)

        if not train_texts or not test_texts:
            _fail(db, run, "Data training/testing kosong (preprocessing/labelisasi mungkin belum lengkap).")
            return

        vectorizer = build_vectorizer(run.tfidf_config)
        x_train = vectorizer.fit_transform(train_texts)
        x_test = vectorizer.transform(test_texts)

        labels_sorted = sorted(set(train_labels) | set(test_labels))
        now = datetime.now(UTC)

        feasible_k = [k for k in sorted(set(k_values)) if k <= len(train_ids)]
        skipped_k = [k for k in k_values if k > len(train_ids)]

        results: list[tuple[int, dict, TrainingRunItem]] = []
        for k in feasible_k:
            cfg = {**run.knn_config, "n_neighbors": k}
            classifier = build_classifier(cfg)

            t0 = time.perf_counter()
            classifier.fit(x_train, train_labels)
            training_time = time.perf_counter() - t0

            t1 = time.perf_counter()
            y_pred = list(classifier.predict(x_test))
            prediction_time = time.perf_counter() - t1

            metrics = compute_metrics(test_labels, y_pred, labels_sorted)

            item = TrainingRunItem(
                training_run_id=run.id,
                k_value=k,
                metric=cfg.get("metric", "euclidean"),
                weights=cfg.get("weights", "uniform"),
                accuracy=metrics["accuracy"],
                precision_weighted=metrics["precision_weighted"],
                recall_weighted=metrics["recall_weighted"],
                f1_weighted=metrics["f1_weighted"],
                training_time_seconds=training_time,
                prediction_time_seconds=prediction_time,
                is_selected=False,
                created_at=now,
            )
            db.add(item)
            results.append((k, metrics, item))

        if not results:
            _fail(
                db,
                run,
                f"Tidak ada nilai K yang dapat diuji (semua K melebihi jumlah "
                f"data training={len(train_ids)}).",
            )
            return

        metric_key = run.selection_metric if run.selection_metric in SELECTABLE_METRICS else "f1_weighted"
        best_k, _best_metrics, best_item = max(results, key=lambda r: (r[1][metric_key], -r[0]))
        best_item.is_selected = True

        tfidf_path = save_model(vectorizer, f"tfidf_experiment_{run.id}.joblib")
        db.add(
            TfidfModel(
                training_run_id=run.id,
                config=run.tfidf_config,
                vocabulary_size=len(vectorizer.vocabulary_),
                feature_names=list(vectorizer.get_feature_names_out()),
                idf_values=[float(v) for v in vectorizer.idf_],
                model_file_path=tfidf_path,
                created_at=now,
            )
        )

        run.status = ProcessingStatus.COMPLETED.value
        if skipped_k:
            run.error_message = (
                "Sebagian nilai K dilewati karena melebihi jumlah data training: "
                + ", ".join(str(k) for k in skipped_k)
            )
        db.commit()

    except Exception as exc:  # noqa: BLE001
        logger.exception("Experiment-K run %s gagal: %s", training_run_id, exc)
        db.rollback()
        run = db.get(TrainingRun, training_run_id)
        if run:
            _fail(db, run, f"Kesalahan tak terduga: {exc}")
    finally:
        db.close()


def _fail(db, run: TrainingRun, message: str) -> None:
    run.status = ProcessingStatus.FAILED.value
    run.error_message = message
    db.commit()


def _maybe_auto_activate(db, run: TrainingRun) -> None:
    """Aktivasi otomatis HANYA bila dataset ini belum punya model aktif sama sekali
    -- tidak pernah menimpa model aktif yang sudah ada tanpa konfirmasi eksplisit
    lewat POST /training-runs/{id}/activate."""
    existing_active = (
        db.query(TrainingRun)
        .filter(TrainingRun.dataset_id == run.dataset_id, TrainingRun.is_active.is_(True))
        .first()
    )
    if existing_active is None:
        run.is_active = True
        run.activated_at = datetime.now(UTC)
        db.commit()
