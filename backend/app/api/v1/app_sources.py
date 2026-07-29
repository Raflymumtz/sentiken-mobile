from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import PageParams, build_pagination, get_current_user, get_db
from app.models.app_source import AppSource
from app.models.user import User
from app.schemas.app_source import (
    AppSourceCreate,
    AppSourceResponse,
    AppSourceUpdate,
    AppSourceValidationResult,
)
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services.audit import write_audit_log
from app.services.play_store import check_package_on_play_store

router = APIRouter(prefix="/app-sources", tags=["Sumber Aplikasi"])


@router.get("", response_model=PaginatedResponse[AppSourceResponse])
def list_app_sources(
    is_active: bool | None = None,
    search: str | None = None,
    page_params: PageParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(AppSource).filter(AppSource.deleted_at.is_(None))
    if is_active is not None:
        query = query.filter(AppSource.is_active == is_active)
    if search:
        query = query.filter(AppSource.app_name.ilike(f"%{search}%"))

    total = query.count()
    items = (
        query.order_by(AppSource.created_at.desc())
        .offset(page_params.offset)
        .limit(page_params.page_size)
        .all()
    )
    return PaginatedResponse(items=items, pagination=build_pagination(page_params, total))


@router.post("", response_model=AppSourceResponse, status_code=status.HTTP_201_CREATED)
def create_app_source(
    payload: AppSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(AppSource).filter(AppSource.package_id == payload.package_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Package ID sudah terdaftar sebagai sumber aplikasi lain.",
        )
    app_source = AppSource(**payload.model_dump())
    db.add(app_source)
    db.commit()
    db.refresh(app_source)

    write_audit_log(
        db,
        user_id=current_user.id,
        action="create",
        entity_type="app_source",
        entity_id=str(app_source.id),
        detail={"app_name": app_source.app_name},
    )
    return app_source


@router.get("/{app_source_id}", response_model=AppSourceResponse)
def get_app_source(
    app_source_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_source = _get_or_404(db, app_source_id)
    return app_source


@router.put("/{app_source_id}", response_model=AppSourceResponse)
def update_app_source(
    app_source_id: str,
    payload: AppSourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_source = _get_or_404(db, app_source_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "package_id" in update_data and update_data["package_id"] != app_source.package_id:
        conflict = (
            db.query(AppSource)
            .filter(AppSource.package_id == update_data["package_id"], AppSource.id != app_source.id)
            .first()
        )
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Package ID sudah digunakan sumber lain."
            )

    for field, value in update_data.items():
        setattr(app_source, field, value)

    db.commit()
    db.refresh(app_source)
    write_audit_log(
        db,
        user_id=current_user.id,
        action="update",
        entity_type="app_source",
        entity_id=str(app_source.id),
        detail=update_data,
    )
    return app_source


@router.delete("/{app_source_id}", response_model=MessageResponse)
def delete_app_source(
    app_source_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_source = _get_or_404(db, app_source_id)
    app_source.deleted_at = datetime.now(UTC)
    app_source.is_active = False
    db.commit()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="delete",
        entity_type="app_source",
        entity_id=str(app_source.id),
    )
    return MessageResponse(message="Sumber aplikasi berhasil dihapus.")


@router.post("/{app_source_id}/validate", response_model=AppSourceValidationResult)
def validate_app_source(
    app_source_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app_source = _get_or_404(db, app_source_id)
    result = check_package_on_play_store(app_source.package_id, country=app_source.country)
    return AppSourceValidationResult(
        package_id=app_source.package_id,
        is_valid=result.is_valid,
        exists_on_play_store=result.exists,
        checked_at=datetime.now(UTC),
        detail=result.detail,
        play_store_app_name=result.app_name,
    )


def _get_or_404(db: Session, app_source_id: str) -> AppSource:
    app_source = (
        db.query(AppSource).filter(AppSource.id == app_source_id, AppSource.deleted_at.is_(None)).first()
    )
    if app_source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sumber aplikasi tidak ditemukan.")
    return app_source
