"""Why did India VIX and USD/INR features degrade the ML models? (diagnosis step 3a)

For every stock and feature, compare the test-window values (2024-01-01 onwards) with the range the
models were fitted on:
  * train range       2015 .. TRAIN_END (2021-12-31): range seen when RF/MLP residuals are calibrated
  * train+val range   2015 .. VAL_END   (2023-12-31): range of the final fit used for test forecasts
and report the share of test days outside each range. Tree models (XGBoost, Random Forest) cannot
extrapolate beyond the fitted range; an MLP extrapolates in an uncontrolled way.

Reads data/frozen only. Writes outputs/tables/diag_feature_ranges.csv (per stock x feature) and
outputs/tables/diag_feature_ranges_summary.csv (median across stocks).

  python src/feature_diagnostics.py
"""
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import nifty50_var_pipeline as p  # noqa: E402

GROUPS = "price+vix+macro+vrel+fxchg"   # every feature family, so one pass covers all variants
FAMILY = {"vix": "VIX level", "vix_chg": "VIX level", "rv_x_vix": "VIX level",
          "usdinr": "USD/INR level", "usdinr_chg": "USD/INR level",
          "vix_rel60": "VIX relative (stationary)", "vix_rel60_chg": "VIX relative (stationary)",
          "usdinr_ret1": "USD/INR change (stationary)", "usdinr_ret21": "USD/INR change (stationary)"}


def main(test_end="2026-11-18"):
    os.chdir(ROOT)
    p.FROZEN_DIR = os.path.join("data", "frozen")
    uni = pd.read_csv(os.path.join("config", "universe.csv"))
    vix = p.load_series("^INDIAVIX", "2015-01-01", test_end)
    rows = []
    for t in uni["ticker"]:
        px = p.load_prices(t, "2015-01-01", test_end)
        ret = np.log(px["Close"]).diff().dropna()
        macro = p.load_macro(ret.index, "2015-01-01", test_end)
        X = p.build_features(ret, vix, macro, px["Volume"].reindex(ret.index), GROUPS).dropna()
        tr, trva, te = X[X.index <= p.TRAIN_END], X[X.index <= p.VAL_END], X[X.index >= p.TEST_START]
        for c in X.columns:
            for lab, base in (("train", tr), ("train_val", trva)):
                lo, hi = base[c].min(), base[c].max()
                out = ((te[c] < lo) | (te[c] > hi)).mean()
                rows.append(dict(ticker=t, feature=c, family=FAMILY.get(c, "price/volume"), fit_window=lab,
                                 fit_min=lo, fit_max=hi, test_min=te[c].min(), test_max=te[c].max(),
                                 test_share_outside=out, test_share_above=(te[c] > hi).mean(),
                                 test_share_below=(te[c] < lo).mean()))
    d = pd.DataFrame(rows)
    os.makedirs(os.path.join("outputs", "tables"), exist_ok=True)
    d.to_csv(os.path.join("outputs", "tables", "diag_feature_ranges.csv"), index=False)
    s = (d.groupby(["family", "feature", "fit_window"])
           .agg(median_share_outside=("test_share_outside", "median"),
                max_share_outside=("test_share_outside", "max"),
                median_share_above=("test_share_above", "median"),
                median_share_below=("test_share_below", "median"),
                fit_min_median=("fit_min", "median"), fit_max_median=("fit_max", "median"),
                test_min_median=("test_min", "median"), test_max_median=("test_max", "median"))
           .reset_index().sort_values(["fit_window", "median_share_outside"], ascending=[True, False]))
    s.to_csv(os.path.join("outputs", "tables", "diag_feature_ranges_summary.csv"), index=False)
    pd.set_option("display.width", 220)
    print(s[s.fit_window == "train_val"][["family", "feature", "median_share_outside", "median_share_above",
                                          "median_share_below", "fit_min_median", "fit_max_median",
                                          "test_min_median", "test_max_median"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
