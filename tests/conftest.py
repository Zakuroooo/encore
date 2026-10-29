"""Shared test setup. Tests that need the built database skip locally if it is missing,
but FAIL in CI (env CI=true), so a missing pipeline run can never look like a pass."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/encore.duckdb"
OUT = ROOT / "outputs"
sys.path.insert(0, str(ROOT / "analysis"))


@pytest.fixture(scope="session")
def db_path():
    if not DB.exists():
        if os.environ.get("CI"):
            pytest.fail("data/encore.duckdb missing in CI: run `python pipeline.py` first")
        pytest.skip("database not built: run `python pipeline.py` first")
    return DB
