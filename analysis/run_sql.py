"""Step 2: build the DuckDB database from the SQL files, in file-name order.
raw.*  = the JSON as it came, clean.* = typed and filtered, analytics.* = metric tables.
Every aggregate analytics table is also written to outputs/<table>.csv (small, aggregated, safe to publish).
"""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/encore.duckdb"
RAW = ROOT / "data/raw/mini_sparkify_event_data.json"

DB.unlink(missing_ok=True)  # rebuild from scratch every run, so results never depend on old state
con = duckdb.connect(str(DB))
con.execute("SET threads=4; SET memory_limit='3GB'")
con.execute("CREATE SCHEMA raw; CREATE SCHEMA clean; CREATE SCHEMA analytics;")

for f in sorted((ROOT / "sql").glob("*.sql")):
    sql = f.read_text().replace("{RAW_PATH}", str(RAW))
    print(f"  {f.name}")
    con.execute(sql)

out = ROOT / "outputs"
out.mkdir(exist_ok=True)
tables = con.execute(
    "SELECT table_name FROM information_schema.tables WHERE table_schema='analytics' ORDER BY 1"
).fetchall()
for (t,) in tables:
    if t.endswith("_users"):  # user-level tables stay in the database, only aggregates are published
        continue
    con.execute(f"COPY analytics.{t} TO '{out / (t + '.csv')}' (HEADER)")
print("  wrote aggregate analytics tables to outputs/")
