# Decisions (ADRs)

Short records of choices that change results. Format: context → decision → why → what it costs.

---

### ADR-001 · DuckDB + plain SQL files, rebuilt from scratch every run
**Context.** 286k events, one laptop, reviewers who read SQL.
**Decision.** One DuckDB file built by running `sql/*.sql` in name order: `raw.*` (file as-is) → `clean.*`
(typed, filtered) → `analytics.*` (metric tables). The database is deleted and rebuilt on every run.
**Why.** Every number can be traced to one SQL file; no hidden state from an old run.
**Cost.** A full rebuild every time (≈2 s here; would need incremental models at real scale).

### ADR-002 · Churn = reached "Cancellation Confirmation"
**Context.** The brief fixes this label. It is clear and has a timestamp.
**Decision.** Use it as the model label. **Also** measure what it misses (ADR-009).
**Cost.** Users who simply stop coming are not counted as churn.

### ADR-003 · Time-based split with two snapshots, 21-day horizon
**Context.** A random split of users would let the model learn from the same weeks it is tested on.
**Decision.** Train: features before **Oct 20**, label = cancel in Oct 20 – Nov 10. Test: features before
**Nov 10**, label = cancel in Nov 10 – Dec 1. Model choice uses 5-fold CV on training users only; the test set
is scored once per model.
**Why 21 days.** Two non-overlapping windows must fit in 61 days with enough history before the first one.
**Cost.** Only 18 training and 13 test churners. Every model number is noisy (ADR-008).

### ADR-004 · Leakage guards are tested, not just promised
**Decision.** Features use only events before the cutoff; Cancel pages are never features.
`tests/test_leakage.py` deletes every event at/after the cutoff, rebuilds the user tables, and requires every
feature to be identical.
**This test found a real leak.** The first version took session length from `clean.sessions` and kept only
sessions that *ended* before the cutoff, so whether a session counted depended on the future. It changed
`avg_session_minutes` for 4.9% of training users. Sessions are now rebuilt from past events only.

### ADR-005 · Fix the log's true end (Nov 30) and move the cutoffs 2 days earlier
**Context.** The first plan used Oct 22 / Nov 12, assuming the log ran to Dec 3. Looking at daily volume,
the log really ends on Nov 30: there are 3 events on Dec 1, none on Dec 2, one on Dec 3. So the "21-day" test
window held only ~18 days of data.
**Decision.** The clean layer stops at `log_end = Dec 1` (4 events dropped, pinned by a check) and the cutoffs
move to Oct 20 / Nov 10, so both windows are a full 21 days of real data.
**Honesty note.** This changed the results. Under the old dates, gradient boosting was chosen and scored
PR-AUC 0.108 (p = 0.25 vs random). Under the corrected dates, logistic regression is chosen and scores 0.215
(p = 0.095). The fix was made because the window was wrong, not because of the score; ADR-008 shows how much
the result moves with the date anyway.

### ADR-006 · Two small models, settings fixed in advance
**Decision.** Logistic regression (scaled, C = 0.5) vs gradient boosting (depth 3, 150 trees, ≥10 users per
leaf), both with `class_weight="balanced"`. No tuning on test data.
**Why.** With ~15 positive examples, a big search would just fit noise in the CV folds.
**Cost.** Probabilities are inflated by the class weighting (mean predicted 0.41 vs actual 0.07 for logistic
regression), so scores are used for **ranking only**, never as "chance of leaving".

### ADR-007 · Compare against random and a simple rule, with a p-value
**Decision.** Report four rankers on the same test set: random order (10,000 shuffles), "days since last
event", logistic regression, gradient boosting. For each: PR-AUC with a bootstrap 95% range, recall and lift in
the top 20%, and the share of random orders that do at least as well.
**Why.** "PR-AUC 0.215" means nothing alone; "beats random in 90.5% of shuffles" is the honest framing.

### ADR-008 · Publish a robustness table instead of one lucky date
**Context.** ADR-005 showed that moving the dates by 2 days flipped the chosen model.
**Decision.** `analysis/robustness.py` repeats the *whole* procedure for 7 test dates (Nov 4 – Nov 10) and
publishes all 7 rows. Nothing is chosen from it.
**Result.** The chosen model beats random at p < 0.05 on 2 of 7 dates; logistic regression catches more
churners than the random average (≈2.7) on all 7 (4–8 caught). The windows overlap, so these are not 7
independent tests. Reading: a weak but consistent signal, not a deployable model.

### ADR-009 · Measure the label's blind spot
**Decision.** `sql/15_outcomes.sql` splits the 184 test users into cancelled (13), went silent (15) and stayed (156).
**Finding.** "Days since last event" is *worse than random* for predicting cancellations (catches 1 vs ≈2.6 by
chance) but is the best ranker for "cancelled **or** went silent" (PR-AUC 0.227 vs base rate 0.152).
People who drift away rarely bother to cancel; people who cancel were active right up to the click.

### ADR-010 · Experiment kept but not adopted: stacking weekly snapshots
**Idea.** Train on snapshots 1 and 2 weeks before Oct 20 as well, to get ~3× more rows (CV grouped by user).
**Result (training CV only).** Mixed. Under the first dates it lowered lift for both models; under the
corrected dates, two snapshots raised gradient boosting's CV PR-AUC (0.170 → 0.238) but lowered logistic
regression's lift, and three snapshots were worse for both. Fold-to-fold spread is 0.01–0.05.
**Decision.** Keep the single snapshot fixed before the experiment. A gain that appears and disappears with a
2-day shift is not a reason to make the design more complex. Revisit with more data.

### ADR-011 · Save offer goes on the Cancel page, not in a model-targeted e-mail
**Context.** All 52 users who opened the Cancel page confirmed, median 25.5 seconds later: there is no save step
today. A model-picked e-mail reaches people of whom about 1 in 8 (13.5%) would cancel.
**Decision.** Recommend an A/B-tested save offer inside the cancel flow (docs/AB_TEST.md). Do not spend
discounts on model-targeted e-mail. Use the model only for **free** actions (e.g. a better-recommendations nudge).
**Why.** Under every scenario we tried, the e-mail option loses money: it needs a 46% save rate to break even,
because over 90% of the discounts (92–98% across the scenarios) go to people who were not leaving.
**Cost.** The cancel-flow offer only reaches people who click Cancel; it cannot help the silent leavers (ADR-009).

### ADR-012 · Assumptions live in one place and are labelled
**Decision.** Price ($9.99), discount ($5 off one month), save rate (5/10/20%), months kept (1/2/3) and the
30% "non-leaver grabs the discount" rate sit at the top of `analysis/decision.py` and are copied into
`outputs/decision.json`. Docs and dashboard label them as assumptions.

### ADR-013 · Deterministic outputs, checked by CI
**Decision.** Fixed seeds, `user_id` tie-breakers in `ntile`, `event_seq` instead of timestamps for
first/last. CI rebuilds everything from the raw file and fails if `outputs/` differs from what is committed.

### ADR-014 · Streamlit dashboard reading only `outputs/`
**Decision.** `dashboard/app.py` reads CSV/JSON from `outputs/`; it never touches raw data or the database. So it
can be deployed without the raw file, and every number on it comes from the pipeline. A test runs it headless.
