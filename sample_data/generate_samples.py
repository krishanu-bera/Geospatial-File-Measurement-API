"""Generate small KML and zipped Shapefile samples for tests and the UI."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import geopandas as gpd
from shapely.geometry import LineString, Point, Polygon

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "sample_data"
STATIC_SAMPLE_DIR = ROOT / "app" / "static" / "samples"


def build_samples(output_dir: Path | None = None) -> dict[str, Path]:
    """Build sample KML and zipped Shapefile files."""

    target = output_dir or SAMPLE_DIR
    target.mkdir(parents=True, exist_ok=True)
    STATIC_SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    frame = gpd.GeoDataFrame(
        [
            {"name": "Equator square", "kind": "polygon", "geometry": Polygon([(0, 0), (0.008983, 0), (0.008983, 0.008983), (0, 0.008983), (0, 0)])},
            {"name": "Short line", "kind": "line", "geometry": LineString([(0.02, 0), (0.028983, 0)])},
            {"name": "Reference point", "kind": "point", "geometry": Point(0.04, 0.004)},
        ],
        crs="EPSG:4326",
    )

    kml_path = target / "sample.kml"
    frame.to_file(kml_path, driver="KML")

    shp_frame = gpd.GeoDataFrame(
        [
            {"name": "Equator square A", "kind": "polygon", "geometry": Polygon([(0, 0), (0.008983, 0), (0.008983, 0.008983), (0, 0.008983), (0, 0)])},
            {"name": "Equator square B", "kind": "polygon", "geometry": Polygon([(0.02, 0), (0.028983, 0), (0.028983, 0.008983), (0.02, 0.008983), (0.02, 0)])},
            {"name": "Equator square C", "kind": "polygon", "geometry": Polygon([(0.04, 0), (0.048983, 0), (0.048983, 0.008983), (0.04, 0.008983), (0.04, 0)])},
        ],
        crs="EPSG:4326",
    )

    shp_dir = target / "sample_shp"
    if shp_dir.exists():
        shutil.rmtree(shp_dir)
    shp_dir.mkdir()
    shp_path = shp_dir / "sample.shp"
    shp_frame.to_file(shp_path, driver="ESRI Shapefile")
    zip_path = target / "sample_shapefile.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in shp_dir.iterdir():
            archive.write(path, arcname=path.name)

    shutil.copy2(kml_path, STATIC_SAMPLE_DIR / "sample.kml")
    shutil.copy2(zip_path, STATIC_SAMPLE_DIR / "sample_shapefile.zip")
    return {"kml": kml_path, "zip": zip_path}


if __name__ == "__main__":
    paths = build_samples()
    for label, path in paths.items():
        print(f"{label}: {path}")
