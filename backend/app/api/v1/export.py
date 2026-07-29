import csv
import io

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.app_source import AppSource
from app.models.dataset import Dataset
from app.models.ml import DataSplit, EvaluationMetric, Prediction, TrainingRun
from app.models.review import Review
from app.models.user import User
from app.services.chart_export import render_confusion_matrix_png
from app.services.pdf_report import build_training_summary_pdf
from app.services.training_service import gather_texts_labels

router = APIRouter(tags=["Ekspor"])


def _csv_response(rows: list[list], header: list[str], filename: str) -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _get_split_or_404(db: Session, dataset_id: str, split_id: str) -> DataSplit:
    split = db.query(DataSplit).filter(DataSplit.id == split_id, DataSplit.dataset_id == dataset_id).first()
    if split is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data split tidak ditemukan.")
    return split


def _get_run_or_404(db: Session, run_id: str) -> TrainingRun:
    run = db.get(TrainingRun, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training run tidak ditemukan.")
    return run


@router.get("/datasets/{dataset_id}/splits/{split_id}/export/train")
def export_train_data(
    dataset_id: str,
    split_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    split = _get_split_or_404(db, dataset_id, split_id)
    ids, texts, labels = gather_texts_labels(db, split.train_review_ids, split.label_mode)
    rows = list(zip(ids, texts, labels, strict=True))
    return _csv_response(rows, ["review_id", "final_text", "label"], f"train_{split_id}.csv")


@router.get("/datasets/{dataset_id}/splits/{split_id}/export/test")
def export_test_data(
    dataset_id: str,
    split_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    split = _get_split_or_404(db, dataset_id, split_id)
    ids, texts, labels = gather_texts_labels(db, split.test_review_ids, split.label_mode)
    rows = list(zip(ids, texts, labels, strict=True))
    return _csv_response(rows, ["review_id", "final_text", "label"], f"test_{split_id}.csv")


@router.get("/training-runs/{run_id}/export/predictions")
def export_predictions(
    run_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    _get_run_or_404(db, run_id)
    predictions = db.query(Prediction).filter(Prediction.training_run_id == run_id).all()
    rows = [
        [
            str(p.id),
            str(p.review_id) if p.review_id else "",
            p.actual_label or "",
            p.predicted_label,
            p.confidence,
            p.k_used,
            p.prediction_time_ms,
        ]
        for p in predictions
    ]
    return _csv_response(
        rows,
        [
            "prediction_id",
            "review_id",
            "actual_label",
            "predicted_label",
            "confidence",
            "k_used",
            "prediction_time_ms",
        ],
        f"predictions_{run_id}.csv",
    )


@router.get("/training-runs/{run_id}/export/metrics")
def export_metrics(
    run_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    metric = (
        db.query(EvaluationMetric)
        .filter(EvaluationMetric.training_run_id == run_id)
        .order_by(EvaluationMetric.created_at.desc())
        .first()
    )
    if metric is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metrik evaluasi belum tersedia.")
    rows = [
        ["accuracy", metric.accuracy],
        ["precision_macro", metric.precision_macro],
        ["recall_macro", metric.recall_macro],
        ["f1_macro", metric.f1_macro],
        ["precision_weighted", metric.precision_weighted],
        ["recall_weighted", metric.recall_weighted],
        ["f1_weighted", metric.f1_weighted],
    ]
    return _csv_response(rows, ["metric", "value"], f"metrics_{run_id}.csv")


@router.get("/training-runs/{run_id}/export/classification-report")
def export_classification_report(
    run_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    metric = (
        db.query(EvaluationMetric)
        .filter(EvaluationMetric.training_run_id == run_id)
        .order_by(EvaluationMetric.created_at.desc())
        .first()
    )
    if metric is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Classification report belum tersedia."
        )
    rows = []
    for label, values in metric.classification_report.items():
        if isinstance(values, dict):
            rows.append(
                [
                    label,
                    values.get("precision"),
                    values.get("recall"),
                    values.get("f1-score"),
                    values.get("support"),
                ]
            )
    return _csv_response(
        rows,
        ["label", "precision", "recall", "f1_score", "support"],
        f"classification_report_{run_id}.csv",
    )


@router.get("/training-runs/{run_id}/export/confusion-matrix.png")
def export_confusion_matrix_png(
    run_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    metric = (
        db.query(EvaluationMetric)
        .filter(EvaluationMetric.training_run_id == run_id)
        .order_by(EvaluationMetric.created_at.desc())
        .first()
    )
    if metric is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Confusion matrix belum tersedia.")
    png_bytes = render_confusion_matrix_png(
        metric.confusion_matrix["labels"], metric.confusion_matrix["matrix"]
    )
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename=confusion_matrix_{run_id}.png"},
    )


@router.get("/training-runs/{run_id}/export/summary.pdf")
def export_summary_pdf(
    run_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    run = _get_run_or_404(db, run_id)
    metric = (
        db.query(EvaluationMetric)
        .filter(EvaluationMetric.training_run_id == run_id)
        .order_by(EvaluationMetric.created_at.desc())
        .first()
    )
    if metric is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hasil evaluasi belum tersedia.")

    dataset = db.get(Dataset, run.dataset_id)
    app_source = db.get(AppSource, dataset.app_source_id) if dataset else None
    split = db.get(DataSplit, run.data_split_id) if run.data_split_id else None
    total_reviews = db.query(Review).filter(Review.dataset_id == run.dataset_id).count() if dataset else 0

    period = "-"
    if dataset and dataset.period_start and dataset.period_end:
        period = f"{dataset.period_start.isoformat()} s.d. {dataset.period_end.isoformat()}"

    context = {
        "dataset_name": dataset.name if dataset else "-",
        "app_name": app_source.app_name if app_source else "-",
        "period": period,
        "total_reviews": total_reviews,
        "label_mode": run.label_mode,
        "split": {
            "train_size": split.train_size if split else "-",
            "test_size": split.test_size if split else "-",
            "random_state": split.random_state if split else "-",
            "stratify": split.stratify if split else "-",
            "train_count": len(split.train_review_ids) if split else 0,
            "test_count": len(split.test_review_ids) if split else 0,
        },
        "tfidf_config": run.tfidf_config,
        "knn_config": run.knn_config,
        "metrics": {
            "accuracy": metric.accuracy,
            "precision_weighted": metric.precision_weighted,
            "recall_weighted": metric.recall_weighted,
            "f1_weighted": metric.f1_weighted,
            "precision_macro": metric.precision_macro,
            "recall_macro": metric.recall_macro,
            "f1_macro": metric.f1_macro,
            "confusion_matrix": metric.confusion_matrix,
            "warnings": metric.warnings,
        },
    }
    pdf_bytes = build_training_summary_pdf(context)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=summary_{run_id}.pdf"},
    )
