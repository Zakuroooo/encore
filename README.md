# Encore: churn and retention analytics for a music-streaming app

Who stops using a music app, can we see it coming, and what is worth doing about it?
Built on the public Udacity **Sparkify** event log (simulated app, 225 users, 278,150 events, Oct 1 – Nov 30 2018)
with **DuckDB SQL**, **scikit-learn** and a **Streamlit** dashboard. One command rebuilds every number.

```bash
pip install -r requirements.txt
python pipeline.py               # download -> SQL layers -> quality checks -> model -> robustness -> decision
streamlit run dashboard/app.py
```

**Bottom line:** a churn model is the wrong first investment here. Every user who opened the Cancel page went
through with it, in a median of 25.5 seconds, so the cheapest win is a tested save offer on that page.
→ [1-page memo](docs/MEMO.md) · [A/B test plan](docs/AB_TEST.md)

## Findings
All numbers come from `outputs/` (rebuilt and compared in CI). "Test" = users at Nov 10, outcome in the next 21 days.

| Area | Finding | Source |
|---|---|---|
| Engagement | Median **52** daily active users; median stickiness (DAU ÷ 28-day MAU) **24.8%** | `daily_active` |
| Paid vs free | Paid sessions are 2.5× longer (median **246 vs 98 min**); free users hear **8.78 ads per 100 songs** vs 0.13 for paid | `session_stats`, `paid_vs_free` |
| Funnel | Of 177 users first seen on free, **40.1%** reached "became paid". Biggest drop: friend added → paid (**53.4%** carry on) | `funnel` |
| Retention | Oct 1 cohort (162 users): **58.6%** still active in week 7. Paid at start **72.7%** vs free **55.0%** | `cohort_retention`, `retention_by_tier` |
| Cancellations | **52 of 225** users cancelled in 61 days (31 while paid, 21 while free) | `churn_summary` |
| Downgrades | 29.7% of ever-paid users downgraded, but they cancelled *less* (18.4% vs 24.4%): not an early warning | `churn_summary` |
| Cancel flow | **52 of 52** who opened Cancel confirmed, median **25.5 s** later: there is no save step | `cancel_flow` |
| RFM | "Loyal" (12.0%) and "Champions" (10.5%) cancelled most in the next 21 days; "At risk / gone quiet" **0 of 19** | `rfm_segments` |
| Label blind spot | At the test snapshot **13** users cancelled but **15** went silent without cancelling | `snapshot_outcomes` |
| Churn model | Logistic regression (chosen on training CV) caught **5 of 13** cancellers in its top 20% vs **2.6** by chance; PR-AUC **0.215** (95% range 0.07–0.44) vs 0.071 random; **p = 0.095** | `model_metrics.json` |
| Robustness | Repeated on 7 test dates: beats the random average on **7 of 7**, but p < 0.05 on only **2 of 7** | `robustness_cutoffs` |
| Decision | Per 10k paid users/month: Cancel-page offer **+\$860 to +\$8,027**; model-targeted e-mail **−\$1,725 to −\$4,114** (needs a 46% save rate to break even). Assumptions labelled | `decision.json`, `decision_scenarios` |
| A/B test | **269 users per group** to detect +5 points in "still paid at day 30" (α 0.05, power 0.8): ~2 weeks at 10k paid users | `decision.json` |

## What did not work (and what that taught me)
- **The model is not reliably better than luck.** 13 test cancellers is too few. I report the p-value and a
  7-date robustness table instead of one good-looking number. Moving the dates by 2 days flipped the chosen
  model ([ADR-005, ADR-008](docs/DECISIONS.md)).
- **"Days since last event" is worse than random for cancellations** (caught 1 vs 2.6). It *is* the best
  ranker for "cancelled or went silent": people who drift away rarely click Cancel.
- **Stacking more weekly snapshots** to get 3× training rows gave mixed results that changed with the dates.
  Not adopted ([ADR-010](docs/DECISIONS.md)).
- **Probabilities are not calibrated.** Class weighting inflates them (mean predicted 0.41 vs actual 0.07),
  so the scores are used for ranking only.
- **A real leak, caught by a test.** The first feature code let future events decide which sessions counted.
  `tests/test_leakage.py` deletes the future and requires every feature to stay the same; it caught the bug.
- **The log ends earlier than it looks.** After Nov 30 there are only 4 stray events. The first plan's
  "21-day" test window really held ~18 days; fixed and pinned by a check ([ADR-005](docs/DECISIONS.md)).

## Limits
Simulated app · 225 users · 61 days · no revenue (price and save rates are assumptions) · churn label = cancel click only ·
the A/B test is a plan, not a result. Details: [docs/DATA.md](docs/DATA.md).

## How it is built
```
scripts/download.py          download + size and SHA-256 check (raw data is never committed)
sql/00-03_*.sql              raw -> clean layers (typed, no names, every dropped row counted)
sql/10-16_*.sql              analytics tables: activity, funnel, paid vs free, cohorts, RFM, outcomes, cancel flow
tests/check_quality.py       18 data-quality checks; any FAIL stops the pipeline
analysis/features.sql        21 user features from events before the cutoff only
analysis/churn_model.py      random vs rule vs logistic regression vs gradient boosting, time-based split
analysis/robustness.py       the same test on 7 dates; analysis/experiment_snapshots.py: the idea that didn't stick
analysis/decision.py         sizing with labelled assumptions + A/B sample size
dashboard/app.py             Streamlit, reads only outputs/
tests/                       20 pytest tests incl. the no-leakage proof; CI in .github/workflows/ci.yml
```

## Docs
[PRD](docs/PRD.md) · [Metrics](docs/METRICS.md) · [Data](docs/DATA.md) · [Decisions (ADRs)](docs/DECISIONS.md) ·
[A/B test](docs/AB_TEST.md) · [Memo](docs/MEMO.md) · [Runbook + deploy steps](docs/RUNBOOK.md) ·
[Learning notes](LEARN/README.md)

Data: Udacity Sparkify mini log, public S3 file with no stated licence. Not redistributed; only aggregates are
published (see [docs/DATA.md](docs/DATA.md)).
