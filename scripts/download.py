"""Step 1: download the Sparkify mini event log from Udacity's public S3 bucket.
Skips the download if the file is already there with the right size.
"""
import sys
import urllib.request
from pathlib import Path

URL = "https://udacity-dsnd.s3.amazonaws.com/sparkify/mini_sparkify_event_data.json"
OUT = Path(__file__).resolve().parents[1] / "data/raw/mini_sparkify_event_data.json"
EXPECTED_BYTES = 128_456_413  # size on S3 (Content-Length), checked 2026-10-29

OUT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists() and OUT.stat().st_size == EXPECTED_BYTES:
    print(f"already downloaded: {OUT.name}")
    sys.exit(0)

print(f"downloading {URL}")
urllib.request.urlretrieve(URL, OUT)
size = OUT.stat().st_size
if size != EXPECTED_BYTES:
    sys.exit(f"FAIL: got {size} bytes, expected {EXPECTED_BYTES}")
print(f"ok: {size:,} bytes")
