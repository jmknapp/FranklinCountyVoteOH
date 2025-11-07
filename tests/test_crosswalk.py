"""Tests for spatial crosswalk building."""

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon

from src.crosswalk import build_crosswalk, validate_crosswalk


@pytest.fixture
def simple_squares():
    """Create two simple square geometries for testing."""
    crs = "EPSG:3734"

    # Past: One large square
    past_gdf = gpd.GeoDataFrame(
        {"PREC_ID": ["P1"], "name": ["Large"]},
        geometry=[Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])],
        crs=crs,
    )

    # Base: Four smaller squares (2x2 grid)
    base_geoms = [
        Polygon([(0, 0), (5, 0), (5, 5), (0, 5)]),  # SW
        Polygon([(5, 0), (10, 0), (10, 5), (5, 5)]),  # SE
        Polygon([(0, 5), (5, 5), (5, 10), (0, 10)]),  # NW
        Polygon([(5, 5), (10, 5), (10, 10), (5, 10)]),  # NE
    ]
    base_gdf = gpd.GeoDataFrame(
        {"PREC_ID": ["B1", "B2", "B3", "B4"], "name": ["SW", "SE", "NW", "NE"]},
        geometry=base_geoms,
        crs=crs,
    )

    return past_gdf, base_gdf


def test_area_crosswalk_equal_split(simple_squares):
    """Test that a square splits equally into four quarters."""
    past_gdf, base_gdf = simple_squares

    crosswalk = build_crosswalk(
        past_gdf=past_gdf,
        base_gdf=base_gdf,
        past_id="PREC_ID",
        base_id="PREC_ID",
        weight="area",
    )

    # Should have 4 mappings (one past precinct to four base precincts)
    assert len(crosswalk) == 4

    # Each should get 25% (0.25) of the original
    assert all(crosswalk["frac"].round(2) == 0.25)

    # Sum should be 1.0
    assert crosswalk["frac"].sum() == pytest.approx(1.0)


def test_crosswalk_partial_overlap():
    """Test crosswalk with partial overlap."""
    crs = "EPSG:3734"

    # Past: Rectangle
    past_gdf = gpd.GeoDataFrame(
        {"PREC_ID": ["P1"]},
        geometry=[Polygon([(0, 0), (10, 0), (10, 5), (0, 5)])],
        crs=crs,
    )

    # Base: Two rectangles, one overlapping 60%, one 40%
    base_gdf = gpd.GeoDataFrame(
        {"PREC_ID": ["B1", "B2"]},
        geometry=[
            Polygon([(0, 0), (6, 0), (6, 5), (0, 5)]),  # 60% overlap
            Polygon([(6, 0), (10, 0), (10, 5), (6, 5)]),  # 40% overlap
        ],
        crs=crs,
    )

    crosswalk = build_crosswalk(
        past_gdf=past_gdf,
        base_gdf=base_gdf,
        past_id="PREC_ID",
        base_id="PREC_ID",
        weight="area",
    )

    assert len(crosswalk) == 2
    assert crosswalk[crosswalk["PREC_ID_2"] == "B1"]["frac"].values[0] == pytest.approx(0.6, rel=1e-2)
    assert crosswalk[crosswalk["PREC_ID_2"] == "B2"]["frac"].values[0] == pytest.approx(0.4, rel=1e-2)


def test_crosswalk_no_overlap():
    """Test crosswalk with geometries that don't overlap."""
    crs = "EPSG:3734"

    past_gdf = gpd.GeoDataFrame(
        {"PREC_ID": ["P1"]},
        geometry=[Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])],
        crs=crs,
    )

    base_gdf = gpd.GeoDataFrame(
        {"PREC_ID": ["B1"]},
        geometry=[Polygon([(10, 10), (15, 10), (15, 15), (10, 15)])],
        crs=crs,
    )

    crosswalk = build_crosswalk(
        past_gdf=past_gdf,
        base_gdf=base_gdf,
        past_id="PREC_ID",
        base_id="PREC_ID",
        weight="area",
    )

    # Should have no mappings
    assert len(crosswalk) == 0


def test_crosswalk_validation(simple_squares):
    """Test crosswalk validation function."""
    past_gdf, base_gdf = simple_squares

    crosswalk = build_crosswalk(
        past_gdf=past_gdf,
        base_gdf=base_gdf,
        past_id="PREC_ID",
        base_id="PREC_ID",
        weight="area",
    )

    stats = validate_crosswalk(crosswalk, past_id="PREC_ID")

    assert stats["n_past_precincts"] == 1
    assert stats["mean_coverage"] == pytest.approx(1.0)
    assert stats["min_coverage"] == pytest.approx(1.0)
    assert stats["n_incomplete"] == 0
    assert stats["mean_splits"] == 4
    assert stats["max_splits"] == 4
    assert stats["n_one_to_one"] == 0


def test_crosswalk_multiple_past_precincts():
    """Test crosswalk with multiple past precincts."""
    crs = "EPSG:3734"

    # Past: Two squares side by side
    past_gdf = gpd.GeoDataFrame(
        {"PREC_ID": ["P1", "P2"]},
        geometry=[
            Polygon([(0, 0), (5, 0), (5, 10), (0, 10)]),
            Polygon([(5, 0), (10, 0), (10, 10), (5, 10)]),
        ],
        crs=crs,
    )

    # Base: Three vertical strips
    base_gdf = gpd.GeoDataFrame(
        {"PREC_ID": ["B1", "B2", "B3"]},
        geometry=[
            Polygon([(0, 0), (3, 0), (3, 10), (0, 10)]),
            Polygon([(3, 0), (7, 0), (7, 10), (3, 10)]),
            Polygon([(7, 0), (10, 0), (10, 10), (7, 10)]),
        ],
        crs=crs,
    )

    crosswalk = build_crosswalk(
        past_gdf=past_gdf,
        base_gdf=base_gdf,
        past_id="PREC_ID",
        base_id="PREC_ID",
        weight="area",
    )

    # P1 should split into B1 (60%) and B2 (40%)
    p1_rows = crosswalk[crosswalk["PREC_ID_1"] == "P1"]
    assert len(p1_rows) == 2
    assert p1_rows["frac"].sum() == pytest.approx(1.0)

    # P2 should split into B2 (40%) and B3 (60%)
    p2_rows = crosswalk[crosswalk["PREC_ID_1"] == "P2"]
    assert len(p2_rows) == 2
    assert p2_rows["frac"].sum() == pytest.approx(1.0)


def test_crs_mismatch_error():
    """Test that mismatched CRS raises an error."""
    past_gdf = gpd.GeoDataFrame(
        {"PREC_ID": ["P1"]},
        geometry=[Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
        crs="EPSG:4326",
    )

    base_gdf = gpd.GeoDataFrame(
        {"PREC_ID": ["B1"]},
        geometry=[Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
        crs="EPSG:3734",
    )

    with pytest.raises(ValueError, match="CRS mismatch"):
        build_crosswalk(
            past_gdf=past_gdf,
            base_gdf=base_gdf,
            past_id="PREC_ID",
            base_id="PREC_ID",
            weight="area",
        )

