#!/usr/bin/env python
"""
Inspect Franklin County precinct shapefiles to determine field names.
Run this after installing dependencies: pip install -r requirements.txt
"""

import sys
from pathlib import Path

import geopandas as gpd


def inspect_shapefile(shp_path):
    """Inspect a shapefile and print its structure."""
    try:
        gdf = gpd.read_file(shp_path)
        return {
            "columns": list(gdf.columns),
            "crs": str(gdf.crs),
            "count": len(gdf),
            "sample": gdf.head(2)[[col for col in gdf.columns if col != "geometry"]],
        }
    except Exception as e:
        return {"error": str(e)}


def main():
    """Inspect all downloaded shapefiles."""
    print("=" * 70)
    print("Franklin County Precinct Shapefiles - Field Inspection")
    print("=" * 70)

    data_dir = Path("data/raw")
    years = [2006, 2008, 2010, 2012, 2014, 2016, 2018, 2020, 2022, 2024]

    for year in years:
        shp_path = data_dir / f"precincts_{year}" / "Voting_Precinct.shp"

        if not shp_path.exists():
            print(f"\n{year}: File not found")
            continue

        print(f"\n{'='*70}")
        print(f"Year: {year}")
        print(f"Path: {shp_path}")
        print("-" * 70)

        info = inspect_shapefile(shp_path)

        if "error" in info:
            print(f"  Error: {info['error']}")
            continue

        print(f"  CRS: {info['crs']}")
        print(f"  Precincts: {info['count']}")
        print(f"  Columns: {', '.join(info['columns'][:-1])}")  # Exclude geometry
        print(f"\n  Sample data:")
        print(info["sample"].to_string(index=False))

    print(f"\n{'='*70}")
    print("\nRecommendation for config/project.yaml:")
    print("  - Look for fields like: PRECINCT, PREC_ID, PRECINCT_ID, NAME")
    print("  - Update id_fields in config/project.yaml with the correct field names")
    print("=" * 70)


if __name__ == "__main__":
    main()

