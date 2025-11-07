"""Build spatial crosswalks between different precinct vintages."""

import logging
from typing import Optional

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon
from tqdm import tqdm

logger = logging.getLogger(__name__)


def build_crosswalk(
    past_gdf: gpd.GeoDataFrame,
    base_gdf: gpd.GeoDataFrame,
    past_id: str,
    base_id: str,
    weight: str = "area",
    blocks_gdf: Optional[gpd.GeoDataFrame] = None,
    block_pop_field: Optional[str] = None,
    sliver_tolerance: float = 1e-9,
) -> pd.DataFrame:
    """
    Build a spatial crosswalk from past geography to base geography.

    Computes overlap weights to reallocate data from past precincts to base precincts.

    Args:
        past_gdf: Historical precinct boundaries
        base_gdf: Base (target) precinct boundaries
        past_id: Column name for past precinct IDs
        base_id: Column name for base precinct IDs
        weight: Weighting method - "area" (default) or "pop"
        blocks_gdf: Census blocks GeoDataFrame (required if weight="pop")
        block_pop_field: Population field in blocks_gdf (required if weight="pop")
        sliver_tolerance: Minimum area threshold for intersection slivers

    Returns:
        DataFrame with columns [past_id, base_id, frac] where frac is the allocation weight

    Raises:
        ValueError: If CRS don't match or required fields missing
    """
    from .io_utils import ensure_crs_match, ensure_id_consistency

    # Validate inputs
    ensure_crs_match(past_gdf, base_gdf)

    if past_id not in past_gdf.columns:
        raise ValueError(f"Column '{past_id}' not found in past_gdf")
    if base_id not in base_gdf.columns:
        raise ValueError(f"Column '{base_id}' not found in base_gdf")

    if weight not in ["area", "pop"]:
        raise ValueError(f"Invalid weight method: {weight}. Must be 'area' or 'pop'")

    if weight == "pop" and (blocks_gdf is None or block_pop_field is None):
        raise ValueError("Population weighting requires blocks_gdf and block_pop_field")

    logger.info(
        f"Building crosswalk: {len(past_gdf)} past precincts → "
        f"{len(base_gdf)} base precincts (weight={weight})"
    )

    # Normalize IDs
    past_gdf = past_gdf.copy()
    base_gdf = base_gdf.copy()
    past_gdf[past_id] = ensure_id_consistency(past_gdf[past_id])
    base_gdf[base_id] = ensure_id_consistency(base_gdf[base_id])

    if weight == "area":
        return _build_area_crosswalk(
            past_gdf, base_gdf, past_id, base_id, sliver_tolerance
        )
    else:
        return _build_population_crosswalk(
            past_gdf, base_gdf, past_id, base_id, blocks_gdf, block_pop_field, sliver_tolerance
        )


def _build_area_crosswalk(
    past_gdf: gpd.GeoDataFrame,
    base_gdf: gpd.GeoDataFrame,
    past_id: str,
    base_id: str,
    sliver_tolerance: float,
) -> pd.DataFrame:
    """
    Build area-weighted crosswalk using spatial overlay.

    Args:
        past_gdf: Historical precinct boundaries
        base_gdf: Base precinct boundaries
        past_id: Past precinct ID column
        base_id: Base precinct ID column
        sliver_tolerance: Minimum area threshold

    Returns:
        Crosswalk DataFrame with [past_id, base_id, frac]
    """
    logger.info("Computing area-weighted overlay (this may take a while)...")

    # Compute original areas for past precincts
    past_gdf = past_gdf.copy()
    past_gdf["_orig_area"] = past_gdf.geometry.area

    # Use spatial index for efficient overlay
    logger.debug("Building spatial index...")
    base_gdf.sindex  # Force spatial index creation

    # Perform overlay intersection
    logger.debug("Performing spatial intersection...")
    overlay = gpd.overlay(
        past_gdf[[past_id, "geometry", "_orig_area"]],
        base_gdf[[base_id, "geometry"]],
        how="intersection",
        keep_geom_type=False,
    )

    if overlay.empty:
        logger.warning("Overlay resulted in no intersections!")
        return pd.DataFrame(columns=[past_id, base_id, "frac"])

    # Compute intersection areas
    overlay["_intersect_area"] = overlay.geometry.area

    # Filter out slivers
    overlay = overlay[overlay["_intersect_area"] > sliver_tolerance]

    # Compute allocation fractions
    overlay["frac"] = overlay["_intersect_area"] / overlay["_orig_area"]

    # Validate coverage
    coverage = overlay.groupby(past_id)["frac"].sum()
    low_coverage = coverage[coverage < 0.98]
    if not low_coverage.empty:
        logger.warning(
            f"{len(low_coverage)} past precincts have < 98% spatial coverage. "
            f"Min coverage: {coverage.min():.2%}"
        )

    # Create final crosswalk
    crosswalk = overlay[[past_id, base_id, "frac"]].copy()

    # Normalize fractions to sum to 1.0 per past precinct (to handle edge effects)
    frac_sums = crosswalk.groupby(past_id)["frac"].transform("sum")
    crosswalk["frac"] = crosswalk["frac"] / frac_sums

    logger.info(f"Created crosswalk with {len(crosswalk)} mappings")

    return crosswalk


def _build_population_crosswalk(
    past_gdf: gpd.GeoDataFrame,
    base_gdf: gpd.GeoDataFrame,
    past_id: str,
    base_id: str,
    blocks_gdf: gpd.GeoDataFrame,
    block_pop_field: str,
    sliver_tolerance: float,
) -> pd.DataFrame:
    """
    Build population-weighted crosswalk using census blocks.

    Args:
        past_gdf: Historical precinct boundaries
        base_gdf: Base precinct boundaries
        past_id: Past precinct ID column
        base_id: Base precinct ID column
        blocks_gdf: Census blocks with population
        block_pop_field: Population column in blocks_gdf
        sliver_tolerance: Minimum area threshold

    Returns:
        Crosswalk DataFrame with [past_id, base_id, frac]
    """
    from .io_utils import ensure_crs_match

    logger.info("Computing population-weighted crosswalk using census blocks...")

    # Ensure all layers have same CRS
    ensure_crs_match(past_gdf, blocks_gdf)
    ensure_crs_match(base_gdf, blocks_gdf)

    # Prepare blocks
    blocks_gdf = blocks_gdf.copy()
    blocks_gdf["_block_id"] = range(len(blocks_gdf))
    blocks_gdf["_pop"] = pd.to_numeric(blocks_gdf[block_pop_field], errors="coerce").fillna(0)

    # First overlay: blocks → past precincts
    logger.debug("Overlaying blocks with past precincts...")
    blocks_past = gpd.overlay(
        blocks_gdf[["_block_id", "_pop", "geometry"]],
        past_gdf[[past_id, "geometry"]],
        how="intersection",
    )
    blocks_past = blocks_past[blocks_past.geometry.area > sliver_tolerance]

    # Allocate block population to past precincts based on area fraction
    block_areas = blocks_gdf.set_index("_block_id").geometry.area
    blocks_past["_block_orig_area"] = blocks_past["_block_id"].map(block_areas)
    blocks_past["_intersect_area"] = blocks_past.geometry.area
    blocks_past["_area_frac"] = (
        blocks_past["_intersect_area"] / blocks_past["_block_orig_area"]
    )
    blocks_past["_allocated_pop"] = blocks_past["_pop"] * blocks_past["_area_frac"]

    # Second overlay: blocks → base precincts
    logger.debug("Overlaying blocks with base precincts...")
    blocks_base = gpd.overlay(
        blocks_gdf[["_block_id", "_pop", "geometry"]],
        base_gdf[[base_id, "geometry"]],
        how="intersection",
    )
    blocks_base = blocks_base[blocks_base.geometry.area > sliver_tolerance]

    # Allocate block population to base precincts
    blocks_base["_block_orig_area"] = blocks_base["_block_id"].map(block_areas)
    blocks_base["_intersect_area"] = blocks_base.geometry.area
    blocks_base["_area_frac"] = blocks_base["_intersect_area"] / blocks_base["_block_orig_area"]
    blocks_base["_allocated_pop"] = blocks_base["_pop"] * blocks_base["_area_frac"]

    # Build mapping: for each past-base pair, sum population from shared blocks
    logger.debug("Computing population flows between past and base precincts...")

    # Aggregate population by past precinct and block
    past_block_pop = (
        blocks_past.groupby([past_id, "_block_id"])["_allocated_pop"].sum().reset_index()
    )
    past_block_pop.columns = [past_id, "_block_id", "_past_pop"]

    # Aggregate population by base precinct and block
    base_block_pop = (
        blocks_base.groupby([base_id, "_block_id"])["_allocated_pop"].sum().reset_index()
    )
    base_block_pop.columns = [base_id, "_block_id", "_base_pop"]

    # Join on block ID to find past-base pairs
    crosswalk_blocks = past_block_pop.merge(base_block_pop, on="_block_id", how="inner")

    # For each past-base pair, population flow is minimum of past and base allocations
    # (conservative approach to avoid double-counting)
    crosswalk_blocks["_pop_flow"] = crosswalk_blocks[["_past_pop", "_base_pop"]].min(axis=1)

    # Aggregate by past-base pairs
    crosswalk = (
        crosswalk_blocks.groupby([past_id, base_id])["_pop_flow"].sum().reset_index()
    )
    crosswalk.columns = [past_id, base_id, "_pop"]

    # Compute fractions: each past precinct's population allocated to base precincts
    total_pop_by_past = crosswalk.groupby(past_id)["_pop"].transform("sum")
    crosswalk["frac"] = crosswalk["_pop"] / total_pop_by_past

    # Drop population column
    crosswalk = crosswalk[[past_id, base_id, "frac"]]

    # Check coverage
    coverage = crosswalk.groupby(past_id)["frac"].sum()
    low_coverage = coverage[coverage < 0.98]
    if not low_coverage.empty:
        logger.warning(
            f"{len(low_coverage)} past precincts have < 98% population coverage. "
            f"Min coverage: {coverage.min():.2%}"
        )

    logger.info(f"Created population-weighted crosswalk with {len(crosswalk)} mappings")

    return crosswalk


def validate_crosswalk(crosswalk: pd.DataFrame, past_id: str) -> dict:
    """
    Validate crosswalk quality and return diagnostic statistics.

    Args:
        crosswalk: Crosswalk DataFrame with [past_id, base_id, frac]
        past_id: Past precinct ID column name

    Returns:
        Dictionary with validation statistics
    """
    stats = {}

    # Check fraction sums
    frac_sums = crosswalk.groupby(past_id)["frac"].sum()
    stats["n_past_precincts"] = len(frac_sums)
    stats["mean_coverage"] = frac_sums.mean()
    stats["min_coverage"] = frac_sums.min()
    stats["n_incomplete"] = (frac_sums < 0.98).sum()

    # Check splits
    n_splits = crosswalk.groupby(past_id).size()
    stats["mean_splits"] = n_splits.mean()
    stats["max_splits"] = n_splits.max()
    stats["n_one_to_one"] = (n_splits == 1).sum()

    logger.info(f"Crosswalk validation: {stats}")

    return stats

