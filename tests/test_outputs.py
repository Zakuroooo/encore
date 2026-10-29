"""Sanity checks on the published outputs: numbers that must agree with each other, do."""
import json
from pathlib import Path

import pandas as pd
import pytest

OUT = Path(__file__).resolve().parents[1] / "outputs"


def csv(name):
    path = OUT / f"{name}.csv"
    if not path.exists():
        pytest.skip(f"{path.name} missing: run `python pipeline.py`")
    return pd.read_csv(path)


def js(name):
    return json.loads((OUT / f"{name}.json").read_text())


def test_no_user_level_data_is_published():
    for f in OUT.glob("*.csv"):
        cols = pd.read_csv(f, nrows=0).columns
        assert "user_id" not in cols, f"{f.name} has user_id: only aggregates may be published"


def test_activity_bounds():
    d = csv("daily_active").dropna(subset=["mau_28d"])
    assert (d.dau <= d.mau_28d).all()
    assert d.stickiness.between(0, 1).all()
    assert (csv("daily_active").is_partial_day.sum()) == 1


def test_cohorts_start_at_100_percent():
    c = csv("cohort_retention")
    assert (c[c.week_number == 0].retention == 1.0).all()
    assert c.retention.between(0, 1).all()
    assert (c.active_users <= c.cohort_users).all()


def test_funnel_never_grows():
    f = csv("funnel").sort_values("step_no")
    assert f.users.is_monotonic_decreasing


def test_churn_counts_add_up():
    s = csv("churn_summary").iloc[0]
    assert s.churned_users == s.churned_while_paid + s.churned_while_free
    flow = csv("cancel_flow").set_index("plan")
    assert flow.loc["all", "confirmed"] == s.churned_users


def test_snapshot_tables_agree_with_model():
    m = js("model_metrics")
    o = csv("snapshot_outcomes")
    everyone = o[o.plan == "all"].set_index("outcome").users
    assert everyone.sum() == m["test_users"]
    assert everyone["cancelled"] == m["test_churners"]
    assert csv("rfm_segments").users.sum() == m["test_users"]
    assert csv("rfm_segments").churned_next_21d.sum() == m["test_churners"]
    r = csv("risk_bands")
    assert r.users.sum() == m["test_users"] and r.churned_next_21d.sum() == m["test_churners"]
    assert r[r.band == "top_20pct"].users.sum() == m["test"][m["chosen_model"]]["k"]


def test_model_chosen_on_training_cv():
    m = js("model_metrics")
    assert m["chosen_model"] == max(m["cv_pr_auc_train"], key=m["cv_pr_auc_train"].get)


def test_decision_numbers_follow_from_inputs():
    d = js("decision")
    sc = csv("decision_scenarios")
    a = sc[sc.option.str.startswith("A")]
    assert (a.wasted_discounts == 0).all()
    # if option B can never break even, every B scenario must lose money (and vice versa)
    b = sc[sc.option.str.startswith("B")]
    if d["option_b_break_even_save_rate"] > b.save_rate.max():
        assert (b.net_per_month < 0).all()
