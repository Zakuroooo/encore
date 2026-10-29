# 11. Defend the code live: a file-by-file tour

If an interviewer opens the repo and asks "show me", go in this order. For each file: what it does in one
sentence, the one line worth pointing at, and a change you should be able to make live.

| Order | File | One sentence | Point at | Practise this live change |
|---|---|---|---|---|
| 1 | `pipeline.py` | runs every step in order and stops at the first failure | the `STEPS` list | add a step; run with `--from model` |
| 2 | `scripts/download.py` | downloads the file and checks size + SHA-256 | `EXPECTED_SHA256` | explain what happens if one byte changes |
| 3 | `sql/00_params.sql` | all key dates in one place | `log_end`, `horizon_days` | change horizon to 14 days and re-run |
| 4 | `sql/02_clean.sql` | keeps real user events, names columns, adds `event_seq` | the `WHERE` with `log_end` | add a new device type to the `CASE` |
| 5 | `sql/03_users_sessions.sql` | one row per session and per user | `arg_min(e.level, e.event_seq)` | add "number of thumbs-down" to `clean.users` |
| 6 | `tests/check_quality.py` | 18 checks; any FAIL stops everything | `check("clean = raw - …")` | add a check: no song shorter than 1 second |
| 7 | `sql/10_activity.sql` | DAU, 28-day MAU, stickiness, WAU | the `BETWEEN d.day - INTERVAL 27 DAY` join | change MAU to 7 days (WAU-style stickiness) |
| 8 | `sql/11_funnel.sql` | ordered 5-step funnel for free starters | `first_friend_ts >= tenth_song_ts` | add a step "added to playlist" |
| 9 | `sql/13_cohorts.sql` | weekly cohort retention | `date_diff('week', f.cohort_week, a.active_week)` | make monthly cohorts |
| 10 | `sql/14_rfm.sql` | forward-looking RFM | `4 - ntile(3) OVER (ORDER BY recency_days, user_id)` | change to 4 groups (quartiles) |
| 11 | `analysis/features.sql` | 21 features from the past only | the `past` CTE | add "ads in last 14 days" |
| 12 | `tests/test_leakage.py` | deletes the future, features must not change | `WHERE event_ts < ?` | add a deliberately leaky feature and watch it fail |
| 13 | `analysis/churn_model.py` | random vs rule vs two models, test once | `chosen = max(cv_pr_auc, …)` | change top 20% to top 10% |
| 14 | `analysis/model_utils.py` | top-k stats, bootstrap, sample size | `top_k_stats` | compute recall@10% by hand for a tiny example |
| 15 | `analysis/decision.py` | sizing with labelled assumptions | the `A = {...}` dict | change the price to ₹119 and explain the new break-even |
| 16 | `dashboard/app.py` | Streamlit page reading only `outputs/` | `csv("...")` helper | add one more metric tile |

## Three things to say if asked "did you write this yourself?"
1. Explain *why* a choice was made, not only what it does (the ADRs in `docs/DECISIONS.md` are your notes).
2. Show a bug you found and how the test caught it (the session-length leak, the Nov 30 data end).
3. Make one of the live changes above, run `python pipeline.py --from build` and `python -m pytest`, and read the new number.

## Commands to know by heart
```bash
python pipeline.py                 # everything
python pipeline.py --from model    # skip download and SQL
python -m pytest -q                # all tests
python tests/check_quality.py      # only the quality checks
streamlit run dashboard/app.py     # the dashboard
```
