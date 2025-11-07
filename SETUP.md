# Python Virtual Environment Setup

## Quick Start (For ksh shell)

```bash
# Navigate to project directory
cd /home/jmknapp/fcvote

# Create virtual environment
python3.11 -m venv .venv

# Activate virtual environment (ksh)
. .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installation
python -m src.cli --help
```

## Step-by-Step Guide

### 1. Check Python Version

```bash
python3.11 --version
```

Should show: `Python 3.11.x` or higher

If not installed:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv

# Or check what's available
python3 --version
```

### 2. Create Virtual Environment

From the project root directory:

```bash
cd /home/jmknapp/fcvote
python3.11 -m venv .venv
```

This creates a `.venv/` directory with an isolated Python environment.

### 3. Activate Virtual Environment

**For ksh (your shell):**
```bash
. .venv/bin/activate
```

**For bash/zsh (alternative):**
```bash
source .venv/bin/activate
```

**You'll know it worked when:**
- Your prompt shows `(.venv)` at the beginning
- Running `which python` shows `.venv/bin/python`

### 4. Upgrade pip

```bash
pip install --upgrade pip
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs all required packages:
- geopandas, pandas, shapely (geospatial)
- matplotlib, folium (visualization)
- typer, rich (CLI)
- pytest, black, ruff (development)
- openpyxl (Excel support)

**Installation takes:** 2-5 minutes

### 6. Verify Installation

```bash
# Check CLI works
python -m src.cli --help

# Or if installed as script
ffs --help

# Check key imports
python -c "import geopandas; import pandas; import shapely; print('✓ All imports successful')"
```

## Common Issues & Solutions

### Issue: "python3.11: command not found"

**Solution:** Use available Python version
```bash
# Check what's available
python3 --version

# If 3.11+, use it
python3 -m venv .venv
```

Minimum requirement: Python 3.11

### Issue: "No module named 'venv'"

**Solution:** Install venv package
```bash
# Ubuntu/Debian
sudo apt install python3.11-venv

# Or
sudo apt install python3-venv
```

### Issue: Activation doesn't work in ksh

**Solution:** Use dot notation
```bash
# Use this (ksh)
. .venv/bin/activate

# Not this
source .venv/bin/activate
```

### Issue: "pip: command not found" after activation

**Solution:** Use python -m pip
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Issue: GDAL/spatial library errors

**Solution:** Install system dependencies first
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    libgeos-dev \
    libproj-dev \
    libspatialindex-dev \
    gdal-bin \
    python3-gdal

# Then retry pip install
pip install -r requirements.txt
```

### Issue: Permission errors during pip install

**Solution:** Don't use sudo with virtual environment
```bash
# Wrong
sudo pip install -r requirements.txt

# Correct (venv active)
pip install -r requirements.txt
```

## Using the Virtual Environment

### Every Time You Work on the Project

```bash
# Navigate to project
cd /home/jmknapp/fcvote

# Activate virtual environment
. .venv/bin/activate

# Now you can run commands
ffs init
python -m src.cli harmonize-all
pytest tests/

# When done, deactivate
deactivate
```

### Adding to Your Shell Profile (Optional)

Add this alias to `~/.kshrc` or `~/.profile`:

```bash
alias fcvote='cd /home/jmknapp/fcvote && . .venv/bin/activate'
```

Then just type:
```bash
fcvote
```

## Using the Makefile (Alternative)

The project includes a Makefile for convenience:

```bash
# Create venv and install dependencies
make setup

# Run linter
make lint

# Run tests
make test

# Run demo
make demo

# Clean temporary files
make clean
```

Note: `make setup` creates the venv but you still need to activate it manually.

## Verification Checklist

Run these to verify everything is set up:

```bash
# 1. Virtual environment is active
echo $VIRTUAL_ENV
# Should show: /home/jmknapp/fcvote/.venv

# 2. Python is from venv
which python
# Should show: /home/jmknapp/fcvote/.venv/bin/python

# 3. Packages installed
pip list | grep geopandas
pip list | grep pandas
pip list | grep shapely

# 4. CLI works
python -m src.cli --help
# Should show Franklin Shifts help

# 5. Import test
python -c "from src import cli, crosswalk, harmonize; print('✓ Imports OK')"
```

## Package List

After installation, you should have these key packages:

```
geopandas    >= 0.14.0
pandas       >= 2.1.0
shapely      >= 2.0.0
pyproj       >= 3.6.0
matplotlib   >= 3.8.0
folium       >= 0.15.0
typer        >= 0.9.0
pytest       >= 7.4.0
black        >= 23.0.0
ruff         >= 0.1.0
openpyxl     >= 3.1.0
```

Check with:
```bash
pip list
```

## Updating Dependencies

If dependencies are updated:

```bash
# Activate venv
. .venv/bin/activate

# Update all packages
pip install --upgrade -r requirements.txt

# Or update specific package
pip install --upgrade geopandas
```

## Recreating Virtual Environment

If something goes wrong:

```bash
# Deactivate if active
deactivate

# Remove old venv
rm -rf .venv

# Create new venv
python3.11 -m venv .venv

# Activate
. .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## IDE Setup (Optional)

### VS Code

1. Open project: `code /home/jmknapp/fcvote`
2. Select interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
3. Choose: `.venv/bin/python`

### PyCharm

1. Open project
2. Settings → Project → Python Interpreter
3. Add → Existing Environment
4. Select: `/home/jmknapp/fcvote/.venv/bin/python`

## Quick Commands Summary

```bash
# Setup (one time)
cd /home/jmknapp/fcvote
python3.11 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Daily use
cd /home/jmknapp/fcvote
. .venv/bin/activate
# ... work on project ...
deactivate

# Verify
python -m src.cli --help
pytest tests/ -v

# Update
pip install --upgrade -r requirements.txt
```

## Need Help?

- **Python venv docs:** https://docs.python.org/3/library/venv.html
- **pip documentation:** https://pip.pypa.io/
- **GeoPandas install:** https://geopandas.org/en/stable/getting_started/install.html

---

**Next Steps After Setup:**
1. Verify with: `python -m src.cli init`
2. Try demo: `python -m src.cli demo`
3. Download BOE results and start preprocessing!

