"""Upload processing orchestration."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.exceptions import AppError
from app.models import Feature, FileStatus, UploadedFile
from app.services.measure import measure_geometry
from app.services.reader import read_features, save_upload, validate_upload_metadata

logger = logging.getLogger(__name__)


def process_upload(file: UploadFile, db: Session, settings: Settings) -> UploadedFile:
    """Persist an upload, parse features, measure them, and update status."""

    suffix = validate_upload_metadata(file, settings.max_upload_bytes)
    file_id = str(uuid.uuid4())
    safe_name = f"source{suffix}"
    upload_path = Path(settings.upload_dir) / file_id / safe_name
    save_upload(file, upload_path, settings.max_upload_bytes)

    uploaded = UploadedFile(
        id=file_id,
        filename=file.filename or safe_name,
        stored_path=str(upload_path),
        status=FileStatus.PROCESSING,
    )
    db.add(uploaded)
    db.commit()
    db.refresh(uploaded)

    try:
        parsed_features, source_crs = read_features(upload_path, suffix)
        uploaded.crs = source_crs
        uploaded.feature_count = len(parsed_features)
        for parsed in parsed_features:
            measurement = measure_geometry(parsed.geometry, parsed.source_crs, parsed.note)
            db.add(
                Feature(
                    file_id=uploaded.id,
                    index=parsed.index,
                    layer_name=parsed.layer_name,
                    geometry_type=parsed.geometry_type,
                    geometry=parsed.geometry_geojson,
                    source_crs=parsed.source_crs,
                    projected_crs_used=measurement.projected_crs_used,
                    properties=parsed.properties,
                    area_m2=measurement.area_m2,
                    area_hectares=measurement.area_hectares,
                    length_m=measurement.length_m,
                    length_km=measurement.length_km,
                    geodesic_area_m2=measurement.geodesic_area_m2,
                    geodesic_length_m=measurement.geodesic_length_m,
                    measurement_status=measurement.status,
                    measurement_note=measurement.note,
                )
            )
        uploaded.status = FileStatus.COMPLETED
        db.commit()
    except AppError as exc:
        uploaded.status = FileStatus.FAILED
        uploaded.error_message = exc.message
        db.commit()
        logger.info("Upload %s failed validation: %s", file_id, exc.message)
        raise
    except (OSError, ValueError, RuntimeError, TypeError) as exc:
        uploaded.status = FileStatus.FAILED
        uploaded.error_message = str(exc)
        db.commit()
        logger.exception("Upload %s failed unexpectedly", file_id)
        raise

    db.refresh(uploaded)
    return uploaded

