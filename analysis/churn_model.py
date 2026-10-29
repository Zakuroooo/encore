"""Step 3: churn model.
Train on users as of Oct 22 (label: cancelled by Nov 12), test on users as of Nov 12 (label: cancelled by Dec 3).
Three rankers are compared on the SAME test set:
  1. a simple rule: "days since last event" (no machine learning) - the bar to beat
  2. logistic regression (the baseline model)
  3. gradient boosting (the more flexible model)
Model choice is made on the TRAINING data only (5-fold cross-validation), before looking at test results.
Writes outputs/model_metrics.json, model_importance.csv, calibration.csv, risk_bands.csv
"""
import json
import math
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
SEED = 7
TOP_SHARE = 0.20  # we can afford to contact the riskiest 20% of listeners (assumption, docs/DECISIONS.md)

con = duckdb.connect(str(ROOT / "data/encore.duckdb"), read_only=True)
train_cutoff, test_cutoff, horizon = con.execute("SELECT * FROM raw.params").fetchone()
feature_sql = (ROOT / "analysis/features.sql").read_text()

def features(cutoff):
    return con.execute(feature_sql, [str(cutoff), horizon]).df()

train, test = features(train_cutoff), features(test_cutoff)
FEATURES = [c for c in train.columns if c not in ("user_id", "churned")]
X_tr, y_tr = train[FEATURES].astype(float), train["churned"]
X_te, y_te = test[FEATURES].astype(float), test["churned"]

models = {
    "logistic_regression": make_pipeline(
        StandardScaler(), LogisticRegression(C=0.5, class_weight="balanced", max_iter=2000)),
    "gradient_boosting": HistGradientBoostingClassifier(
        max_depth=3, learning_rate=0.05, max_iter=150, min_samples_leaf=10,
        class_weight="balanced", random_state=SEED),
}

def top_k_stats(y, score, share=TOP_SHARE):
    """Precision and recall if we contact only the top `share` of users by risk score."""
    k = math.ceil(share * len(y))
    order = np.argsort(-np.asarray(score), kind="stable")[:k]
    hits = int(np.asarray(y)[order].sum())
    return {"k": k, "churners_caught": hits,
            "precision_at_k": round(hits / k, 4),
            "recall_at_k": round(hits / max(int(np.sum(y)), 1), 4)}

def bootstrap_pr_auc(y, score, n=2000):
    """95% interval for PR-AUC by resampling test users with replacement (small test set = wide interval)."""
    rng = np.random.default_rng(SEED)
    y, score = np.asarray(y), np.asarray(score)
    vals = []
    for _ in range(n):
        idx = rng.integers(0, len(y), len(y))
        if y[idx].sum() == 0:
            continue
        vals.append(average_precision_score(y[idx], score[idx]))
    return [round(float(np.percentile(vals, 2.5)), 4), round(float(np.percentile(vals, 97.5)), 4)]

# 1. Choose the model on training data only (cross-validated PR-AUC).
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
cv_pr_auc = {}
for name, m in models.items():
    p = cross_val_predict(m, X_tr, y_tr, cv=cv, method="predict_proba")[:, 1]
    cv_pr_auc[name] = round(average_precision_score(y_tr, p), 4)
chosen = max(cv_pr_auc, key=cv_pr_auc.get)

# 2. Fit on all training users, score the test users once.
scores = {"rule_days_since_last_event": X_te["days_since_last_event"].to_numpy()}
for name, m in models.items():
    m.fit(X_tr, y_tr)
    scores[name] = m.predict_proba(X_te)[:, 1]

results = {}
for name, s in scores.items():
    results[name] = {
        "pr_auc": round(average_precision_score(y_te, s), 4),
        "pr_auc_95ci": bootstrap_pr_auc(y_te, s),
        "roc_auc": round(roc_auc_score(y_te, s), 4),
        **top_k_stats(y_te, s),
    }
    if name in models:
        results[name]["brier"] = round(brier_score_loss(y_te, s), 4)
        results[name]["mean_predicted"] = round(float(np.mean(s)), 4)

# 3. Calibration of the chosen model: predicted vs actual churn in three equal-size risk groups.
s = scores[chosen]
bands = pd.qcut(pd.Series(s).rank(method="first"), 3, labels=["low", "middle", "high"])
calib = (pd.DataFrame({"band": bands, "pred": s, "actual": y_te})
         .groupby("band", observed=True).agg(users=("actual", "size"), mean_predicted=("pred", "mean"),
                                             actual_churn_rate=("actual", "mean")).round(4).reset_index())
calib.to_csv(OUT / "calibration.csv", index=False)

# 4. Plain-English importance: permutation importance on the test set (how much PR-AUC drops
#    when one feature is shuffled), plus logistic-regression coefficients (direction of the effect).
perm = permutation_importance(models[chosen], X_te, y_te, scoring="average_precision",
                              n_repeats=50, random_state=SEED)
coef = models["logistic_regression"][-1].coef_[0]
imp = pd.DataFrame({"feature": FEATURES,
                    "pr_auc_drop_when_shuffled": perm.importances_mean.round(4),
                    "lr_coefficient_per_sd": coef.round(3)}).sort_values("pr_auc_drop_when_shuffled", ascending=False)
imp.to_csv(OUT / "model_importance.csv", index=False)

# 5. Risk bands at the test snapshot for the decision step (aggregated only).
test = test.assign(risk=s)
k = math.ceil(TOP_SHARE * len(test))
test["band"] = "rest"
test.loc[test["risk"].rank(method="first", ascending=False) <= k, "band"] = "top_20pct"
risk = (test.groupby("band").agg(users=("user_id", "size"), churned_next_21d=("churned", "sum"),
                                 paid_users=("is_paid_now", "sum"))
        .assign(churn_rate=lambda d: (d.churned_next_21d / d.users).round(4)).reset_index())
risk.to_csv(OUT / "risk_bands.csv", index=False)

metrics = {
    "train_cutoff": str(train_cutoff), "test_cutoff": str(test_cutoff), "horizon_days": horizon,
    "n_features": len(FEATURES), "features": FEATURES,
    "train_users": len(train), "train_churners": int(y_tr.sum()), "train_churn_rate": round(float(y_tr.mean()), 4),
    "test_users": len(test), "test_churners": int(y_te.sum()), "test_churn_rate": round(float(y_te.mean()), 4),
    "top_share": TOP_SHARE, "cv_pr_auc_train": cv_pr_auc, "chosen_model": chosen, "test": results,
}
(OUT / "model_metrics.json").write_text(json.dumps(metrics, indent=2))
print(json.dumps({k: v for k, v in metrics.items() if k != "features"}, indent=2))
