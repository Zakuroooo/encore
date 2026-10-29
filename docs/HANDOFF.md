> **Historical note.** This was the hand-over from the local session. Everything listed under "Next" is now done;
> see README.md. Two things changed since: the cutoffs moved to Oct 20 / Nov 10 (ADR-005), and the licence
> finding is recorded in docs/DATA.md (no licence found).

# Hand-over: local session → cloud session (Oct 29, 2026)

The project was started in a local session on Pranay's Mac and moved to the cloud. Continue from exactly this
state; nothing else is running locally and the local folder is frozen until the cloud work is pulled back.

## Decisions already made
- Name **Encore**. Data: Udacity "Sparkify" mini event log (128 MB JSON, still downloadable; licence/terms checked by
  the local session — record the finding in `docs/DATA.md`). Raw data is not redistributed (not in git).
- Stack: Python + pandas + **DuckDB**, scikit-learn (see `requirements.txt`).
- SQL layers written: `sql/00_params.sql`, `01_raw.sql`, `02_clean.sql`, `03_users_sessions.sql`,
  `10_activity.sql`, `11_funnel.sql`, `12_paid_vs_free.sql`, `13_cohorts.sql` (weekly cohort retention), `14_rfm.sql`.
- `analysis/run_sql.py` runs the layers; `analysis/features.sql` + `analysis/churn_model.py` started for the churn model.
- `tests/check_quality.py` = data-quality checks that must fail loudly.

## Where it stopped
The local session was writing the cohort-retention and RFM SQL while the download finished (~54 of 128 MB).
Next: re-download, run the layers end to end, verify every number, then continue with the churn model,
decision/A-B design, dashboard, docs, LEARN/ and docs/RESUME-FACTS.md as in the task brief.

## Rules
Every number comes from pipeline output (never typed by hand) · no fabricated users · simple code he can explain
line by line · commits with plain messages and NO Co-Authored-By / Claude / AI lines.
