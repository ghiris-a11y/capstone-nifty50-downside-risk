"""Create the frozen, hashed snapshot used for every report number (P2 steps 3 and 5).

Downloads adjusted daily OHLCV for each config/universe.csv ticker plus ^NSEI, ^INDIAVIX and
INR=X, saves one parquet per symbol in data/frozen/, writes data/frozen/manifest.csv
(SHA-256, rows, first/last date, snapshot date) and marks the files read-only.
Rows are stored exactly as Yahoo returned them; placeholder rows (zero volume) are dropped and
logged later by the pipeline's loader, never here.

Refuses to run if data/frozen/ already contains a manifest (CLAUDE.md rule 5).

  python src/download_history.py --end 2026-11-18
"""
import argparse
import hashlib
import os
import stat
import sys
from datetime import datetime, timezone

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yahoo import ROOT, fetch, file_name, log_failure  # noqa: E402

FROZEN = os.path.join(ROOT, "data", "frozen")
EXTRA = ["^NSEI", "^INDIAVIX", "INR=X"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2015-01-01")
    ap.add_argument("--end", required=True, help="exclusive end date; last row is the previous trading day")
    a = ap.parse_args()

    if os.path.exists(os.path.join(FROZEN, "manifest.csv")):
        sys.exit("data/frozen/ already holds a snapshot; it is never overwritten. "
                 "Archive it by hand first if a new snapshot is really intended.")
    os.makedirs(FROZEN, exist_ok=True)
    symbols = pd.read_csv(os.path.join(ROOT, "config", "universe.csv"))["ticker"].tolist() + EXTRA
    snap = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rows, failed = [], []
    for i, s in enumerate(symbols, 1):
        df = fetch(s, a.start, a.end, stage="download_history")
        if not len(df):
            failed.append(s)
            continue
        path = os.path.join(FROZEN, file_name(s))
        df.to_parquet(path)
        rows.append(dict(symbol=s, file=file_name(s), rows=len(df), first_date=str(df.index.min().date()),
                         last_date=str(df.index.max().date()), sha256=sha256(path),
                         snapshot_utc=snap, requested_end_exclusive=a.end))
        print(f"[{i}/{len(symbols)}] {s:15s} {len(df)} rows {df.index.min().date()} .. {df.index.max().date()}")

    man = pd.DataFrame(rows)
    man.to_csv(os.path.join(FROZEN, "manifest.csv"), index=False)
    for f in os.listdir(FROZEN):  # read-only snapshot
        p = os.path.join(FROZEN, f)
        os.chmod(p, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
    print(f"\nFrozen {len(man)} symbols at {snap}; {len(failed)} failed: {failed}")
    if failed:
        for s in failed:
            log_failure(s, "download_history", "excluded from snapshot after retries")
        sys.exit(1)


if __name__ == "__main__":
    main()
