"""File upload and measurement endpoints."""

from __future__ import annotations

from collections import Counter
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db import get_db
from app.exceptions import ProcessingConflictError
from app.models import Feature, FileStatus, UploadedFile
from app.schemas import FileResponse, MeasurementFeature, MeasurementsResponse, MeasurementSummary
from app.services.processor import process_upload

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post(
    "/",
    response_model=FileResponse,
    status_code=201,
    responses={400: {"description": "Invalid input"}, 413: {"description": "Too large"}, 415: {"description": "Unsupported type"}, 422: {"description": "Unreadable geospatial file"}},
)
def upload_file(
    file: Annotated[UploadFile, File(description="A .zip Shapefile or .kml file.")],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UploadedFile:
    """Upload and synchronously process a geospatial file."""

    return process_upload(file, db, settings)


@router.get("/{file_id}/", response_model=FileResponse)
def get_file(file_id: str, db: Annotated[Session, Depends(get_db)]) -> UploadedFile:
    """Return metadata for one uploaded file."""

    uploaded = db.get(UploadedFile, file_id)
    if uploaded is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="File not found.")
    return uploaded


@router.get("/{file_id}/measurements/", response_model=MeasurementsResponse)
def get_measurements(
    file_id: str,
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MeasurementsResponse:
    """Return summary and paginated feature measurements."""

    uploaded = db.get(UploadedFile, file_id)
    if uploaded is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="File not found.")
    if uploaded.status != FileStatus.COMPLETED:
        raise ProcessingConflictError("Measurements are only available for completed files.")

    total = db.scalar(select(func.count()).select_from(Feature).where(Feature.file_id == file_id)) or 0
    all_features = list(db.scalars(select(Feature).where(Feature.file_id == file_id)))
    page_features = list(
        db.scalars(
            select(Feature)
            .where(Feature.file_id == file_id)
            .order_by(Feature.index)
            .limit(limit)
            .offset(offset)
        )
    )
    counts = Counter(feature.geometry_type for feature in all_features)
    summary = MeasurementSummary(
        total_area_m2=sum(feature.area_m2 or 0 for feature in all_features),
        total_length_m=sum(feature.length_m or 0 for feature in all_features),
        counts_by_geometry_type=dict(counts),
        polygon_count=sum(counts[key] for key in ("Polygon", "MultiPolygon")),
        line_count=sum(counts[key] for key in ("LineString", "MultiLineString")),
        point_count=sum(counts[key] for key in ("Point", "MultiPoint")),
        unsupported_count=sum(
            1
            for feature in all_features
            if feature.measurement_status in {"UNSUPPORTED", "ERROR"}
        ),
    )
    return MeasurementsResponse(
        file=FileResponse.model_validate(uploaded),
        summary=summary,
        limit=limit,
        offset=offset,
        total=total,
        features=[MeasurementFeature.model_validate(feature) for feature in page_features],
    )

