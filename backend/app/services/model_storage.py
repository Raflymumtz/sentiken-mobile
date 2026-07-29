from pathlib import Path

import joblib

from app.config import get_settings


def get_model_dir() -> Path:
    settings = get_settings()
    path = Path(settings.ml_model_storage_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_model(obj, filename: str) -> str:
    path = get_model_dir() / filename
    joblib.dump(obj, path)
    return str(path)


def load_model(path: str):
    return joblib.load(path)
