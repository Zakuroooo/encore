"""Experiment (the result was mixed, so the simpler single snapshot stays): train on several weekly
snapshots stacked together.
Idea: more training rows. Each user appears once per snapshot, so folds are grouped by user
(the same person never sits in both the training and the checking fold).
Judged on TRAINING data only (cross-validation), never on the test set.
Writes outputs/experiment_snapshots.csv
"""
import sys
from datetime import timedelta
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
from sklearn.model_selection import StratifiedGroupKFold, cross_val_predict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from model_utils import make_models  # noqa: E402

con = duckdb.connect(str(ROOT / "data/encore.duckdb"), read_only=True)
sql = (ROOT / "analysis/features.sql").read_text()
train_cutoff, horizon = con.execute("SELECT train_cutoff, horizon_days FROM raw.params").fetchone()

# Extra snapshots are 1 and 2 weeks BEFORE the training cutoff, so every label window still ends on or
# before the test snapshot and nothing overlaps the test period.
snap = [str(train_cutoff - timedelta(days=d)) for d in (14, 7, 0)]
OPTIONS = {f"1 snapshot ({snap[2]}) - used": snap[2:],
           f"2 snapshots ({snap[1]}, {snap[2]})": snap[1:],
           f"3 snapshots ({snap[0]} to {snap[2]})": snap}
MODELS = make_models(7)

rows = []
for option, cuts in OPTIONS.items():
    # .round(6): same reason as in churn_model.py (parallel float sums differ in the last digits)
    df = pd.concat([con.execute(sql, [c, horizon]).df().round(6) for c in cuts], ignore_index=True)
    X = df.drop(columns=["user_id", "churned"]).astype(float)
    y, groups = df["churned"], df["user_id"]
    for name, m in MODELS.items():
        runs = []
        for seed in range(5):  # 5 different fold shuffles, to show how much the number moves by luck
            cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
            p = cross_val_predict(m, X, y, groups=groups, cv=cv, method="predict_proba")[:, 1]
            runs.append(average_precision_score(y, p))
        rows.append({"training_data": option, "model": name, "rows": len(df), "churn_rows": int(y.sum()),
                     "churn_rate": round(float(y.mean()), 4),
                     "cv_pr_auc_mean": round(float(np.mean(runs)), 4),
                     "cv_pr_auc_sd": round(float(np.std(runs)), 4),
                     # PR-AUC divided by the churn rate: fair comparison when churn rates differ
                     "lift_over_random": round(float(np.mean(runs) / y.mean()), 2)})
out = pd.DataFrame(rows)
out.to_csv(ROOT / "outputs/experiment_snapshots.csv", index=False)
print(out.to_string(index=False))
