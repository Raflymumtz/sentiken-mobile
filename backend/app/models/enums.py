import enum


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LabelMode(str, enum.Enum):
    BINARY = "binary"
    TERNARY = "ternary"


class SentimentLabel(str, enum.Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class CollectionMethod(str, enum.Enum):
    GOOGLE_PLAY_SCRAPER = "google_play_scraper"
    CSV_IMPORT = "csv_import"


class ReviewSource(str, enum.Enum):
    SCRAPED = "scraped"
    CSV_IMPORT = "csv_import"


class PredictionSource(str, enum.Enum):
    SINGLE = "single"
    EVALUATION = "evaluation"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
