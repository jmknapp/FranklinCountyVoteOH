"""Tests for vote harmonization and reallocation."""

import tempfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def simple_test_data(temp_data_dir):
    """Create simple test shapefiles and CSVs."""
    crs = "EPSG:3734"

    # Create directories
    raw_dir = temp_data_dir / "raw"
    raw_dir.mkdir()

    # Past year (2020): Two precincts
    past_dir = raw_dir / "precincts_2020"
    past_dir.mkdir()

    past_gdf = gpd.GeoDataFrame(
        {"PREC_ID": ["P1", "P2"]},
        geometry=[
            Polygon([(0, 0), (10, 0), (10, 5), (0, 5)]),
            Polygon([(0, 5), (10, 5), (10, 10), (0, 10)]),
        ],
        crs=crs,
    )
    past_shp = past_dir / "precincts_2020.shp"
    past_gdf.to_file(past_shp)

    # Past results
    past_results = pd.DataFrame(
        {
            "PREC_ID": ["P1", "P2"],
            "D_votes": [100, 200],
            "R_votes": [50, 100],
        }
    )
    past_csv = raw_dir / "results_2020.csv"
    past_results.to_csv(past_csv, index=False)

    # Base year (2024): Four precincts (2x2 grid)
    base_dir = raw_dir / "precincts_2024"
    base_dir.mkdir()

    base_gdf = gpd.GeoDataFrame(
        {"PREC_ID": ["B1", "B2", "B3", "B4"]},
        geometry=[
            Polygon([(0, 0), (5, 0), (5, 5), (0, 5)]),
            Polygon([(5, 0), (10, 0), (10, 5), (5, 5)]),
            Polygon([(0, 5), (5, 5), (5, 10), (0, 10)]),
            Polygon([(5, 5), (10, 5), (10, 10), (5, 10)]),
        ],
        crs=crs,
    )
    base_shp = base_dir / "precincts_2024.shp"
    base_gdf.to_file(base_shp)

    # Base results
    base_results = pd.DataFrame(
        {
            "PREC_ID": ["B1", "B2", "B3", "B4"],
            "D_votes": [60, 80, 100, 120],
            "R_votes": [40, 60, 70, 90],
        }
    )
    base_csv = raw_dir / "results_2024.csv"
    base_results.to_csv(base_csv, index=False)

    # Create config
    config = {
        "base_year": "2024",
        "crs": crs,
        "id_fields": {"2020": "PREC_ID", "2024": "PREC_ID"},
        "paths": {
            "shapefiles": {
                "2020": str(past_shp),
                "2024": str(base_shp),
            },
            "results_csv": {
                "2020": str(past_csv),
                "2024": str(base_csv),
            },
        },
        "output": {
            "harmonized_gpkg": str(temp_data_dir / "harmonized.gpkg"),
            "timeseries_csv": str(temp_data_dir / "timeseries.csv"),
            "county_aggregates_csv": str(temp_data_dir / "county_aggregates.csv"),
            "crosswalk_dir": str(temp_data_dir / "crosswalks"),
        },
        "options": {
            "sliver_tolerance": 1e-9,
        },
    }

    return config, past_results, base_results


def test_reallocate_votes_simple(simple_test_data):
    """Test basic vote reallocation."""
    from src.harmonize import reallocate_votes_to_base

    config, past_results, base_results = simple_test_data

    # Reallocate 2020 votes to 2024 base
    gdf, crosswalk = reallocate_votes_to_base("2020", config, weight="area", save_outputs=False)

    # Check that we have 4 base precincts
    assert len(gdf) == 4

    # Check that total votes are conserved
    original_d_total = past_results["D_votes"].sum()
    original_r_total = past_results["R_votes"].sum()

    harmonized_d_total = gdf["D_votes"].sum()
    harmonized_r_total = gdf["R_votes"].sum()

    assert harmonized_d_total == pytest.approx(original_d_total, rel=1e-2)
    assert harmonized_r_total == pytest.approx(original_r_total, rel=1e-2)

    # Check D_share is computed
    assert "D_share" in gdf.columns
    assert all(gdf["D_share"] >= 0)
    assert all(gdf["D_share"] <= 1)


def test_harmonize_conserves_votes(simple_test_data):
    """Test that harmonization conserves total vote counts."""
    from src.harmonize import reallocate_votes_to_base

    config, past_results, _ = simple_test_data

    gdf, _ = reallocate_votes_to_base("2020", config, weight="area", save_outputs=False)

    # Original totals
    orig_d = past_results["D_votes"].sum()
    orig_r = past_results["R_votes"].sum()
    orig_total = orig_d + orig_r

    # Harmonized totals
    harm_d = gdf["D_votes"].sum()
    harm_r = gdf["R_votes"].sum()
    harm_total = harm_d + harm_r

    # Should be approximately equal (within rounding)
    assert harm_d == pytest.approx(orig_d, abs=2)  # Allow small rounding error
    assert harm_r == pytest.approx(orig_r, abs=2)
    assert harm_total == pytest.approx(orig_total, abs=2)


def test_crosswalk_saved(simple_test_data):
    """Test that crosswalk is saved correctly."""
    from src.harmonize import reallocate_votes_to_base

    config, _, _ = simple_test_data

    _, crosswalk = reallocate_votes_to_base("2020", config, weight="area", save_outputs=True)

    # Check crosswalk structure
    assert "PREC_ID" in crosswalk.columns  # past_id
    # Note: After merge, column names might be suffixed
    assert "frac" in crosswalk.columns

    # Check that fractions sum to ~1 for each past precinct
    # Group by first occurrence of PREC_ID (the past precinct)
    past_col = [col for col in crosswalk.columns if col.startswith("PREC_ID")][0]
    frac_sums = crosswalk.groupby(past_col)["frac"].sum()

    for prec_id, frac_sum in frac_sums.items():
        assert frac_sum == pytest.approx(1.0, rel=1e-2)


def test_harmonize_base_year_error(simple_test_data):
    """Test that harmonizing base year to itself raises error."""
    from src.harmonize import reallocate_votes_to_base

    config, _, _ = simple_test_data

    with pytest.raises(ValueError, match="Cannot harmonize base year"):
        reallocate_votes_to_base("2024", config, weight="area", save_outputs=False)


def test_missing_precinct_in_results(simple_test_data):
    """Test handling of precincts in shapefile but not in results CSV."""
    from src.harmonize import reallocate_votes_to_base

    config, _, _ = simple_test_data

    # Remove one precinct from results CSV
    incomplete_results = pd.DataFrame(
        {
            "PREC_ID": ["P1"],  # Only P1, missing P2
            "D_votes": [100],
            "R_votes": [50],
        }
    )
    csv_path = config["paths"]["results_csv"]["2020"]
    incomplete_results.to_csv(csv_path, index=False)

    # Should still work, treating missing precinct as zero votes
    gdf, _ = reallocate_votes_to_base("2020", config, weight="area", save_outputs=False)

    # Should have all 4 base precincts
    assert len(gdf) == 4

    # Total votes should be less (only from P1)
    assert gdf["D_votes"].sum() <= 100

