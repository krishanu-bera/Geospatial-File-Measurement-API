"""Database models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db import Base


class FileStatus(StrEnum):
    """Processing status for uploaded files."""

    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MeasurementStatus(StrEnum):
    """Per-feature measurement status."""

    OK = "OK"
    NOT_REQUIRED = "NOT_REQUIRED"
    UNSUPPORTED = "UNSUPPORTED"
    ERROR = "ERROR"


class UploadedFile(Base):
    """Uploaded geospatial file metadata."""

    __tablename__ = "uploaded_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(Text, nullable=False)
    feature_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    crs: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=FileStatus.PROCESSING)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    features: Mapped[list[Feature]] = relationship(
        back_populates="file", cascade="all, delete-orphan", order_by="Feature.index"
    )


class Feature(Base):
    """Extracted geospatial feature and measurement result."""

    __tablename__ = "features"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[str] = mapped_column(ForeignKey("uploaded_files.id"), index=True)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    layer_name: Mapped[str | None] = mapped_column(String(255))
    geometry_type: Mapped[str] = mapped_column(String(64), nullable=False)
    geometry: Mapped[dict | None] = mapped_column(JSON)
    source_crs: Mapped[str] = mapped_column(String(64), nullable=False)
    projected_crs_used: Mapped[str | None] = mapped_column(String(64))
    properties: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    area_m2: Mapped[float | None] = mapped_column(Float)
    area_hectares: Mapped[float | None] = mapped_column(Float)
    length_m: Mapped[float | None] = mapped_column(Float)
    length_km: Mapped[float | None] = mapped_column(Float)
    geodesic_area_m2: Mapped[float | None] = mapped_column(Float)
    geodesic_length_m: Mapped[float | None] = mapped_column(Float)
    measurement_status: Mapped[str] = mapped_column(String(32), nullable=False)
    measurement_note: Mapped[str | None] = mapped_column(Text)

    file: Mapped[UploadedFile] = relationship(back_populates="features")
