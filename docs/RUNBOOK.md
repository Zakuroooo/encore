# Runbook

## Run everything locally
Needs Python 3.13 (3.11+ should work; CI uses 3.13), about 1 GB free disk and an internet connection for the
first download.

```bash
git clone https://github.com/Zakuroooo/encore.git && cd encore
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python pipeline.py                   # download -> build -> checks -> model -> experiment -> robustness -> decide
python -m pytest                     # 20 tests
streamlit run dashboard/app.py       # opens http://localhost:8501
```
`python pipeline.py --from model` restarts from a later step (skips the download and the SQL build).
A full run takes about 1 minute after the download.

## What each step writes
| Step | Script | Writes |
|---|---|---|
| download | `scripts/download.py` | `data/raw/mini_sparkify_event_data.json` (not in git) |
| build | `analysis/run_sql.py` | `data/encore.duckdb` (not in git), `outputs/*.csv` (aggregates) |
| check | `tests/check_quality.py` | nothing; prints PASS/FAIL per check |
| model | `analysis/churn_model.py` | `outputs/model_metrics.json`, `model_importance.csv`, `calibration.csv`, `risk_bands.csv` |
| experiment | `analysis/experiment_snapshots.py` | `outputs/experiment_snapshots.csv` |
| robustness | `analysis/robustness.py` | `outputs/robustness_cutoffs.csv` |
| decide | `analysis/decision.py` | `outputs/decision.json`, `outputs/decision_scenarios.csv` |

## When something fails
| Message | Meaning | What to do |
|---|---|---|
| `FAIL: got N bytes` / `SHA-256 ... does not match` | the download is incomplete or the file on S3 changed | delete `data/raw/`, re-run. If it still fails, the source changed: **stop**, every number may change. Re-check DATA.md before updating the pinned hash |
| `FAIL  raw row count` | not the documented 286,500 rows | same as above |
| `FAIL  registration quirk is the known one` / `tail after log_end` | the data differs from what the docs describe | investigate; update the pinned number and DATA.md together, never one without the other |
| `FAIL  no near-empty days` | a day inside the window has almost no events | coverage is broken; check `log_end` in `sql/00_params.sql` |
| `PIPELINE FAILED at step 'X'` | that script exited with an error | run that script alone (`python <script>`) to see the full error |
| CI step "Committed outputs must match a fresh run" fails | someone changed code but did not commit the new outputs, or the run is not deterministic | run `python pipeline.py` locally and commit `outputs/`; if it differs between two local runs, find the unordered step |

## Deploy the dashboard (NOT done yet: needs your Streamlit login)
The dashboard reads only `outputs/`, which is in git, so the raw data is not needed on the server.
Deploy config is ready: `dashboard/requirements.txt` (Streamlit reads the file next to the app first) and
`.streamlit/config.toml` (theme).

**Streamlit Community Cloud (free):**
1. Make sure `main` has the latest `outputs/` (CI green).
2. Go to **https://share.streamlit.io** and sign in with the GitHub account that owns `Zakuroooo/encore`.
3. The repo is **private**: when Streamlit asks for permission to read private repositories, allow it.
   (Check Streamlit's current docs for who can view an app made from a private repo; you may have to invite
   viewers by e-mail, or make the app public in its settings.)
4. Click **Create app** → **Deploy a public app from GitHub** (wording may differ slightly).
5. Repository `Zakuroooo/encore`, branch `main`, main file path **`dashboard/app.py`**.
6. Open **Advanced settings** → Python version **3.13**. No secrets are needed.
7. Optionally choose a custom subdomain (e.g. `encore-churn`). Click **Deploy**.
8. Wait for the build (a few minutes), then open every tab once and check there is no red error box.
9. Put the app URL at the top of `README.md` and commit.

Updating later: push to `main`; Streamlit Cloud redeploys on its own. If the numbers change, re-run
`python pipeline.py` and commit `outputs/` first.

**Fallback if Streamlit Cloud is not possible:** run locally (above) and record a 60-second screen capture
of the tabs for the portfolio.
