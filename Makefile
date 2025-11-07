.PHONY: help setup lint test demo clean

help:
	@echo "Franklin Shifts - Makefile targets:"
	@echo "  setup    - Create venv and install dependencies"
	@echo "  lint     - Run black and ruff formatters"
	@echo "  test     - Run pytest test suite"
	@echo "  demo     - Run pipeline on synthetic example data"
	@echo "  clean    - Remove temporary files and caches"

setup:
	python3.11 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	@echo "Activated venv with: source .venv/bin/activate"

lint:
	black src/ tests/
	ruff check src/ tests/ --fix

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

demo:
	python -m src.cli demo

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ build/ dist/


