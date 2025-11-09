#!/usr/bin/env python3
"""Generate a turnout cartogram for the 2025 election."""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
from cartogram import Cartogram

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_CARTOGRAM_DIR = PROJECT_ROOT / "data" / "processed" / "cartograms"
TURNOUT_CSV = RAW_DIR / "results_2025_turnout.csv"
SHAPEFILE_2025 = RAW_DIR / "precincts_2025" / "VotingPrecinct.shp"
OUTPUT_GEOJSON = PROCESSED_CARTOGRAM_DIR / "results_2025_turnout.geojson"


def main() -> None:
    if not TURNOUT_CSV.exists():
        raise FileNotFoundError(
            f"Turnout CSV not found: {TURNOUT_CSV}. Run scripts/extract_turnout_2025.py first."
        )

    if not SHAPEFILE_2025.exists():
        raise FileNotFoundError(
            "2025 precinct shapefile not found. Ensure VotingPrecinct.shp is present under data/raw/precincts_2025/."
        )

    turnout_df = pd.read_csv(TURNOUT_CSV)
    shp_gdf = gpd.read_file(SHAPEFILE_2025)

    if "NAME" not in shp_gdf.columns:
        raise ValueError("Shapefile does not contain NAME column for precinct names.")

    merged = shp_gdf.merge(turnout_df, left_on="NAME", right_on="PRECINCT", how="inner")

    if merged.empty:
        raise ValueError("Merge between shapefile and turnout CSV produced no records.")

    if merged["ballots"].le(0).any():
        merged.loc[merged["ballots"].le(0), "ballots"] = 1

    if merged.crs is None:
        merged = merged.set_crs("EPSG:3735")

    carto_gdf = Cartogram(merged, "ballots", max_iterations=8)
    carto_gdf = carto_gdf.to_crs("EPSG:4326")

    carto_gdf["turnout_pct"] = carto_gdf["turnout_share"].astype(float) * 100

    PROCESSED_CARTOGRAM_DIR.mkdir(parents=True, exist_ok=True)
    carto_gdf.to_file(OUTPUT_GEOJSON, driver="GeoJSON")

    total_ballots = int(carto_gdf["ballots"].sum())
    registered = int(carto_gdf["registered"].sum())
    turnout_pct = 100 * total_ballots / registered if registered else 0

    print(
        "Created", OUTPUT_GEOJSON.relative_to(PROJECT_ROOT),
        f"with {len(carto_gdf):,} precincts (overall turnout {turnout_pct:.1f}% | {total_ballots:,} ballots)."
    )


if __name__ == "__main__":
    main()
