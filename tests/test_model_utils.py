"""The helper maths, checked on tiny hand-made examples where the right answer is obvious."""
from sklearn.metrics import average_precision_score

from model_utils import bootstrap_pr_auc, sample_size_two_proportions, top_k_stats


def test_top_k_perfect_ranking():
    y = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0]
    score = [0.9, 0.8, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
    r = top_k_stats(y, score, share=0.2)          # contact 2 of 10
    assert r["k"] == 2 and r["churners_caught"] == 2
    assert r["precision_at_k"] == 1.0 and r["recall_at_k"] == 1.0
    assert r["lift_at_k"] == 5.0                  # 100% precision vs 20% base rate


def test_top_k_worst_ranking():
    y = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0]
    score = [0.0, 0.0, 1, 1, 1, 1, 1, 1, 1, 1]
    r = top_k_stats(y, score, share=0.2)
    assert r["churners_caught"] == 0 and r["lift_at_k"] == 0.0


def test_top_k_rounds_k_up():
    r = top_k_stats([0, 1, 0], [0.1, 0.9, 0.2], share=0.2)   # 20% of 3 = 0.6 -> contact 1
    assert r["k"] == 1 and r["churners_caught"] == 1


def test_bootstrap_interval_contains_point_estimate():
    y = [1, 0, 0, 1, 0, 0, 0, 1, 0, 0] * 5
    # one churner (0.3) scores below two non-churners, so the ranking is good but not perfect
    score = [0.9, 0.2, 0.5, 0.7, 0.1, 0.4, 0.2, 0.3, 0.6, 0.1] * 5
    point = average_precision_score(y, score)
    lo, hi = bootstrap_pr_auc(y, score, n=300)
    assert 0 <= lo <= point <= hi <= 1
    assert hi - lo > 0.01                         # real resampling gives a real spread


def test_sample_size_textbook_case():
    # 10% vs 15%, alpha 0.05 two-sided, power 0.8 -> about 686 per group (standard tables)
    n = sample_size_two_proportions(0.10, 0.15)
    assert 680 <= n <= 690


def test_sample_size_grows_for_smaller_effects():
    assert sample_size_two_proportions(0.10, 0.12) > sample_size_two_proportions(0.10, 0.15)
