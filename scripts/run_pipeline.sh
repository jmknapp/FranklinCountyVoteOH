#!/bin/bash
# Complete pipeline runner for Franklin Shifts
# Usage: ./scripts/run_pipeline.sh [config_path]

set -e  # Exit on error

CONFIG_PATH="${1:-config/project.yaml}"

echo "=================================="
echo "Franklin Shifts - Pipeline Runner"
echo "=================================="
echo "Config: $CONFIG_PATH"
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Step 1: Initialize
echo "Step 1/5: Initializing..."
python -m src.cli init --config "$CONFIG_PATH"

# Step 2: Harmonize all years
echo ""
echo "Step 2/5: Harmonizing all years to base geography..."
python -m src.cli harmonize-all --config "$CONFIG_PATH"

# Step 3: Compute metrics
echo ""
echo "Step 3/5: Computing metrics..."
python -m src.cli metrics --config "$CONFIG_PATH"

# Step 4: Create maps
echo ""
echo "Step 4/5: Creating visualizations..."
# Get base year from config
BASE_YEAR=$(python -c "import yaml; print(yaml.safe_load(open('$CONFIG_PATH'))['base_year'])")

python -m src.cli maps "$BASE_YEAR" D_share --config "$CONFIG_PATH"
python -m src.cli maps "$BASE_YEAR" swing_vs_2008 --config "$CONFIG_PATH" || true  # May fail if 2008 doesn't exist

# Step 5: Summary
echo ""
echo "Step 5/5: Generating summary..."
python -m src.cli summary --config "$CONFIG_PATH"

echo ""
echo "=================================="
echo "Pipeline complete!"
echo "=================================="
echo "Outputs:"
echo "  - GeoPackage: data/processed/harmonized.gpkg"
echo "  - Time series: data/processed/timeseries_per_precinct.csv"
echo "  - County aggregates: data/processed/county_aggregates.csv"
echo "  - Maps: data/processed/maps/"
echo "  - Interactive: data/processed/interactive/"
echo "=================================="

