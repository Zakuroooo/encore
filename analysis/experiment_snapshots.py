"""Experiment (kept because it did NOT help): train on several weekly snapshots stacked together.
Idea: more training rows. Each user appears once per snapshot, so folds are grouped by user
(the same person never sits in both the training and the checking fold).
Judged on TRAINING data only (cross-validation), never on the test set.
Writes outputs/experiment_snapshots.csv
"""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.model_selection import StratifiedGroupKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
con = duckdb.connect(str(ROOT / "data/encore.duckdb"), read_only=True)
sql = (ROOT / "analysis/features.sql").read_text()
horizon = con.execute("SELECT horizon_days FROM raw.params").fetchone()[0]

# Every label window ends on or before Nov 12, the test snapshot, so nothing overlaps the test period.
OPTIONS = {"1 snapshot (Oct 22) - used": ["2018-10-22"],
           "2 snapshots (Oct 15, 22)": ["2018-10-15", "2018-10-22"],
           "3 snapshots (Oct 8, 15, 22)": ["2018-10-08", "2018-10-15", "2018-10-22"]}
MODELS = {
    "logistic_regression": make_pipeline(
        StandardScaler(), LogisticRegression(C=0.5, class_weight="balanced", max_iter=2000)),
    "gradient_boosting": HistGradientBoostingClassifier(
        max_depth=3, learning_rate=0.05, max_iter=150, min_samples_leaf=10,
        class_weight="balanced", random_state=7),
}

rows = []
for option, cuts in OPTIONS.items():
    df = pd.concat([con.execute(sql, [c, horizon]).df() for c in cuts], ignore_index=True)
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
