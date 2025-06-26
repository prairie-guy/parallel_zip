#!/usr/bin/env python3

# conftest.py
import os
from pathlib import Path

# Set test configuration
TEST_DIR = Path("test_data")

def setup_module():
    """Global test setup"""
    print("Setting up parallel_zip tests...")

def teardown_module():
    """Global test cleanup"""
    print("Cleaning up parallel_zip tests...")
