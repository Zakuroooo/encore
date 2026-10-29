# Metric definitions

Every metric is computed in SQL (`sql/`) or Python (`analysis/`) and written to `outputs/`. This page says
exactly what each one counts, so two people computing it get the same number.

**Common rules**
- An **active user** on a day = a logged-in user with *any* event that day (a song, a page view, anything).
- **Plan** (free / paid) = the `level` on the event. A user who upgrades counts as free before and paid after.
- **Weeks** start on Monday. The log starts Monday Oct 1, so week 1 is full; the last week (Nov 26–30) has 5 days.
- All times are UTC.

## Engagement — `sql/10_activity.sql`
| Metric | Definition | Output |
|---|---|---|
| DAU | distinct active users per calendar day | `daily_active.dau` (+ `dau_paid`, `dau_free`) |
| WAU | distinct active users per Monday-start week | `weekly_active.wau` |
| MAU (28-day) | distinct active users in the 28 days ending that day. Empty for the first 27 days (not enough history) | `daily_active.mau_28d` |
| Stickiness | DAU ÷ 28-day MAU. "What share of this month's users came today?" | `daily_active.stickiness` |
| Session length | first to last event in a session, in minutes. A one-event session = 0 minutes | `session_stats` |

Why 28 days and not a calendar month: 28 = 4 full weeks, so every window has the same number of weekdays and weekends.

## Activation funnel — `sql/11_funnel.sql`
Who is in it: the **177 users whose first event in the log is on the free plan**. The 48 users already paying
on day one passed the funnel before the log started, so they are left out.

| Step | Counts a user if… |
|---|---|
| 1. Signed up (free) | first event is on the free plan |
| 2. First song | played at least one song |
| 3. 10 songs | played a 10th song |
| 4. Added a friend | added a friend **at or after** the 10th song |
| 5. Became paid | had a paid event **at or after** adding that friend |

It is an *ordered* funnel: each step must happen after the one before, so a user who paid first and added a
friend later stops at step 4. `pct_of_previous` = step ÷ previous step.

## Cohort retention — `sql/13_cohorts.sql`
- **Cohort** = the Monday-start week of the user's **first event in the log**.
- **Week-k retention** = share of the cohort with any event in the k-th week after the cohort week.
  Week 0 is always 100%.
- The partial last week (Nov 26–30) is left out, so it cannot show a fake drop.
- Caveat: the Oct 1 cohort (162 users) is everyone already using the app when the log began, not new sign-ups.
  Later cohorts are small (2–33 users).
- `retention_by_tier`: the Oct 1 cohort split by plan at first event.

## RFM — `sql/14_rfm.sql`
Measured at the **test snapshot (Nov 10)** with events before it only, then compared with who cancelled in
the 21 days after. Users: the 184 seen before Nov 10 who had not cancelled yet.

| Letter | Here means | Score |
|---|---|---|
| R (recency) | days since last event | 3 = most recent third |
| F (frequency) | number of sessions | 3 = top third |
| M (monetary) | songs played (no money in the data, so listening is the stand-in for value) | 3 = top third |

Thirds are made with `ntile(3)`; ties are broken by `user_id` so every run is the same.
Segments: **Champions** R=3 and F+M≥5 · **Loyal** R≥2 and F+M≥4 · **At risk** R=1 and F+M≥4 ·
**Casual** R≥2 (others) · **Hibernating** everyone else.

## Paid vs free, downgrades, cancellations — `sql/12_paid_vs_free.sql`
- Behaviour per **100 songs** (thumbs up/down, ads, friends, playlist adds), so tiers of different size compare fairly.
- **Churn (whole log)** = user reached `Cancellation Confirmation`. Tier at cancel = plan on that event.
- **Downgrade rate** = users who did `Submit Downgrade` ÷ users who were ever paid.

## Cancel flow — `sql/16_cancel_flow.sql`
- `opened_cancel_page` = users with a `Cancel` event; `confirmed` = of those, users with `Cancellation Confirmation`.
- Seconds to confirm = first `Cancel` → first `Cancellation Confirmation`.

## Outcomes after the snapshot — `sql/15_outcomes.sql`
For the 184 users at Nov 10, what happened in the next 21 days:
**cancelled** (confirmation in the window) · **went silent** (no cancel, *zero* events in the window) · **stayed**.

## Churn model — `analysis/features.sql`, `analysis/churn_model.py`
- **Label**: reached `Cancellation Confirmation` in the 21 days after the snapshot date.
- **Train** snapshot Oct 20 (label window Oct 20 – Nov 10); **test** snapshot Nov 10 (window Nov 10 – Dec 1).
  The windows touch but do not overlap, and the test window ends exactly where the data ends.
- **Scored users**: seen before the snapshot and not cancelled before it.
- **Features**: 21 numbers per user from events *before* the snapshot only (list and meaning in
  `outputs/model_importance.csv`).
- **PR-AUC** (average precision): area under the precision–recall curve. A random order scores the churn rate
  (0.071 on test), a perfect one scores 1.
- **Recall@top-20%**: of all churners, the share found among the 20% of users with the highest risk score.
  Precision@top-20% = share of those contacted who are churners. **Lift** = precision ÷ churn rate.
- **p-value vs random**: share of 10,000 random user orders that put at least as many churners in the top 20%.
- **95% range for PR-AUC**: 2.5th–97.5th percentile over 2,000 bootstrap resamples of the test users.

## Decision sizing — `analysis/decision.py`
Rates come from the outputs above; price, discount, save rate and months kept are **assumptions**
(listed at the top of the script and in `outputs/decision.json`). Monthly rates are 21-day rates × 30/21.
