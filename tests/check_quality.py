"""Data-quality checks. Run after analysis/run_sql.py. Any failed check stops the pipeline (exit code 1).
Each check prints PASS/FAIL with the real number, so the output can be pasted into docs as proof.
"""
import sys
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
con = duckdb.connect(str(ROOT / "data/encore.duckdb"), read_only=True)
q = lambda sql: con.execute(sql).fetchone()[0]

EXPECTED_RAW_ROWS = 286_500          # documented size of the mini Sparkify file
WINDOW = ("2018-10-01", "2018-12-04")  # documented log window (UTC)
failures = []

def check(name, ok, detail):
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
    if not ok:
        failures.append(name)

# 1. Row counts: the raw file is complete, and the clean layer only lost the rows we meant to drop.
raw_rows = q("SELECT count(*) FROM raw.events")
check("raw row count", raw_rows == EXPECTED_RAW_ROWS, f"{raw_rows:,} rows (expected {EXPECTED_RAW_ROWS:,})")
no_user = q("SELECT count(*) FROM raw.events WHERE userId IS NULL OR userId = ''")
raw_dupes = q("""SELECT count(*) - count(DISTINCT (userId, sessionId, itemInSession, ts, page))
                 FROM raw.events WHERE userId <> ''""")
clean_rows = q("SELECT count(*) FROM clean.events")
check("clean = raw - no-user rows - duplicates", clean_rows == raw_rows - no_user - raw_dupes,
      f"{clean_rows:,} = {raw_rows:,} - {no_user:,} - {raw_dupes:,}")

# 2. Nulls in the columns every metric depends on.
for col in ["user_id", "session_id", "event_ts", "page", "level", "registration_ts"]:
    n = q(f"SELECT count(*) FROM clean.events WHERE {col} IS NULL")
    check(f"no nulls in clean.events.{col}", n == 0, f"{n} nulls")

# 3. Duplicate events left after cleaning.
dupes = q("""SELECT count(*) - count(DISTINCT (user_id, session_id, item_in_session, event_ts, page))
             FROM clean.events""")
check("no duplicate events in clean layer", dupes == 0, f"{dupes} duplicates")

# 4. Time range: all events inside the documented window, and registration before first event.
lo, hi = con.execute("SELECT min(event_ts), max(event_ts) FROM clean.events").fetchone()
check("events inside log window", str(lo) >= WINDOW[0] and str(hi) < WINDOW[1], f"{lo} to {hi}")
bad_reg = q("SELECT count(*) FROM clean.users WHERE registration_ts > first_event_ts")
check("registration before first event", bad_reg == 0, f"{bad_reg} users registered after their first event")

# 5. Allowed values.
bad_level = q("SELECT count(*) FROM clean.events WHERE level NOT IN ('free', 'paid')")
check("level is free/paid only", bad_level == 0, f"{bad_level} bad rows")

# 6. Churn logic: each churner has exactly one confirmation and nothing after it.
multi = q("""SELECT count(*) FROM (SELECT user_id FROM clean.events WHERE page = 'Cancellation Confirmation'
             GROUP BY 1 HAVING count(*) > 1)""")
check("one cancellation per churner", multi == 0, f"{multi} users with more than one")
after = q("""SELECT count(*) FROM clean.events e JOIN clean.users u USING (user_id)
             WHERE u.churned AND e.event_ts > u.churn_ts""")
check("no events after cancellation", after == 0, f"{after} events after churn")

# 7. Users table covers every user exactly once.
n_users = q("SELECT count(*) FROM clean.users")
n_distinct = q("SELECT count(DISTINCT user_id) FROM clean.events")
check("users table = distinct users", n_users == n_distinct, f"{n_users} vs {n_distinct}")

if failures:
    sys.exit(f"\n{len(failures)} quality check(s) failed: {', '.join(failures)}")
print(f"\nall quality checks passed")
