"""Projected CRS selection and transformation helpers."""

from __future__ import annotations

from functools import lru_cache

from pyproj import CRS, Transformer
from shapely import Geometry


def choose_measurement_crs(geometry: Geometry, source_crs: CRS) -> CRS:
    """Choose the projected CRS to use for a feature measurement."""

    if not source_crs.is_geographic:
        return source_crs

    centroid = geometry.centroid
    lon = float(centroid.x)
    lat = float(centroid.y)
    if lat > 84:
        return CRS.from_epsg(3413)
    if lat < -80:
        return CRS.from_epsg(3031)
    zone = int((lon + 180) // 6) + 1
    zone = max(1, min(zone, 60))
    epsg = 32600 + zone if lat >= 0 else 32700 + zone
    return CRS.from_epsg(epsg)


def unit_to_meter_factor(crs: CRS) -> float:
    """Return the conversion factor from CRS axis units to meters."""

    if not crs.axis_info:
        return 1.0
    return float(crs.axis_info[0].unit_conversion_factor or 1.0)


def crs_to_string(crs: CRS) -> str:
    """Return a compact authority string when available."""

    authority = crs.to_authority()
    return f"{authority[0]}:{authority[1]}" if authority else crs.to_string()


@lru_cache(maxsize=256)
def get_transformer(source: str, target: str) -> Transformer:
    """Return a cached pyproj transformer."""

    return Transformer.from_crs(CRS.from_user_input(source), CRS.from_user_input(target), always_xy=True)

