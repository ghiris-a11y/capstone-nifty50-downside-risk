"""P6: export dashboard data to frontend/public/data/ (derived data only; the repository is public).

  python src/export_dashboard_json.py              # full export, run locally after a model run
  python src/export_dashboard_json.py --live-only  # run by the daily Action: live_risk.json + meta.json

Contents: test results, returns, VaR/ES forecasts, breach counts and Plotly figure JSON from
src/make_figures.py. No raw OHLCV price levels are written (a guard below rejects price-like columns).
"""
import argparse
import glob
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(ROOT, "outputs", "tables")
OUT = os.path.join(ROOT, "frontend", "public", "data")
LABELS = {"price": "Price/volume only",
          "price_vixlevel": "Price/volume + India VIX level (selected on validation)",
          "price_vixrel": "Price/volume + VIX relative to 60-day mean (selected stationary variant)",
          "price_fxchg": "Price/volume + USD/INR changes",
          "price_vixrel_fxchg": "Price/volume + VIX relative + USD/INR changes",
          "price_vixrel_fxchg_repo": "Price/volume + VIX relative + USD/INR + repo-rate changes"}
FORBIDDEN = {"open", "high", "low", "close", "adj_close", "volume", "last_adj_close", "india_vix", "Open", "High",
             "Low", "Close", "Volume"}


def clean(obj):
    """JSON-safe: NaN -> None, numpy -> python."""
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        return None if not np.isfinite(obj) else round(float(obj), 8)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def write(name, obj):
    path = os.path.join(OUT, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(clean(obj), f, separators=(",", ":"))


def records(df):
    bad = FORBIDDEN & set(df.columns)
    if bad:
        raise SystemExit(f"refusing to export raw price columns: {bad}")
    return df.to_dict(orient="records")


def export_live():
    p = os.path.join(ROOT, "outputs", "live", "latest_risk.csv")
    if not os.path.exists(p):
        print("no outputs/live/latest_risk.csv; live_risk.json not written")
        return None
    r = pd.read_csv(p)
    write("live_risk.json", records(r))
    return str(r["as_of"].max()), str(r["generated_utc"].max())


def update_meta(live):
    path = os.path.join(OUT, "meta.json")
    meta = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    if live:
        meta["live_as_of"], meta["live_generated_utc"] = live
    meta["exported_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    meta["macro_note"] = macro_note()  # also refreshed by the daily --live-only run
    meta["approval_note"] = "Draft results: our project guide has not yet approved them."
    write("meta.json", meta)


def export_full():
    sys.path.insert(0, os.path.join(ROOT, "src"))
    import make_figures as mf
    uni = pd.read_csv(os.path.join(ROOT, "config", "universe.csv"))
    exc = pd.read_csv(os.path.join(ROOT, "config", "universe_excluded.csv"))
    man = pd.read_csv(os.path.join(ROOT, "data", "frozen", "manifest.csv"))
    sel = json.load(open(os.path.join(T, "validation", "selected_variant.json")))

    summaries, backtests, regimes, dms, breach = {}, {}, {}, {}, {}
    for lab in LABELS:
        s = pd.read_csv(os.path.join(T, f"summary_{lab}.csv"))
        summaries[lab] = records(s)
        b = pd.read_csv(os.path.join(T, f"backtest_results_{lab}.csv"))
        backtests[lab] = records(b.drop(columns=["ind_p"]).assign(ind_p=b["ind_p"]))
        regimes[lab] = records(pd.read_csv(os.path.join(T, f"regime_results_{lab}.csv")))
        c = {}
        for kind, f, al in (("fz0_95", f"diebold_mariano_{lab}.csv", None),
                            ("pinball_95", f"diebold_mariano_pinball_{lab}.csv", 0.05),
                            ("pinball_99", f"diebold_mariano_pinball_{lab}.csv", 0.01)):
            d = pd.read_csv(os.path.join(T, f))
            if al is not None:
                d = d[d.alpha == al]
            c[kind] = records(mf.dm_counts(d).reset_index())
        dms[lab] = c
        bs = pd.read_csv(os.path.join(T, f"breach_days_summary_{lab}.csv"))
        breach[lab] = records(bs)
    write("summary.json", {"labels": LABELS, "default": "price", "summary": summaries})
    write("backtest.json", backtests)
    write("regime.json", regimes)
    write("dm.json", dms)
    write("breach_summary.json", breach)
    bd = pd.read_csv(os.path.join(T, "breach_days_price.csv"))
    bd = bd[bd.alpha == 0.01]
    write("breach_days.json", {"dates": sorted(bd.date.unique().tolist()),
                               "stress": bd.drop_duplicates("date").sort_values("date").stress_day.tolist(),
                               "nifty_ret": bd.drop_duplicates("date").sort_values("date").nifty_ret.round(6).tolist(),
                               "models": {m: g.sort_values("date").breaches.tolist() for m, g in bd.groupby("model")}})
    write("stocks.json", records(uni[["ticker", "name", "sector", "first_date", "n_days"]]))
    write("excluded.json", records(exc[["ticker", "name", "sector", "reason"]]))
    write("exclusion_review.json", records(pd.read_csv(os.path.join(T, "exclusion_review.csv"))))
    write("validation.json", {"selection": sel,
                              "variants": records(pd.read_csv(os.path.join(T, "validation", "variant_selection.csv")))})
    write("feature_ranges.json", records(pd.read_csv(os.path.join(T, "diag_feature_ranges_summary.csv"))))
    write("shap.json", records(pd.read_csv(os.path.join(T, "xgb_shap_importance_price_vixlevel_summary.csv"))))

    # daily VaR per stock (price set): columnar to keep files small
    files = glob.glob(os.path.join(T, "by_ticker", "price", "*__daily.parquet"))
    for f in files:
        d = pd.read_parquet(f)
        t = d.ticker.iloc[0]
        base = d[(d.model == "GJR-t") & (d.alpha == 0.01)].sort_values("date")
        out = {"ticker": t, "dates": pd.to_datetime(base.date).dt.strftime("%Y-%m-%d").tolist(),
               "ret": base.ret.round(6).tolist(), "var": {}, "es": {}}
        for (m, a), g in d.groupby(["model", "alpha"]):
            g = g.sort_values("date")
            key = f"{m}|{int(round((1 - a) * 100))}"
            out["var"][key] = g["var"].round(6).tolist()
            out["es"][key] = g["es"].round(6).tolist()
        write(f"daily/{t.replace('&', '_and_')}.json", out)

    caps = mf.captions()
    figs = {}
    os.makedirs(os.path.join(OUT, "figures"), exist_ok=True)
    for name, fn in mf.FIGURES.items():
        fig = fn()
        fig.update_layout(width=None, autosize=True)
        with open(os.path.join(OUT, "figures", f"{name}.json"), "w", encoding="utf-8") as fh:
            fh.write(fig.to_json())
        figs[name] = caps[name]
    write("figures/index.json", figs)

    meta = {"snapshot_utc": man.snapshot_utc.iloc[0], "data_first": man.first_date.min(), "data_last": man.last_date.max(),
            "test_start": "2024-01-01", "n_stocks": int(len(uni)), "n_excluded": int(len(exc)),
            "train_end": "2021-12-31", "val_end": "2023-12-31", "hike_date": "2026-10-07",
            "macro_note": macro_note(),
            "approval_note": "Draft results: our project guide has not yet approved them.",
            "results_generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
    write("meta.json", meta)
    print(f"exported {len(files)} daily files and {len(figs)} figures to {OUT}")


def macro_note():
    """Scope sentence for the dashboard. Interest rates count as tested only when a verified repo-rate file exists and a
    labelled run with the ratechg features is in outputs/ (CPI and IIP are excluded by design: monthly, late, revised)."""
    path = os.path.join(ROOT, "data", "raw", "repo_rate.csv")
    verified = False
    if os.path.exists(path):
        rr = pd.read_csv(path)
        verified = not rr["value"].isna().any() and (rr.get("status", pd.Series(["VERIFIED"])).astype(str).str.strip().str.upper() == "VERIFIED").all()
    tested = verified and any("repo" in f for f in os.listdir(T) if f.startswith("summary_"))
    if tested:
        # one plain sentence on the effect, from the 99% ML miss rates with and without repo-rate changes
        base = pd.read_csv(os.path.join(T, "summary_price_vixrel_fxchg.csv")).set_index(["model", "alpha"])
        repo = pd.read_csv(os.path.join(T, "summary_price_vixrel_fxchg_repo.csv")).set_index(["model", "alpha"])
        ml = ["XGBoost", "RandomForest", "MLP"]
        shift = max(abs(repo.loc[(m, 0.01)].exc_rate - base.loc[(m, 0.01)].exc_rate) for m in ml) * 100
        closer = sum(abs(repo.loc[(m, 0.01)].exc_rate - 0.01) < abs(base.loc[(m, 0.01)].exc_rate - 0.01) for m in ml)
        effect = (f"they changed how often the machine-learning models were beaten by at most {shift:.2f} points, so they did not help"
                  if shift < 0.10 else
                  f"they brought {closer} of 3 machine-learning models closer to expected" if closer else
                  "they did not bring the machine-learning models closer to expected")
        return (f"Interest-rate changes were tested as an extra input: {effect}. Price rises and factory output were left out "
                "on purpose: they come monthly and late.")
    return ("The models use market data only. Interest rates, price rises and factory output were left out on purpose: "
            "they change rarely or come monthly and late.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live-only", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if not a.live_only:
        export_full()
    update_meta(export_live())


if __name__ == "__main__":
    main()
