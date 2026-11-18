"""Pilot (P1) analysis: tables and figures built only from pipeline outputs.

Reads outputs/{summary,backtest_results,regime_results,diebold_mariano}_<tag>.csv and
re-creates the daily VaR/ES forecasts by calling the unchanged functions in
nifty50_var_pipeline.py (same data, same seeds). The re-created exception counts are
checked against backtest_results_<tag>.csv before anything is written.

Usage:
  python src/pilot_analysis.py --tickers RELIANCE.NS,HDFCBANK.NS,INFY.NS \
      --features price+vix --test-end 2026-11-18
"""
import argparse, os, sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import nifty50_var_pipeline as p  # noqa: E402

HIKE_DATE = "2026-10-07"   # RBI repo hike to 5.50%
GARCH_MODELS = ["GARCH-normal", "GARCH-t", "EGARCH-normal", "EGARCH-t", "GJR-normal", "GJR-t"]
ML_MODELS = ["XGBoost", "RandomForest", "MLP"]
BENCH = ["HistSim250"]
MODEL_ORDER = GARCH_MODELS + BENCH + ML_MODELS
# GARCH = red palette, ML = blue palette, benchmark = neutral grey (colour-blind safe pairs)
COLOURS = {"GARCH-normal": "#fcae91", "GARCH-t": "#fb6a4a", "EGARCH-normal": "#ef3b2c",
           "EGARCH-t": "#cb181d", "GJR-normal": "#a50f15", "GJR-t": "#67000d",
           "HistSim250": "#7f7f7f",
           "XGBoost": "#08519c", "RandomForest": "#3182bd", "MLP": "#6baed6"}


def family(m):
    return "GARCH" if m in GARCH_MODELS else ("ML" if m in ML_MODELS else "Benchmark")


def daily_forecasts(tickers, features, start, test_end):
    """Same steps as run_ticker() in the pipeline, but keeps the daily VaR/ES series."""
    vix = p.load_series("^INDIAVIX", start, test_end)
    rows = []
    for t in tickers:
        px = p.load_prices(t, start, test_end)
        ret = np.log(px["Close"]).diff().dropna()
        macro = p.load_macro(ret.index, start, test_end)
        X_all = p.build_features(ret, vix, macro, px["Volume"].reindex(ret.index), features)
        data = pd.concat([X_all, ret.rename("y")], axis=1).dropna()
        X, y = data.drop(columns="y"), data["y"]
        fc = {}
        for kind in ("GARCH", "EGARCH", "GJR"):
            for dist in ("normal", "t"):
                try:
                    fc[f"{kind}-{dist}"] = p.garch_forecasts(ret, kind, dist, p.TEST_START)
                except Exception as ex:  # same behaviour as the pipeline
                    print(f"  {t} {kind}-{dist} failed: {ex}")
        fc["HistSim250"] = p.hist_sim(ret, p.TEST_START)
        fc["XGBoost"] = p.xgb_quantile(X, y)
        fc["RandomForest"] = p.vol_scaled(X, y, "rf")
        fc["MLP"] = p.vol_scaled(X, y, "mlp")
        yt = ret[ret.index >= p.TEST_START]
        lag_vix = vix.reindex(ret.index).ffill().shift(1)
        for m, d in fc.items():
            for a, (var, es) in d.items():
                df = pd.DataFrame({"date": var.index, "ticker": t, "model": m, "alpha": a,
                                   "ret": yt.reindex(var.index).values, "var": var.values,
                                   "es": es.reindex(var.index).values,
                                   "vix_prev": lag_vix.reindex(var.index).values})
                rows.append(df)
    out = pd.concat(rows, ignore_index=True)
    out["exception"] = (out["ret"] < -out["var"]).astype(int)
    return out


def check_against_pipeline(daily, bt):
    got = daily.groupby(["ticker", "model", "alpha"])["exception"].agg(["sum", "size"]).reset_index()
    m = bt.merge(got, on=["ticker", "model", "alpha"], how="outer")
    bad = m[(m["sum"] != m["exceptions"]) | (m["size"] != m["n"])]
    if len(bad):
        raise SystemExit(f"Re-created forecasts do not match pipeline output:\n{bad}")
    print(f"Consistency check passed: {len(m)} ticker/model/alpha rows match backtest_results.")


def build_tables(tag, daily, bt, summ, reg, dm, outdir):
    os.makedirs(outdir, exist_ok=True)
    # 1. headline table per model and level
    ind = (bt.assign(pass_ind=bt["ind_p"] > 0.05)
             .groupby(["model", "alpha"])["pass_ind"].mean().rename("pass_ind"))
    t1 = summ.join(ind, on=["model", "alpha"]).reset_index()
    t1["family"] = t1["model"].map(family)
    t1["nominal"] = t1["alpha"]
    t1["model"] = pd.Categorical(t1["model"], MODEL_ORDER, ordered=True)
    t1 = t1.sort_values(["alpha", "model"], ascending=[False, True])
    t1.to_csv(f"{outdir}/pilot_model_summary_{tag}.csv", index=False)

    # 2. mean FZ0 (95%) by India VIX quartile
    t2 = reg.groupby(["model", "regime"], observed=True)["mean_fz0"].mean().unstack("regime")
    t2 = t2.reindex(MODEL_ORDER)
    t2.to_csv(f"{outdir}/pilot_fz0_by_vix_quartile_{tag}.csv")

    # 3. post-hike window (on and after the repo-hike date)
    post = daily[daily["date"] >= HIKE_DATE]
    t3 = (post.groupby(["model", "alpha"])
              .agg(days=("date", "nunique"), obs=("exception", "size"),
                   exceptions=("exception", "sum"), exc_rate=("exception", "mean"))
              .reset_index())
    t3["model"] = pd.Categorical(t3["model"], MODEL_ORDER, ordered=True)
    t3 = t3.sort_values(["alpha", "model"], ascending=[False, True])
    t3.to_csv(f"{outdir}/pilot_post_hike_{tag}.csv", index=False)

    # 4. Diebold-Mariano: each ML model vs each GARCH model (95% FZ0); negative stat = ML lower loss
    d = dm.copy()
    flip = d["model_a"].isin(GARCH_MODELS + BENCH) & d["model_b"].isin(ML_MODELS)
    d.loc[flip, ["model_a", "model_b"]] = d.loc[flip, ["model_b", "model_a"]].values
    d.loc[flip, "dm_stat"] = -d.loc[flip, "dm_stat"]
    d = d[d["model_a"].isin(ML_MODELS) & d["model_b"].isin(GARCH_MODELS)]
    t4 = (d.assign(ml_better=(d["p"] < 0.05) & (d["dm_stat"] < 0),
                   garch_better=(d["p"] < 0.05) & (d["dm_stat"] > 0),
                   no_diff=d["p"] >= 0.05)
            .groupby("model_a")[["ml_better", "garch_better", "no_diff"]].sum()
            .rename_axis("ml_model"))
    t4.to_csv(f"{outdir}/pilot_dm_ml_vs_garch_{tag}.csv")
    return t1, t2, t3, t4


def figures(tag, t1, daily, figdir, focus="RELIANCE.NS"):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    os.makedirs(figdir, exist_ok=True)
    font = dict(family="Times New Roman", size=14)

    # Figure A: exception rate by model with nominal line
    fig = make_subplots(rows=1, cols=2, subplot_titles=("95% VaR (nominal 5%)", "99% VaR (nominal 1%)"))
    for c, a in enumerate((0.05, 0.01), start=1):
        s = t1[t1["alpha"] == a]
        fig.add_bar(x=s["model"].astype(str), y=s["exc_rate"] * 100,
                    marker_color=[COLOURS[m] for m in s["model"].astype(str)],
                    text=[f"{v:.2f}%" for v in s["exc_rate"] * 100], textposition="outside",
                    showlegend=False, row=1, col=c)
        fig.add_hline(y=a * 100, line_dash="dash", line_color="black", line_width=2, layer="above",
                      row=1, col=c, annotation_text=f"nominal {a:.0%}", annotation_position="top right",
                      annotation_bgcolor="white")
        fig.update_yaxes(title_text="Exception rate (% of test days)", row=1, col=c)
        fig.update_xaxes(tickangle=-40, row=1, col=c)
    fig.update_layout(title="Pilot: VaR exception rate by model (mean of 3 stocks, test 2024 to Nov 2026)",
                      font=font, template="simple_white", width=1200, height=560,
                      margin=dict(t=90, b=120))
    fig.write_html(f"{figdir}/pilot_exception_rate_{tag}.html", include_plotlyjs="cdn")
    fig.write_image(f"{figdir}/pilot_exception_rate_{tag}.png", scale=300 / 96)

    # Figure B: 99% VaR vs actual returns for one stock with breach markers
    d = daily[(daily["ticker"] == focus) & (daily["alpha"] == 0.01)]
    show = ["GJR-t", "XGBoost"]
    base = d[d["model"] == show[0]]
    fig = go.Figure()
    fig.add_scatter(x=base["date"], y=base["ret"] * 100, mode="lines", name="Actual daily return",
                    line=dict(color="#4d4d4d", width=1))
    symbols = {"GJR-t": "triangle-down", "XGBoost": "x"}
    for m in show:
        s = d[d["model"] == m]
        fig.add_scatter(x=s["date"], y=-s["var"] * 100, mode="lines", name=f"{m} 99% VaR (as return)",
                        line=dict(color=COLOURS[m], width=1.8))
        b = s[s["exception"] == 1]
        fig.add_scatter(x=b["date"], y=b["ret"] * 100, mode="markers",
                        name=f"{m} breach ({len(b)})",
                        marker=dict(color=COLOURS[m], size=10, symbol=symbols[m],
                                    line=dict(width=1, color="black")))
    fig.add_vline(x=pd.Timestamp(HIKE_DATE).timestamp() * 1000, line_dash="dash", line_color="#b8860b",
                  line_width=2.5, layer="above",
                  annotation_text="RBI repo hike to 5.50% (7 Oct 2026)", annotation_position="top left")
    fig.update_layout(title=f"Pilot: {focus} 99% VaR forecast vs actual return, with breaches",
                      xaxis_title="Date", yaxis_title="Daily log return (%)", font=font,
                      template="simple_white", width=1200, height=560,
                      legend=dict(orientation="h", y=-0.18))
    fig.write_html(f"{figdir}/pilot_var_vs_returns_{focus.split('.')[0]}_{tag}.html", include_plotlyjs="cdn")
    fig.write_image(f"{figdir}/pilot_var_vs_returns_{focus.split('.')[0]}_{tag}.png", scale=300 / 96)


SNAP = os.path.join("data", "processed", "pilot_snapshot")


def make_snapshot(symbols, start, end):
    """Download each symbol once (pipeline loader, so zero-volume drops are logged) and
    save parquet + SHA-256 manifest. Yahoo's adjusted closes vary by ~1e-7 between
    downloads, which is enough to change tree-model splits, so every pilot step must
    read the same snapshot."""
    import hashlib
    os.makedirs(SNAP, exist_ok=True)
    rows = []
    for s in symbols:
        df = p.load_prices(s, start, end)
        path = os.path.join(SNAP, s.replace("^", "_").replace("=", "_") + ".parquet")
        df.to_parquet(path)
        rows.append(dict(symbol=s, file=os.path.basename(path), rows=len(df),
                         first=str(df.index.min().date()), last=str(df.index.max().date()),
                         sha256=hashlib.sha256(open(path, "rb").read()).hexdigest()))
    m = pd.DataFrame(rows).assign(snapshot_utc=pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M"))
    m.to_csv(os.path.join(SNAP, "manifest.csv"), index=False)
    print(m.to_string(index=False))


def use_snapshot():
    """Point the pipeline's loader at the snapshot (no change to the pipeline file)."""
    def load_prices(ticker, start="2015-01-01", end=None):
        path = os.path.join(SNAP, ticker.replace("^", "_").replace("=", "_") + ".parquet")
        if not os.path.exists(path):
            raise FileNotFoundError(f"{ticker} not in pilot snapshot")
        return pd.read_parquet(path)
    p.load_prices = load_prices


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", default="RELIANCE.NS,HDFCBANK.NS,INFY.NS")
    ap.add_argument("--features", default="price+vix")
    ap.add_argument("--start", default="2015-01-01")
    ap.add_argument("--test-end", default=None)
    ap.add_argument("--refresh-snapshot", action="store_true",
                    help="download a new snapshot; otherwise reuse data/processed/pilot_snapshot")
    a = ap.parse_args()
    os.chdir(ROOT)
    tag = a.features.replace("+", "_")
    tickers = [t.strip() for t in a.tickers.split(",") if t.strip()]
    if a.refresh_snapshot or not os.path.exists(os.path.join(SNAP, "manifest.csv")):
        make_snapshot(tickers + ["^INDIAVIX", "INR=X"], a.start, a.test_end)
    use_snapshot()
    import time
    t0 = time.time()
    sys.argv = ["nifty50_var_pipeline.py", "--tickers", ",".join(tickers), "--features", a.features,
                "--start", a.start] + (["--test-end", a.test_end] if a.test_end else [])
    p.main()  # unchanged pipeline, reading the snapshot
    runtime = time.time() - t0
    print(f"Pipeline runtime on snapshot: {runtime:.1f} s")
    bt = pd.read_csv(f"outputs/backtest_results_{tag}.csv")
    summ = pd.read_csv(f"outputs/summary_{tag}.csv").set_index(["model", "alpha"])
    reg = pd.read_csv(f"outputs/regime_results_{tag}.csv")
    dm = pd.read_csv(f"outputs/diebold_mariano_{tag}.csv")

    daily = daily_forecasts(tickers, a.features, a.start, a.test_end)
    check_against_pipeline(daily, bt)
    os.makedirs("outputs/tables", exist_ok=True)
    daily.to_csv(f"outputs/tables/pilot_daily_forecasts_{tag}.csv", index=False)
    t1, *_ = build_tables(tag, daily, bt, summ, reg, dm, "outputs/tables")
    figures(tag, t1, daily, "outputs/figures/pilot")
    meta = pd.DataFrame([dict(tickers=",".join(tickers), features=a.features,
                              data_start=a.start,
                              test_start=p.TEST_START, test_last_date=str(daily["date"].max())[:10],
                              test_days_per_stock=int(daily.groupby(["ticker", "model", "alpha"]).size().iloc[0]),
                              train_end=p.TRAIN_END, val_end=p.VAL_END, refit_days=p.REFIT, seed=p.SEED,
                              pipeline_runtime_s=round(runtime, 1))])
    meta.to_csv(f"outputs/tables/pilot_meta_{tag}.csv", index=False)
    print("Wrote pilot tables to outputs/tables/ and figures to outputs/figures/pilot/")


if __name__ == "__main__":
    main()
