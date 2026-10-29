# 2. The SQL pipeline

## The three layers
Think of a kitchen: raw vegetables → washed and cut → cooked dishes.

| Layer | Schema | What it holds | File |
|---|---|---|---|
| Raw | `raw.events` | the JSON file loaded exactly as it is | `sql/01_raw.sql` |
| Clean | `clean.events`, `clean.sessions`, `clean.users` | only real user events, clear column names, right types | `sql/02_clean.sql`, `sql/03_users_sessions.sql` |
| Analytics | `analytics.*` | one table per question (DAU, funnel, cohorts, RFM…) | `sql/10_…` to `sql/16_…` |

Why layers? If a number looks wrong, you can walk back: analytics → clean → raw, and find where it changed.
We never edit the raw layer.

## DuckDB
DuckDB is a database that runs inside Python, with no server. It reads JSON directly and runs normal SQL very fast.
`analysis/run_sql.py` deletes the database, runs every SQL file in name order, and saves small result tables
as CSV files in `outputs/`.

## One command
`python pipeline.py` runs: download → build → quality checks → model → experiment → robustness → decision.
If any step fails, it stops and says which one.

## Data-quality checks that "fail loudly"
A quiet bad number is the most dangerous bug. So `tests/check_quality.py` checks 18 things and **stops the
pipeline** if any is false, for example:
- raw file has exactly 286,500 rows;
- clean rows = raw − no-user rows − stray tail rows − duplicates (every lost row explained);
- no empty values in key columns; no duplicate events;
- every day in the window has real volume;
- each churner cancelled once, and has no events after cancelling.

## SQL tricks used (learn these, interviewers ask)
| Trick | Example | Meaning |
|---|---|---|
| `FILTER` | `count(*) FILTER (WHERE page = 'NextSong')` | count only rows that match, inside one `GROUP BY` |
| `arg_min(x, y)` | `arg_min(level, event_seq)` | the value of `x` on the row where `y` is smallest = "plan at first event" |
| Window function | `row_number() OVER (PARTITION BY user_id ORDER BY event_ts)` | number each user's rows in time order, without collapsing them |
| `ntile(3)` | `ntile(3) OVER (ORDER BY monetary_songs, user_id)` | split users into 3 equal groups by a value |
| `date_trunc('week', d)` | | the Monday of that date's week |
| `ROLLUP` / `GROUPING SETS` | | add an "all" total row next to the per-group rows |
| CTE (`WITH name AS (...)`) | | name a step of the query, so long queries read top to bottom |

## Same answer every time (determinism)
Two events can share the same timestamp. If "first event" is chosen by time alone, the database may pick
either one, and results can change between runs. So the clean layer adds `event_seq`, a unique running number,
and "first/last" always uses it. CI rebuilds everything and fails if the outputs differ from the committed ones.

## Say it in one line
"Raw, clean and analytics layers in DuckDB, rebuilt from scratch by one command, with 18 checks that stop the
run if any row is unexplained."
