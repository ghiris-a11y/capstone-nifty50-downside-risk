"""Every number and table used in the Phase 2 report, computed from outputs/ (CLAUDE.md rule 1).

build() returns (N, T):
  N[key] = (text, source)          -> used in chapter text as {{key}}
  T[key] = dict(caption, source, head, rows, widths=None)   -> used as [[TABLE:key]]
Derived tables that are not already in outputs/ are also written to outputs/tables/report/ so each one is traceable.
"""
import glob
import json
import os
import re
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from first_results import dm_counts, rel_pin  # noqa: E402

T_DIR = os.path.join(ROOT, "outputs", "tables")
R_DIR = os.path.join(T_DIR, "report")
GARCH = ["GARCH-normal", "GARCH-t", "EGARCH-normal", "EGARCH-t", "GJR-normal", "GJR-t"]
ML = ["XGBoost", "RandomForest", "MLP"]
ORDER = GARCH + ["HistSim250"] + ML
SLUG = {"GARCH-normal": "garchn", "GARCH-t": "garcht", "EGARCH-normal": "egarchn", "EGARCH-t": "egarcht", "GJR-normal": "gjrn",
        "GJR-t": "gjrt", "HistSim250": "hs", "XGBoost": "xgb", "RandomForest": "rf", "MLP": "mlp"}
SETS = {"price": "Price/volume only", "price_vixlevel": "+ India VIX level", "price_vixrel": "+ VIX relative to 60-day mean",
        "price_fxchg": "+ USD/INR changes", "price_vixrel_fxchg": "+ VIX relative + USD/INR changes",
        "price_vixrel_fxchg_repo": "+ VIX relative + USD/INR + repo-rate changes"}
REPO, REPO_BASE = "price_vixrel_fxchg_repo", "price_vixrel_fxchg"
HIKE = "2026-10-07"


def rd(rel):
    return pd.read_csv(os.path.join(T_DIR, rel), float_precision="round_trip")


def pct(v, d=2):
    return f"{100 * v:.{d}f}%"


def fam(m):
    return "GARCH" if m in GARCH else "ML" if m in ML else "Benchmark"


def daily(label="price"):
    d = pd.concat([pd.read_parquet(f) for f in glob.glob(os.path.join(T_DIR, "by_ticker", label, "*__daily.parquet"))], ignore_index=True)
    d["date"] = pd.to_datetime(d["date"])
    return d


def save(df, name):
    os.makedirs(R_DIR, exist_ok=True)
    df.to_csv(os.path.join(R_DIR, name), index=False)
    return f"outputs/tables/report/{name}"


def build():
    N, T = {}, {}

    def n(key, val, src):
        N[key] = (str(val), src)

    # ---------------------------------------------------------------- sample and data
    uni = pd.read_csv(os.path.join(ROOT, "config", "universe.csv"))
    exc = pd.read_csv(os.path.join(ROOT, "config", "universe_excluded.csv"))
    cand = pd.read_csv(os.path.join(ROOT, "config", "nifty50_dec2025_candidates.csv"))
    man = pd.read_csv(os.path.join(ROOT, "data", "frozen", "manifest.csv"))
    late = exc[exc.reason.str.startswith("first price")]
    ca = exc[exc.reason.str.startswith("suspected")]
    n("n_cand", len(cand), "config/nifty50_dec2025_candidates.csv")
    n("n_stocks", len(uni), "config/universe.csv")
    n("n_excl", len(exc), "config/universe_excluded.csv")
    n("n_excl_late", len(late), "config/universe_excluded.csv")
    n("n_excl_ca", len(ca), "config/universe_excluded.csv")
    n("n_sectors", uni.sector.nunique(), "config/universe.csv")
    n("snapshot", man.snapshot_utc.iloc[0], "data/frozen/manifest.csv")
    n("data_first", man.first_date.min(), "data/frozen/manifest.csv")
    n("data_last", man[man.symbol.isin(uni.ticker)].last_date.max(), "data/frozen/manifest.csv")
    n("rows_per_stock", int(man[man.symbol.isin(uni.ticker)].rows.median()), "data/frozen/manifest.csv")
    n("n_frozen_files", len(man), "data/frozen/manifest.csv")
    T["excluded"] = dict(caption="Candidates excluded from the balanced panel", source="config/universe_excluded.csv",
                         head=["Stock", "Company", "Sector", "Reason"],
                         rows=[[r.ticker.replace(".NS", ""), r["name"], r.sector, r.reason] for _, r in exc.iterrows()], widths=[2.2, 4, 3, 6.3])
    funnel = pd.DataFrame([dict(step="Nifty 50 constituents (Dec 2025 list)", stocks=len(cand)),
                           dict(step="Listed after 15 Jan 2015 (no full history)", stocks=-len(late)),
                           dict(step="Suspected unadjusted corporate action", stocks=-len(ca)),
                           dict(step="Balanced panel used in the study", stocks=len(uni))])
    save(funnel, "sample_funnel.csv")

    b = rd("backtest_results_price.csv")
    s = rd("summary_price.csv").set_index(["model", "alpha"])
    nd = b[(b.model == "GJR-t") & (b.alpha == 0.01)]
    n("test_days_min", int(nd.n.min()), "outputs/tables/backtest_results_price.csv")
    n("test_days_max", int(nd.n.max()), "outputs/tables/backtest_results_price.csv")
    n("test_obs", f"{int(nd.n.sum()):,}", "outputs/tables/backtest_results_price.csv")
    n("exp_breaches_stock", f"{nd.n.median() * 0.01:.1f}", "outputs/tables/backtest_results_price.csv")
    n("n_pairs_per_ml", len(GARCH) * len(uni), "outputs/tables/diebold_mariano_price.csv")

    # cleaning log
    dr = pd.read_csv(os.path.join(ROOT, "data", "logs", "dropped_rows.csv")).drop_duplicates()
    dr = dr[dr.ticker.isin(uni.ticker)]
    n("zero_vol_rows", len(dr), "data/logs/dropped_rows.csv")
    n("zero_vol_stocks", dr.ticker.nunique(), "data/logs/dropped_rows.csv")
    vc = pd.read_csv(os.path.join(ROOT, "data", "logs", "validation_checks.csv"))
    vcu = vc[vc.symbol.isin(uni.ticker)]
    n("hash_ok", int(vcu.hash_ok.sum()), "data/logs/validation_checks.csv")
    n("null_cells", int(vcu.nulls.sum()), "data/logs/validation_checks.csv")
    n("dup_dates", int(vcu.duplicate_dates.sum()), "data/logs/validation_checks.csv")
    n("nonpos", int(vcu.non_positive.sum()), "data/logs/validation_checks.csv")
    big = vcu.moves_over_20pct.dropna().str.split("; ").explode()
    n("moves20", len(big), "data/logs/validation_checks.csv")
    T["cleaning"] = dict(caption="Data cleaning and validation log for the 41-stock panel", source="data/logs/validation_checks.csv, data/logs/dropped_rows.csv, config/universe_excluded.csv",
                         head=["Step", "Rule", "Result"], widths=[3.5, 7, 5],
                         rows=[["Hash check", "SHA-256 of every frozen file matches the manifest", f"{int(vcu.hash_ok.sum())} of {len(vcu)} files match"],
                               ["Missing values", "No empty price cells", f"{int(vcu.nulls.sum())} empty cells"],
                               ["Duplicate dates", "One row per stock per day", f"{int(vcu.duplicate_dates.sum())} duplicates"],
                               ["Non-positive prices", "Prices must be above zero", f"{int(vcu.non_positive.sum())} rows"],
                               ["Zero-volume rows", "Yahoo placeholder rows (volume 0) dropped and logged", f"{len(dr)} rows in {dr.ticker.nunique()} stocks dropped"],
                               ["Large one-day moves", "Moves beyond 20% flagged for review", f"{len(big)} flags; reviewed against market moves"],
                               ["Corporate-action rule", "Move of 35% or more while the Nifty moved under 3%", f"{len(ca)} stocks excluded"],
                               ["Listing rule", "First price on or before 15 Jan 2015, gaps of 10 days or less", f"{len(late)} stocks excluded"]])

    # descriptive statistics of test-window returns (derived)
    d = daily()
    r = d[(d.model == "GJR-t") & (d.alpha == 0.01)][["ticker", "date", "ret"]]
    desc = r.groupby("ticker")["ret"].agg(mean="mean", sd="std", skew=lambda x: x.skew(), kurt=lambda x: x.kurt(), min="min", max="max").reset_index()
    desc = desc.merge(uni[["ticker", "sector"]], on="ticker")
    src_desc = save(desc, "descriptive_test_returns.csv")
    n("kurt_med", f"{desc["kurt"].median():.1f}", src_desc)
    n("kurt_min", f"{desc["kurt"].min():.1f}", src_desc)
    n("kurt_max", f"{desc["kurt"].max():.1f}", src_desc)
    n("n_negskew", int((desc["skew"] < 0).sum()), src_desc)
    n("sd_med", pct(desc.sd.median()), src_desc)
    n("worst_day_ret", pct(desc["min"].min(), 1), src_desc)
    n("worst_day_stock", desc.loc[desc["min"].idxmin(), "ticker"].replace(".NS", ""), src_desc)
    pooled = r.ret
    T["desc_panel"] = dict(caption="Descriptive statistics of daily log returns, test window (41 stocks)", source=src_desc,
                           head=["Statistic", "Median across stocks", "Lowest stock", "Highest stock"], widths=[5, 3.6, 3.6, 3.6],
                           rows=[["Mean daily return", pct(desc["mean"].median(), 3), pct(desc["mean"].min(), 3), pct(desc["mean"].max(), 3)],
                                 ["Standard deviation", pct(desc.sd.median()), pct(desc.sd.min()), pct(desc.sd.max())],
                                 ["Skewness", f"{desc["skew"].median():.2f}", f"{desc["skew"].min():.2f}", f"{desc["skew"].max():.2f}"],
                                 ["Excess kurtosis", f"{desc["kurt"].median():.2f}", f"{desc["kurt"].min():.2f}", f"{desc["kurt"].max():.2f}"],
                                 ["Worst day", pct(desc["min"].median()), pct(desc["min"].min()), pct(desc["min"].max())],
                                 ["Best day", pct(desc["max"].median()), pct(desc["max"].min()), pct(desc["max"].max())]])
    n("pooled_small", pct(((pooled.abs() < 0.02).mean()), 0), src_desc)
    T["desc_stock"] = dict(caption="Descriptive statistics of daily log returns by stock, test window", source=src_desc,
                           head=["Stock", "Sector", "Mean", "SD", "Skew", "Ex. kurt.", "Min", "Max"], widths=[2.6, 4.2, 1.6, 1.5, 1.3, 1.5, 1.7, 1.6], small=True,
                           rows=[[x.ticker.replace(".NS", ""), x.sector, pct(x["mean"], 3), pct(x.sd), f"{x["skew"]:.2f}", f"{x["kurt"]:.1f}", pct(x["min"], 1), pct(x["max"], 1)]
                                 for _, x in desc.sort_values("ticker").iterrows()])

    # ---------------------------------------------------------------- backtests (price set)
    src_s = "outputs/tables/summary_price.csv"
    for m in ORDER:
        k = SLUG[m]
        for a, tag in ((0.01, "99"), (0.05, "95")):
            row = s.loc[(m, a)]
            n(f"exc{tag}_{k}", pct(row.exc_rate), src_s)
            n(f"kup{tag}_{k}", pct(row.pass_kupiec, 0), src_s)
            n(f"cc{tag}_{k}", pct(row.pass_cc, 0), src_s)
            n(f"fz{tag}_{k}", f"{row.fz0:.4f}", src_s)
            n(f"fzmed{tag}_{k}", f"{row.fz0_median_stocks:.4f}", src_s)
            n(f"es{tag}_{k}", f"{row.es_ratio:.3f}", src_s)
            n(f"norisk{tag}_{k}", int(row.norisk_days), src_s)
        n(f"green_{k}", pct(s.loc[(m, 0.01)].green99, 0), src_s)
        n(f"per100_{k}", f"{100 * s.loc[(m, 0.01)].exc_rate:.2f}", src_s)
    closest = sorted(ORDER, key=lambda m: abs(s.loc[(m, 0.01)].exc_rate - 0.01))
    for i, m in enumerate(closest[:3], 1):
        n(f"closest{i}", m, src_s)
        n(f"closest{i}_exc", pct(s.loc[(m, 0.01)].exc_rate), src_s)
    n("n_es_above1", sum(s.loc[(m, 0.01)].es_ratio > 1 for m in ORDER), src_s)
    n("n_models", len(ORDER), src_s)
    gap = (s.loc[("XGBoost", 0.01)].exc_rate - s.loc[("GJR-t", 0.01)].exc_rate) * 250
    n("gap_xgb_gjrt_yr", f"{gap:.1f}", src_s)
    gap_rf = (s.loc[("RandomForest", 0.01)].exc_rate - s.loc[("GJR-t", 0.01)].exc_rate) * 250
    n("gap_rf_gjrt_yr", f"{gap_rf:.1f}", src_s)
    n("gap_xgb_gjrt_panel", f"{gap * len(uni):.0f}", src_s)

    def summ_table(a):
        rows = []
        for m in ORDER:
            r_ = s.loc[(m, a)]
            rows.append([m, fam(m), pct(r_.exc_rate), pct(r_.pass_kupiec, 0), pct(r_.pass_cc, 0)] + ([pct(r_.green99, 0)] if a == 0.01 else [])
                        + [f"{r_.fz0:.3f}", f"{r_.fz0_median_stocks:.3f}", f"{r_.es_ratio:.3f}"])
        head = ["Model", "Family", "Breach rate", "Kupiec pass", "Christ. CC pass"] + (["Basel Green"] if a == 0.01 else []) + ["Mean FZ0", "Median FZ0", "Actual/forecast ES"]
        return dict(caption=f"Backtest summary across 41 stocks, {'99% VaR (nominal breach rate 1%)' if a == 0.01 else '95% VaR (nominal breach rate 5%)'}",
                    source=src_s, head=head, rows=rows, family_col=1)
    T["bt99"] = summ_table(0.01)
    T["bt95"] = summ_table(0.05)
    b99 = b[b.alpha == 0.01]
    for m in ("GJR-t", "XGBoost", "GARCH-t", "EGARCH-t"):
        n(f"above1_{SLUG[m]}", int((b99[b99.model == m].exc_rate > 0.01).sum()), "outputs/tables/backtest_results_price.csv")
    both = lambda ms: (b99[b99.model.isin(ms)].pipe(lambda x: ((x.kupiec_p > 0.05) & (x.ind_p > 0.05)).mean()))
    n("bothpass_garch", pct(both(GARCH), 0), "outputs/tables/backtest_results_price.csv")
    n("bothpass_ml", pct(both(ML), 0), "outputs/tables/backtest_results_price.csv")
    n("abovegrid_garch", pct((b99[b99.model.isin(GARCH)].exc_rate > 0.01).mean(), 0), "outputs/tables/backtest_results_price.csv")
    n("abovegrid_ml", pct((b99[b99.model.isin(ML)].exc_rate > 0.01).mean(), 0), "outputs/tables/backtest_results_price.csv")

    # Reliance example
    rel = d[(d.ticker == "RELIANCE.NS") & (d.alpha == 0.01)]
    n("rel_gjrt", int(rel[rel.model == "GJR-t"].exception.sum()), "outputs/tables/by_ticker/price/RELIANCE.NS__daily.parquet")
    n("rel_xgb", int(rel[rel.model == "XGBoost"].exception.sum()), "outputs/tables/by_ticker/price/RELIANCE.NS__daily.parquet")
    n("rel_days", int(rel[rel.model == "GJR-t"].shape[0]), "outputs/tables/by_ticker/price/RELIANCE.NS__daily.parquet")

    # ---------------------------------------------------------------- Diebold-Mariano
    src_dm = "outputs/tables/diebold_mariano_price.csv, diebold_mariano_pinball_price.csv"
    ad = lambda x: x.set_index("model").rename(columns={"garch_lower": "garch", "ml_lower": "ml", "no_difference": "none"})[["garch", "ml", "none"]]
    dmf = ad(dm_counts(rd("diebold_mariano_price.csv")))  # FZ0 file holds the 95% level only
    dmp = rd("diebold_mariano_pinball_price.csv")
    p95, p99 = ad(dm_counts(dmp, 0.05)), ad(dm_counts(dmp, 0.01))
    tot = dmf.sum()
    n("dm_g", int(tot.garch), src_dm); n("dm_m", int(tot.ml), src_dm); n("dm_n", int(tot["none"]), src_dm)
    n("dm_total", int(tot.sum()), src_dm)
    n("dm_none_share", pct(tot["none"] / tot.sum(), 0), src_dm)
    n("dmp95_g", int(p95.sum().garch), src_dm); n("dmp95_m", int(p95.sum().ml), src_dm)
    n("dmp99_g", int(p99.sum().garch), src_dm); n("dmp99_m", int(p99.sum().ml), src_dm)
    for m in ML:
        n(f"dm_g_{SLUG[m]}", int(dmf.loc[m, "garch"]), src_dm)
        n(f"dm_m_{SLUG[m]}", int(dmf.loc[m, "ml"]), src_dm)
        n(f"dmp95_g_{SLUG[m]}", int(p95.loc[m, "garch"]), src_dm); n(f"dmp95_m_{SLUG[m]}", int(p95.loc[m, "ml"]), src_dm)
        n(f"dmp99_g_{SLUG[m]}", int(p99.loc[m, "garch"]), src_dm); n(f"dmp99_m_{SLUG[m]}", int(p99.loc[m, "ml"]), src_dm)
    T["dm"] = dict(caption="Diebold-Mariano tests, each ML model against each GARCH model per stock (5% level): GARCH lower loss / ML lower loss / no significant difference",
                   source=src_dm, head=["ML model", "FZ0 loss, 95%", "Pinball loss, 95%", "Pinball loss, 99%"], widths=[3.5, 4, 4, 4],
                   rows=[[m, f"{dmf.loc[m].garch} / {dmf.loc[m].ml} / {dmf.loc[m]['none']}", f"{p95.loc[m].garch} / {p95.loc[m].ml} / {p95.loc[m]['none']}",
                          f"{p99.loc[m].garch} / {p99.loc[m].ml} / {p99.loc[m]['none']}"] for m in ML]
                   + [["All three", f"{int(tot.garch)} / {int(tot.ml)} / {int(tot['none'])}", f"{int(p95.sum().garch)} / {int(p95.sum().ml)} / {int(p95.sum()['none'])}",
                       f"{int(p99.sum().garch)} / {int(p99.sum().ml)} / {int(p99.sum()['none'])}"]])
    save(pd.DataFrame({"model": ML, "garch_better": dmf.garch.values, "ml_better": dmf.ml.values, "no_difference": dmf["none"].values}), "dm_fz0_95_counts.csv")

    # ---------------------------------------------------------------- XGBoost no-risk days and the L&T case
    xr = b[(b.model == "XGBoost") & (b.alpha == 0.01) & (b.norisk_days > 0)].sort_values("fz0", ascending=False)
    lt = xr.iloc[0]
    src_b = "outputs/tables/backtest_results_price.csv"
    n("nr_stock", lt.ticker.replace(".NS", ""), src_b)
    n("nr_fz0", f"{lt.fz0:.2f}", src_b)
    n("nr_fz0med", f"{lt.fz0_median:.2f}", src_b)
    n("nr_days", int(lt.norisk_days), src_b)
    n("nr_stocks99", int((b[(b.model == 'XGBoost') & (b.alpha == 0.01)].norisk_days > 0).sum()), src_b)
    ltd = d[(d.ticker == lt.ticker) & (d.model == "XGBoost") & (d.alpha == 0.01)].sort_values("date")
    z = ltd[ltd["var"] <= 1e-5]
    src_lt = f"outputs/tables/by_ticker/price/{lt.ticker}__daily.parquet"
    if len(z):
        zz = z.iloc[0]
        n("nr_date", zz.date.strftime("%d %B %Y").lstrip("0"), src_lt)
        n("nr_ret", pct(zz.ret), src_lt)
        n("nr_breach", "a breach" if zz.exception == 1 else "no breach", src_lt)
        g = d[(d.ticker == lt.ticker) & (d.model == "GJR-t") & (d.alpha == 0.01) & (d.date == zz.date)]
        n("nr_gjrt_var", pct(float(g["var"].iloc[0])), src_lt.replace("XGBoost", ""))
    rows = []
    for k in SETS:
        sk = rd(f"summary_{k}.csv").set_index(["model", "alpha"])
        rows.append([SETS[k], int(sk.loc[("XGBoost", 0.05)].norisk_days), int(sk.loc[("XGBoost", 0.01)].norisk_days),
                     f"{sk.loc[('XGBoost', 0.01)].fz0:.3f}", f"{sk.loc[('XGBoost', 0.01)].fz0_median_stocks:.3f}"])
    T["norisk"] = dict(caption="XGBoost no-risk days (forecast quantile at or above zero) and the mean and median 99% FZ0 loss",
                       source="outputs/tables/summary_*.csv", head=["ML input set", "No-risk days, 95%", "No-risk days, 99%", "Mean FZ0, 99%", "Median FZ0, 99%"],
                       rows=rows, widths=[5.5, 2.5, 2.5, 2.5, 2.5])

    # ---------------------------------------------------------------- regimes and post-hike
    rg = rd("regime_results_price.csv")
    g = rg.groupby(["model", "regime"])["mean_fz0"].mean().unstack()[["Q1 calm", "Q2", "Q3", "Q4 stressed"]].reindex(ORDER)
    src_rg = "outputs/tables/regime_results_price.csv"
    n("q4_best", g["Q4 stressed"].idxmin(), src_rg)
    n("q1_best", g["Q1 calm"].idxmin(), src_rg)
    n("q4_worse_all", "all" if bool((g["Q4 stressed"] > g["Q1 calm"]).all()) else "not all", src_rg)
    n("q4_gjrt", f"{g.loc['GJR-t', 'Q4 stressed']:.3f}", src_rg); n("q4_xgb", f"{g.loc['XGBoost', 'Q4 stressed']:.3f}", src_rg)
    n("q1_gjrt", f"{g.loc['GJR-t', 'Q1 calm']:.3f}", src_rg); n("q1_xgb", f"{g.loc['XGBoost', 'Q1 calm']:.3f}", src_rg)
    T["regime"] = dict(caption="Mean FZ0 loss (95% VaR and ES) by quartile of the previous day's India VIX, averaged across stocks (lower is better)",
                       source=src_rg, head=["Model", "Q1 calm", "Q2", "Q3", "Q4 stressed"], family_col=None,
                       rows=[[m] + [f"{v:.3f}" for v in g.loc[m]] for m in ORDER])
    ph = d[(d.date >= pd.Timestamp(HIKE)) & (d.alpha == 0.01)]
    post = ph.groupby("model").agg(days=("date", "nunique"), obs=("exception", "size"), breaches=("exception", "sum")).reindex(ORDER).reset_index()
    post["rate"] = post.breaches / post.obs
    src_ph = save(post, "post_hike_breaches_99.csv")
    n("ph_days", int(post.days.max()), src_ph)
    n("ph_obs", int(post.obs.max()), src_ph)
    n("ph_gjrt", pct(post.set_index("model").loc["GJR-t", "rate"]), src_ph)
    n("ph_xgb", pct(post.set_index("model").loc["XGBoost", "rate"]), src_ph)
    n("ph_exp", f"{post.obs.max() * 0.01:.1f}", src_ph)
    T["posthike"] = dict(caption=f"99% VaR breaches after the RBI repo hike (from {HIKE} to the end of the test window, all stocks)",
                         source=src_ph, head=["Model", "Trading days", "Stock-days", "Breaches", "Breach rate"],
                         rows=[[x.model, int(x.days), int(x.obs), int(x.breaches), pct(x.rate)] for x in post.itertuples()])

    # post-hike view for the repo-rate set's ML models (same window, from its own daily files)
    dr_ = daily(REPO)
    phr = dr_[(dr_.date >= pd.Timestamp(HIKE)) & (dr_.alpha == 0.01) & dr_.model.isin(ML)]
    postr = phr.groupby("model").agg(days=("date", "nunique"), obs=("exception", "size"), breaches=("exception", "sum")).reindex(ML).reset_index()
    postr["rate"] = postr.breaches / postr.obs
    postr["model"] = postr.model + " (+repo)"
    src_phr = save(postr, "post_hike_breaches_99_repo.csv")
    n("ph_first", pd.Timestamp(HIKE).strftime("%d %B %Y").lstrip("0"), src_ph)
    n("ph_last", ph.date.max().strftime("%d %B %Y").lstrip("0"), src_ph)
    n("ph_xgb_repo", pct(postr.set_index("model").loc["XGBoost (+repo)", "rate"]), src_phr)
    T["posthike"]["rows"] += [[x.model, int(x.days), int(x.obs), int(x.breaches), pct(x.rate)] for x in postr.itertuples()]
    T["posthike"]["source"] = f"{src_ph}; {src_phr}"
    T["posthike"]["head"] = ["Model", "Days", "Stock-days", "Breaches", "Breach rate"]

    # ---------------------------------------------------------------- breach clustering on stress days
    bs = rd("breach_days_summary_price.csv")
    bs = bs[bs.alpha == 0.01].set_index("model").reindex(ORDER)
    src_bs = "outputs/tables/breach_days_summary_price.csv"
    n("stress_days", int(bs.stress_days.iloc[0]), src_bs)
    n("mkt_days", int(bs.test_days.iloc[0]), src_bs)
    n("stress_share_days", pct(bs.share_of_days_stress.iloc[0], 1), src_bs)
    for m in ORDER:
        n(f"stress_{SLUG[m]}", pct(bs.loc[m].share_of_breaches_on_stress_days, 1), src_bs)
        n(f"maxday_{SLUG[m]}", int(bs.loc[m].max_breaches_one_day), src_bs)
    n("stress_min", pct(bs.share_of_breaches_on_stress_days.min(), 1), src_bs)
    n("stress_max", pct(bs.share_of_breaches_on_stress_days.max(), 1), src_bs)
    top = re.match(r"(\S+) (\d+) \(Nifty ([-\d.]+%)\)", bs.loc["GJR-t"].top_days.split(";")[0].strip())
    n("worst_date", pd.Timestamp(top.group(1)).strftime("%d %B %Y").lstrip("0"), src_bs)
    n("worst_n", top.group(2), src_bs)
    n("worst_nifty", top.group(3).replace("-", "−"), src_bs)
    T["stress"] = dict(caption="Clustering of 99% VaR breaches across the 41 stocks (stress day = Nifty 50 fell 2% or more)",
                       source=src_bs, head=["Model", "Breaches", "Share on stress days", "Most stocks in one day", "Days with 10+ stocks"],
                       rows=[[m, int(x.total_breaches), pct(x.share_of_breaches_on_stress_days, 1), int(x.max_breaches_one_day), int(x.days_with_10plus_breaches)]
                             for m, x in bs.iterrows()])

    # ---------------------------------------------------------------- input sets (ablation) and validation
    base_b = rd("backtest_results_price.csv")
    rows = []
    for k in SETS:
        sk = rd(f"summary_{k}.csv").set_index(["model", "alpha"])
        bk = rd(f"backtest_results_{k}.csv")
        for m in ML:
            rows.append([SETS[k], m, pct(sk.loc[(m, 0.05)].exc_rate), pct(sk.loc[(m, 0.01)].exc_rate), pct(sk.loc[(m, 0.01)].pass_kupiec, 0),
                         f"{rel_pin(bk, base_b, m):.3f}"])
            if k == "price_vixlevel":
                n(f"vix_exc99_{SLUG[m]}", pct(sk.loc[(m, 0.01)].exc_rate), f"outputs/tables/summary_{k}.csv")
                n(f"vix_relpin_{SLUG[m]}", f"{rel_pin(bk, base_b, m):.3f}", f"outputs/tables/backtest_results_{k}.csv")
    T["sets"] = dict(caption="ML results by input set, test window (pinball ratio below 1 = better than price/volume only)",
                     source="outputs/tables/summary_*.csv, backtest_results_*.csv", head=["Input set", "Model", "Breach 95%", "Breach 99%", "Kupiec pass 99%", "Pinball vs price"],
                     rows=rows, widths=[5, 2.8, 2, 2, 2.2, 2.2])
    vs = rd("validation/variant_selection.csv")
    sel = json.load(open(os.path.join(T_DIR, "validation", "selected_variant.json")))
    n("sel_overall", sel["selected_overall"].replace("val_", ""), "outputs/tables/validation/selected_variant.json")
    n("sel_stationary", sel["selected_stationary"].replace("val_", ""), "outputs/tables/validation/selected_variant.json")
    n("sel_time", sel["created_utc"], "outputs/tables/validation/selected_variant.json")
    rows, flip = [], 0
    for _, v in vs[vs.variant.str.replace("val_", "").isin(SETS)].iterrows():
        k = v.variant.replace("val_", "")
        if k == "price":
            continue
        tp = rel_pin(rd(f"backtest_results_{k}.csv"), base_b, v.model)
        te99 = rd(f"summary_{k}.csv").set_index(["model", "alpha"]).loc[(v.model, 0.01)].exc_rate
        flip += int(v.rel_pinball < 1 and tp > 1)
        rows.append([SETS[k], v.model, f"{v.rel_pinball:.3f}", f"{tp:.3f}", pct(v.exc99), pct(te99)])
    n("flip", flip, "outputs/tables/validation/variant_selection.csv, backtest_results_*.csv")
    n("flip_of", len(rows), "outputs/tables/validation/variant_selection.csv")
    T["valtest"] = dict(caption="Pinball loss relative to price/volume only: validation window (2022-23) against test window (2024-26)",
                        source="outputs/tables/validation/variant_selection.csv, backtest_results_*.csv",
                        head=["Input set", "Model", "Validation ratio", "Test ratio", "Validation breach 99%", "Test breach 99%"], rows=rows, widths=[5, 2.8, 2.1, 1.8, 2.2, 2.2])
    fr = rd("diag_feature_ranges_summary.csv")
    fr = fr[fr.fit_window == "train_val"]
    for f_ in ("usdinr", "vix"):
        n(f"out_{f_}", pct(fr.set_index("feature").loc[f_, "median_share_outside"], 1), "outputs/tables/diag_feature_ranges_summary.csv")
    n("vix_fit_max", f"{100 * fr.set_index('feature').loc['vix', 'fit_max_median']:.1f}", "outputs/tables/diag_feature_ranges_summary.csv")
    n("vix_test_max", f"{100 * fr.set_index('feature').loc['vix', 'test_max_median']:.1f}", "outputs/tables/diag_feature_ranges_summary.csv")
    T["ranges"] = dict(caption="Share of test days on which a market feature lay outside the range the final models were fitted on (2015-2023, median across stocks)",
                       source="outputs/tables/diag_feature_ranges_summary.csv", head=["Feature", "Family", "Share outside", "Fitted range", "Test range"],
                       rows=[[x.feature, x.family, pct(x.median_share_outside, 1), f"{x.fit_min_median:.4g} to {x.fit_max_median:.4g}",
                              f"{x.test_min_median:.4g} to {x.test_max_median:.4g}"] for x in fr[fr.family != "price/volume"].itertuples()], widths=[2.6, 4, 2.2, 3.4, 3.4])
    sh = rd("xgb_shap_importance_price_vixlevel_summary.csv").sort_values("mean", ascending=False)
    n("shap_top", sh.iloc[0].feature, "outputs/tables/xgb_shap_importance_price_vixlevel_summary.csv")
    n("shap_top_bp", f"{1e4 * sh.iloc[0]['mean']:.1f}", "outputs/tables/xgb_shap_importance_price_vixlevel_summary.csv")
    n("shap_2nd", sh.iloc[1].feature, "outputs/tables/xgb_shap_importance_price_vixlevel_summary.csv")
    n("shap_2nd_bp", f"{1e4 * sh.iloc[1]['mean']:.1f}", "outputs/tables/xgb_shap_importance_price_vixlevel_summary.csv")

    # ---------------------------------------------------------------- GARCH estimates
    gp = rd("garch_params_teststart.csv")
    src_gp = "outputs/tables/garch_params_teststart.csv"
    med = gp.groupby("model")[["alpha", "gamma", "beta", "nu", "persistence"]].median().reindex(GARCH)
    T["garch"] = dict(caption="GARCH parameter estimates at the start of the test window (fitted on 2015-2023; median across 41 stocks)",
                      source=src_gp, head=["Model", "alpha", "gamma (asymmetry)", "beta", "nu (t tail)", "Persistence"],
                      rows=[[m] + [("–" if pd.isna(v) else f"{v:.3f}") for v in med.loc[m]] for m in GARCH])
    gj = gp[gp.model == "GJR-t"]
    n("gjr_gamma_sig", int((gj.gamma_pvalue < 0.05).sum()), src_gp)
    n("gjr_gamma_pos", int((gj.gamma > 0).sum()), src_gp)
    n("eg_gamma_neg", int((gp[gp.model == "EGARCH-t"].gamma < 0).sum()), src_gp)
    n("nu_med", f"{gj.nu.median():.1f}", src_gp)
    n("pers_med", f"{gj.persistence.median():.3f}", src_gp)
    best = gp.pivot(index="ticker", columns="model", values="aic").idxmin(axis=1).value_counts()
    n("aic_egarcht", int(best.get("EGARCH-t", 0)), src_gp)
    n("aic_tshare", int(sum(v for k, v in best.items() if k.endswith("-t"))), src_gp)
    T["garch_stock"] = dict(caption="GJR-GARCH(1,1) with Student-t errors: estimates by stock at the start of the test window", source=src_gp,
                            head=["Stock", "alpha", "gamma", "gamma p", "beta", "nu", "Persistence"], small=True,
                            rows=[[x.ticker.replace(".NS", ""), f"{x.alpha:.3f}", f"{x.gamma:.3f}", f"{x.gamma_pvalue:.3f}", f"{x.beta:.3f}", f"{x.nu:.2f}", f"{x.persistence:.3f}"]
                                  for x in gj.sort_values("ticker").itertuples()])

    # ---------------------------------------------------------------- sector view and capital buffer
    v = d[(d.model == "GJR-t") & (d.alpha == 0.01)].groupby("ticker")["var"].mean().rename("avg_var99").reset_index().merge(uni[["ticker", "sector"]], on="ticker")
    ex = b99.pivot(index="ticker", columns="model", values="exc_rate")[["GJR-t", "XGBoost"]].reset_index()
    sec = v.merge(ex, on="ticker").groupby("sector").agg(stocks=("ticker", "count"), median_var99=("avg_var99", "median"),
                                                         exc99_gjrt=("GJR-t", "mean"), exc99_xgb=("XGBoost", "mean")).sort_values("median_var99").reset_index()
    src_sec = save(sec, "sector_summary_price.csv")
    T["sector"] = dict(caption="Sector view: average one-day 99% VaR (GJR-t) and 99% breach rates of GJR-t and XGBoost", source=src_sec,
                       head=["Sector", "Stocks", "Median avg. 99% VaR", "GJR-t breach rate", "XGBoost breach rate"],
                       rows=[[x.sector, int(x.stocks), pct(x.median_var99), pct(x.exc99_gjrt), pct(x.exc99_xgb)] for x in sec.itertuples()], widths=[5, 1.6, 3, 3, 3])
    n("sec_low", sec.iloc[0].sector, src_sec); n("sec_low_var", pct(sec.iloc[0].median_var99), src_sec)
    n("sec_high", sec.iloc[-1].sector, src_sec); n("sec_high_var", pct(sec.iloc[-1].median_var99), src_sec)
    n("sec_high_n", int(sec.iloc[-1].stocks), src_sec)
    n("n_sec", len(sec), src_sec)
    n("sec_xgb_worse", int((sec.exc99_xgb > sec.exc99_gjrt).sum()), src_sec)
    avg_var = v.avg_var99.mean()
    src_v = save(v, "avg_var99_gjrt_by_stock.csv")
    n("avg_var99", pct(avg_var), src_v)
    n("buffer_100cr", f"{avg_var * 100:.2f}", src_v)  # Rs crore per Rs 100 crore position
    n("avg_var99_min", pct(v.avg_var99.min()), src_v); n("avg_var99_max", pct(v.avg_var99.max()), src_v)

    # ---------------------------------------------------------------- robustness
    sens = rd("sensitivity/summary_sens_adanient_price.csv").set_index(["model", "alpha"])
    n("adani_gjrt", pct(sens.loc[("GJR-t", 0.01)].exc_rate), "outputs/tables/sensitivity/summary_sens_adanient_price.csv")
    n("adani_xgb", pct(sens.loc[("XGBoost", 0.01)].exc_rate), "outputs/tables/sensitivity/summary_sens_adanient_price.csv")
    n("adani_hs", pct(sens.loc[("HistSim250", 0.01)].exc_rate), "outputs/tables/sensitivity/summary_sens_adanient_price.csv")
    eb = rd("xgb_es_approx_bias.csv")
    n("es_bias_max", f"{eb.understatement_pct.max():.1f}%", "outputs/tables/xgb_es_approx_bias.csv")

    # ---------------------------------------------------------------- compute time
    log = open(os.path.join(ROOT, "data", "logs", "run_test_rerun.log"), encoding="utf-8").read()
    secs = [int(x) for x in re.findall(r": done \((\d+) s\)", open(os.path.join(ROOT, "data", "logs", "run.log"), encoding="utf-8").read())]
    sets = re.findall(r"--- (\S+) \(\S+\) finished in (\d+) s", log)
    n("sec_per_stock", int(np.median(secs)), "data/logs/run.log")
    n("min_per_set", f"{np.median([int(x[1]) for x in sets]) / 60:.0f}", "data/logs/run_test_rerun.log")
    n("n_jobs", re.search(r"n_jobs=(\d+)", log).group(1), "data/logs/run_test_rerun.log")

    # ---------------------------------------------------------------- dashboard readability (src/dashboard_check.py)
    rj = json.load(open(os.path.join(ROOT, "outputs", "dashboard_check", "readability.json"), encoding="utf-8"))
    fk = [v["fk_grade"] for v in rj["tabs"].values()]
    n("fk_min", f"{min(fk):.1f}", "outputs/dashboard_check/readability.json")
    n("fk_max", f"{max(fk):.1f}", "outputs/dashboard_check/readability.json")
    n("n_tabs", len(fk), "outputs/dashboard_check/readability.json")

    # ---------------------------------------------------------------- per-stock appendix table
    piv = b99.pivot(index="ticker", columns="model", values="exc_rate")
    kp = b99.pivot(index="ticker", columns="model", values="kupiec_p")
    T["perstock"] = dict(caption="99% VaR breach rate by stock and model (nominal 1%), with Kupiec p-values for GJR-t and XGBoost",
                         source="outputs/tables/backtest_results_price.csv", small=True,
                         head=["Stock", "GARCH-t", "EGARCH-t", "GJR-t", "HistSim", "XGBoost", "RF", "MLP", "Kupiec p GJR-t", "Kupiec p XGB"],
                         rows=[[t.replace(".NS", "")] + [pct(piv.loc[t, m]) for m in ("GARCH-t", "EGARCH-t", "GJR-t", "HistSim250", "XGBoost", "RandomForest", "MLP")]
                               + [f"{kp.loc[t, 'GJR-t']:.3f}", f"{kp.loc[t, 'XGBoost']:.3f}"] for t in piv.index])

    # ---------------------------------------------------------------- business quantities for Chapter 6 (all from outputs/)
    d99 = d[d.alpha == 0.01].copy()
    # (a) capital or margin set aside per Rs 100 crore: average 99% VaR over all stock-days, by model
    buf = d99.groupby("model").agg(avg_var99=("var", "mean"), breach_rate=("exception", "mean")).reindex(ORDER).reset_index()
    buf["per_100cr"] = buf.avg_var99 * 100
    src_buf = save(buf, "buffer_by_model.csv")
    for m in ORDER:
        n(f"buf_{SLUG[m]}", f"{buf.set_index('model').loc[m, 'per_100cr']:.2f}", src_buf)
    tfam = buf[buf.model.isin(["GARCH-t", "EGARCH-t", "GJR-t"])].per_100cr.mean()
    mlfam = buf[buf.model.isin(ML)].per_100cr.mean()
    n("buf_tfam", f"{tfam:.2f}", src_buf); n("buf_mlfam", f"{mlfam:.2f}", src_buf)
    n("buf_diff_ml_t", f"{mlfam - tfam:.2f}", src_buf)
    T["buffers"] = dict(caption="Money set aside for one bad day: average one-day 99% VaR by model, as Rs crore per Rs 100 crore held (test window, all stock-days)",
                        source=src_buf, head=["Model", "Family", "Average 99% VaR", "Rs crore per Rs 100 crore", "99% breach rate"],
                        rows=[[r.model, fam(r.model), pct(r.avg_var99), f"{r.per_100cr:.2f}", pct(r.breach_rate)] for r in buf.itertuples()])
    # (b) stress-day cushion for GJR-t (stress day = Nifty 50 fell 2% or more, as in breach_days_price.csv)
    bd = rd("breach_days_price.csv"); bd["date"] = pd.to_datetime(bd["date"])
    sdays = set(bd.loc[bd.stress_day.astype(bool), "date"])
    gj = d99[d99.model == "GJR-t"].copy()
    gj["stress"] = gj.date.isin(sdays)
    gj["ratio"] = -gj.ret / gj["var"]
    st, ns = gj[gj.stress], gj[~gj.stress]
    k99 = st.ratio.quantile(0.99)
    src_g = "outputs/tables/by_ticker/price/*__daily.parquet; outputs/tables/breach_days_price.csv"
    n("st_obs", f"{len(st):,}", src_g)
    n("st_br_gjrt", pct(st.exception.mean(), 1), src_g)
    n("ns_br_gjrt", pct(ns.exception.mean(), 2), src_g)
    n("st_mult99", f"{k99:.2f}", src_g)
    n("st_excess", pct((st.loc[st.exception.astype(bool), "ret"].abs() - st.loc[st.exception.astype(bool), "var"]).mean()), src_g)
    # (c) India VIX rule: previous trading day's VIX, quartiles over the test window (same split as the regime table)
    vix = pd.read_parquet(os.path.join(ROOT, "data", "frozen", "_INDIAVIX.parquet"))["Close"]
    dates = pd.DatetimeIndex(sorted(gj.date.unique()))
    vprev = vix.reindex(vix.index.union(dates)).ffill().shift(1).reindex(dates)
    edge = vprev.quantile(0.75)
    q4 = set(vprev[vprev > edge].index)
    gj["q4"] = gj.date.isin(q4)
    k_q4 = gj[gj.q4].ratio.quantile(0.99)
    src_v = "data/frozen/_INDIAVIX.parquet; outputs/tables/by_ticker/price/*__daily.parquet"
    n("vix_q4_edge", f"{edge:.1f}", src_v)
    n("vix_q4_days", len(q4), src_v)
    n("br_q4_gjrt", pct(gj[gj.q4].exception.mean()), src_v)
    n("br_q13_gjrt", pct(gj[~gj.q4].exception.mean()), src_v)
    n("mult_q4", f"{k_q4:.2f}", src_v)
    vr = pd.DataFrame([dict(group="stress days (Nifty <= -2%)", stock_days=len(st), breach_rate=st.exception.mean(), multiplier_for_1pct=k99),
                       dict(group="other days", stock_days=len(ns), breach_rate=ns.exception.mean(), multiplier_for_1pct=ns.ratio.quantile(0.99)),
                       dict(group=f"previous-day India VIX above {edge:.1f} (top quartile)", stock_days=int(gj.q4.sum()), breach_rate=gj[gj.q4].exception.mean(), multiplier_for_1pct=k_q4),
                       dict(group="previous-day India VIX in lower three quartiles", stock_days=int((~gj.q4).sum()), breach_rate=gj[~gj.q4].exception.mean(), multiplier_for_1pct=gj[~gj.q4].ratio.quantile(0.99))])
    src_vr = save(vr, "stress_vix_cushion_gjrt.csv")
    T["cushion"] = dict(caption="GJR-t 99% VaR on stress days and high-VIX days: breach rate and the VaR multiplier that would have cut breaches to 1% (test window, 41 stocks)",
                        source=src_vr, family_col=None, head=["Group of stock-days", "Stock-days", "99% breach rate", "Multiplier for 1% breaches"],
                        rows=[[r.group, f"{r.stock_days:,}", pct(r.breach_rate), f"{r.multiplier_for_1pct:.2f}"] for r in vr.itertuples()])
    # (d) Basel coverage: complete non-overlapping 250-day blocks from the test start (as in basel_green_share)
    nb = b99[b99.model == "GJR-t"][["ticker", "n"]].copy()
    nb["blocks"] = nb.n // 250
    nb["covered_days"] = nb.blocks * 250
    nb["uncovered_days"] = nb.n - nb.covered_days
    last_cov = []
    for r in nb.itertuples():
        dd = sorted(gj[gj.ticker == r.ticker].date)
        last_cov.append(dd[r.covered_days - 1].date() if r.covered_days else None)
    nb["last_covered_date"] = last_cov
    src_nb = save(nb, "basel_coverage.csv")
    n("basel_blocks", "-".join(sorted({str(x) for x in nb.blocks})), src_nb)
    n("basel_cov_days", "-".join(sorted({str(x) for x in nb.covered_days})), src_nb)
    n("basel_uncov_min", int(nb.uncovered_days.min()), src_nb); n("basel_uncov_max", int(nb.uncovered_days.max()), src_nb)
    lc = max(x for x in nb.last_covered_date if x)
    n("basel_last_cov", pd.Timestamp(lc).strftime("%d %B %Y").lstrip("0"), src_nb)
    n("basel_hike_outside", "yes" if pd.Timestamp(lc) < pd.Timestamp(HIKE) else "no", src_nb)
    n("basel_values", ", ".join(f"{i / nb.blocks.max():g}" for i in range(int(nb.blocks.max()) + 1)), src_nb)

    # ---------------------------------------------------------------- Path A: repo-rate changes added to the VIX-relative + USD/INR set
    sb, sr = rd(f"summary_{REPO_BASE}.csv").set_index(["model", "alpha"]), rd(f"summary_{REPO}.csv").set_index(["model", "alpha"])
    db = ad(dm_counts(rd(f"diebold_mariano_{REPO_BASE}.csv"))); dr = ad(dm_counts(rd(f"diebold_mariano_{REPO}.csv")))
    src_r = f"outputs/tables/summary_{REPO_BASE}.csv, summary_{REPO}.csv, diebold_mariano_{REPO_BASE}.csv, diebold_mariano_{REPO}.csv"
    rr = []
    for m in ML:
        a99, b99_ = sb.loc[(m, 0.01)], sr.loc[(m, 0.01)]
        rr.append([m, pct(a99.exc_rate), pct(b99_.exc_rate), pct(a99.pass_kupiec, 0), pct(b99_.pass_kupiec, 0),
                   f"{int(db.loc[m].garch)} / {int(db.loc[m].ml)} / {int(db.loc[m]['none'])}", f"{int(dr.loc[m].garch)} / {int(dr.loc[m].ml)} / {int(dr.loc[m]['none'])}"])
        n(f"repo_exc99_{SLUG[m]}", pct(b99_.exc_rate), src_r); n(f"base2_exc99_{SLUG[m]}", pct(a99.exc_rate), src_r)
        n(f"repo_kup99_{SLUG[m]}", pct(b99_.pass_kupiec, 0), src_r); n(f"base2_kup99_{SLUG[m]}", pct(a99.pass_kupiec, 0), src_r)
    tb, tr = db.sum(), dr.sum()
    n("base2_dm_g", int(tb.garch), src_r); n("base2_dm_m", int(tb.ml), src_r); n("base2_dm_n", int(tb["none"]), src_r)
    n("repo_dm_g", int(tr.garch), src_r); n("repo_dm_m", int(tr.ml), src_r); n("repo_dm_n", int(tr["none"]), src_r)
    d_exc = [100 * (sr.loc[(m, 0.01)].exc_rate - sb.loc[(m, 0.01)].exc_rate) for m in ML]   # percentage points
    n("repo_maxshift_pp", f"{max(abs(x) for x in d_exc):.2f}", src_r)
    closer = sum(abs(sr.loc[(m, 0.01)].exc_rate - 0.01) < abs(sb.loc[(m, 0.01)].exc_rate - 0.01) for m in ML)
    n("repo_closer", closer, src_r)
    # plain one-line verdict, decided from the numbers (little = every 99% breach rate within 0.10 points and DM totals within 5%)
    little = max(abs(x) for x in d_exc) < 0.10 and abs(int(tr.garch) - int(tb.garch)) <= 0.05 * max(int(tb.garch), 1) + 1
    n("repo_verdict", "changed the results very little" if little else ("brought some ML miss rates closer to 1%" if closer else "moved the ML miss rates further from 1%"), src_r)
    T["repo"] = dict(caption="Effect of adding repo-rate changes to the ML inputs (VIX relative + USD/INR set; Diebold-Mariano on FZ0 at 95%: GARCH better / ML better / no difference)",
                     source=src_r, family_col=0,
                     head=["Model", "Breach 99% without", "Breach 99% with", "Kupiec pass without", "Kupiec pass with", "DM without", "DM with"],
                     rows=rr + [["All three", "", "", "", "", f"{int(tb.garch)} / {int(tb.ml)} / {int(tb['none'])}", f"{int(tr.garch)} / {int(tr.ml)} / {int(tr['none'])}"]])

    # ---------------------------------------------------------------- hypotheses (decided only from the numbers above)
    ml_closer = any(abs(s.loc[(m, 0.01)].exc_rate - 0.01) < min(abs(s.loc[(g_, 0.01)].exc_rate - 0.01) for g_ in GARCH) for m in ML)
    h1 = "Supported" if ml_closer else "Rejected"
    h2 = "Supported" if tot.ml > tot.garch else "Rejected"
    q4 = g["Q4 stressed"].idxmin()
    h3 = "Supported" if q4 in ML else "Rejected"
    vix_better = [abs(rd("summary_price_vixlevel.csv").set_index(["model", "alpha"]).loc[(m, 0.01)].exc_rate - 0.01) < abs(s.loc[(m, 0.01)].exc_rate - 0.01) for m in ML]
    h4 = "Supported" if all(vix_better) else "Partly supported" if any(vix_better) or flip < len(rows) else "Rejected"
    repo_better = N["repo_closer"][0] != "0"
    h4 = ("Rejected for India VIX and repo-rate changes; CPI and IIP outside scope" if not any(vix_better) and not repo_better
          else h4 + "; repo-rate changes " + N["repo_verdict"][0] + "; CPI and IIP outside scope")
    for k_, v_ in (("h1", h1), ("h2", h2), ("h3", h3), ("h4", h4)):
        n(k_, v_, "derived from the tables above (src/report_numbers.py)")
    T["hyp"] = dict(caption="Hypotheses and decisions", source="src/report_numbers.py (decision rules applied to the tables in this chapter)",
                    head=["Hypothesis", "Evidence", "Decision"], widths=[6, 7, 2.5],
                    rows=[["H1: ML models give 99% breach rates closer to nominal than GARCH models",
                           f"Closest three: {closest[0]} {pct(s.loc[(closest[0], 0.01)].exc_rate)}, {closest[1]} {pct(s.loc[(closest[1], 0.01)].exc_rate)}, {closest[2]} {pct(s.loc[(closest[2], 0.01)].exc_rate)}; ML {', '.join(f'{m} ' + pct(s.loc[(m, 0.01)].exc_rate) for m in ML)}", h1],
                          ["H2: ML models have significantly lower joint VaR-ES loss (FZ0) than GARCH models",
                           f"DM pairs: GARCH lower {int(tot.garch)}, ML lower {int(tot.ml)}, no difference {int(tot['none'])}", h2],
                          ["H3: Any ML advantage is larger when the India VIX is high (Q4)",
                           f"Lowest mean FZ0 in Q4: {q4}; Q4 loss above Q1 loss for {'all' if (g['Q4 stressed'] > g['Q1 calm']).all() else 'some'} models", h3],
                          ["H4: India VIX and macro inputs improve ML forecasts over price/volume inputs",
                           f"Adding the VIX level moved 99% breach rates of {sum(not x for x in vix_better)} of 3 ML models further from 1%; helped on validation but not on test in {flip} of {len(rows)} cases; adding repo-rate changes " + N["repo_verdict"][0] + "; CPI and IIP excluded by design", h4]])
    # ---------------------------------------------------------------- compact tables for the restructured report
    FAMS = {"GARCH": "GARCH", "ML": "ML", "Benchmark": "Bench."}
    T["bt"] = dict(caption="Backtest summary across 41 stocks. Breach = share of days the loss exceeded VaR (ideal 5% and 1%); pass and green = share of stocks",
                   source="outputs/tables/summary_price.csv", family_col=0,
                   head=["Model", "Family", "Breach 95%", "Breach 99%", "Kupiec pass 99%", "Basel green 99%", "Median FZ0 99%"],
                   rows=[[m, FAMS[fam(m)], pct(s.loc[(m, 0.05)].exc_rate), pct(s.loc[(m, 0.01)].exc_rate), pct(s.loc[(m, 0.01)].pass_kupiec, 0),
                          pct(s.loc[(m, 0.01)].green99, 0), f"{s.loc[(m, 0.01)].fz0_median_stocks:.3f}"] for m in ORDER])
    for k_ in ("bt99", "bt95"):  # appendix versions with short labels
        T[k_]["head"] = [{"Breach rate": "Breach", "Christ. CC pass": "Christ. pass", "Basel Green": "Basel green", "Mean FZ0": "Mean FZ0",
                          "Median FZ0": "Median FZ0", "Actual/forecast ES": "ES ratio"}.get(h, h) for h in T[k_]["head"]]
        T[k_]["rows"] = [[r_[0], FAMS.get(r_[1], r_[1])] + r_[2:] for r_ in T[k_]["rows"]]
    # Appendix B: the backtest columns not shown in Chapter 5's summary table
    T["bt_extra"] = dict(caption="Further backtest measures across 41 stocks (pass = share of stocks; ES ratio = real loss on miss days over forecast ES)",
                         source="outputs/tables/summary_price.csv", family_col=0,
                         head=["Model", "Kupiec pass 95%", "Christ. pass 95%", "Christ. pass 99%", "Mean FZ0 95%", "Mean FZ0 99%", "ES ratio 95%", "ES ratio 99%"],
                         rows=[[m, pct(s.loc[(m, 0.05)].pass_kupiec, 0), pct(s.loc[(m, 0.05)].pass_cc, 0), pct(s.loc[(m, 0.01)].pass_cc, 0),
                                f"{s.loc[(m, 0.05)].fz0:.3f}", f"{s.loc[(m, 0.01)].fz0:.2f}", f"{s.loc[(m, 0.05)].es_ratio:.3f}", f"{s.loc[(m, 0.01)].es_ratio:.3f}"]
                               for m in ORDER])
    # Appendix B: per-stock 99% breach rates summarised by model (full file linked in the text)
    pb = b99.groupby("model").agg(med=("exc_rate", "median"), lo=("exc_rate", "min"), hi=("exc_rate", "max"),
                                  above=("exc_rate", lambda x: int((x > 0.01).sum())), kfail=("kupiec_p", lambda x: int((x <= 0.05).sum()))).reindex(ORDER)
    T["perstock_compact"] = dict(caption="99% breach rate per stock, summarised by model (41 stocks)", source="outputs/tables/backtest_results_price.csv",
                                 family_col=0, head=["Model", "Median", "Lowest", "Highest", "Stocks above 1%", "Kupiec fails"],
                                 rows=[[m, pct(r_.med), pct(r_.lo), pct(r_.hi), int(r_.above), int(r_.kfail)] for m, r_ in pb.iterrows()])
    # Appendix C: return statistics by sector
    ds = desc.groupby("sector").agg(stocks=("ticker", "count"), sd=("sd", "median"), skew=("skew", "median"), kurt=("kurt", "median"),
                                    worst=("min", "min")).reset_index().sort_values("sd")
    T["desc_sector"] = dict(caption="Daily return statistics by sector, test window (medians across the sector's stocks; worst day is the sector minimum)",
                            source=src_desc, family_col=None, head=["Sector", "Stocks", "SD", "Skew", "Excess kurtosis", "Worst day"],
                            rows=[[x.sector, int(x.stocks), pct(x.sd), f"{x.skew + 0.0:.2f}".replace("-0.00", "0.00"), f"{x.kurt:.1f}", pct(x.worst, 1)] for x in ds.itertuples()])
    # Appendix D: GJR-t estimates across stocks
    gq = gp[gp.model == "GJR-t"][["alpha", "gamma", "beta", "nu", "persistence"]].describe(percentiles=[0.25, 0.5, 0.75]).T
    T["garch_compact"] = dict(caption="GJR-GARCH(1,1) with Student-t errors: estimates across the 41 stocks at the start of the test window",
                              source=src_gp, family_col=None, head=["Parameter", "Lowest", "25th pct.", "Median", "75th pct.", "Highest"],
                              rows=[[{"alpha": "alpha (reaction)", "gamma": "gamma (bad-news extra)", "beta": "beta (memory)", "nu": "nu (tail thickness)",
                                      "persistence": "Persistence"}[k_], f"{v['min']:.3f}", f"{v['25%']:.3f}", f"{v['50%']:.3f}", f"{v['75%']:.3f}", f"{v['max']:.3f}"]
                                    for k_, v in gq.iterrows()])

    # ---------------------------------------------------------------- monthly monitoring scorecard (Chapter 6)
    gr = s.loc[("GJR-t", 0.01)]
    n("gjrt_breaches_yr", f"{gr.exc_rate * 250:.1f}", src_s)
    n("ideal_yr", f"{0.01 * 250:.1f}", "nominal 1% x 250 trading days")
    n("gjrt_kupfail", pct(1 - gr.pass_kupiec, 0), src_s)
    T["kpis"] = dict(
        caption="Monthly monitoring scorecard: what to track, its value for GJR-t in the test window, and when to act",
        source="outputs/tables/summary_price.csv, breach_days_summary_price.csv, diag_feature_ranges_summary.csv (values as in Chapter 5)",
        head=["Measure", "Value in the test window", "Act when"], widths=[5, 4, 6], family_col=None,
        rows=[["99% breaches per stock per year (GJR-t)", f"{gr.exc_rate * 250:.1f} (ideal {N['ideal_yr'][0]})", "Five or more in the last 250 days for a stock (Basel amber zone): review that stock's model"],
              ["Stocks failing the \u201ctoo often?\u201d check (Kupiec, 99%)", N["gjrt_kupfail"][0], "The share rises above this level: re-estimate and review"],
              ["Days with 10 or more stocks breached together", N["d10_gjrt"][0] if "d10_gjrt" in N else str(int(bs.loc["GJR-t"].days_with_10plus_breaches)), "Any such day: stress review the same week; check the stress buffer"],
              ["Share of breaches on market-wide stress days", N["stress_gjrt"][0], "Re-size the stress buffer each year from this share"],
              ["Real loss on very bad days / forecast ES (99%)", N["es99_gjrt"][0], "Above 1: keep the prudence margin on ES"],
              ["No-risk forecasts by any ML challenger (99%)", f"{N['norisk99_xgb'][0]} stock-days (XGBoost)", "Any: the challenger fails review"],
              ["Inputs outside the range seen in training", f"USD/INR level {N['out_usdinr'][0]} of test days", "Above a few per cent: drop the input or refit"]])

    # ---------------------------------------------------------------- findings table (end of Chapter 5)
    v_ = lambda k: N[k][0]
    T["findings"] = dict(
        caption="Summary of findings: evidence, business implication and the matching recommendation",
        source="src/report_numbers.py; the source file of each number is listed in outputs/tables/report/report_numbers.csv",
        head=["Finding", "Number (source)", "Business implication", "Chapter 6"], widths=[4, 5, 5, 1.6], small=True, family_col=None,
        rows=[
            ["Student-t GARCH models were closest to the 1% breach rate", f"{v_('closest1')} {v_('closest1_exc')}, {v_('closest2')} {v_('closest2_exc')}, {v_('closest3')} {v_('closest3_exc')} (summary_price.csv)", "Use them for 99% limits, margins and capital", "6.1"],
            ["The ML models we tested were breached more often", f"XGBoost {v_('exc99_xgb')}, Random Forest {v_('exc99_rf')}, MLP {v_('exc99_mlp')}; about {v_('gap_xgb_gjrt_panel')} extra breaches a year across {v_('n_stocks')} stocks for XGBoost (summary_price.csv)", "Switching to ML would leave more days uncovered", "6.2, 6.5"],
            ["Most score gaps could be luck; real gaps favour GARCH", f"GARCH better {v_('dm_g')}, ML better {v_('dm_m')}, no difference {v_('dm_n')} of {v_('dm_total')} pairs (diebold_mariano_price.csv)", "No case for replacing GARCH; ML only as a challenger", "6.2"],
            ["XGBoost sometimes forecast no risk", f"{v_('norisk99_xgb')} stock-days at 99%; {v_('nr_stock')} mean FZ0 {v_('nr_fz0')} against median {v_('nr_fz0med')} (backtest_results_price.csv)", "Screen any ML model for zero-risk forecasts before use", "6.2, 6.8"],
            ["Losses on the very bad days were bigger than forecast", f"Actual/forecast ES above 1 for {v_('n_es_above1')} of {v_('n_models')} models (summary_price.csv)", "Add a prudence margin to ES", "6.8"],
            ["Breaches cluster on market-wide stress days", f"{v_('stress_share_days')} of days held {v_('stress_gjrt')} of GJR-t breaches; stress-day breach rate {v_('st_br_gjrt')} against {v_('ns_br_gjrt')}; 1% coverage needs about {v_('st_mult99')} times VaR (breach_days_price.csv, daily files)", "Keep a stress add-on sized from stress days", "6.3"],
            ["A high India VIX the day before did not predict breaches", f"Top-quartile VIX (above {v_('vix_q4_edge')}) breach rate {v_('br_q4_gjrt')} against {v_('br_q13_gjrt')}; VIX inputs moved ML further from 1% (summary_price_vixlevel.csv)", "Use the VIX as an alert, not as a margin multiplier or paid input", "6.3"],
            ["Interest-rate changes did not help the ML models either", f"With repo-rate changes, 99% miss rates XGBoost {v_('repo_exc99_xgb')}, Random Forest {v_('repo_exc99_rf')}, MLP {v_('repo_exc99_mlp')} (without: {v_('base2_exc99_xgb')}, {v_('base2_exc99_rf')}, {v_('base2_exc99_mlp')}) (summary_price_vixrel_fxchg_repo.csv)", "Do not buy a rate feed for one-day stock risk", "6.2"],
            ["Risk differs widely by sector", f"Median average 99% VaR from {v_('sec_low_var')} ({v_('sec_low')}) to {v_('sec_high_var')} ({v_('sec_high')}) (sector_summary_price.csv)", "Set margins and limits by sector, not one rate", "6.4"],
            ["The money at stake is large", f"Average 99% VaR {v_('avg_var99')}: about Rs {v_('buffer_100cr')} crore per Rs 100 crore; ML family Rs {v_('buf_mlfam')} crore against Rs {v_('buf_tfam')} crore for Student-t GARCH (buffer_by_model.csv)", "ML sets aside less money and is breached more often", "6.5"],
            ["The weeks after the October 2026 rate rise were calm for the models", f"{v_('ph_days')} trading days; 99% breach rate GJR-t {v_('ph_gjrt')}, XGBoost {v_('ph_xgb')} (post_hike_breaches_99.csv)", "Too short to judge; keep monthly monitoring", "6.9"],
        ])
    return N, T


if __name__ == "__main__":
    N, T = build()
    pd.DataFrame([dict(key=k, value=v[0], source=v[1]) for k, v in N.items()]).to_csv(os.path.join(R_DIR, "report_numbers.csv"), index=False)
    for k, v in N.items():
        print(f"{k:22s} {v[0]:>14s}   {v[1]}")
    print(len(N), "numbers;", len(T), "tables")
