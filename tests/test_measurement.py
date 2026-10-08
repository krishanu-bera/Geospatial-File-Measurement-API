from __future__ import annotations

from pyproj import CRS
from shapely.geometry import LineString, Polygon

from app.services.crs import choose_measurement_crs, crs_to_string, unit_to_meter_factor
from app.services.measure import measure_geometry


def test_area_accuracy_near_equator_and_60n():
    equator_square = Polygon([(0, 0), (0.008983, 0), (0.008983, 0.008983), (0, 0.008983), (0, 0)])
    north_square = Polygon([(10, 60), (10.017966, 60), (10.017966, 60.008983), (10, 60.008983), (10, 60)])

    equator = measure_geometry(equator_square, "EPSG:4326", None)
    north = measure_geometry(north_square, "EPSG:4326", None)

    assert equator.area_m2 is not None
    assert north.area_m2 is not None
    assert abs(equator.area_m2 - 1_000_000) / 1_000_000 < 0.01
    assert abs(north.area_m2 - 1_000_000) / 1_000_000 < 0.02
    assert equator.area_m2 != equator_square.area


def test_line_length_accuracy():
    line = LineString([(0, 0), (0.008983, 0)])
    result = measure_geometry(line, "EPSG:4326", None)
    assert result.length_m is not None
    assert abs(result.length_m - 1000) / 1000 < 0.01
    assert result.geodesic_length_m is not None


def test_crs_selector_northern_southern_polar_and_feet():
    north = choose_measurement_crs(Polygon([(12, 1), (13, 1), (13, 2), (12, 2), (12, 1)]), CRS.from_epsg(4326))
    south = choose_measurement_crs(Polygon([(12, -1), (13, -1), (13, -2), (12, -2), (12, -1)]), CRS.from_epsg(4326))
    polar = choose_measurement_crs(Polygon([(0, 85), (1, 85), (1, 86), (0, 86), (0, 85)]), CRS.from_epsg(4326))
    feet = CRS.from_epsg(2272)
    assert crs_to_string(north).startswith("EPSG:326")
    assert crs_to_string(south).startswith("EPSG:327")
    assert crs_to_string(polar) == "EPSG:3413"
    assert unit_to_meter_factor(feet) != 1.0

