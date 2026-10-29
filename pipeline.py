"""Run the whole project with one command:   python pipeline.py

Steps (each one stops everything if it fails):
  1. download    scripts/download.py          get the raw file, check its size and fingerprint
  2. build       analysis/run_sql.py          raw -> clean -> analytics tables in DuckDB, CSVs in outputs/
  3. check       tests/check_quality.py       data-quality checks; any FAIL stops the pipeline
  4. model       analysis/churn_model.py      churn model, test-set results
  5. experiment  analysis/experiment_snapshots.py   the "more snapshots" idea that did not help
  6. robustness  analysis/robustness.py       repeat the model test on 7 different dates, report all
  7. decide      analysis/decision.py         sizing of the save options + A/B test size

Use --from <step> to restart from a step, e.g.  python pipeline.py --from model
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [
    ("download", "scripts/download.py"),
    ("build", "analysis/run_sql.py"),
    ("check", "tests/check_quality.py"),
    ("model", "analysis/churn_model.py"),
    ("experiment", "analysis/experiment_snapshots.py"),
    ("robustness", "analysis/robustness.py"),
    ("decide", "analysis/decision.py"),
]

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--from", dest="start", choices=[s for s, _ in STEPS], default="download")
args = parser.parse_args()

names = [s for s, _ in STEPS]
start = time.time()
for name, script in STEPS[names.index(args.start):]:
    print(f"\n=== {name}: {script}", flush=True)
    t = time.time()
    result = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT)
    if result.returncode != 0:
        sys.exit(f"\nPIPELINE FAILED at step '{name}' ({script}), exit code {result.returncode}")
    print(f"--- {name} done in {time.time() - t:.1f}s", flush=True)
print(f"\nPIPELINE OK in {time.time() - start:.1f}s - results are in outputs/")
