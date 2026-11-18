"""Build the balanced panel (P2 step 2).

Keeps candidates whose first valid price is on or before --first-by (default 2015-01-15) and that
have no gap longer than --max-gap trading days (measured against the ^NSEI calendar).
Writes config/universe.csv and config/universe_excluded.csv; raw downloads are cached in
data/raw/universe_check/ (not committed) and reused by validate_data.py as a second download.

  python src/build_universe.py --end 2026-11-18
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yahoo import ROOT, fetch, file_name  # noqa: E402

# Known corporate events to flag (dates from company / exchange announcements)
EVENTS = {
    "HDFCBANK.NS": [("2023-07-13", "HDFC Ltd merged into HDFC Bank (effective 1 Jul 2023, new shares listed 13 Jul 2023)")],
    "TMPV.NS": [("2025-10-14", "Tata Motors demerger: commercial-vehicle business split off; listed entity renamed "
                               "Tata Motors Passenger Vehicles")],
}


def max_gap(px_index, cal_index):
    """Longest run of consecutive market days (from cal_index) missing in px_index."""
    cal = cal_index[(cal_index >= px_index.min()) & (cal_index <= px_index.max())]
    missing = ~cal.isin(px_index)
    run = best = 0
    for m in missing:
        run = run + 1 if m else 0
        best = max(best, run)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2015-01-01")
    ap.add_argument("--end", required=True, help="exclusive end date (yfinance convention)")
    ap.add_argument("--first-by", default="2015-01-15")
    ap.add_argument("--max-gap", type=int, default=10)
    ap.add_argument("--ca-move", type=float, default=0.35,
                    help="|one-day log move| at or above this, while the Nifty moves less than --ca-nifty, "
                         "is treated as an unadjusted corporate action and the stock is excluded")
    ap.add_argument("--ca-nifty", type=float, default=0.03)
    ap.add_argument("--use-cache", action="store_true", help="reuse data/raw/universe_check downloads")
    a = ap.parse_args()

    cand = pd.read_csv(os.path.join(ROOT, "config", "nifty50_dec2025_candidates.csv"))
    cache = os.path.join(ROOT, "data", "raw", "universe_check")
    os.makedirs(cache, exist_ok=True)

    def get(sym):
        path = os.path.join(cache, file_name(sym))
        if a.use_cache and os.path.exists(path):
            return pd.read_parquet(path)
        df = fetch(sym, a.start, a.end, stage="build_universe")
        if len(df):
            df.to_parquet(path)
        return df

    nsei = get("^NSEI")
    cal = nsei.index
    nifty_ret = np.log(nsei["Close"]).diff()

    keep, drop = [], []
    for r in cand.itertuples(index=False):
        df = get(r.ticker)
        if not len(df):
            drop.append(dict(ticker=r.ticker, name=r.name, sector=r.sector, reason="no data returned by Yahoo"))
            continue
        valid = df[(df["Close"] > 0)].dropna(subset=["Close"])
        first = valid.index.min()
        gap = max_gap(valid.index, cal)
        ret = np.log(valid["Close"]).diff()
        big = ret[ret.abs() > 0.20]
        flags = [f"{d}: {txt}" for d, txt in EVENTS.get(r.ticker, [])]
        flags += [f"{d.date()}: one-day log move {v:+.1%}" for d, v in big.items()]
        zero_vol = int((valid["Volume"] <= 0).sum())
        row = dict(ticker=r.ticker, name=r.name, sector=r.sector, first_date=str(first.date()),
                   last_date=str(valid.index.max().date()), n_days=len(valid), max_gap_days=gap,
                   zero_volume_rows=zero_vol, flags=" | ".join(flags))
        if first > pd.Timestamp(a.first_by):
            drop.append({**row, "reason": f"first price {first.date()} after {a.first_by}"})
        elif gap > a.max_gap:
            drop.append({**row, "reason": f"gap of {gap} trading days > {a.max_gap}"})
        elif len(ca := ret[(ret.abs() >= a.ca_move) & (nifty_ret.reindex(ret.index).abs() < a.ca_nifty)]):
            drop.append({**row, "reason": "suspected unadjusted corporate action: " + "; ".join(
                f"{d.date()} move {v:+.1%} vs Nifty {nifty_ret.get(d, np.nan):+.1%}" for d, v in ca.items())})
        else:
            keep.append(row)
        print(f"{r.ticker:15s} first {first.date()} gap {gap:3d} {'KEEP' if keep and keep[-1]['ticker'] == r.ticker else 'DROP'}"
              + (f"  FLAGS: {row['flags']}" if row["flags"] else ""))

    uni = pd.DataFrame(keep)
    uni.to_csv(os.path.join(ROOT, "config", "universe.csv"), index=False)
    pd.DataFrame(drop).to_csv(os.path.join(ROOT, "config", "universe_excluded.csv"), index=False)
    print(f"\nUniverse: {len(uni)} stocks kept, {len(drop)} excluded "
          f"(rule: first price <= {a.first_by}, max gap <= {a.max_gap} trading days)")


if __name__ == "__main__":
    main()
