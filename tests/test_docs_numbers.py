"""The headline numbers written in the docs must match the pipeline outputs.
Each expected string is rebuilt from outputs/ here; if the data or code changes, this test fails
until README.md and docs/RESUME-FACTS.md are updated. (No number in the docs is allowed to go stale.)"""
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"


def pct(x):
    return f"{100 * x:.1f}%"


def money(x):
    return f"${abs(x):,.0f}"


def test_headline_numbers_match_outputs(db_path):
    m = json.loads((OUT / "model_metrics.json").read_text())
    d = json.loads((OUT / "decision.json").read_text())
    churn = pd.read_csv(OUT / "churn_summary.csv").iloc[0]
    flow = pd.read_csv(OUT / "cancel_flow.csv").set_index("plan").loc["all"]
    funnel = pd.read_csv(OUT / "funnel.csv")
    daily = pd.read_csv(OUT / "daily_active.csv")
    coh = pd.read_csv(OUT / "cohort_retention.csv").query("cohort_week == '2018-10-01'")
    tier = pd.read_csv(OUT / "retention_by_tier.csv")
    rob = pd.read_csv(OUT / "robustness_cutoffs.csv")
    outc = pd.read_csv(OUT / "snapshot_outcomes.csv").query("plan == 'all'").set_index("outcome").users
    sc = pd.read_csv(OUT / "decision_scenarios.csv")
    a, b = sc[sc.option.str.startswith("A")].net_per_month, sc[sc.option.str.startswith("B")].net_per_month
    chosen = m["test"][m["chosen_model"]]
    last_week = tier.week_number.max()
    t = tier[tier.week_number == last_week].set_index("tier").retention

    checks = subprocess.run([sys.executable, str(ROOT / "tests/check_quality.py")], capture_output=True, text=True)
    n_checks = checks.stdout.count("PASS  ")

    expected = {
        "clean events": "278,150",
        "users": f"{int(churn.users)} users",
        "cancellations": f"{int(churn.churned_users)} of {int(churn.users)}",
        "churn rate": pct(churn.churn_rate),
        "cancel flow": f"{int(flow.confirmed)} of {int(flow.opened_cancel_page)}",
        "seconds": f"{flow.median_seconds_to_confirm} s",
        "funnel": pct(funnel.iloc[-1].pct_of_start),
        "week-7 retention": pct(coh[coh.week_number == last_week].retention.iloc[0]),
        "paid retention": pct(t["paid"]),
        "free retention": pct(t["free"]),
        "stickiness": pct(daily.stickiness.median()),
        "test cancellers": f"{m['test_churners']} cancellers",
        "caught": f"{chosen['churners_caught']} of {m['test_churners']}",
        "random caught": f"{m['test']['random_order']['churners_caught']:.2f}",
        "p-value": f"{chosen['p_value_vs_random']}",
        "PR-AUC": f"{chosen['pr_auc']}",
        "robustness": f"{int((rob.chosen_p_value < 0.05).sum())} of {len(rob)}",
        "silent": f"{int(outc['went_silent'])} users",
        "A low": money(a.min()), "A high": money(a.max()),
        "B low": money(b.max()), "B high": money(b.min()),
        "break-even": f"{100 * d['option_b_break_even_save_rate']:.0f}%",
        "A/B size": f"{d['ab_test']['users_per_arm']} per group",
        "quality checks": f"| {n_checks} |",
    }
    facts = (ROOT / "docs/RESUME-FACTS.md").read_text()
    missing = {k: v for k, v in expected.items() if v not in facts}
    assert not missing, f"docs/RESUME-FACTS.md is out of date: {missing}"

    readme = (ROOT / "README.md").read_text().replace("\\$", "$")
    for v in [expected[k] for k in ("cancel flow", "funnel", "week-7 retention", "caught", "robustness",
                                    "A low", "B low", "break-even", "stickiness")]:
        assert v in readme, f"README.md is out of date: {v!r} not found"
