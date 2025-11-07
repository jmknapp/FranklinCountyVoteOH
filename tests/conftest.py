"""Pytest configuration and shared fixtures."""

import logging
import sys
from pathlib import Path

import pytest

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging for tests
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise during tests
    format="%(levelname)s - %(name)s - %(message)s",
)


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory):
    """Create a temporary directory for test data."""
    return tmp_path_factory.mktemp("test_data")

