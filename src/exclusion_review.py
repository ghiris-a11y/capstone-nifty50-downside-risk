"""Review of the three stocks excluded as suspected unadjusted corporate actions (step 5).

For TRENT, ADANIENT and TMPV lists every one-day log move above 20% with the Nifty move that day,
volume relative to the previous 20-day median, and whether the new price level persisted
(mean close of the next 10 days / close on the event day). Each move is then classified:

  * unadjusted corporate action: large move, Nifty flat, price level persists (no rebound); and a
    documented corporate event where one is known
  * data error: large move that reverses within a few days with the Nifty flat
  * genuine move: market-wide day (|Nifty| >= 3%) or a documented news event

Data: data/raw/universe_check/ (independent download of 18 Nov 2026, same day as the frozen
snapshot; these stocks are not in data/frozen because they were excluded).
Writes outputs/tables/exclusion_review.csv.
"""
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from yahoo import file_name  # noqa: E402

CACHE = os.path.join(ROOT, "data", "raw", "universe_check")
# Documented events (source noted; [UNVERIFIED] where not yet confirmed against NSE corporate-action records)
KNOWN = {
    ("TMPV.NS", "2025-10-14"): "Tata Motors demerger ex-date (commercial-vehicle business split off); company announcement",
    ("ADANIENT.NS", "2015-06-03"): "consistent with the 2015 demerger of Adani Transmission from Adani Enterprises [UNVERIFIED]",
    ("ADANIENT.NS", "2023-01-27"): "Hindenburg Research report (25 Jan 2023) sell-off: genuine news-driven move",
    ("ADANIENT.NS", "2023-02-01"): "Hindenburg sell-off and withdrawal of the follow-on public offer: genuine move",
    ("ADANIENT.NS", "2023-02-02"): "Hindenburg sell-off continued: genuine move",
    ("ADANIENT.NS", "2024-11-21"): "US indictment news involving Adani group: genuine move",
    ("ADANIENT.NS", "2024-06-04"): "general-election result day (market-wide sell-off): genuine move",
}


def main():
    nsei = pd.read_parquet(os.path.join(CACHE, file_name("^NSEI")))["Close"]
    nret = np.log(nsei).diff()
    rows = []
    for t in ("TRENT.NS", "ADANIENT.NS", "TMPV.NS"):
        px = pd.read_parquet(os.path.join(CACHE, file_name(t)))
        px = px[px["Volume"] > 0]
        ret = np.log(px["Close"]).diff()
        for d, v in ret[ret.abs() > 0.20].items():
            i = px.index.get_loc(d)
            vol_ratio = px["Volume"].iloc[i] / px["Volume"].iloc[max(0, i - 20):i].median()
            after = px["Close"].iloc[i + 1:i + 11]
            persist = after.mean() / px["Close"].iloc[i] if len(after) else np.nan
            prev = px["Close"].iloc[i - 1]
            recovered = (after.max() / prev - 1) if len(after) else np.nan
            nifty = nret.get(d, np.nan)
            known = KNOWN.get((t, str(d.date())), "")
            if abs(nifty) >= 0.03:
                cls = "genuine move (market-wide day)"
            elif "genuine" in known:
                cls = "genuine move (documented news)"
            elif abs(v) >= 0.35 and 0.85 <= persist <= 1.15 and recovered < -0.2:
                cls = "unadjusted corporate action (level persists, no rebound, Nifty flat)"
            elif recovered > -0.05 and v < 0:
                cls = "possible data error (price reverts)"
            else:
                cls = "unclassified: needs NSE corporate-action check"
            rows.append(dict(ticker=t, date=str(d.date()), log_move=v, nifty_move=nifty, volume_vs_20d_median=vol_ratio,
                             next10_mean_over_event_close=persist, best_next10_vs_prev_close=recovered,
                             classification=cls, note=known, triggered_exclusion=abs(v) >= 0.35 and abs(nifty) < 0.03))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(ROOT, "outputs", "tables", "exclusion_review.csv"), index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 70)
    print(out.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
