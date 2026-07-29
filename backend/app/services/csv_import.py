import re
from dataclasses import dataclass, field
from datetime import date
from io import BytesIO

import pandas as pd

# Alias header yang diterima (dinormalisasi tanpa spasi/underscore, huruf kecil)
# -> nama kolom kanonik yang dipakai internal.
COLUMN_ALIASES: dict[str, str] = {
    "reviewid": "review_id",
    "username": "username",
    "userimage": "user_image",
    "content": "content",
    "score": "score",
    "thumbsupcount": "thumbs_up_count",
    "at": "review_date",
    "appversion": "app_version",
}

REQUIRED_CANONICAL_COLUMNS = ["content"]
MAX_CONTENT_LENGTH = 5000


def _normalize_key(col: str) -> str:
    return re.sub(r"[\s_]+", "", str(col).strip().lower())


def _map_columns(columns: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for col in columns:
        canonical = COLUMN_ALIASES.get(_normalize_key(col))
        if canonical and canonical not in mapping.values():
            mapping[col] = canonical
    return mapping


def _parse_date(value) -> date | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        parsed = pd.to_datetime(value, errors="raise")
        return parsed.date()
    except (ValueError, TypeError, pd.errors.ParserError):
        return None


def _clean_str(value) -> str | None:
    """Mengonversi nilai sel pandas menjadi str bersih, atau None bila kosong/NaN.

    Perlu berhati-hati: `float('nan') or default` selalu bernilai `nan` (NaN
    dianggap truthy di Python), sehingga pengecekan harus eksplisit lewat
    `pd.isna()`, bukan pola `value or default`.
    """
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _parse_score(value) -> tuple[int | None, bool]:
    """Mengembalikan (score, is_valid). score None + is_valid True berarti kolom kosong (opsional)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None, True
    if isinstance(value, str) and not value.strip():
        return None, True
    try:
        score = int(float(value))
    except (ValueError, TypeError):
        return None, False
    if score < 1 or score > 5:
        return None, False
    return score, True


@dataclass
class ParsedRow:
    row_number: int
    is_valid: bool
    errors: list[str]
    data: dict


@dataclass
class ParsedCsv:
    detected_columns: list[str]
    canonical_columns_found: list[str]
    missing_required_columns: list[str]
    rows: list[ParsedRow] = field(default_factory=list)

    @property
    def total_rows(self) -> int:
        return len(self.rows)

    @property
    def valid_rows(self) -> int:
        return sum(1 for r in self.rows if r.is_valid)

    @property
    def invalid_rows(self) -> int:
        return self.total_rows - self.valid_rows


class CsvFormatError(Exception):
    pass


def parse_csv_bytes(raw: bytes) -> ParsedCsv:
    try:
        df = pd.read_csv(BytesIO(raw), dtype=str, keep_default_na=False, na_values=[""], index_col=False)
    except Exception as exc:  # noqa: BLE001
        raise CsvFormatError(f"File CSV tidak dapat dibaca: {exc}") from exc

    if df.empty and len(df.columns) == 0:
        raise CsvFormatError("File CSV kosong atau tidak memiliki header kolom.")

    detected_columns = list(df.columns)
    column_map = _map_columns(detected_columns)
    canonical_found = sorted(set(column_map.values()))
    missing_required = [c for c in REQUIRED_CANONICAL_COLUMNS if c not in canonical_found]

    df = df.rename(columns=column_map)
    df = df[[c for c in df.columns if c in COLUMN_ALIASES.values()]]
    df = df.reset_index(drop=True)

    parsed = ParsedCsv(
        detected_columns=detected_columns,
        canonical_columns_found=canonical_found,
        missing_required_columns=missing_required,
    )

    if missing_required:
        return parsed

    records = df.to_dict(orient="records")

    for position, row in enumerate(records):
        row_number = position + 2  # +1 header, +1 karena dimulai dari baris data pertama
        errors: list[str] = []

        content = _clean_str(row.get("content")) or ""
        if not content:
            errors.append("Kolom 'content' kosong.")
        elif len(content) > MAX_CONTENT_LENGTH:
            errors.append(f"Kolom 'content' melebihi {MAX_CONTENT_LENGTH} karakter.")

        score, score_valid = _parse_score(row.get("score"))
        if not score_valid:
            errors.append("Kolom 'score' harus berupa angka 1-5.")

        review_date_str = _clean_str(row.get("review_date"))
        review_date = _parse_date(review_date_str) if review_date_str else None
        if review_date_str and review_date is None:
            errors.append("Kolom 'at'/'review_date' tidak dapat dikenali formatnya.")

        thumbs_up_str = _clean_str(row.get("thumbs_up_count"))
        try:
            thumbs_up_count = int(float(thumbs_up_str)) if thumbs_up_str else 0
        except (ValueError, TypeError):
            thumbs_up_count = 0

        data = {
            "review_id": _clean_str(row.get("review_id")),
            "username": _clean_str(row.get("username")),
            "user_image": _clean_str(row.get("user_image")),
            "content": content,
            "score": score,
            "thumbs_up_count": thumbs_up_count,
            "review_date": review_date,
            "app_version": _clean_str(row.get("app_version")),
        }

        parsed.rows.append(ParsedRow(row_number=row_number, is_valid=not errors, errors=errors, data=data))

    return parsed
