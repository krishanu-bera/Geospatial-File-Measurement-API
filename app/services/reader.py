"""Upload validation and geospatial file reading."""

from __future__ import annotations

import logging
import math
import zipfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path, PurePosixPath
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
from fastapi import UploadFile
from shapely import Geometry, force_2d, is_valid_reason, make_valid
from shapely.geometry import mapping

from app.exceptions import (
    InvalidFileError,
    UnreadableFileError,
    UnsupportedFormatError,
    UploadTooLargeError,
)

logger = logging.getLogger(__name__)

MAX_ZIP_MEMBERS = 256
MAX_ZIP_UNCOMPRESSED_MB = 512


@dataclass(frozen=True)
class ParsedFeature:
    """A feature parsed from an uploaded geospatial file."""

    index: int
    layer_name: str | None
    geometry_type: str
    geometry: Geometry | None
    geometry_geojson: dict[str, Any] | None
    source_crs: str
    properties: dict[str, Any]
    note: str | None = None


def validate_upload_metadata(file: UploadFile, max_bytes: int) -> str:
    """Validate upload extension and optional content-length metadata."""

    filename = file.filename or "upload"
    suffix = Path(filename).suffix.lower()
    if suffix not in {".zip", ".kml"}:
        raise UnsupportedFormatError("Only .zip Shapefiles and .kml files are supported.")
    size_header = file.headers.get("content-length")
    if size_header and int(size_header) > max_bytes:
        raise UploadTooLargeError(f"Upload exceeds the {max_bytes} byte size limit.")
    return suffix


def save_upload(file: UploadFile, target_path: Path, max_bytes: int) -> int:
    """Save an uploaded file while enforcing size and non-empty checks."""

    target_path.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with target_path.open("wb") as output:
        while chunk := file.file.read(1024 * 1024):
            total += len(chunk)
            if total > max_bytes:
                raise UploadTooLargeError(f"Upload exceeds the {max_bytes} byte size limit.")
            output.write(chunk)
    if total == 0:
        raise InvalidFileError("Uploaded file is empty.")
    return total


def read_features(path: Path, suffix: str) -> tuple[list[ParsedFeature], str]:
    """Read every feature from a supported geospatial file."""

    if suffix == ".zip":
        return _read_shapefile_zip(path)
    if suffix == ".kml":
        return _read_kml(path)
    raise UnsupportedFormatError("Only .zip Shapefiles and .kml files are supported.")


def _read_shapefile_zip(path: Path) -> tuple[list[ParsedFeature], str]:
    _validate_zip(path)
    shapefile_name, has_prj = _find_shapefile_members(path)
    zip_uri = f"zip://{path.resolve().as_posix()}!{shapefile_name}"
    try:
        frame = gpd.read_file(zip_uri, engine="pyogrio")
    except (pyogrio.errors.DataSourceError, ValueError, RuntimeError) as exc:
        raise UnreadableFileError(f"Could not read Shapefile zip: {exc}") from exc

    crs = _crs_to_string(frame.crs) if frame.crs is not None else "EPSG:4326"
    note = None
    if not has_prj or frame.crs is None:
        note = "Source .prj was missing; assumed EPSG:4326."
        logger.warning("Assuming EPSG:4326 for Shapefile without .prj: %s", path)
    return _frame_to_features(frame, crs, None, note), crs


def _read_kml(path: Path) -> tuple[list[ParsedFeature], str]:
    try:
        layer_rows = pyogrio.list_layers(path)
    except (pyogrio.errors.DataSourceError, ValueError, RuntimeError) as exc:
        raise UnreadableFileError(f"Could not inspect KML layers: {exc}") from exc

    features: list[ParsedFeature] = []
    next_index = 0
    for layer_row in layer_rows:
        layer_name = str(layer_row[0])
        try:
            frame = gpd.read_file(path, driver="KML", layer=layer_name, engine="pyogrio")
        except (pyogrio.errors.DataSourceError, ValueError, RuntimeError) as exc:
            raise UnreadableFileError(f"Could not read KML layer '{layer_name}': {exc}") from exc
        layer_features = _frame_to_features(frame, "EPSG:4326", layer_name, None, next_index)
        next_index += len(layer_features)
        features.extend(layer_features)
    return features, "EPSG:4326"


def _validate_zip(path: Path) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            bad_member = archive.testzip()
            if bad_member:
                raise UnreadableFileError(f"Zip archive is corrupt at member {bad_member}.")
            infos = archive.infolist()
            if len(infos) > MAX_ZIP_MEMBERS:
                raise UnreadableFileError("Zip archive contains too many files.")
            total_size = sum(info.file_size for info in infos)
            if total_size > MAX_ZIP_UNCOMPRESSED_MB * 1024 * 1024:
                raise UnreadableFileError("Zip archive is too large when uncompressed.")
            for info in infos:
                name = info.filename.replace("\\", "/")
                pure = PurePosixPath(name)
                if pure.is_absolute() or ".." in pure.parts:
                    raise UnreadableFileError("Zip archive contains unsafe paths.")
    except zipfile.BadZipFile as exc:
        raise UnreadableFileError("Zip archive is corrupt or unreadable.") from exc


def _find_shapefile_members(path: Path) -> tuple[str, bool]:
    with zipfile.ZipFile(path) as archive:
        names = [info.filename.replace("\\", "/") for info in archive.infolist()]
    lower_names = {name.lower(): name for name in names}
    shp_files = [name for name in names if name.lower().endswith(".shp")]
    if not shp_files:
        raise UnreadableFileError("Zip must contain a .shp file.")
    shapefile = shp_files[0]
    stem = shapefile[:-4].lower()
    required = {f"{stem}.shp", f"{stem}.shx", f"{stem}.dbf"}
    missing = sorted(required - set(lower_names))
    if missing:
        raise UnreadableFileError(f"Shapefile zip is missing required files: {missing}.")
    return shapefile, f"{stem}.prj" in lower_names


def _frame_to_features(
    frame: gpd.GeoDataFrame,
    source_crs: str,
    layer_name: str | None,
    base_note: str | None,
    start_index: int = 0,
) -> list[ParsedFeature]:
    features: list[ParsedFeature] = []
    properties_frame = frame.drop(columns=[frame.geometry.name], errors="ignore")
    for offset, row in frame.iterrows():
        index = start_index + len(features)
        geom = row.geometry
        note = base_note
        if geom is None or geom.is_empty:
            features.append(
                ParsedFeature(
                    index=index,
                    layer_name=layer_name,
                    geometry_type="Null" if geom is None else geom.geom_type,
                    geometry=None,
                    geometry_geojson=None,
                    source_crs=source_crs,
                    properties=_json_safe(properties_frame.loc[offset].to_dict()),
                    note=_join_notes(note, "Geometry is null or empty."),
                )
            )
            continue
        try:
            if getattr(geom, "has_z", False):
                geom = force_2d(geom)
                note = _join_notes(note, "Dropped Z coordinates before measurement.")
            if not geom.is_valid:
                reason = is_valid_reason(geom)
                geom = make_valid(geom)
                note = _join_notes(note, f"Geometry was invalid and make_valid was applied: {reason}.")
            features.append(
                ParsedFeature(
                    index=index,
                    layer_name=layer_name,
                    geometry_type=geom.geom_type,
                    geometry=geom,
                    geometry_geojson=mapping(geom),
                    source_crs=source_crs,
                    properties=_json_safe(properties_frame.loc[offset].to_dict()),
                    note=note,
                )
            )
        except (ValueError, TypeError, RuntimeError) as exc:
            features.append(
                ParsedFeature(
                    index=index,
                    layer_name=layer_name,
                    geometry_type=getattr(geom, "geom_type", "Unknown"),
                    geometry=None,
                    geometry_geojson=None,
                    source_crs=source_crs,
                    properties=_json_safe(properties_frame.loc[offset].to_dict()),
                    note=_join_notes(note, f"Feature geometry could not be normalized: {exc}."),
                )
            )
    return features


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, pd.Timestamp):
        return None if pd.isna(value) else value.isoformat()
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, float) and math.isnan(value):
        return None
    if pd.isna(value):
        return None
    return value


def _crs_to_string(crs: Any) -> str:
    auth = crs.to_authority() if hasattr(crs, "to_authority") else None
    return f"{auth[0]}:{auth[1]}" if auth else str(crs)


def _join_notes(first: str | None, second: str) -> str:
    return f"{first} {second}" if first else second

