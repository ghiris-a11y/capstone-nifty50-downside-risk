"""Choose ML feature variants on the validation window only (step 3, selection).

Validation protocol (runs in outputs/tables/validation/, created before any test-window rerun):
  ML models trained on 2015-2019, residual calibration 2020-2021, out-of-sample evaluation 2022-2023.
  The 2024-2026 test window is not read by this script.

Pre-registered rule (fixed before the validation results were read):
  for each ML model, stock and VaR level compute pinball loss of the variant / pinball loss of the
  price-only set; average the ratio over stocks and both levels; a variant's score is the mean of that
  ratio over XGBoost, Random Forest and MLP. Lowest score = selected. Calibration (|exception rate -
  nominal|) is reported alongside but is not part of the score.

Writes outputs/tables/validation/variant_selection.csv and selected_variant.json.
"""
import json
import os
from datetime import datetime, timezone

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAL = os.path.join(ROOT, "outputs", "tables", "validation")
VARIANTS = {  # label -> what the set actually contains
    "val_price": "price/volume only",
    "val_price_vixlevel": "price/volume + India VIX level (vix, vix_chg, rv_x_vix)",
    "val_price_vixlevel_fxlevel": "price/volume + VIX level + USD/INR level (usdinr, usdinr_chg)",
    "val_price_vixrel": "price/volume + VIX relative to its 60-day mean (stationary)",
    "val_price_fxchg": "price/volume + USD/INR 1- and 21-day log changes (stationary)",
    "val_price_vixrel_fxchg": "price/volume + VIX relative + USD/INR changes (stationary)",
}
ML = ["XGBoost", "RandomForest", "MLP"]


def main():
    bt = {k: pd.read_csv(os.path.join(VAL, f"backtest_results_{k}.csv")) for k in VARIANTS}
    for k, d in bt.items():
        assert d["n"].max() <= 502, f"{k}: more rows than the 2022-2023 window"  # sanity: validation only
    base = bt["val_price"].set_index(["ticker", "model", "alpha"])["pinball"]
    rows = []
    for k, d in bt.items():
        d = d[d["model"].isin(ML)].set_index(["ticker", "model", "alpha"])
        rel = (d["pinball"] / base.reindex(d.index)).rename("rel")
        for m in ML:
            dm = d.xs(m, level="model")
            rows.append(dict(variant=k, contains=VARIANTS[k], model=m,
                             rel_pinball=float(rel.xs(m, level="model").mean()),
                             exc95=float(dm.xs(0.05, level="alpha")["exc_rate"].mean()),
                             exc99=float(dm.xs(0.01, level="alpha")["exc_rate"].mean()),
                             calib_err=float(((dm.xs(0.05, level="alpha")["exc_rate"] - 0.05).abs().mean()
                                              + (dm.xs(0.01, level="alpha")["exc_rate"] - 0.01).abs().mean()) / 2),
                             kupiec99=float(dm.xs(0.01, level="alpha")["pass_kupiec"].mean()),
                             fz0_median_stocks=float(dm.xs(0.05, level="alpha")["fz0"].median())))
    t = pd.DataFrame(rows)
    score = t.groupby("variant")["rel_pinball"].mean().rename("score")
    t = t.merge(score, on="variant").sort_values(["score", "model"])
    t.to_csv(os.path.join(VAL, "variant_selection.csv"), index=False)
    stationary = [v for v in VARIANTS if "vixrel" in v or "fxchg" in v]
    best_all = score.idxmin()
    best_stat = score[stationary].idxmin()
    best_by_model = t.loc[t.groupby("model")["rel_pinball"].idxmin(), ["model", "variant"]].set_index("model")["variant"].to_dict()
    sel = dict(created_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
               rule="lowest mean (variant pinball / price-only pinball) over stocks, 95%+99%, and the 3 ML models; "
                    "validation window 2022-2023 only",
               selected_overall=best_all, selected_stationary=best_stat, best_by_model=best_by_model,
               scores=score.round(4).to_dict())
    json.dump(sel, open(os.path.join(VAL, "selected_variant.json"), "w"), indent=2)
    pd.set_option("display.width", 220)
    print(t.round(4).to_string(index=False))
    print(json.dumps(sel, indent=2))


if __name__ == "__main__":
    main()
