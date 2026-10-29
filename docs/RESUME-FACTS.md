# Resume facts (verified)

Every fact below is read from a file the pipeline writes. `tests/test_docs_numbers.py` re-checks the starred (★)
ones against `outputs/` on every CI run, so if the data or code changes, this page cannot silently go stale.

| Fact | Value | Where it comes from |
|---|---|---|
| ★ Raw events / clean events | 286,500 / 278,150 | `tests/check_quality.py` output |
| ★ Users, days covered | 225 users, 61 days (Oct 1 – Nov 30, 2018) | `outputs/churn_summary.csv`, `daily_active.csv` |
| ★ Data-quality checks (all must pass) | 18 | `tests/check_quality.py` |
| Automated tests | 20 (pytest, run in GitHub Actions CI) | `tests/` |
| ★ Cancellations in the log | 52 of 225 (23.1%) | `churn_summary.csv` |
| ★ Cancel page → confirmed | 52 of 52, median 25.5 s | `cancel_flow.csv` |
| ★ Free → paid funnel | 40.1% of 177 free starters reached paid | `funnel.csv` |
| ★ Oct 1 cohort, week-7 retention | 58.6% (paid 72.7%, free 55.0%) | `cohort_retention.csv`, `retention_by_tier.csv` |
| ★ Median stickiness (DAU / 28-day MAU) | 24.8% | `daily_active.csv` |
| ★ Test set | 184 users, 13 cancellers in 21 days | `model_metrics.json` |
| ★ Model (logistic regression) top-20% catch | 5 of 13 (random: 2.63 on average), p = 0.0954 | `model_metrics.json` |
| ★ PR-AUC | 0.2152 vs 0.0707 for random | `model_metrics.json` |
| ★ Robustness | p < 0.05 on 2 of 7 test dates | `robustness_cutoffs.csv` |
| ★ Went silent without cancelling (test) | 15 users (vs 13 cancelled) | `snapshot_outcomes.csv` |
| ★ Cancel-page offer, per 10K paid users/month | +$860 to +$8,027 (assumed save rate 5–20%) | `decision_scenarios.csv` |
| ★ Model-targeted e-mail, same basis | −$1,725 to −$4,114; break-even save rate 46% | `decision_scenarios.csv`, `decision.json` |
| ★ A/B test size | 269 per group (538 total) | `decision.json` |
| Leakage bug caught by test | changed `avg_session_minutes` for 4.9% of training users before the fix | docs/DECISIONS.md ADR-004 (one-off check, not re-run in CI) |

**What you must say if asked:** the app is *simulated* (Udacity Sparkify); money figures use *assumed* price
and save rates; the model is *not* reliably better than chance on this sample.

## Resume bullets
(Under 110 characters each; bold marks the phrases a recruiter should see first.)

1. Built a **one-command DuckDB SQL pipeline** on 278K streaming events, guarded by **18 data-quality checks** in CI
2. Found **52 of 52** Cancel-page visitors confirmed (median 25.5 s); recommended an **A/B-tested in-flow save offer**
3. Sized save offers per 10K paid users: **+$0.9K–8.0K/month** in the cancel flow vs **−$1.7K–4.1K** via model e-mail
4. Built a **leak-tested churn model** on a time split; caught **5 of 13 churners vs 2.6 by chance**, reported p = 0.095

Notes for using them:
- Bullet 3 rests on assumptions (price \$9.99, 5–20% save rate). Be ready to say so in the first sentence.
- Bullet 4 is deliberately honest: the interview story is "I showed the model was not yet good enough, and why".
- Put "Udacity Sparkify (simulated) data" in the project title line, not in every bullet.
