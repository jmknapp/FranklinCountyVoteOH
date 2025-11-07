"""Compute partisan metrics, swings, and aggregates from harmonized data."""

import logging
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

from .io_utils import ensure_output_dir

logger = logging.getLogger(__name__)


def compute_two_party_metrics(df_long: pd.DataFrame, base_id: str = "PREC_ID") -> pd.DataFrame:
    """
    Compute two-party metrics including year-over-year swings.

    Args:
        df_long: Long-format DataFrame with columns [base_id, year, D_votes, R_votes, total, D_share]
        base_id: Name of base precinct ID column

    Returns:
        DataFrame with additional swing columns
    """
    logger.info("Computing two-party metrics and swings...")

    df = df_long.copy()

    # Ensure year is sorted
    df = df.sort_values([base_id, "year"])

    # Compute year-over-year swing (change in D_share from previous election)
    df["D_share_prev"] = df.groupby(base_id)["D_share"].shift(1)
    df["swing_yoy"] = df["D_share"] - df["D_share_prev"]

    # Compute swing vs earliest year
    earliest_year = df["year"].min()
    earliest_shares = df[df["year"] == earliest_year][[base_id, "D_share"]].copy()
    earliest_shares.columns = [base_id, "D_share_earliest"]

    df = df.merge(earliest_shares, on=base_id, how="left")
    df[f"swing_vs_{earliest_year}"] = df["D_share"] - df["D_share_earliest"]

    # Compute swing vs latest year
    latest_year = df["year"].max()
    latest_shares = df[df["year"] == latest_year][[base_id, "D_share"]].copy()
    latest_shares.columns = [base_id, "D_share_latest"]

    df = df.merge(latest_shares, on=base_id, how="left")
    df[f"swing_vs_{latest_year}"] = df["D_share"] - df["D_share_latest"]

    # Compute turnout (total votes)
    df["turnout"] = df["total"]

    # Compute turnout change year-over-year
    df["turnout_prev"] = df.groupby(base_id)["turnout"].shift(1)
    df["turnout_change_yoy"] = df["turnout"] - df["turnout_prev"]
    df["turnout_change_yoy_pct"] = (
        df["turnout_change_yoy"] / df["turnout_prev"].replace(0, pd.NA)
    )

    logger.info(f"Computed metrics for {len(df)} precinct-year observations")

    return df


def county_aggregates(df_long: pd.DataFrame) -> pd.DataFrame:
    """
    Compute county-wide aggregates by year.

    Args:
        df_long: Long-format DataFrame with precinct-level data

    Returns:
        DataFrame with county-level aggregates by year
    """
    logger.info("Computing county-wide aggregates...")

    agg = (
        df_long.groupby("year")
        .agg(
            {
                "D_votes": "sum",
                "R_votes": "sum",
                "total": "sum",
            }
        )
        .reset_index()
    )

    # Compute county-wide D_share
    agg["D_share"] = agg["D_votes"] / agg["total"]

    # Compute year-over-year swing at county level
    agg = agg.sort_values("year")
    agg["D_share_prev"] = agg["D_share"].shift(1)
    agg["swing_yoy"] = agg["D_share"] - agg["D_share_prev"]

    # Turnout change
    agg["turnout"] = agg["total"]
    agg["turnout_prev"] = agg["turnout"].shift(1)
    agg["turnout_change_yoy"] = agg["turnout"] - agg["turnout_prev"]
    agg["turnout_change_yoy_pct"] = agg["turnout_change_yoy"] / agg["turnout_prev"]

    logger.info(f"Computed aggregates for {len(agg)} years")

    return agg


def build_timeseries_table(cfg: dict[str, Any]) -> pd.DataFrame:
    """
    Build combined time-series table from all harmonized layers.

    Args:
        cfg: Configuration dictionary

    Returns:
        Long-format DataFrame with all years
    """
    logger.info("Building time-series table from harmonized data...")

    gpkg_path = Path(cfg["output"]["harmonized_gpkg"])
    if not gpkg_path.exists():
        raise FileNotFoundError(
            f"Harmonized GeoPackage not found: {gpkg_path}. "
            "Run harmonization first with 'ffs harmonize-all'"
        )

    base_year = str(cfg["base_year"])
    base_id = cfg["id_fields"][base_year]
    all_years = sorted(cfg["paths"]["shapefiles"].keys())

    # Load all layers
    dfs = []
    for year in all_years:
        layer_name = f"yr_{year}_on_{base_year}"
        try:
            gdf = gpd.read_file(gpkg_path, layer=layer_name)
            # Extract just the data columns (drop geometry for timeseries table)
            df = pd.DataFrame(gdf.drop(columns="geometry"))
            dfs.append(df)
            logger.debug(f"Loaded layer {layer_name}: {len(df)} records")
        except Exception as e:
            logger.warning(f"Failed to load layer {layer_name}: {e}")

    if not dfs:
        raise ValueError(f"No layers found in {gpkg_path}")

    # Combine all years
    df_long = pd.concat(dfs, ignore_index=True)

    logger.info(f"Built time-series table with {len(df_long)} precinct-year observations")

    return df_long


def compute_and_save_metrics(cfg: dict[str, Any]) -> None:
    """
    Compute all metrics and save to output files.

    Args:
        cfg: Configuration dictionary
    """
    base_year = str(cfg["base_year"])
    base_id = cfg["id_fields"][base_year]

    # Build time-series table
    df_long = build_timeseries_table(cfg)

    # Compute metrics
    df_with_metrics = compute_two_party_metrics(df_long, base_id=base_id)

    # Save long-format table
    output_path = Path(cfg["output"]["timeseries_csv"])
    ensure_output_dir(output_path.parent)
    df_with_metrics.to_csv(output_path, index=False)
    logger.info(f"Saved time-series table to {output_path}")

    # Also save wide format (pivot on year)
    logger.info("Creating wide-format table...")
    df_wide = pivot_to_wide(df_with_metrics, base_id=base_id)
    wide_path = output_path.parent / "timeseries_per_precinct_wide.csv"
    df_wide.to_csv(wide_path, index=False)
    logger.info(f"Saved wide-format table to {wide_path}")

    # Compute and save county aggregates
    agg = county_aggregates(df_long)
    agg_path = Path(cfg["output"]["county_aggregates_csv"])
    agg.to_csv(agg_path, index=False)
    logger.info(f"Saved county aggregates to {agg_path}")

    # Print summary
    _print_summary(df_with_metrics, agg)


def pivot_to_wide(df_long: pd.DataFrame, base_id: str) -> pd.DataFrame:
    """
    Pivot long-format data to wide format with years as columns.

    Args:
        df_long: Long-format DataFrame
        base_id: Base precinct ID column

    Returns:
        Wide-format DataFrame
    """
    # Select key columns
    cols_to_pivot = [base_id, "year", "D_votes", "R_votes", "total", "D_share"]
    df_subset = df_long[cols_to_pivot].copy()

    # Pivot each metric
    dfs_wide = []

    for metric in ["D_votes", "R_votes", "total", "D_share"]:
        pivot = df_subset.pivot(index=base_id, columns="year", values=metric)
        pivot.columns = [f"{metric}_{col}" for col in pivot.columns]
        dfs_wide.append(pivot)

    # Combine all pivots
    df_wide = pd.concat(dfs_wide, axis=1).reset_index()

    return df_wide


def _print_summary(df_metrics: pd.DataFrame, df_agg: pd.DataFrame) -> None:
    """Print summary statistics to console."""
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 60)

    # County-level summary
    logger.info("\nCounty-Wide Results by Year:")
    for _, row in df_agg.iterrows():
        logger.info(
            f"  {row['year']}: D={row['D_share']:.1%}, "
            f"Turnout={row['turnout']:,.0f}, "
            f"Swing={row['swing_yoy']:.1%}" if pd.notna(row['swing_yoy']) else
            f"  {row['year']}: D={row['D_share']:.1%}, Turnout={row['turnout']:,.0f}"
        )

    # Precinct-level summary
    logger.info("\nPrecinct-Level Statistics:")
    n_precincts = df_metrics[df_metrics["year"] == df_metrics["year"].max()].shape[0]
    logger.info(f"  Number of base precincts: {n_precincts}")

    for year in sorted(df_metrics["year"].unique()):
        year_data = df_metrics[df_metrics["year"] == year]
        logger.info(
            f"  {year}: Mean D_share={year_data['D_share'].mean():.1%}, "
            f"Median={year_data['D_share'].median():.1%}, "
            f"Std={year_data['D_share'].std():.1%}"
        )

    logger.info("=" * 60 + "\n")

