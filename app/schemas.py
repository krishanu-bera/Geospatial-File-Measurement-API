"""Pydantic response schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    """Structured API error detail."""

    code: str = Field(examples=["unsupported_format"])
    message: str = Field(examples=["Only .zip Shapefiles and .kml files are supported."])


class ErrorResponse(BaseModel):
    """Structured API error response."""

    error: ErrorDetail


class FileResponse(BaseModel):
    """Uploaded file metadata response."""

    id: str = Field(examples=["a4d6ecf4-8433-4587-844f-c931ea7a0e5f"])
    filename: str = Field(examples=["parcel.kml"])
    feature_count: int = Field(examples=[3])
    crs: str | None = Field(default=None, examples=["EPSG:4326"])
    status: Literal["PROCESSING", "COMPLETED", "FAILED"] = Field(examples=["COMPLETED"])
    error_message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MeasurementFeature(BaseModel):
    """Per-feature measurement response."""

    index: int
    layer_name: str | None = None
    geometry_type: str
    geometry: dict[str, Any] | None
    source_crs: str
    projected_crs_used: str | None
    properties: dict[str, Any]
    area_m2: float | None
    area_hectares: float | None
    length_m: float | None
    length_km: float | None
    geodesic_area_m2: float | None
    geodesic_length_m: float | None
    measurement_status: Literal["OK", "NOT_REQUIRED", "UNSUPPORTED", "ERROR"]
    measurement_note: str | None

    model_config = ConfigDict(from_attributes=True)


class MeasurementSummary(BaseModel):
    """Measurement totals and counts."""

    total_area_m2: float
    total_length_m: float
    counts_by_geometry_type: dict[str, int]
    polygon_count: int
    line_count: int
    point_count: int
    unsupported_count: int
    units: dict[str, str] = Field(
        default_factory=lambda: {"area": "square meters", "length": "meters"}
    )


class MeasurementsResponse(BaseModel):
    """Paginated measurements response."""

    file: FileResponse
    summary: MeasurementSummary
    limit: int
    offset: int
    total: int
    features: list[MeasurementFeature]
