"""Breaches by day across stocks, and the share of breaches on market-wide stress days (step 6).

Reads the per-ticker daily files outputs/tables/by_ticker/<label>/*__daily.parquet (test window) and
the Nifty 50 from data/frozen. A market-wide stress day is defined in advance as a Nifty one-day log
return of -2% or worse; the share of test days that meet this definition is reported so the breach
share can be compared with it.

Writes outputs/tables/breach_days_<label>.csv (date x model x level) and
outputs/tables/breach_days_summary_<label>.csv (per model and level).

  python src/breach_days.py --label price
"""
import argparse
import glob
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from yahoo import file_name  # noqa: E402

STRESS = -0.02


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(ROOT, "outputs", "tables", "by_ticker", a.label, "*__daily.parquet")))
    if not files:
        sys.exit(f"no daily files for {a.label}")
    d = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    d["date"] = pd.to_datetime(d["date"])
    nifty = pd.read_parquet(os.path.join(ROOT, "data", "frozen", file_name("^NSEI")))["Close"]
    nret = np.log(nifty).diff().rename("nifty_ret")
    days = (d.groupby(["date", "model", "alpha"])
              .agg(breaches=("exception", "sum"), stocks=("ticker", "nunique")).reset_index()
              .merge(nret, left_on="date", right_index=True, how="left"))
    days["stress_day"] = days["nifty_ret"] <= STRESS
    days.to_csv(os.path.join(ROOT, "outputs", "tables", f"breach_days_{a.label}.csv"), index=False)

    test_days = days[["date", "stress_day"]].drop_duplicates()
    stress_share_days = test_days["stress_day"].mean()
    rows = []
    for (m, al), g in days.groupby(["model", "alpha"]):
        tot = g["breaches"].sum()
        top = g.sort_values("breaches", ascending=False).head(3)
        rows.append(dict(model=m, alpha=al, total_breaches=int(tot), test_days=len(g),
                         stress_days=int(g["stress_day"].sum()), share_of_days_stress=stress_share_days,
                         share_of_breaches_on_stress_days=g.loc[g["stress_day"], "breaches"].sum() / tot if tot else np.nan,
                         max_breaches_one_day=int(g["breaches"].max()),
                         days_with_10plus_breaches=int((g["breaches"] >= 10).sum()),
                         share_of_breaches_on_10plus_days=g.loc[g["breaches"] >= 10, "breaches"].sum() / tot if tot else np.nan,
                         top_days="; ".join(f"{r.date.date()} {int(r.breaches)} (Nifty {r.nifty_ret:+.1%})"
                                            for r in top.itertuples())))
    s = pd.DataFrame(rows)
    s.to_csv(os.path.join(ROOT, "outputs", "tables", f"breach_days_summary_{a.label}.csv"), index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 90)
    print(f"stress days (Nifty <= {STRESS:.0%}): {int(test_days['stress_day'].sum())} of {len(test_days)} test days "
          f"({stress_share_days:.1%})")
    print(s.drop(columns=["share_of_days_stress"]).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
