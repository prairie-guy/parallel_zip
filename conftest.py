#!/usr/bin/env python3
"""
pytest/ward configuration for parallel_zip tests

This file is automatically discovered by pytest and ward test runners.
It provides shared fixtures and configuration for all tests.
"""
import os
import sys
from pathlib import Path

# Ensure parallel_zip can be imported in tests
sys.path.insert(0, str(Path(__file__).parent))

# Test configuration
TEST_DATA_DIR = Path(__file__).parent / "sample_data"

def pytest_configure(config):
    """pytest configuration hook"""
    config.addinivalue_line(
        "markers", "gawk: mark test as requiring GNU AWK"
    )

# Ward doesn't use pytest_configure, but the fixtures in test files handle setup