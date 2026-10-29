# PRD: Encore, churn and retention analytics for a music-streaming app

## Problem
A subscription streaming app loses users every week. The team does not know (1) how healthy engagement and
retention are, (2) where new users drop off, (3) whether it can spot leavers early, and (4) what action is
worth paying for. Every lost paid subscriber is lost monthly revenue.

## Users of this work
| Who | Needs |
|---|---|
| Product manager (retention) | one place for DAU/WAU/MAU, funnel, cohorts; a clear "what do we do next" |
| Growth / CRM | which users to target, with what, and what it is worth |
| Data team | a pipeline they can re-run and trust: checked data, no leakage, reproducible numbers |

## Questions and how we answer them
| # | Question | Answer lives in |
|---|---|---|
| 1 | How engaged are listeners, and how sticky is the app? | `daily_active`, `weekly_active`, `session_stats` |
| 2 | Where do free users drop off before paying? | `funnel` |
| 3 | How fast do cohorts fade, and do paid users stay longer? | `cohort_retention`, `retention_by_tier` |
| 4 | Do free and paid users behave differently? How common are downgrades and cancels? | `paid_vs_free`, `churn_summary`, `weekly_cancels` |
| 5 | Do classic RFM segments find the people about to cancel? | `rfm_segments` |
| 6 | Can a model flag cancellers 21 days ahead, better than chance? | `model_metrics.json`, `robustness_cutoffs` |
| 7 | Which users should we try to save, how, and is it worth it? | `cancel_flow`, `decision.json`, docs/AB_TEST.md |

## Scope
**In:** the public Sparkify mini log (225 users, Oct 1 – Nov 30, 2018); SQL metrics; one churn model with
honest evaluation; a sized recommendation; an A/B test plan; a dashboard.
**Out:** real revenue (none in the data); deploying a live model; running the A/B test (needs a live app);
the 12 GB full Sparkify log (would need Spark; the mini log is enough to build and prove the method).

## Success criteria
- One command rebuilds every number from the raw file; data-quality checks stop the run on any surprise.
- Every published number is reproducible: CI rebuilds and compares with the committed outputs.
- The model is judged against random and a simple rule, on a later time period, with uncertainty shown.
- The recommendation states its assumptions and a decision rule fixed before any test result.

## Definitions
See `docs/METRICS.md`. Churn = reached `Cancellation Confirmation`.

## Risks
| Risk | Mitigation |
|---|---|
| Tiny sample: 13 test churners | bootstrap ranges, permutation p-values, robustness across 7 dates; say "weak signal" plainly |
| Simulated data | presented as a method demo; real-app numbers will differ |
| Label misses silent leavers | measured (15 silent vs 13 cancelled at the test snapshot) and reported |
| Overfitting through many tries | model choice on training CV only; all tried variants published |
