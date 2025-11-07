#!/bin/bash
# Quick installation script for Franklin Shifts
# Usage: bash INSTALL.sh

set -e

echo "=========================================="
echo "Franklin Shifts - Installation"
echo "=========================================="
echo ""

# Check Python version
echo "Step 1: Checking Python version..."
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo "✓ Found python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if (( $(echo "$PYTHON_VERSION >= 3.11" | bc -l) )); then
        PYTHON_CMD="python3"
        echo "✓ Found Python $PYTHON_VERSION"
    else
        echo "✗ Python 3.11+ required, found $PYTHON_VERSION"
        echo "Please install Python 3.11 or higher"
        exit 1
    fi
else
    echo "✗ Python not found"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

# Create virtual environment
echo ""
echo "Step 2: Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "⚠ Virtual environment already exists at .venv/"
    read -p "Remove and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf .venv
        $PYTHON_CMD -m venv .venv
        echo "✓ Virtual environment recreated"
    else
        echo "Keeping existing virtual environment"
    fi
else
    $PYTHON_CMD -m venv .venv
    echo "✓ Virtual environment created"
fi

# Detect shell and show activation command
echo ""
echo "Step 3: Activating virtual environment..."
if [ -n "$KSH_VERSION" ]; then
    echo "Detected ksh shell"
    ACTIVATE_CMD=". .venv/bin/activate"
else
    ACTIVATE_CMD="source .venv/bin/activate"
fi

# Activate (works in bash/ksh when sourced)
if [ -f ".venv/bin/activate" ]; then
    . .venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "✗ Could not find activation script"
    exit 1
fi

# Upgrade pip
echo ""
echo "Step 4: Upgrading pip..."
python -m pip install --upgrade pip -q
echo "✓ pip upgraded"

# Install dependencies
echo ""
echo "Step 5: Installing dependencies..."
echo "(This may take 2-5 minutes...)"
pip install -r requirements.txt -q
echo "✓ Dependencies installed"

# Verify installation
echo ""
echo "Step 6: Verifying installation..."
python -m src.cli --help > /dev/null 2>&1 && echo "✓ CLI working" || echo "✗ CLI test failed"
python -c "import geopandas; import pandas; import shapely" && echo "✓ Core imports working" || echo "✗ Import test failed"

# Summary
echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Virtual environment created at: .venv/"
echo ""
echo "To activate the virtual environment:"
echo "  $ACTIVATE_CMD"
echo ""
echo "To verify installation:"
echo "  python -m src.cli --help"
echo ""
echo "To run demo:"
echo "  python -m src.cli demo"
echo ""
echo "Next steps:"
echo "  1. Download election results from Franklin County BOE"
echo "  2. Save to: data/raw/boe_downloads/"
echo "  3. Run preprocessing script"
echo "  4. Run pipeline with: python -m src.cli harmonize-all"
echo ""
echo "See SETUP.md for detailed instructions"
echo "=========================================="

