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
CD7_RESULTS_CSV = RAW_DIR / "results_2025_columbus_cd7.csv"
SHAPEFILE_2025 = RAW_DIR / "precincts_2025" / "VotingPrecinct.shp"
OUTPUT_GEOJSON = PROCESSED_CARTOGRAM_DIR / "results_2025_turnout.geojson"


def main() -> None:
    if not TURNOUT_CSV.exists():
        raise FileNotFoundError(
            f"Turnout CSV not found: {TURNOUT_CSV}. Run scripts/extract_turnout_2025.py first."
        )

    if not CD7_RESULTS_CSV.exists():
        raise FileNotFoundError(
            f"City council results not found: {CD7_RESULTS_CSV}."
        )

    if not SHAPEFILE_2025.exists():
        raise FileNotFoundError(
            "2025 precinct shapefile not found. Ensure VotingPrecinct.shp is present under data/raw/precincts_2025/."
        )

    turnout_df = pd.read_csv(TURNOUT_CSV)
    results_df = pd.read_csv(CD7_RESULTS_CSV)

    turnout_df = turnout_df.rename(
        columns={
            "D_votes": "ballots_cast",
            "R_votes": "non_voters_calc"
        }
    )

    results_df = results_df.rename(
        columns={
            "D_votes": "vogel_votes",
            "R_votes": "ross_votes"
        }
    )
    results_df["total_votes"] = results_df[["vogel_votes", "ross_votes"]].sum(axis=1)
    results_df = results_df[results_df["total_votes"] > 0]
    results_df["vogel_share"] = results_df["vogel_votes"] / results_df["total_votes"]

    shp_gdf = gpd.read_file(SHAPEFILE_2025)

    if "NAME" not in shp_gdf.columns:
        raise ValueError("Shapefile does not contain NAME column for precinct names.")

    merged = shp_gdf.merge(turnout_df, left_on="NAME", right_on="PRECINCT", how="inner")
    # Left merge with CD7 results so we get all precincts, not just Columbus
    merged = merged.merge(results_df[["PRECINCT", "vogel_votes", "ross_votes", "vogel_share", "total_votes"]],
                          on="PRECINCT",
                          how="left")

    if merged.empty:
        raise ValueError("Merge between shapefile, turnout, and results CSV produced no records.")

    # For precincts without CD7 data, vogel_share will be NaN - use neutral 0.5
    merged["vogel_share"] = merged["vogel_share"].fillna(0.5)
    merged["vogel_votes"] = merged["vogel_votes"].fillna(0)
    merged["ross_votes"] = merged["ross_votes"].fillna(0)
    
    # Ensure ballots and registered are positive
    if merged["registered"].le(0).any():
        merged.loc[merged["registered"].le(0), "registered"] = 1
    if merged["ballots"].le(0).any():
        merged.loc[merged["ballots"].le(0), "ballots"] = 1
    
    merged["non_voters"] = merged["registered"] - merged["ballots"]
    merged.loc[merged["non_voters"] < 0, "non_voters"] = 0
    merged["turnout_share"] = merged["ballots"] / merged["registered"].replace({0: pd.NA})
    merged["turnout_share"] = merged["turnout_share"].fillna(0)

    if merged.crs is None:
        merged = merged.set_crs("EPSG:3735")

    carto_gdf = Cartogram(merged, "ballots", max_iterations=8)
    carto_gdf = carto_gdf.to_crs("EPSG:4326")

    carto_gdf["vogel_share_pct"] = carto_gdf["vogel_share"].astype(float) * 100
    carto_gdf["turnout_pct"] = carto_gdf["turnout_share"].astype(float) * 100

    PROCESSED_CARTOGRAM_DIR.mkdir(parents=True, exist_ok=True)
    carto_gdf.to_file(OUTPUT_GEOJSON, driver="GeoJSON")

    total_ballots = int(carto_gdf["ballots"].sum())
    registered = int(carto_gdf["registered"].sum())
    total_vogel = int(carto_gdf["vogel_votes"].sum())
    total_ross = int(carto_gdf["ross_votes"].sum())
    turnout_pct = 100 * total_ballots / registered if registered else 0
    vogel_pct = 100 * total_vogel / total_ballots if total_ballots else 0

    print(
        "Created", OUTPUT_GEOJSON.relative_to(PROJECT_ROOT),
        f"with {len(carto_gdf):,} precincts (turnout {turnout_pct:.1f}% | {total_ballots:,} ballots)"
        f" and Vogel share {vogel_pct:.1f}% ({total_vogel:,} vs {total_ross:,})."
    )


if __name__ == "__main__":
    main()
