"""Test suite for MCP Project Orchestrator."""

import pytest
from pathlib import Path

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"

# Ensure test data directory exists
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True) 