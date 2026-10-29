"""The dashboard runs from outputs/ without errors (Streamlit's built-in headless tester)."""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_runs_without_errors():
    if not (ROOT / "outputs/model_metrics.json").exists():
        pytest.skip("outputs missing: run `python pipeline.py`")
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=60).run()
    assert not at.exception, at.exception
    assert len(at.tabs) == 7
    assert at.metric[0].value == "225"           # read from outputs/churn_summary.csv
