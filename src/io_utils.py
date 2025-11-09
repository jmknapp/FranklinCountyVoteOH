"""I/O utilities for loading shapefiles, CSVs, and managing data consistency."""

import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd
from pyproj import CRS

logger = logging.getLogger(__name__)


def load_shapefile(path: str | Path, target_crs: str) -> gpd.GeoDataFrame:
    """
    Load a shapefile and reproject to target CRS.

    Args:
        path: Path to shapefile
        target_crs: Target coordinate reference system (e.g., "EPSG:3734")

    Returns:
        GeoDataFrame reprojected to target CRS

    Raises:
        FileNotFoundError: If shapefile doesn't exist
        ValueError: If geometry is invalid
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Shapefile not found: {path}")

    logger.info(f"Loading shapefile: {path}")
    try:
        gdf = gpd.read_file(path)
    except Exception as e:
        raise ValueError(f"Failed to read shapefile {path}: {e}")

    if gdf.empty:
        raise ValueError(f"Shapefile is empty: {path}")

    # Reproject to target CRS
    original_crs = gdf.crs
    if original_crs is None:
        logger.warning(f"Shapefile has no CRS defined, assuming {target_crs}")
        gdf = gdf.set_crs(target_crs)
    elif gdf.crs != CRS.from_string(target_crs):
        logger.info(f"Reprojecting from {gdf.crs} to {target_crs}")
        gdf = gdf.to_crs(target_crs)

    # Validate geometries
    invalid_mask = ~gdf.is_valid
    if invalid_mask.any():
        n_invalid = invalid_mask.sum()
        logger.warning(f"Found {n_invalid} invalid geometries, attempting to fix")
        gdf.loc[invalid_mask, "geometry"] = gdf.loc[invalid_mask, "geometry"].buffer(0)

    logger.info(f"Loaded {len(gdf)} features")
    return gdf


def load_results_csv(
    path: str | Path, id_field: str, d_col: str = "D_votes", r_col: str = "R_votes"
) -> pd.DataFrame:
    """
    Load election results CSV with Democratic and Republican vote columns.

    Args:
        path: Path to CSV file
        id_field: Name of precinct ID column
        d_col: Name of Democratic votes column (default: "D_votes")
        r_col: Name of Republican votes column (default: "R_votes")

    Returns:
        DataFrame with columns [precinct_id, D_votes, R_votes, total]

    Raises:
        FileNotFoundError: If CSV doesn't exist
        ValueError: If required columns are missing
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Results CSV not found: {path}")

    logger.info(f"Loading results CSV: {path}")
    try:
        df = pd.read_csv(path, dtype={id_field: str})
    except Exception as e:
        raise ValueError(f"Failed to read CSV {path}: {e}")

    # Verify required columns
    required_cols = [id_field, d_col, r_col]
    missing_cols = set(required_cols) - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"Missing required columns in {path}: {missing_cols}. "
            f"Available columns: {list(df.columns)}"
        )

    # Normalize and create output dataframe
    result = pd.DataFrame()
    result["precinct_id"] = ensure_id_consistency(df[id_field])
    result["D_votes"] = pd.to_numeric(df[d_col], errors="coerce").fillna(0).astype(int)
    result["R_votes"] = pd.to_numeric(df[r_col], errors="coerce").fillna(0).astype(int)
    result["total"] = result["D_votes"] + result["R_votes"]

    # Warn about zero-vote precincts
    zero_mask = result["total"] == 0
    if zero_mask.any():
        n_zero = zero_mask.sum()
        logger.warning(f"Found {n_zero} precincts with zero total votes")

    logger.info(f"Loaded results for {len(result)} precincts")
    return result


def ensure_id_consistency(ids: pd.Series) -> pd.Series:
    """
    Normalize precinct IDs to consistent string format.

    Converts to string, strips whitespace, and converts to uppercase.

    Args:
        ids: Series of precinct IDs

    Returns:
        Series of normalized ID strings
    """
    return ids.astype(str).str.strip().str.upper()


def ensure_crs_match(gdf1: gpd.GeoDataFrame, gdf2: gpd.GeoDataFrame) -> None:
    """
    Assert that two GeoDataFrames have identical CRS.

    Args:
        gdf1: First GeoDataFrame
        gdf2: Second GeoDataFrame

    Raises:
        ValueError: If CRS don't match
    """
    if gdf1.crs != gdf2.crs:
        raise ValueError(
            f"CRS mismatch: gdf1 has {gdf1.crs}, gdf2 has {gdf2.crs}. "
            "Ensure both are reprojected to the same CRS before overlay operations."
        )


def safe_read_csv(path: str | Path, **kwargs) -> pd.DataFrame:
    """
    Safely read CSV with error handling and logging.

    Args:
        path: Path to CSV file
        **kwargs: Additional arguments passed to pd.read_csv

    Returns:
        DataFrame from CSV

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If CSV is malformed
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    try:
        df = pd.read_csv(path, **kwargs)
        logger.debug(f"Read CSV with {len(df)} rows from {path}")
        return df
    except Exception as e:
        raise ValueError(f"Failed to read CSV {path}: {e}")


def ensure_output_dir(path: str | Path) -> Path:
    """
    Ensure output directory exists, creating if necessary.

    Args:
        path: Directory path

    Returns:
        Path object for directory
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured directory exists: {path}")
    return path

