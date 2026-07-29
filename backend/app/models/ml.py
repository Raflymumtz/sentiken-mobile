from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import LabelMode, PredictionSource, ProcessingStatus
from app.models.types import GUID


class DataSplit(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "data_splits"

    dataset_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label_mode: Mapped[str] = mapped_column(String(10), default=LabelMode.BINARY.value, nullable=False)
    train_size: Mapped[float] = mapped_column(Float, nullable=False, default=0.8)
    test_size: Mapped[float] = mapped_column(Float, nullable=False, default=0.2)
    random_state: Mapped[int] = mapped_column(Integer, nullable=False, default=42)
    stratify: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    train_review_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    test_review_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    class_distribution: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TrainingRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "training_runs"

    dataset_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    data_split_id: Mapped[str | None] = mapped_column(
        GUID, ForeignKey("data_splits.id", ondelete="SET NULL"), nullable=True
    )
    label_mode: Mapped[str] = mapped_column(String(10), default=LabelMode.BINARY.value, nullable=False)
    run_type: Mapped[str] = mapped_column(String(20), default="single", nullable=False)  # single | experiment

    tfidf_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    knn_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    status: Mapped[str] = mapped_column(String(20), default=ProcessingStatus.PENDING.value, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    selection_metric: Mapped[str] = mapped_column(String(30), default="f1_weighted", nullable=False)

    training_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    prediction_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    items: Mapped[list["TrainingRunItem"]] = relationship(
        back_populates="training_run", cascade="all, delete-orphan"
    )
    evaluation_metrics: Mapped[list["EvaluationMetric"]] = relationship(
        back_populates="training_run", cascade="all, delete-orphan"
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="training_run", cascade="all, delete-orphan"
    )
    tfidf_model: Mapped["TfidfModel | None"] = relationship(
        back_populates="training_run", cascade="all, delete-orphan", uselist=False
    )
    knn_model: Mapped["KnnModel | None"] = relationship(
        back_populates="training_run", cascade="all, delete-orphan", uselist=False
    )


class TrainingRunItem(UUIDPrimaryKeyMixin, Base):
    """Hasil satu nilai K dalam eksperimen (POST /datasets/{id}/experiment-k)."""

    __tablename__ = "training_run_items"

    training_run_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("training_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    k_value: Mapped[int] = mapped_column(Integer, nullable=False)
    metric: Mapped[str] = mapped_column(String(30), nullable=False, default="euclidean")
    weights: Mapped[str] = mapped_column(String(20), nullable=False, default="uniform")

    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    precision_weighted: Mapped[float] = mapped_column(Float, nullable=False)
    recall_weighted: Mapped[float] = mapped_column(Float, nullable=False)
    f1_weighted: Mapped[float] = mapped_column(Float, nullable=False)

    training_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    prediction_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)

    is_selected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    training_run: Mapped["TrainingRun"] = relationship(back_populates="items")


class TfidfModel(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "tfidf_models"

    training_run_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("training_runs.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    vocabulary_size: Mapped[int] = mapped_column(Integer, nullable=False)
    feature_names: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    idf_values: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    model_file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    training_run: Mapped["TrainingRun"] = relationship(back_populates="tfidf_model")


class KnnModel(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "knn_models"

    training_run_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("training_runs.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    n_neighbors: Mapped[int] = mapped_column(Integer, nullable=False)
    metric: Mapped[str] = mapped_column(String(30), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(20), nullable=False, default="brute")
    weights: Mapped[str] = mapped_column(String(20), nullable=False, default="uniform")
    leaf_size: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    model_file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    training_run: Mapped["TrainingRun"] = relationship(back_populates="knn_model")


class EvaluationMetric(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "evaluation_metrics"

    training_run_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("training_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    precision_macro: Mapped[float] = mapped_column(Float, nullable=False)
    recall_macro: Mapped[float] = mapped_column(Float, nullable=False)
    f1_macro: Mapped[float] = mapped_column(Float, nullable=False)
    precision_weighted: Mapped[float] = mapped_column(Float, nullable=False)
    recall_weighted: Mapped[float] = mapped_column(Float, nullable=False)
    f1_weighted: Mapped[float] = mapped_column(Float, nullable=False)
    support: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    confusion_matrix: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    classification_report: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    warnings: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    training_run: Mapped["TrainingRun"] = relationship(back_populates="evaluation_metrics")


class Prediction(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "predictions"

    training_run_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("training_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    review_id: Mapped[str | None] = mapped_column(
        GUID, ForeignKey("reviews.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[str] = mapped_column(String(20), default=PredictionSource.SINGLE.value, nullable=False)

    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    final_text: Mapped[str] = mapped_column(Text, nullable=False)
    actual_label: Mapped[str | None] = mapped_column(String(10), nullable=True)
    predicted_label: Mapped[str] = mapped_column(String(10), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    k_used: Mapped[int] = mapped_column(Integer, nullable=False)
    neighbors: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    prediction_time_ms: Mapped[float] = mapped_column(Float, nullable=False)

    created_by: Mapped[str | None] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    training_run: Mapped["TrainingRun"] = relationship(back_populates="predictions")
