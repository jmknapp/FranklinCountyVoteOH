"""Tests for metrics computation."""

import pandas as pd
import pytest

from src.metrics import compute_two_party_metrics, county_aggregates, pivot_to_wide


@pytest.fixture
def sample_timeseries():
    """Create sample time-series data for testing."""
    data = {
        "PREC_ID": ["P1", "P1", "P1", "P2", "P2", "P2"],
        "year": ["2020", "2022", "2024", "2020", "2022", "2024"],
        "D_votes": [100, 120, 140, 200, 180, 160],
        "R_votes": [50, 60, 70, 100, 120, 140],
        "total": [150, 180, 210, 300, 300, 300],
    }
    df = pd.DataFrame(data)
    df["D_share"] = df["D_votes"] / df["total"]
    return df


def test_compute_two_party_metrics(sample_timeseries):
    """Test computation of two-party metrics."""
    df = compute_two_party_metrics(sample_timeseries, base_id="PREC_ID")

    # Check that swing columns were added
    assert "swing_yoy" in df.columns
    assert "swing_vs_2020" in df.columns

    # Check year-over-year swing for P1
    p1_data = df[df["PREC_ID"] == "P1"].sort_values("year")

    # First year should have no previous swing
    assert pd.isna(p1_data.iloc[0]["swing_yoy"])

    # Subsequent years should have swing values
    assert pd.notna(p1_data.iloc[1]["swing_yoy"])
    assert pd.notna(p1_data.iloc[2]["swing_yoy"])

    # Swing vs 2020 should be 0 for 2020
    assert p1_data[p1_data["year"] == "2020"]["swing_vs_2020"].values[0] == 0.0


def test_d_share_calculation(sample_timeseries):
    """Test that D_share is calculated correctly."""
    df = sample_timeseries.copy()

    # Verify D_share calculation
    for _, row in df.iterrows():
        expected_share = row["D_votes"] / row["total"]
        assert row["D_share"] == pytest.approx(expected_share)


def test_county_aggregates(sample_timeseries):
    """Test county-wide aggregation."""
    agg = county_aggregates(sample_timeseries)

    # Should have one row per year
    assert len(agg) == 3
    assert set(agg["year"]) == {"2020", "2022", "2024"}

    # Check that votes are summed correctly
    for year in ["2020", "2022", "2024"]:
        year_agg = agg[agg["year"] == year].iloc[0]
        year_orig = sample_timeseries[sample_timeseries["year"] == year]

        assert year_agg["D_votes"] == year_orig["D_votes"].sum()
        assert year_agg["R_votes"] == year_orig["R_votes"].sum()
        assert year_agg["total"] == year_orig["total"].sum()

        # Check D_share
        expected_d_share = year_orig["D_votes"].sum() / year_orig["total"].sum()
        assert year_agg["D_share"] == pytest.approx(expected_d_share)


def test_pivot_to_wide(sample_timeseries):
    """Test pivoting to wide format."""
    df_wide = pivot_to_wide(sample_timeseries, base_id="PREC_ID")

    # Should have one row per precinct
    assert len(df_wide) == 2
    assert set(df_wide["PREC_ID"]) == {"P1", "P2"}

    # Should have columns for each year and metric
    assert "D_votes_2020" in df_wide.columns
    assert "D_votes_2022" in df_wide.columns
    assert "D_votes_2024" in df_wide.columns
    assert "D_share_2020" in df_wide.columns

    # Check values
    p1_row = df_wide[df_wide["PREC_ID"] == "P1"].iloc[0]
    assert p1_row["D_votes_2020"] == 100
    assert p1_row["D_votes_2022"] == 120
    assert p1_row["D_votes_2024"] == 140


def test_swing_calculation():
    """Test swing calculation with known values."""
    data = {
        "PREC_ID": ["P1", "P1"],
        "year": ["2020", "2024"],
        "D_votes": [100, 150],
        "R_votes": [100, 150],
        "total": [200, 300],
    }
    df = pd.DataFrame(data)
    df["D_share"] = df["D_votes"] / df["total"]

    df_with_metrics = compute_two_party_metrics(df, base_id="PREC_ID")

    # D_share should be 0.5 for both years (50-50 split)
    assert all(df_with_metrics["D_share"] == 0.5)

    # Swing should be 0 (no change)
    row_2024 = df_with_metrics[df_with_metrics["year"] == "2024"].iloc[0]
    assert row_2024["swing_yoy"] == pytest.approx(0.0)


def test_turnout_metrics(sample_timeseries):
    """Test turnout change metrics."""
    df = compute_two_party_metrics(sample_timeseries, base_id="PREC_ID")

    assert "turnout" in df.columns
    assert "turnout_change_yoy" in df.columns
    assert "turnout_change_yoy_pct" in df.columns

    # Check P1 turnout growth
    p1_data = df[df["PREC_ID"] == "P1"].sort_values("year")

    # 2020: 150, 2022: 180, 2024: 210
    row_2022 = p1_data[p1_data["year"] == "2022"].iloc[0]
    assert row_2022["turnout_change_yoy"] == 30  # 180 - 150

    row_2024 = p1_data[p1_data["year"] == "2024"].iloc[0]
    assert row_2024["turnout_change_yoy"] == 30  # 210 - 180


def test_zero_vote_precinct():
    """Test handling of precincts with zero votes."""
    data = {
        "PREC_ID": ["P1", "P1"],
        "year": ["2020", "2024"],
        "D_votes": [0, 100],
        "R_votes": [0, 100],
        "total": [0, 200],
    }
    df = pd.DataFrame(data)

    # Compute D_share with zero total
    df["D_share"] = df["D_votes"] / df["total"].replace(0, pd.NA)
    df["D_share"] = df["D_share"].fillna(0)

    # Should handle without error
    df_with_metrics = compute_two_party_metrics(df, base_id="PREC_ID")

    # Zero vote precinct should have 0 D_share
    row_2020 = df_with_metrics[df_with_metrics["year"] == "2020"].iloc[0]
    assert row_2020["D_share"] == 0.0

