"""Small helper functions for the churn model, kept separate so tests can check them on tiny examples."""
import math

import numpy as np
from sklearn.metrics import average_precision_score


def top_k_stats(y, score, share):
    """If we contact only the top `share` of users by risk score:
    how many churners do we reach (recall) and how many contacts are churners (precision)?"""
    y, score = np.asarray(y), np.asarray(score)
    k = math.ceil(share * len(y))
    order = np.argsort(-score, kind="stable")[:k]   # highest score first; ties keep input order
    hits = int(y[order].sum())
    total = int(y.sum())
    base_rate = total / len(y)
    return {"k": k, "churners_caught": hits,
            "precision_at_k": round(hits / k, 4),
            "recall_at_k": round(hits / max(total, 1), 4),
            # lift = how many times better than contacting k users at random
            "lift_at_k": round((hits / k) / base_rate, 2) if base_rate else None}


def bootstrap_pr_auc(y, score, n=2000, seed=7):
    """95% interval for PR-AUC by resampling users with replacement.
    A small test set gives a wide interval: that width is the honest size of our uncertainty."""
    rng = np.random.default_rng(seed)
    y, score = np.asarray(y), np.asarray(score)
    vals = []
    for _ in range(n):
        idx = rng.integers(0, len(y), len(y))
        if y[idx].sum() == 0:      # a resample with no churners has no PR-AUC
            continue
        vals.append(average_precision_score(y[idx], score[idx]))
    return [round(float(np.percentile(vals, 2.5)), 4), round(float(np.percentile(vals, 97.5)), 4)]


def sample_size_two_proportions(p1, p2, alpha=0.05, power=0.80):
    """Users needed PER GROUP to detect a change from rate p1 to p2 (two-sided z-test, normal approximation)."""
    from statistics import NormalDist
    z_a = NormalDist().inv_cdf(1 - alpha / 2)
    z_b = NormalDist().inv_cdf(power)
    p_bar = (p1 + p2) / 2
    num = (z_a * math.sqrt(2 * p_bar * (1 - p_bar)) + z_b * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    return math.ceil(num / (p1 - p2) ** 2)
