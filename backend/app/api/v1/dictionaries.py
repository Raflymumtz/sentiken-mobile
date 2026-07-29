import csv
import io
from dataclasses import dataclass

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import PageParams, build_pagination, get_current_user, get_db
from app.models.dictionary import (
    DictionaryNegative,
    DictionaryPositive,
    NormalizationDictionary,
    Stopword,
)
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.dictionary import DictionaryImportReport
from app.services.audit import write_audit_log

router = APIRouter(prefix="/dictionaries", tags=["Kamus"])


@dataclass
class DictSpec:
    model: type
    unique_field: str
    fields: tuple[str, ...]
    csv_columns: tuple[str, ...]


DICT_SPECS: dict[str, DictSpec] = {
    "positive": DictSpec(DictionaryPositive, "word", ("word", "weight"), ("word", "weight")),
    "negative": DictSpec(DictionaryNegative, "word", ("word", "weight"), ("word", "weight")),
    "normalization": DictSpec(
        NormalizationDictionary,
        "informal_word",
        ("informal_word", "formal_word"),
        ("informal_word", "formal_word"),
    ),
    "stopwords": DictSpec(Stopword, "word", ("word",), ("word",)),
}


def _get_spec(dict_type: str) -> DictSpec:
    spec = DICT_SPECS.get(dict_type)
    if spec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jenis kamus tidak dikenal. Gunakan: positive, negative, normalization, stopwords.",
        )
    return spec


def _normalize_word(value: str) -> str:
    return value.strip().lower()


def _to_dict(instance) -> dict:
    result = {"id": str(instance.id), "created_at": instance.created_at, "updated_at": instance.updated_at}
    for field in ("word", "weight", "informal_word", "formal_word"):
        if hasattr(instance, field):
            result[field] = getattr(instance, field)
    return result


@router.get("/{dict_type}", response_model=PaginatedResponse[dict])
def list_dictionary_entries(
    dict_type: str,
    search: str | None = None,
    page_params: PageParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    spec = _get_spec(dict_type)
    query = db.query(spec.model)
    if search:
        col = getattr(spec.model, spec.unique_field)
        query = query.filter(col.ilike(f"%{search}%"))

    total = query.count()
    items = (
        query.order_by(getattr(spec.model, spec.unique_field))
        .offset(page_params.offset)
        .limit(page_params.page_size)
        .all()
    )
    return PaginatedResponse(
        items=[_to_dict(i) for i in items], pagination=build_pagination(page_params, total)
    )


@router.post("/{dict_type}", status_code=status.HTTP_201_CREATED)
def create_dictionary_entry(
    dict_type: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    spec = _get_spec(dict_type)
    data = {}
    for field in spec.fields:
        if field not in payload:
            raise HTTPException(status_code=422, detail=f"Field '{field}' wajib diisi.")
        value = payload[field]
        if field in ("word", "informal_word", "formal_word") and isinstance(value, str):
            value = _normalize_word(value)
        data[field] = value

    unique_value = data[spec.unique_field]
    existing = db.query(spec.model).filter(getattr(spec.model, spec.unique_field) == unique_value).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Kata sudah ada di kamus ini.")

    instance = spec.model(**data)
    db.add(instance)
    db.commit()
    db.refresh(instance)
    write_audit_log(
        db,
        user_id=current_user.id,
        action="create",
        entity_type=f"dictionary_{dict_type}",
        entity_id=str(instance.id),
    )
    return _to_dict(instance)


@router.put("/{dict_type}/{entry_id}")
def update_dictionary_entry(
    dict_type: str,
    entry_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    spec = _get_spec(dict_type)
    instance = db.get(spec.model, entry_id)
    if instance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entri kamus tidak ditemukan.")

    for field in spec.fields:
        if field not in payload:
            continue
        value = payload[field]
        if field in ("word", "informal_word", "formal_word") and isinstance(value, str):
            value = _normalize_word(value)
            conflict = (
                db.query(spec.model)
                .filter(getattr(spec.model, field) == value, spec.model.id != instance.id)
                .first()
            )
            if field == spec.unique_field and conflict:
                raise HTTPException(status_code=409, detail="Kata sudah ada di kamus ini.")
        setattr(instance, field, value)

    db.commit()
    db.refresh(instance)
    write_audit_log(
        db,
        user_id=current_user.id,
        action="update",
        entity_type=f"dictionary_{dict_type}",
        entity_id=str(instance.id),
    )
    return _to_dict(instance)


@router.delete("/{dict_type}/{entry_id}", response_model=MessageResponse)
def delete_dictionary_entry(
    dict_type: str,
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    spec = _get_spec(dict_type)
    instance = db.get(spec.model, entry_id)
    if instance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entri kamus tidak ditemukan.")
    db.delete(instance)
    db.commit()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="delete",
        entity_type=f"dictionary_{dict_type}",
        entity_id=str(entry_id),
    )
    return MessageResponse(message="Entri kamus berhasil dihapus.")


@router.post("/{dict_type}/import", response_model=DictionaryImportReport)
async def import_dictionary(
    dict_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    spec = _get_spec(dict_type)
    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Berkas tidak dapat dibaca: {exc}") from exc

    reader = csv.reader(io.StringIO(text))
    rows = [r for r in reader if r and any(cell.strip() for cell in r)]

    header_lower = [c.strip().lower() for c in rows[0]] if rows else []
    start_index = 1 if header_lower == list(spec.csv_columns) else 0

    total = 0
    inserted = 0
    duplicates = 0
    errors: list[str] = []
    seen_in_file: set[str] = set()

    for line_no, row in enumerate(rows[start_index:], start=start_index + 1):
        total += 1
        if len(row) < len(spec.csv_columns):
            expected_format = ",".join(spec.csv_columns)
            errors.append(f"Baris {line_no}: jumlah kolom tidak sesuai (format: {expected_format}).")
            continue

        values = {}
        ok = True
        for i, field in enumerate(spec.fields):
            raw_value = row[i].strip()
            if field == "weight":
                try:
                    values[field] = float(raw_value) if raw_value else 1.0
                except ValueError:
                    errors.append(f"Baris {line_no}: bobot '{raw_value}' bukan angka.")
                    ok = False
                    break
            else:
                if not raw_value:
                    errors.append(f"Baris {line_no}: kolom '{field}' kosong.")
                    ok = False
                    break
                values[field] = _normalize_word(raw_value)
        if not ok:
            continue

        unique_value = values[spec.unique_field]
        if unique_value in seen_in_file:
            duplicates += 1
            continue
        seen_in_file.add(unique_value)

        existing = db.query(spec.model).filter(getattr(spec.model, spec.unique_field) == unique_value).first()
        if existing:
            duplicates += 1
            continue

        db.add(spec.model(**values))
        inserted += 1

    db.commit()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="import",
        entity_type=f"dictionary_{dict_type}",
        detail={"inserted": inserted, "duplicates": duplicates},
    )

    return DictionaryImportReport(
        total_rows=total,
        valid_rows=inserted + duplicates,
        invalid_rows=total - inserted - duplicates,
        inserted=inserted,
        duplicates_skipped=duplicates,
        errors=errors[:200],
    )


@router.get("/{dict_type}/export")
def export_dictionary(
    dict_type: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    spec = _get_spec(dict_type)
    items = db.query(spec.model).order_by(getattr(spec.model, spec.unique_field)).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(spec.csv_columns)
    for item in items:
        writer.writerow([getattr(item, field) for field in spec.fields])
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=kamus_{dict_type}.csv"},
    )
