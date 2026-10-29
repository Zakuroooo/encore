"""No-leakage proof for the churn features.
Idea: if a feature at the cutoff only uses the past, then DELETING every event at or after the cutoff
must not change it. We rebuild the clean user/session tables from the cut-down events and compare."""
from pathlib import Path

import duckdb
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
FEATURE_SQL = (ROOT / "analysis/features.sql").read_text()
USERS_SQL = (ROOT / "sql/03_users_sessions.sql").read_text()


def features_full_and_truncated(db_path, cutoff):
    full = duckdb.connect(str(db_path), read_only=True)
    horizon = full.execute("SELECT horizon_days FROM raw.params").fetchone()[0]
    a = full.execute(FEATURE_SQL, [cutoff, horizon]).df()

    cut = duckdb.connect()  # in memory
    cut.execute(f"ATTACH '{db_path}' AS src (READ_ONLY)")
    cut.execute("CREATE SCHEMA raw; CREATE SCHEMA clean;")
    cut.execute("CREATE TABLE raw.params AS SELECT * FROM src.raw.params")
    cut.execute("CREATE TABLE clean.events AS SELECT * FROM src.clean.events WHERE event_ts < ?::TIMESTAMP",
                [cutoff])
    cut.execute(USERS_SQL)
    b = cut.execute(FEATURE_SQL, [cutoff, horizon]).df()
    return a, b


@pytest.mark.parametrize("which", ["train_cutoff", "test_cutoff"])
def test_features_ignore_the_future(db_path, which):
    cutoff = str(duckdb.connect(str(db_path), read_only=True).execute(f"SELECT {which} FROM raw.params").fetchone()[0])
    a, b = features_full_and_truncated(db_path, cutoff)
    assert list(a.user_id) == list(b.user_id), "the set of scored users must not depend on the future"
    cols = [c for c in a.columns if c != "churned"]   # the label is SUPPOSED to use the future
    pd.testing.assert_frame_equal(a[cols].reset_index(drop=True), b[cols].reset_index(drop=True),
                                  check_dtype=False)
    assert b["churned"].sum() == 0                     # with the future deleted, nobody can be labelled


def test_label_windows_do_not_overlap(db_path):
    con = duckdb.connect(str(db_path), read_only=True)
    train, test, h, log_end = con.execute("SELECT train_cutoff, test_cutoff, horizon_days, log_end FROM raw.params"
                                          ).fetchone()
    assert con.execute("SELECT max(event_ts) < ?::TIMESTAMP FROM clean.events", [str(log_end)]).fetchone()[0]
    assert pd.Timestamp(train) + pd.Timedelta(days=h) <= pd.Timestamp(test), "train label window runs into test"
    assert pd.Timestamp(test) + pd.Timedelta(days=h) <= pd.Timestamp(log_end), "test label window not fully observed"


def test_cancel_pages_are_not_features():
    body = FEATURE_SQL.split("-- the label")[0]
    for line in body.splitlines():
        code = line.split("--")[0]
        assert "Cancel" not in code, f"cancel page used as a feature: {line.strip()}"
