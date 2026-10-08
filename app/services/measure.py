"""Feature measurement calculations."""

from __future__ import annotations

from dataclasses import dataclass

from pyproj import CRS, Geod
from shapely import Geometry
from shapely.ops import transform

from app.models import MeasurementStatus
from app.services.crs import (
    choose_measurement_crs,
    crs_to_string,
    get_transformer,
    unit_to_meter_factor,
)

GEOD = Geod(ellps="WGS84")


@dataclass(frozen=True)
class MeasurementResult:
    """Measurement fields for one feature."""

    projected_crs_used: str | None
    area_m2: float | None
    area_hectares: float | None
    length_m: float | None
    length_km: float | None
    geodesic_area_m2: float | None
    geodesic_length_m: float | None
    status: MeasurementStatus
    note: str | None


def measure_geometry(geometry: Geometry | None, source_crs_text: str, note: str | None) -> MeasurementResult:
    """Measure area or length for a geometry with correct metric projection."""

    if geometry is None or geometry.is_empty:
        return _result(
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            MeasurementStatus.UNSUPPORTED,
            _join(note, "Geometry is null or empty."),
        )

    geom_type = geometry.geom_type
    if geom_type in {"Point", "MultiPoint"}:
        return _result(
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            MeasurementStatus.NOT_REQUIRED,
            _join(note, "Points do not require area or length measurement."),
        )
    if geom_type == "GeometryCollection":
        return _result(
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            MeasurementStatus.UNSUPPORTED,
            _join(note, "GeometryCollection measurements are not supported."),
        )
    if geom_type not in {"Polygon", "MultiPolygon", "LineString", "MultiLineString"}:
        return _result(
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            MeasurementStatus.UNSUPPORTED,
            _join(note, f"{geom_type} measurements are not supported."),
        )

    try:
        source_crs = CRS.from_user_input(source_crs_text)
        measurement_crs = choose_measurement_crs(geometry, source_crs)
        projected = _project_geometry(geometry, source_crs, measurement_crs)
        factor = unit_to_meter_factor(measurement_crs)
        projected_text = crs_to_string(measurement_crs)
        geodesic_geom = _project_geometry(geometry, source_crs, CRS.from_epsg(4326))

        if geom_type in {"Polygon", "MultiPolygon"}:
            area_m2 = abs(projected.area) * factor * factor
            geodesic_area, _ = GEOD.geometry_area_perimeter(geodesic_geom)
            return _result(
                projected_text,
                area_m2,
                area_m2 / 10_000,
                None,
                None,
                abs(float(geodesic_area)),
                None,
                MeasurementStatus.OK,
                note,
            )

        length_m = projected.length * factor
        return _result(
            projected_text,
            None,
            None,
            length_m,
            length_m / 1000,
            None,
            float(GEOD.geometry_length(geodesic_geom)),
            MeasurementStatus.OK,
            note,
        )
    except (ValueError, RuntimeError, TypeError) as exc:
        return _result(
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            MeasurementStatus.ERROR,
            _join(note, f"Measurement failed: {exc}."),
        )


def _project_geometry(geometry: Geometry, source_crs: CRS, target_crs: CRS) -> Geometry:
    if source_crs == target_crs:
        return geometry
    transformer = get_transformer(crs_to_string(source_crs), crs_to_string(target_crs))
    return transform(transformer.transform, geometry)


def _result(
    projected_crs_used: str | None,
    area_m2: float | None,
    area_hectares: float | None,
    length_m: float | None,
    length_km: float | None,
    geodesic_area_m2: float | None,
    geodesic_length_m: float | None,
    status: MeasurementStatus,
    note: str | None,
) -> MeasurementResult:
    return MeasurementResult(
        projected_crs_used=projected_crs_used,
        area_m2=area_m2,
        area_hectares=area_hectares,
        length_m=length_m,
        length_km=length_km,
        geodesic_area_m2=geodesic_area_m2,
        geodesic_length_m=geodesic_length_m,
        status=status,
        note=note,
    )


def _join(first: str | None, second: str) -> str:
    return f"{first} {second}" if first else second
