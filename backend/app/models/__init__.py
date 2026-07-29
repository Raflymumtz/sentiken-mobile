"""Import semua model agar terdaftar pada SQLAlchemy declarative registry.

Alembic autogenerate dan `Base.metadata.create_all()` (dipakai oleh test suite)
bergantung pada modul ini untuk mengetahui seluruh tabel yang ada.
"""

from app.database import Base
from app.models.app_source import AppSource
from app.models.audit import AuditLog
from app.models.dataset import Dataset
from app.models.dictionary import (
    DictionaryNegative,
    DictionaryPositive,
    NormalizationDictionary,
    Stopword,
)
from app.models.job import CollectionJob, ImportJob
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
from app.models.user import User

__all__ = [
    "Base",
    "AppSource",
    "AuditLog",
    "Dataset",
    "DictionaryNegative",
    "DictionaryPositive",
    "NormalizationDictionary",
    "Stopword",
    "CollectionJob",
    "ImportJob",
    "SentimentLabel",
    "DataSplit",
    "EvaluationMetric",
    "KnnModel",
    "Prediction",
    "TfidfModel",
    "TrainingRun",
    "TrainingRunItem",
    "PreprocessingResult",
    "Review",
    "User",
]
