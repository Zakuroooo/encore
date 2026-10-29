"""Step 4: churn model.
Train on users as of Oct 20 (label: cancelled by Nov 10), test on users as of Nov 10 (label: cancelled by Nov 30).
Four rankers are compared on the SAME test set:
  0. random order - what you get with no information (10,000 random shuffles)
  1. a simple rule: "days since last event" (no machine learning)
  2. logistic regression (the baseline model)
  3. gradient boosting (the more flexible model)
The model is chosen on the TRAINING data only (5-fold cross-validation), before looking at test results.
Writes outputs/model_metrics.json, model_importance.csv, calibration.csv, risk_bands.csv
"""
import json
import math
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.inspection import permutation_importance
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_utils import bootstrap_pr_auc, make_models, random_caught, top_k_stats  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
SEED = 7
TOP_SHARE = 0.20  # we can afford to contact the riskiest 20% of listeners (assumption, docs/DECISIONS.md)

# What each feature means, in plain words (used in the importance table and the dashboard).
MEANING = {
    "tenure_days": "days since the user signed up",
    "days_since_last_event": "days since the user last did anything",
    "active_days": "number of days the user was active",
    "sessions": "number of listening sessions",
    "songs": "number of songs played",
    "songs_last14": "songs played in the last 14 days",
    "listening_trend": "last 14 days of listening compared with the 14 days before",
    "avg_session_minutes": "average session length in minutes",
    "thumbs_up_per_100": "thumbs-up per 100 songs",
    "thumbs_down_per_100": "thumbs-down per 100 songs",
    "friends_per_100": "friends added per 100 songs",
    "playlist_adds_per_100": "songs added to playlists per 100 songs",
    "ads_per_100": "ads heard per 100 songs",
    "errors": "error pages seen",
    "help_visits": "visits to the Help page",
    "downgrade_page_visits": "visits to the Downgrade page",
    "downgrades": "downgrades from paid to free",
    "settings_visits": "visits to Settings",
    "is_paid_now": "is on the paid plan at the snapshot",
    "is_male": "gender recorded as male",
    "is_apple_device": "uses a Mac or iPhone/iPad",
}

con = duckdb.connect(str(ROOT / "data/encore.duckdb"), read_only=True)
train_cutoff, test_cutoff, horizon = con.execute(
    "SELECT train_cutoff, test_cutoff, horizon_days FROM raw.params").fetchone()
feature_sql = (ROOT / "analysis/features.sql").read_text()


def features(cutoff):
    return con.execute(feature_sql, [str(cutoff), horizon]).df()


train, test = features(train_cutoff), features(test_cutoff)
FEATURES = [c for c in train.columns if c not in ("user_id", "churned")]
assert set(FEATURES) == set(MEANING), "every feature needs a plain-English meaning"
X_tr, y_tr = train[FEATURES].astype(float), train["churned"]
X_te, y_te = test[FEATURES].astype(float), test["churned"]

models = make_models(SEED)

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
        "pr_auc_95ci": bootstrap_pr_auc(y_te, s, seed=SEED),
        "roc_auc": round(roc_auc_score(y_te, s), 4),
        **top_k_stats(y_te, s, TOP_SHARE),
    }
    if name in models:
        results[name]["brier"] = round(brier_score_loss(y_te, s), 4)
        results[name]["mean_predicted"] = round(float(np.mean(s)), 4)

# 2b. Is any of this better than luck? Shuffle the users into a random order 10,000 times and count
#     how many churners land in the top 20% each time. p_value = share of random orders that catch
#     at least as many churners as the ranker did. Small p (< 0.05) = unlikely to be luck.
rand = random_caught(y_te, TOP_SHARE, seed=SEED)
results["random_order"] = {
    "pr_auc": round(float(y_te.mean()), 4),  # expected PR-AUC of a random order = the churn rate
    "k": math.ceil(TOP_SHARE * len(y_te)), "churners_caught": round(float(rand.mean()), 2),
    "churners_caught_95_range": [int(np.percentile(rand, 2.5)), int(np.percentile(rand, 97.5))],
    "recall_at_k": round(float(rand.mean()) / max(int(y_te.sum()), 1), 4), "lift_at_k": 1.0,
}
for name in scores:
    results[name]["p_value_vs_random"] = round(float(np.mean(rand >= results[name]["churners_caught"])), 4)

# 2c. Label check (no training): the label only counts users who click Cancel. Some users just stop
#     coming. With a wider label "left = cancelled OR no events at all in the 21 days", how do the
#     rankers do? This shows how much the label definition changes the story.
last_ts = con.execute("SELECT max(event_ts) FROM clean.events").fetchone()[0]
active_after = set(con.execute(
    "SELECT DISTINCT user_id FROM clean.events WHERE event_ts >= ?::TIMESTAMP AND event_ts < ?::TIMESTAMP "
    "+ INTERVAL (?) DAY", [str(test_cutoff), str(test_cutoff), horizon]).df()["user_id"])
left_any = ((y_te == 1) | ~test["user_id"].isin(active_after)).astype(int)
wide_label = {"users_left_any_way": int(left_any.sum()), "rate": round(float(left_any.mean()), 4)}
for name, sc in scores.items():
    wide_label[name] = {"pr_auc": round(average_precision_score(left_any, sc), 4),
                        "roc_auc": round(roc_auc_score(left_any, sc), 4)}

# 3. Calibration of the chosen model: predicted vs actual churn in three equal-size risk groups.
s = scores[chosen]
bands = pd.qcut(pd.Series(s).rank(method="first"), 3, labels=["low", "middle", "high"])
calib = (pd.DataFrame({"band": bands, "pred": s, "actual": y_te})
         .groupby("band", observed=True).agg(users=("actual", "size"), churners=("actual", "sum"),
                                             mean_predicted=("pred", "mean"),
                                             actual_churn_rate=("actual", "mean")).round(4).reset_index())
calib.to_csv(OUT / "calibration.csv", index=False)

# 4. Plain-English importance, measured on TRAINING users the model had not seen (held-out folds):
#    how much PR-AUC drops when one feature is shuffled. The test set has too few churners for this.
#    The logistic-regression coefficient gives the direction (+ = higher value, higher risk).
drops = []
for fold_tr, fold_val in cv.split(X_tr, y_tr):
    m = clone(models[chosen]).fit(X_tr.iloc[fold_tr], y_tr.iloc[fold_tr])
    r = permutation_importance(m, X_tr.iloc[fold_val], y_tr.iloc[fold_val], scoring="average_precision",
                               n_repeats=20, random_state=SEED)
    drops.append(r.importances_mean)
coef = models["logistic_regression"][-1].coef_[0]
imp = pd.DataFrame({"feature": FEATURES,
                    "meaning": [MEANING[f] for f in FEATURES],
                    "pr_auc_drop_when_shuffled": np.mean(drops, axis=0).round(4),
                    "lr_coefficient_per_sd": coef.round(3)})
imp["direction"] = np.where(imp.lr_coefficient_per_sd > 0, "higher = more risk", "higher = less risk")
imp = imp.sort_values("pr_auc_drop_when_shuffled", ascending=False)
imp.to_csv(OUT / "model_importance.csv", index=False)

# 5. Risk bands at the test snapshot for the decision step (aggregated only, split by plan).
test = test.assign(risk=s)
k = math.ceil(TOP_SHARE * len(test))
test["band"] = "rest"
test.loc[test["risk"].rank(method="first", ascending=False) <= k, "band"] = "top_20pct"
test["plan"] = np.where(test.is_paid_now == 1, "paid", "free")
risk = (test.groupby(["band", "plan"]).agg(users=("user_id", "size"), churned_next_21d=("churned", "sum"))
        .assign(churn_rate=lambda d: (d.churned_next_21d / d.users).round(4)).reset_index())
risk.to_csv(OUT / "risk_bands.csv", index=False)

metrics = {
    "train_cutoff": str(train_cutoff), "test_cutoff": str(test_cutoff), "horizon_days": horizon,
    "n_features": len(FEATURES), "features": FEATURES,
    "train_users": len(train), "train_churners": int(y_tr.sum()), "train_churn_rate": round(float(y_tr.mean()), 4),
    "test_users": len(test), "test_churners": int(y_te.sum()), "test_churn_rate": round(float(y_te.mean()), 4),
    "top_share": TOP_SHARE, "cv_pr_auc_train": cv_pr_auc, "chosen_model": chosen, "test": results,
    "test_wide_label_cancel_or_silent": wide_label, "log_ends": str(last_ts),
}
(OUT / "model_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
summary = {n: {k: r.get(k) for k in ("pr_auc", "churners_caught", "lift_at_k", "p_value_vs_random")}
           for n, r in results.items()}
print(f"  chosen on training CV: {chosen} {cv_pr_auc}")
print(f"  test: {metrics['test_users']} users, {metrics['test_churners']} churners")
for n, r in summary.items():
    print(f"  {n:28s} {r}")
print(f"  wide label (cancel or silent): {wide_label}")
