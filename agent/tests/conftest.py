"""Pytest configuration — adds src/ to the Python path for all tests."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
