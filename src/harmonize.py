"""Harmonize election results across different precinct vintages."""

import logging
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
import yaml
from tqdm import tqdm

from .crosswalk import build_crosswalk
from .io_utils import (
    ensure_output_dir,
    load_results_csv,
    load_shapefile,
)

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config/project.yaml") -> dict[str, Any]:
    """Load project configuration from YAML file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def reallocate_votes_to_base(
    year: str,
    cfg: dict[str, Any],
    weight: str = "area",
    save_outputs: bool = True,
) -> tuple[gpd.GeoDataFrame, pd.DataFrame]:
    """
    Reallocate votes from a source year to base geography.

    Args:
        year: Source year to harmonize (as string, e.g., "2008")
        cfg: Configuration dictionary
        weight: Weighting method - "area" or "pop"
        save_outputs: Whether to save GeoPackage layer and CSV

    Returns:
        Tuple of (GeoDataFrame with base geometry and votes, crosswalk DataFrame)

    Raises:
        ValueError: If year is the base year or configuration is invalid
    """
    base_year = str(cfg["base_year"])
    if year == base_year:
        raise ValueError(f"Cannot harmonize base year {base_year} to itself")

    logger.info(f"Harmonizing year {year} → base year {base_year}")

    # Load shapefiles
    target_crs = cfg["crs"]
    year_shp_path = cfg["paths"]["shapefiles"][year]
    base_shp_path = cfg["paths"]["shapefiles"][base_year]

    year_gdf = load_shapefile(year_shp_path, target_crs)
    base_gdf = load_shapefile(base_shp_path, target_crs)

    # Get ID fields
    year_id = cfg["id_fields"][year]
    base_id = cfg["id_fields"][base_year]

    # Load results CSV
    year_csv_path = cfg["paths"]["results_csv"][year]
    results_df = load_results_csv(year_csv_path, year_id)

    # Build crosswalk
    logger.info(f"Building {weight}-weighted crosswalk for {year}...")

    # Handle population weights if requested
    blocks_gdf = None
    block_pop_field = None
    if weight == "pop":
        blocks_config = cfg.get("weights", {})
        blocks_path = blocks_config.get("blocks_gpkg")
        if blocks_path:
            logger.info(f"Loading census blocks from {blocks_path}")
            blocks_gdf = gpd.read_file(blocks_path)
            blocks_gdf = blocks_gdf.to_crs(target_crs)
            block_pop_field = blocks_config.get("block_pop_field")
        else:
            logger.warning("Population weighting requested but no blocks configured, using area")
            weight = "area"

    crosswalk = build_crosswalk(
        past_gdf=year_gdf,
        base_gdf=base_gdf,
        past_id=year_id,
        base_id=base_id,
        weight=weight,
        blocks_gdf=blocks_gdf,
        block_pop_field=block_pop_field,
        sliver_tolerance=cfg.get("options", {}).get("sliver_tolerance", 1e-9),
    )

    # Save crosswalk to interim directory
    if save_outputs:
        crosswalk_dir = ensure_output_dir(cfg["output"]["crosswalk_dir"])
        crosswalk_path = crosswalk_dir / f"crosswalk_{year}_to_{base_year}.csv"
        crosswalk.to_csv(crosswalk_path, index=False)
        logger.info(f"Saved crosswalk to {crosswalk_path}")

    # Reallocate votes using crosswalk
    logger.info("Reallocating votes to base geography...")

    # Merge results with crosswalk
    crosswalk_with_votes = crosswalk.merge(
        results_df, left_on=year_id, right_on="precinct_id", how="left"
    )

    # Handle missing precincts
    missing_mask = crosswalk_with_votes["precinct_id"].isna()
    if missing_mask.any():
        n_missing = crosswalk_with_votes[missing_mask][year_id].nunique()
        logger.warning(
            f"{n_missing} precincts from crosswalk not found in results CSV. "
            "Treating as zero votes."
        )
        crosswalk_with_votes.loc[missing_mask, ["D_votes", "R_votes", "total"]] = 0

    # Allocate votes proportionally
    crosswalk_with_votes["D_allocated"] = crosswalk_with_votes["D_votes"] * crosswalk_with_votes["frac"]
    crosswalk_with_votes["R_allocated"] = crosswalk_with_votes["R_votes"] * crosswalk_with_votes["frac"]
    crosswalk_with_votes["total_allocated"] = (
        crosswalk_with_votes["total"] * crosswalk_with_votes["frac"]
    )

    # Aggregate to base precincts
    harmonized = (
        crosswalk_with_votes.groupby(base_id)
        .agg(
            {
                "D_allocated": "sum",
                "R_allocated": "sum",
                "total_allocated": "sum",
            }
        )
        .reset_index()
    )

    harmonized.columns = [base_id, "D_votes", "R_votes", "total"]

    # Round to integers
    harmonized["D_votes"] = harmonized["D_votes"].round().astype(int)
    harmonized["R_votes"] = harmonized["R_votes"].round().astype(int)
    harmonized["total"] = harmonized["total"].round().astype(int)

    # Add year column
    harmonized["year"] = year

    # Compute two-party share
    harmonized["D_share"] = harmonized["D_votes"] / harmonized["total"]
    harmonized["D_share"] = harmonized["D_share"].fillna(0)  # Handle zero-vote precincts

    logger.info(
        f"Harmonized {harmonized['total'].sum():,} votes across {len(harmonized)} base precincts"
    )

    # Join with base geometry
    base_gdf_slim = base_gdf[[base_id, "geometry"]].copy()
    harmonized_gdf = base_gdf_slim.merge(harmonized, on=base_id, how="left")

    # Fill missing precincts with zeros
    missing_mask = harmonized_gdf["year"].isna()
    if missing_mask.any():
        n_missing = missing_mask.sum()
        logger.warning(
            f"{n_missing} base precincts have no data from {year}. Filling with zeros."
        )
        harmonized_gdf.loc[missing_mask, ["D_votes", "R_votes", "total", "D_share"]] = 0
        harmonized_gdf.loc[missing_mask, "year"] = year

    # Save outputs
    if save_outputs:
        # Save to GeoPackage
        gpkg_path = Path(cfg["output"]["harmonized_gpkg"])
        ensure_output_dir(gpkg_path.parent)

        layer_name = f"yr_{year}_on_{base_year}"
        harmonized_gdf.to_file(gpkg_path, layer=layer_name, driver="GPKG")
        logger.info(f"Saved GeoPackage layer '{layer_name}' to {gpkg_path}")

        # Save CSV
        csv_dir = ensure_output_dir(gpkg_path.parent)
        csv_path = csv_dir / f"harmonized_{year}_on_{base_year}.csv"
        harmonized[[ base_id, "year", "D_votes", "R_votes", "total", "D_share"]].to_csv(
            csv_path, index=False
        )
        logger.info(f"Saved CSV to {csv_path}")

    return harmonized_gdf, crosswalk


def harmonize_all(cfg: dict[str, Any], weight: str = "area") -> None:
    """
    Harmonize all non-base years to base geography.

    Args:
        cfg: Configuration dictionary
        weight: Weighting method - "area" or "pop"
    """
    base_year = str(cfg["base_year"])
    all_years = sorted(cfg["paths"]["shapefiles"].keys())
    non_base_years = [y for y in all_years if y != base_year]

    logger.info(f"Harmonizing {len(non_base_years)} years to base year {base_year}")
    logger.info(f"Years to process: {', '.join(non_base_years)}")

    for year in tqdm(non_base_years, desc="Harmonizing years"):
        try:
            reallocate_votes_to_base(year, cfg, weight=weight, save_outputs=True)
        except Exception as e:
            logger.error(f"Failed to harmonize year {year}: {e}", exc_info=True)

    logger.info("Harmonization complete for all years")

    # Also save base year data in same format
    logger.info(f"Saving base year {base_year} data...")
    _save_base_year_data(cfg)


def _save_base_year_data(cfg: dict[str, Any]) -> None:
    """
    Save base year data in harmonized format (no crosswalk needed).

    Args:
        cfg: Configuration dictionary
    """
    base_year = str(cfg["base_year"])
    target_crs = cfg["crs"]

    # Load base shapefile and results
    base_shp_path = cfg["paths"]["shapefiles"][base_year]
    base_csv_path = cfg["paths"]["results_csv"][base_year]
    base_id = cfg["id_fields"][base_year]

    base_gdf = load_shapefile(base_shp_path, target_crs)
    results_df = load_results_csv(base_csv_path, base_id)

    # Merge geometry with results
    base_gdf_slim = base_gdf[[base_id, "geometry"]].copy()
    harmonized_gdf = base_gdf_slim.merge(
        results_df, left_on=base_id, right_on="precinct_id", how="left"
    )

    # Fill missing values
    harmonized_gdf[["D_votes", "R_votes", "total"]] = harmonized_gdf[
        ["D_votes", "R_votes", "total"]
    ].fillna(0)

    # Add year and D_share
    harmonized_gdf["year"] = base_year
    harmonized_gdf["D_share"] = harmonized_gdf["D_votes"] / harmonized_gdf["total"]
    harmonized_gdf["D_share"] = harmonized_gdf["D_share"].fillna(0)

    # Save to GeoPackage
    gpkg_path = Path(cfg["output"]["harmonized_gpkg"])
    layer_name = f"yr_{base_year}_on_{base_year}"
    harmonized_gdf.to_file(gpkg_path, layer=layer_name, driver="GPKG")
    logger.info(f"Saved base year GeoPackage layer '{layer_name}' to {gpkg_path}")

    # Save CSV
    csv_path = gpkg_path.parent / f"harmonized_{base_year}_on_{base_year}.csv"
    harmonized_gdf[[base_id, "year", "D_votes", "R_votes", "total", "D_share"]].to_csv(
        csv_path, index=False
    )
    logger.info(f"Saved base year CSV to {csv_path}")

