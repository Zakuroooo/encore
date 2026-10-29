"""Step 1: download the Sparkify mini event log from Udacity's public S3 bucket.
Skips the download if the file is already there and its fingerprint (SHA-256) matches.
Fails loudly if the file is the wrong size or the fingerprint does not match.
"""
import hashlib
import sys
import urllib.request
from pathlib import Path

URL = "https://udacity-dsnd.s3.amazonaws.com/sparkify/mini_sparkify_event_data.json"
OUT = Path(__file__).resolve().parents[1] / "data/raw/mini_sparkify_event_data.json"
# Checked 2026-10-29 against the S3 headers (Content-Length 128477301, Last-Modified 2019-02-02).
EXPECTED_BYTES = 128_477_301
EXPECTED_SHA256 = "94620a8c00036956d43f619f85bdded3bf8cc8996a152a9df61f8c3d6e154f97"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


OUT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists() and OUT.stat().st_size == EXPECTED_BYTES and sha256(OUT) == EXPECTED_SHA256:
    print(f"already downloaded: {OUT.name}")
    sys.exit(0)

print(f"downloading {URL}")
urllib.request.urlretrieve(URL, OUT)
size = OUT.stat().st_size
if size != EXPECTED_BYTES:
    sys.exit(f"FAIL: got {size} bytes, expected {EXPECTED_BYTES}")
digest = sha256(OUT)
if digest != EXPECTED_SHA256:
    sys.exit(f"FAIL: SHA-256 {digest} does not match the pinned {EXPECTED_SHA256}")
print(f"ok: {size:,} bytes, SHA-256 matches")
