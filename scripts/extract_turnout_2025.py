#!/usr/bin/env python3
"""Extract 2025 turnout (ballots / registered) from the BOE Excel export."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = ROOT / "data" / "raw" / "boe_downloads" / "2025general.xlsx"
OUTPUT_PATH = ROOT / "data" / "raw" / "results_2025_turnout.csv"


def main() -> None:
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(
            f"Input Excel file not found: {EXCEL_PATH}. Ensure the 2025 general "
            "election file is downloaded into data/raw/boe_downloads/."
        )

    df = pd.read_excel(EXCEL_PATH, sheet_name=0)

    required_cols = [
        "PRECINCT NAME",
        "REGISTERED VOTERS TOTAL",
        "BALLOTS CAST TOTAL",
    ]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns in Excel file: {missing}")

    turnout = df[required_cols].copy()
    turnout = turnout.dropna(subset=["PRECINCT NAME"]).copy()
    turnout["REGISTERED VOTERS TOTAL"] = (
        pd.to_numeric(turnout["REGISTERED VOTERS TOTAL"], errors="coerce")
        .fillna(0)
        .astype(int)
    )
    turnout["BALLOTS CAST TOTAL"] = (
        pd.to_numeric(turnout["BALLOTS CAST TOTAL"], errors="coerce")
        .fillna(0)
        .astype(int)
    )
    turnout = turnout[turnout["REGISTERED VOTERS TOTAL"] > 0]

    turnout["non_voters"] = (
        turnout["REGISTERED VOTERS TOTAL"] - turnout["BALLOTS CAST TOTAL"]
    ).clip(lower=0)
    turnout["turnout_share"] = (
        turnout["BALLOTS CAST TOTAL"] / turnout["REGISTERED VOTERS TOTAL"]
    )

    turnout = turnout.rename(
        columns={
            "PRECINCT NAME": "PRECINCT",
            "REGISTERED VOTERS TOTAL": "registered",
            "BALLOTS CAST TOTAL": "ballots",
        }
    )
    turnout["D_votes"] = turnout["ballots"]
    turnout["R_votes"] = turnout["non_voters"]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    turnout[
        [
            "PRECINCT",
            "D_votes",
            "R_votes",
            "registered",
            "ballots",
            "non_voters",
            "turnout_share",
        ]
    ].to_csv(OUTPUT_PATH, index=False)

    print(
        f"Wrote {len(turnout):,} precincts to {OUTPUT_PATH.relative_to(ROOT)} "
        f"(overall turnout: {turnout['turnout_share'].mean():.1%})"
    )


if __name__ == "__main__":
    main()
