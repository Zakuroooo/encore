"""Robustness check (reported in full, NOT used to pick anything).
The main result uses one pair of dates. With only ~15 churners, moving those dates by a few days can
change the answer. So we repeat the WHOLE procedure - choose the model on training CV, then score the
test set once - for 7 different test dates (each 1 day earlier), and publish every result.
Writes outputs/robustness_cutoffs.csv
"""
import math
import sys
from datetime import timedelta
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from model_utils import make_models, random_caught, top_k_stats  # noqa: E402

SEED, TOP_SHARE = 7, 0.20
con = duckdb.connect(str(ROOT / "data/encore.duckdb"), read_only=True)
sql = (ROOT / "analysis/features.sql").read_text()
test_cutoff, horizon = con.execute("SELECT test_cutoff, horizon_days FROM raw.params").fetchone()

rows = []
for shift in range(7):
    te_cut = test_cutoff - timedelta(days=shift)
    tr_cut = te_cut - timedelta(days=horizon)
    tr = con.execute(sql, [str(tr_cut), horizon]).df().round(6)   # .round(6): see churn_model.py
    te = con.execute(sql, [str(te_cut), horizon]).df().round(6)
    X_tr, y_tr = tr.drop(columns=["user_id", "churned"]).astype(float), tr["churned"]
    X_te, y_te = te.drop(columns=["user_id", "churned"]).astype(float), te["churned"]
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    models = make_models(SEED)
    cv_score = {n: average_precision_score(y_tr, cross_val_predict(m, X_tr, y_tr, cv=cv, method="predict_proba")[:, 1])
                for n, m in models.items()}
    chosen = max(cv_score, key=cv_score.get)
    rand = random_caught(y_te, TOP_SHARE, n=5_000, seed=SEED)
    row = {"train_cutoff": str(tr_cut), "test_cutoff": str(te_cut), "train_churners": int(y_tr.sum()),
           "test_users": len(te), "test_churners": int(y_te.sum()), "chosen_on_train_cv": chosen,
           "random_expected_caught": round(float(rand.mean()), 2)}
    for n, m in models.items():
        s = m.fit(X_tr, y_tr).predict_proba(X_te)[:, 1]
        caught = top_k_stats(y_te, s, TOP_SHARE)["churners_caught"]
        row[f"{n}_test_pr_auc"] = round(average_precision_score(y_te, s), 4)
        row[f"{n}_caught_top20"] = caught
        row[f"{n}_p_value"] = round(float(np.mean(rand >= caught)), 4)
    row["chosen_test_pr_auc"] = row[f"{chosen}_test_pr_auc"]
    row["chosen_p_value"] = row[f"{chosen}_p_value"]
    rows.append(row)

out = pd.DataFrame(rows)
out.to_csv(ROOT / "outputs/robustness_cutoffs.csv", index=False)
print(out[["test_cutoff", "test_churners", "chosen_on_train_cv", "chosen_test_pr_auc", "chosen_p_value",
           "random_expected_caught", "logistic_regression_caught_top20", "gradient_boosting_caught_top20"]]
      .to_string(index=False))
print(f"\n  chosen model beats random at p < 0.05 in {int((out.chosen_p_value < 0.05).sum())} of {len(out)} date choices")
