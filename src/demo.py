"""Generate synthetic example data for testing and demos."""

import logging
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

logger = logging.getLogger(__name__)


def generate_synthetic_example() -> dict[str, Any]:
    """
    Generate synthetic precinct data for testing.

    Creates simple rectangular precincts with different configurations
    across years to test crosswalk functionality.

    Returns:
        Configuration dictionary for demo data
    """
    logger.info("Generating synthetic example data...")

    # Setup paths
    base_dir = Path("data/examples")
    base_dir.mkdir(parents=True, exist_ok=True)

    raw_dir = base_dir / "raw"
    raw_dir.mkdir(exist_ok=True)

    # CRS for synthetic data (use a simple projected CRS)
    crs = "EPSG:3734"  # NAD83 / Ohio South

    # Generate synthetic years
    years = ["2020", "2022", "2024"]

    config = {
        "base_year": "2024",
        "crs": crs,
        "id_fields": {year: "PREC_ID" for year in years},
        "paths": {"shapefiles": {}, "results_csv": {}},
        "output": {
            "harmonized_gpkg": str(base_dir / "harmonized.gpkg"),
            "timeseries_csv": str(base_dir / "timeseries.csv"),
            "county_aggregates_csv": str(base_dir / "county_aggregates.csv"),
            "maps_dir": str(base_dir / "maps"),
            "interactive_dir": str(base_dir / "interactive"),
            "crosswalk_dir": str(base_dir / "crosswalks"),
        },
        "options": {
            "overlap_warning_threshold": 0.98,
            "sliver_tolerance": 1e-9,
            "default_weight_method": "area",
        },
    }

    # Generate 2024 base geography (4 precincts in 2x2 grid)
    logger.info("Creating 2024 base precincts...")
    precincts_2024 = _create_2x2_grid(base_x=0, base_y=0, cell_size=1000, id_prefix="2024_P")
    precincts_2024["PREC_ID"] = [f"P{i+1}" for i in range(len(precincts_2024))]

    year_dir = raw_dir / "precincts_2024"
    year_dir.mkdir(exist_ok=True)
    shp_path = year_dir / "precincts_2024.shp"
    precincts_2024.to_file(shp_path)
    config["paths"]["shapefiles"]["2024"] = str(shp_path)

    # Generate 2024 results (lean Dem overall)
    results_2024 = pd.DataFrame(
        {
            "PREC_ID": ["P1", "P2", "P3", "P4"],
            "D_votes": [450, 550, 400, 600],
            "R_votes": [350, 250, 400, 300],
        }
    )
    csv_path = raw_dir / "results_2024.csv"
    results_2024.to_csv(csv_path, index=False)
    config["paths"]["results_csv"]["2024"] = str(csv_path)

    # Generate 2022 geography (3 precincts with different boundaries)
    logger.info("Creating 2022 precincts (split differently)...")
    # 2022: vertical split + one large precinct
    geoms_2022 = [
        Polygon([(0, 0), (1000, 0), (1000, 2000), (0, 2000)]),  # Left half
        Polygon([(1000, 0), (2000, 0), (2000, 1000), (1000, 1000)]),  # Top right
        Polygon([(1000, 1000), (2000, 1000), (2000, 2000), (1000, 2000)]),  # Bottom right
    ]
    precincts_2022 = gpd.GeoDataFrame(
        {"PREC_ID": ["P1", "P2", "P3"], "name": ["Left", "TopRight", "BottomRight"]},
        geometry=geoms_2022,
        crs=crs,
    )

    year_dir = raw_dir / "precincts_2022"
    year_dir.mkdir(exist_ok=True)
    shp_path = year_dir / "precincts_2022.shp"
    precincts_2022.to_file(shp_path)
    config["paths"]["shapefiles"]["2022"] = str(shp_path)

    # Generate 2022 results (slightly less Dem)
    results_2022 = pd.DataFrame(
        {
            "PREC_ID": ["P1", "P2", "P3"],
            "D_votes": [800, 500, 550],  # Left, TopRight, BottomRight
            "R_votes": [700, 400, 350],
        }
    )
    csv_path = raw_dir / "results_2022.csv"
    results_2022.to_csv(csv_path, index=False)
    config["paths"]["results_csv"]["2022"] = str(csv_path)

    # Generate 2020 geography (2 precincts - horizontal split)
    logger.info("Creating 2020 precincts (horizontal split)...")
    geoms_2020 = [
        Polygon([(0, 0), (2000, 0), (2000, 1000), (0, 1000)]),  # Top
        Polygon([(0, 1000), (2000, 1000), (2000, 2000), (0, 2000)]),  # Bottom
    ]
    precincts_2020 = gpd.GeoDataFrame(
        {"PREC_ID": ["P1", "P2"], "name": ["Top", "Bottom"]},
        geometry=geoms_2020,
        crs=crs,
    )

    year_dir = raw_dir / "precincts_2020"
    year_dir.mkdir(exist_ok=True)
    shp_path = year_dir / "precincts_2020.shp"
    precincts_2020.to_file(shp_path)
    config["paths"]["shapefiles"]["2020"] = str(shp_path)

    # Generate 2020 results (even more competitive)
    results_2020 = pd.DataFrame(
        {
            "PREC_ID": ["P1", "P2"],
            "D_votes": [900, 850],
            "R_votes": [800, 850],
        }
    )
    csv_path = raw_dir / "results_2020.csv"
    results_2020.to_csv(csv_path, index=False)
    config["paths"]["results_csv"]["2020"] = str(csv_path)

    # Save demo config
    import yaml

    config_path = base_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    logger.info(f"Synthetic example data generated in {base_dir}")
    logger.info(f"  2024 (base): 4 precincts (2x2 grid)")
    logger.info(f"  2022: 3 precincts (different boundaries)")
    logger.info(f"  2020: 2 precincts (horizontal split)")

    return config


def _create_2x2_grid(
    base_x: float, base_y: float, cell_size: float, id_prefix: str
) -> gpd.GeoDataFrame:
    """Create a 2x2 grid of square polygons."""
    polygons = []
    ids = []

    for i in range(2):
        for j in range(2):
            x0 = base_x + j * cell_size
            y0 = base_y + i * cell_size
            x1 = x0 + cell_size
            y1 = y0 + cell_size

            poly = Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
            polygons.append(poly)
            ids.append(f"{id_prefix}_{i}_{j}")

    gdf = gpd.GeoDataFrame(
        {"id": ids, "name": [f"Cell_{i}" for i in range(len(polygons))]},
        geometry=polygons,
        crs="EPSG:3734",
    )

    return gdf

