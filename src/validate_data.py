"""Validate the frozen snapshot (P2 step 4) and write data/logs/validation_report.md.

Checks: manifest hashes; nulls; non-positive prices; duplicate dates; one-day moves above 20%;
zero-volume placeholder rows and stock dates absent from the ^NSEI calendar; adjusted close
compared with an independent second download (data/raw/universe_check/) for 5 sample tickers.
Reads data/frozen/ only; never writes to it. Exit code 1 if a blocking check fails.

  python src/validate_data.py
"""
import hashlib
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yahoo import ROOT, file_name  # noqa: E402

FROZEN = os.path.join(ROOT, "data", "frozen")
SECOND = os.path.join(ROOT, "data", "raw", "universe_check")
SAMPLE = ["RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "TCS.NS", "SBIN.NS"]


def main():
    man = pd.read_csv(os.path.join(FROZEN, "manifest.csv"))
    nsei = pd.read_parquet(os.path.join(FROZEN, file_name("^NSEI")))
    out, blocking = [], []
    out += ["# Frozen snapshot validation report", "",
            f"Snapshot: {man['snapshot_utc'].iloc[0]} | symbols: {len(man)} | "
            f"dates {man['first_date'].min()} to {man['last_date'].max()}", ""]

    rows = []
    for r in man.itertuples(index=False):
        path = os.path.join(FROZEN, r.file)
        h = hashlib.sha256(open(path, "rb").read()).hexdigest()
        df = pd.read_parquet(path)
        px = df[["Open", "High", "Low", "Close"]]
        is_stock = not (r.symbol.startswith("^") or r.symbol == "INR=X")
        ret = np.log(df["Close"]).diff()
        zero_vol = df.index[(df["Volume"] <= 0)] if is_stock else pd.DatetimeIndex([])
        off_cal = df.index.difference(nsei.index) if is_stock else pd.DatetimeIndex([])
        rec = dict(symbol=r.symbol, rows=len(df), hash_ok=h == r.sha256, nulls=int(px.isna().sum().sum()),
                   non_positive=int((px <= 0).sum().sum()), duplicate_dates=int(df.index.duplicated().sum()),
                   moves_over_20pct="; ".join(f"{d.date()} {v:+.1%}" for d, v in ret[ret.abs() > 0.20].items()),
                   zero_volume_rows="; ".join(str(d.date()) for d in zero_vol),
                   dates_not_in_nifty="; ".join(str(d.date()) for d in off_cal))
        rows.append(rec)
        if not rec["hash_ok"] or rec["nulls"] or rec["non_positive"] or rec["duplicate_dates"]:
            blocking.append(r.symbol)
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(ROOT, "data", "logs", "validation_checks.csv"), index=False)

    out += ["## Blocking checks", "",
            f"- Manifest SHA-256 matches: {int(t.hash_ok.sum())}/{len(t)}",
            f"- Symbols with nulls: {int((t.nulls > 0).sum())}",
            f"- Symbols with non-positive prices: {int((t.non_positive > 0).sum())}",
            f"- Symbols with duplicate dates: {int((t.duplicate_dates > 0).sum())}",
            f"- Result: {'PASS' if not blocking else 'FAIL: ' + ', '.join(blocking)}", ""]

    zv = t[t.zero_volume_rows != ""]
    dates = pd.Series([d for s in zv.zero_volume_rows for d in s.split("; ")]).value_counts()
    out += ["## Zero-volume placeholder rows (dropped and logged by the pipeline loader)", "",
            f"{len(zv)} stocks have such rows. Dates and number of stocks affected:", ""]
    out += [f"- {d}: {n} stocks{' (not a ^NSEI trading day)' if pd.Timestamp(d) not in nsei.index else ' (^NSEI traded)'}"
            for d, n in dates.sort_index().items()]
    oc = pd.Series([d for s in t.dates_not_in_nifty if s for d in s.split("; ")]).value_counts()
    out += ["", "## Stock dates absent from the ^NSEI calendar", ""]
    out += [f"- {d}: {n} stocks" for d, n in oc.sort_index().items()] or ["- none"]

    out += ["", "## One-day log moves above 20% (flag only; kept as genuine unless excluded in config/universe_excluded.csv)", ""]
    out += [f"- {r.symbol}: {r.moves_over_20pct}" for r in t.itertuples() if r.moves_over_20pct] or ["- none"]

    out += ["", "## Adjusted close vs an independent second download (5 sample tickers)", ""]
    for s in SAMPLE:
        a = pd.read_parquet(os.path.join(FROZEN, file_name(s)))["Close"]
        p2 = os.path.join(SECOND, file_name(s))
        if not os.path.exists(p2):
            out.append(f"- {s}: second download missing")
            continue
        b = pd.read_parquet(p2)["Close"]
        j = a.index.intersection(b.index)
        rel = (a[j] / b[j] - 1).abs()
        out.append(f"- {s}: {len(j)} common dates, max relative difference {rel.max():.2e}, "
                   f"dates differing by more than 0.1%: {int((rel > 1e-3).sum())}")
    out += ["", "Yahoo's adjusted closes differ by tiny floating-point amounts between downloads; this is why "
            "every report number is computed from this frozen copy only.", ""]
    path = os.path.join(ROOT, "data", "logs", "validation_report.md")
    open(path, "w", encoding="utf-8").write("\n".join(out))
    print("\n".join(out))
    sys.exit(1 if blocking else 0)


if __name__ == "__main__":
    main()
