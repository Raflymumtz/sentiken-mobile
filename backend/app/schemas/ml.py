import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import ORMModel


# --- Split ---------------------------------------------------------------
class SplitRequest(BaseModel):
    train_size: float = Field(default=0.8, gt=0, lt=1)
    test_size: float = Field(default=0.2, gt=0, lt=1)
    random_state: int = Field(default=42)
    stratify: bool = True
    label_mode: str = Field(default="binary", pattern="^(binary|ternary)$")

    @model_validator(mode="after")
    def validate_sizes(self):
        if abs((self.train_size + self.test_size) - 1.0) > 1e-6:
            raise ValueError("train_size + test_size harus sama dengan 1.0")
        return self


class SplitResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    label_mode: str
    train_size: float
    test_size: float
    random_state: int
    stratify: bool
    train_count: int
    test_count: int
    class_distribution: dict
    created_at: datetime


# --- TF-IDF ---------------------------------------------------------------
class TfidfConfig(BaseModel):
    max_features: int | None = Field(default=5000, gt=0)
    min_df: int | float = Field(
        default=2, description="Integer = jumlah dokumen absolut, float (0-1] = proporsi."
    )
    max_df: int | float = Field(
        default=0.9, gt=0, description="Integer = jumlah dokumen absolut, float (0-1] = proporsi."
    )
    ngram_min: int = Field(default=1, ge=1)
    ngram_max: int = Field(default=1, ge=1)
    sublinear_tf: bool = False
    norm: str = Field(default="l2", pattern="^(l1|l2|none)$")

    @model_validator(mode="after")
    def validate_ngram(self):
        if self.ngram_max < self.ngram_min:
            raise ValueError("ngram_max harus >= ngram_min")
        return self


# --- K-NN ------------------------------------------------------------------
class KnnConfig(BaseModel):
    n_neighbors: int = Field(default=3, ge=1)
    metric: str = Field(default="euclidean")
    algorithm: str = Field(default="brute")
    weights: str = Field(default="uniform", pattern="^(uniform|distance)$")
    leaf_size: int = Field(default=30, ge=1)


class TrainRequest(BaseModel):
    data_split_id: uuid.UUID
    tfidf_config: TfidfConfig = Field(default_factory=TfidfConfig)
    knn_config: KnnConfig = Field(default_factory=KnnConfig)
    activate: bool = False


class ExperimentKRequest(BaseModel):
    data_split_id: uuid.UUID
    k_values: list[int] = Field(default_factory=lambda: [1, 3, 5, 7, 9, 11])
    tfidf_config: TfidfConfig = Field(default_factory=TfidfConfig)
    metric: str = Field(default="euclidean")
    weights: str = Field(default="uniform", pattern="^(uniform|distance)$")
    selection_metric: str = Field(default="f1_weighted")

    @model_validator(mode="after")
    def validate_k(self):
        if not self.k_values or any(k < 1 for k in self.k_values):
            raise ValueError("k_values harus berisi bilangan bulat positif.")
        return self


class TrainingRunItemResponse(BaseModel):
    id: uuid.UUID
    k_value: int
    metric: str
    weights: str
    accuracy: float
    precision_weighted: float
    recall_weighted: float
    f1_weighted: float
    training_time_seconds: float
    prediction_time_seconds: float
    is_selected: bool


class TrainingRunResponse(ORMModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    data_split_id: uuid.UUID | None
    label_mode: str
    run_type: str
    tfidf_config: dict
    knn_config: dict
    status: str
    is_active: bool
    model_version: str | None
    selection_metric: str
    training_time_seconds: float | None
    prediction_time_seconds: float | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    activated_at: datetime | None
    items: list[TrainingRunItemResponse] = []


class ActivateRunRequest(BaseModel):
    confirm: bool = Field(description="Harus true untuk mengonfirmasi penggantian model aktif.")


# --- Evaluation --------------------------------------------------------------
class ConfusionMatrixResponse(BaseModel):
    labels: list[str]
    matrix: list[list[int]]


class EvaluationMetricResponse(BaseModel):
    training_run_id: uuid.UUID
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    precision_weighted: float
    recall_weighted: float
    f1_weighted: float
    support: dict
    confusion_matrix: ConfusionMatrixResponse
    classification_report: dict
    warnings: list[str]
    created_at: datetime


# --- Prediction ---------------------------------------------------------------
class SinglePredictionRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    training_run_id: uuid.UUID | None = Field(
        default=None, description="Default memakai model aktif bila kosong."
    )


class NeighborInfo(BaseModel):
    review_id: uuid.UUID | None
    distance: float
    label: str
    text: str


class SinglePredictionResponse(BaseModel):
    original_text: str
    final_text: str
    predicted_label: str
    confidence: float
    k_used: int
    neighbors: list[NeighborInfo]
    model_version: str | None
    training_run_id: uuid.UUID
    prediction_time_ms: float
