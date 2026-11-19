"""Write report/first_results.md from output files only (no hand-typed numbers).

Wording rules (from the guide's brief): say "closest to nominal", not "wins", for breach rates; state
Diebold-Mariano results as counts of significant pairs; do not attribute ML degradation to overfitting
unless the diagnostics support it.

  python src/first_results.py
"""
import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(ROOT, "outputs", "tables")
GARCH = ["GARCH-normal", "GARCH-t", "EGARCH-normal", "EGARCH-t", "GJR-normal", "GJR-t"]
ML = ["XGBoost", "RandomForest", "MLP"]
ORDER = GARCH + ["HistSim250"] + ML
SETS = {"price": "price/volume only",
        "price_vixlevel": "price/volume + India VIX level",
        "price_vixrel": "price/volume + VIX relative to its 60-day mean",
        "price_fxchg": "price/volume + USD/INR changes",
        "price_vixrel_fxchg": "price/volume + VIX relative + USD/INR changes"}


def pct(x, d=2):
    return "n/a" if pd.isna(x) else f"{100 * x:.{d}f}%"


def table(df):
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(lines)


def rd(name):
    return pd.read_csv(os.path.join(T, name))


def dm_counts(dm, alpha=None):
    """For each ML model: pairs (GARCH model x stock) where GARCH has significantly lower loss, ML lower,
    or no significant difference (5% level). dm_stat = mean(loss_a - loss_b)."""
    d = dm.copy() if alpha is None else dm[dm["alpha"] == alpha].copy()
    flip = d["model_a"].isin(GARCH) & d["model_b"].isin(ML)
    d.loc[flip, ["model_a", "model_b"]] = d.loc[flip, ["model_b", "model_a"]].values
    d.loc[flip, "dm_stat"] = -d.loc[flip, "dm_stat"]
    d = d[d["model_a"].isin(ML) & d["model_b"].isin(GARCH)]
    out = []
    for m in ML:
        g = d[d["model_a"] == m]
        out.append(dict(model=m, pairs=len(g), garch_lower=int(((g.p < 0.05) & (g.dm_stat > 0)).sum()),
                        ml_lower=int(((g.p < 0.05) & (g.dm_stat < 0)).sum()), no_difference=int((g.p >= 0.05).sum())))
    return pd.DataFrame(out)


def rel_pin(bk, bbase, model, levels=(0.05, 0.01)):
    """Mean over stocks and levels of (pinball of set / pinball of price-only set) for one model, from the
    unrounded per-stock backtest files (same method as src/select_variants.py)."""
    k = ["ticker", "model", "alpha"]
    a = bk[(bk.model == model) & bk.alpha.isin(levels)].set_index(k)["pinball"]
    b = bbase[(bbase.model == model) & bbase.alpha.isin(levels)].set_index(k)["pinball"]
    return float((a / b.reindex(a.index)).mean())


def main():
    meta = pd.read_csv(os.path.join(ROOT, "data", "frozen", "manifest.csv"))
    uni = pd.read_csv(os.path.join(ROOT, "config", "universe.csv"))
    exc = pd.read_csv(os.path.join(ROOT, "config", "universe_excluded.csv"))
    S = {k: rd(f"summary_{k}.csv") for k in SETS if os.path.exists(os.path.join(T, f"summary_{k}.csv"))}
    B = {k: rd(f"backtest_results_{k}.csv") for k in S}
    base = S["price"].set_index(["model", "alpha"])
    bt = B["price"]
    n_days = f"{int(bt.n.min())}-{int(bt.n.max())}"
    L = []
    L += ["# First full-panel results (working draft)", "",
          "Status: Dr. Pardeshi's approval of the balanced panel and the November 2026 window is **pending**. "
          "These are working results for discussion, not report conclusions.", "",
          "Every number below is read from files in `outputs/tables/` (listed under Sources).", "",
          "## Setup", "",
          f"- Panel: {len(uni)} Nifty 50 stocks with full history from 2015 (config/universe.csv); "
          f"{len(exc)} candidates excluded (config/universe_excluded.csv).",
          f"- Frozen snapshot: {meta['snapshot_utc'].iloc[0]}, data {meta['first_date'].min()} to "
          f"{meta['last_date'].max()}, SHA-256 hashes in data/frozen/manifest.csv.",
          f"- Test window: 2024-01-01 to {meta['last_date'].max()} ({n_days} trading days per stock). "
          "Train to 2021-12-31, validation 2022-2023.",
          "- Feature sets are named by what they contain. Macro series (repo rate, CPI, IIP) are **not yet "
          "included**; the official files have not been supplied.", ""]

    # 1. headline table (price set)
    rows = []
    for m in ORDER:
        r5, r1 = base.loc[(m, 0.05)], base.loc[(m, 0.01)]
        rows.append({"Model": m, "Exc. 95% (nominal 5%)": pct(r5.exc_rate), "Exc. 99% (nominal 1%)": pct(r1.exc_rate),
                     "Kupiec pass 95%": pct(r5.pass_kupiec, 0), "Kupiec pass 99%": pct(r1.pass_kupiec, 0),
                     "Christoffersen CC pass 99%": pct(r1.pass_cc, 0), "Basel Green (99%)": pct(r1.green99, 0),
                     "Mean FZ0 95%": f"{r5.fz0:.4f}", "Median FZ0 95% (stocks)": f"{r5.fz0_median_stocks:.4f}",
                     "Pinball 99% (x10,000)": f"{1e4 * bt[(bt.model == m) & (bt.alpha == 0.01)].pinball.mean():.3f}"})
    gap = {m: abs(base.loc[(m, 0.01), "exc_rate"] - 0.01) for m in ORDER}
    closest = sorted(gap, key=gap.get)[:3]
    L += ["## 1. Breach rates and backtests (price/volume features for the ML models)", "",
          "Pass shares are the percentage of the stocks with p > 0.05. Basel zones apply to 99% VaR only and must be "
          "read with Kupiec: the traffic light penalises too many breaches, not too few. Lower FZ0 and pinball are better.", "",
          table(pd.DataFrame(rows)), "",
          f"**What this means.** At 99%, the breach rates closest to the nominal 1% were {', '.join(f'{m} ({pct(base.loc[(m, 0.01), 'exc_rate'])})' for m in closest)}. "
          f"The ML models breached {', '.join(f'{m} {pct(base.loc[(m, 0.01), 'exc_rate'])}' for m in ML)} of days at 99%. "
          "A breach rate above nominal means a desk using that model would hold too little capital or margin on the worst days; "
          "below nominal means it would tie up more capital than needed.", ""]

    # 2. Diebold-Mariano
    L += ["## 2. Diebold-Mariano tests: ML models against each GARCH model (pairs = 6 GARCH models x stocks)", ""]
    for k in [x for x in ("price", "price_vixlevel", "price_vixrel") if x in S]:
        fz = dm_counts(rd(f"diebold_mariano_{k}.csv"))
        p5 = dm_counts(rd(f"diebold_mariano_pinball_{k}.csv"), 0.05)
        p1 = dm_counts(rd(f"diebold_mariano_pinball_{k}.csv"), 0.01)
        t = pd.DataFrame({"ML model": fz.model,
                          "FZ0 95%: GARCH lower / ML lower / no diff": [f"{a} / {b} / {c}" for a, b, c in zip(fz.garch_lower, fz.ml_lower, fz.no_difference)],
                          "Pinball 95%: GARCH lower / ML lower / no diff": [f"{a} / {b} / {c}" for a, b, c in zip(p5.garch_lower, p5.ml_lower, p5.no_difference)],
                          "Pinball 99%: GARCH lower / ML lower / no diff": [f"{a} / {b} / {c}" for a, b, c in zip(p1.garch_lower, p1.ml_lower, p1.no_difference)]})
        L += [f"Feature set `{k}` ({SETS[k]}); {int(fz.pairs.iloc[0])} pairs per ML model:", "", table(t), ""]
    fzp = dm_counts(rd("diebold_mariano_price.csv"))
    tot = fzp[["garch_lower", "ml_lower", "no_difference"]].sum()
    L += [f"**What this means.** Across the three ML models (price set, FZ0 95%), GARCH had significantly lower loss in "
          f"{int(tot.garch_lower)} pairs, ML in {int(tot.ml_lower)}, and {int(tot.no_difference)} pairs showed no "
          "significant difference at the 5% level. A breach rate further from nominal does not by itself mean a "
          "significantly worse forecast on these loss functions; the test results should be quoted alongside the breach rates.", ""]

    # 3. XGBoost no-risk days and FZ0 robustness
    rows = []
    for k in S:
        s = S[k].set_index(["model", "alpha"])
        for a in (0.05, 0.01):
            rows.append({"Feature set": k, "Level": f"{int((1 - a) * 100)}%", "XGBoost no-risk days (all stocks)": int(s.loc[("XGBoost", a), "norisk_days"]),
                         "XGBoost mean FZ0": f"{s.loc[('XGBoost', a), 'fz0']:.4f}",
                         "XGBoost median FZ0 (stocks)": f"{s.loc[('XGBoost', a), 'fz0_median_stocks']:.4f}"})
    L += ["## 3. XGBoost 'no-risk' days and the effect on mean FZ0", "",
          "A no-risk day is a day on which XGBoost's forecast lower-tail quantile was at or above zero, so VaR hit its "
          "floor (0.0001%). FZ0 is unbounded on such days if a loss follows, so the mean can be dominated by a single day; "
          "the median across stocks is reported next to it.", "", table(pd.DataFrame(rows)), ""]

    # 4. feature sets
    rows = []
    for k in S:
        s = S[k].set_index(["model", "alpha"])
        for m in ML:
            rows.append({"Feature set": k, "Contains": SETS[k], "Model": m,
                         "Exc. 95%": pct(s.loc[(m, 0.05), "exc_rate"]), "Exc. 99%": pct(s.loc[(m, 0.01), "exc_rate"]),
                         "Kupiec pass 99%": pct(s.loc[(m, 0.01), "pass_kupiec"], 0),
                         "Pinball vs price (95%+99%)": f"{rel_pin(B[k], B['price'], m):.3f}"})
    sup = os.path.join(T, "superseded", "pre_es_floor_2026-11-18", "summary_price_vix_macro.csv")
    L += ["## 4. ML models by feature set (test window)", "",
          "GARCH and historical simulation do not use these features, so their rows are identical across sets.", "",
          table(pd.DataFrame(rows)), ""]
    if os.path.exists(sup):
        o = pd.read_csv(sup).set_index(["model", "alpha"])
        L += ["For reference, the earlier run labelled `price_vix_macro`, which actually contained VIX level + USD/INR "
              "level (no repo rate, CPI or IIP) and predates the XGBoost ES floor, gave 99% breach rates of "
              + ", ".join(f"{m} {pct(o.loc[(m, 0.01), 'exc_rate'])}" for m in ML)
              + " (outputs/tables/superseded/pre_es_floor_2026-11-18/).", ""]

    # 5. diagnosis
    rng = rd("diag_feature_ranges_summary.csv")
    rng = rng[rng.fit_window == "train_val"].set_index("feature")
    sel = json.load(open(os.path.join(T, "validation", "selected_variant.json")))
    vs = rd(os.path.join("validation", "variant_selection.csv"))
    rows = []
    for k_val, k_test in (("val_price_vixlevel", "price_vixlevel"), ("val_price_vixrel", "price_vixrel"),
                          ("val_price_fxchg", "price_fxchg"), ("val_price_vixrel_fxchg", "price_vixrel_fxchg")):
        if k_test not in S:
            continue
        s = S[k_test].set_index(["model", "alpha"])
        for m in ML:
            v = vs[(vs.variant == k_val) & (vs.model == m)].iloc[0]
            test_rel = rel_pin(B[k_test], B["price"], m)
            rows.append({"Variant": k_test, "Model": m, "Validation pinball vs price (2022-23)": f"{v.rel_pinball:.3f}",
                         "Test pinball vs price (2024-26)": f"{test_rel:.3f}",
                         "Validation exc. 99%": pct(v.exc99), "Test exc. 99%": pct(s.loc[(m, 0.01), "exc_rate"])})
    flips = [r for r in rows if float(r["Validation pinball vs price (2022-23)"]) < 1 < float(r["Test pinball vs price (2024-26)"])]
    L += ["## 5. Why did market features change the ML results? (diagnosis)", "",
          "**Feature ranges.** Share of test days on which a feature lies outside the range of the data the final "
          "models were fitted on (2015-2023), median across stocks:", "",
          table(pd.DataFrame([{"Feature": f, "Share of test days outside fitted range": pct(rng.loc[f, "median_share_outside"], 1),
                               "Fitted range (median)": f"{rng.loc[f, 'fit_min_median']:.4g} to {rng.loc[f, 'fit_max_median']:.4g}",
                               "Test range (median)": f"{rng.loc[f, 'test_min_median']:.4g} to {rng.loc[f, 'test_max_median']:.4g}"}
                              for f in ("usdinr", "vix", "rv_x_vix", "vix_rel60", "usdinr_ret1", "usdinr_ret21") if f in rng.index])), "",
          "**Validation window versus test window.** Pinball loss relative to the price-only set (below 1 = the "
          "features helped). Validation: models trained on 2015-2019, calibrated on 2020-2021, evaluated on 2022-2023.", "",
          table(pd.DataFrame(rows)), "",
          f"Variant chosen on the validation window only (rule and timestamp in outputs/tables/validation/selected_variant.json, "
          f"created {sel['created_utc']} UTC, before the test rerun): overall `{sel['selected_overall'].replace('val_', '')}`, "
          f"stationary `{sel['selected_stationary'].replace('val_', '')}`.", "",
          f"**What this means.** The USD/INR level was outside its fitted range on most test days "
          f"({pct(rng.loc['usdinr', 'median_share_outside'], 0)}); tree models cannot extrapolate beyond the values they "
          f"were fitted on, so poor results with that feature are consistent with a range shift. The VIX level was outside "
          f"its range on only {pct(rng.loc['vix', 'median_share_outside'], 1)} of test days, so range shift does not explain "
          f"the VIX result. In {len(flips)} of {len(rows)} model-variant cases the features lowered pinball loss on the "
          f"validation window (2022-23) but raised it on the test window (2024-26)"
          + (": the value of these features changed between periods. " if flips else ". ")
          + "Overfitting was not tested directly (for example by comparing in-sample and out-of-sample loss), so the "
            "report should not attribute the ML results to overfitting on this evidence.", ""]

    # 6. breach clustering
    bd_path = os.path.join(T, "breach_days_summary_price.csv")
    if os.path.exists(bd_path):
        bd = pd.read_csv(bd_path)
        bd = bd[bd.alpha == 0.01].set_index("model").reindex(ORDER).reset_index()
        share_days = bd["share_of_days_stress"].iloc[0]
        L += ["## 6. Do breaches cluster on market-wide stress days? (99% VaR, price set)", "",
              f"Stress day = Nifty 50 one-day log return of -2% or worse, defined in advance: "
              f"{int(bd['stress_days'].iloc[0])} of {int(bd['test_days'].iloc[0])} test days ({pct(share_days, 1)}).", "",
              table(pd.DataFrame({"Model": bd.model, "Breaches (all stocks)": bd.total_breaches,
                                  "Share on stress days": bd.share_of_breaches_on_stress_days.map(lambda v: pct(v, 1)),
                                  "Max in one day": bd.max_breaches_one_day,
                                  "Days with 10+ stocks breaching": bd.days_with_10plus_breaches,
                                  "Top days": bd.top_days})), "",
              f"**What this means.** If breaches were spread evenly, about {pct(share_days, 1)} would fall on stress days. "
              "A much higher share means breaches arrive together across many stocks on the same day, which is what matters "
              "for a portfolio or a clearing house: losses that hit many positions at once.", ""]

    # 7. exclusions
    er = rd("exclusion_review.csv")
    er_t = er[er.triggered_exclusion | er.ticker.eq("ADANIENT.NS")]
    L += ["## 7. The three stocks excluded as suspected unadjusted corporate actions", "",
          table(pd.DataFrame({"Stock": er_t.ticker, "Date": er_t.date, "Move": er_t.log_move.map(pct),
                              "Nifty": er_t.nifty_move.map(pct), "Assessment": er_t.classification,
                              "Note": er_t.note.fillna("")})), "",
          "Rule: excluded if a one-day move of 35% or more occurred while the Nifty moved less than 3% (moves that "
          "triggered exclusion are those with |move| >= 35%). Event notes come from general knowledge and need a cited "
          "source (NSE corporate-action records or news) before they appear in the report.", ""]
    sens = [f for f in ("sens_adanient_price", "sens_adanient_price_vixlevel")
            if os.path.exists(os.path.join(T, "sensitivity", f"backtest_results_{f}.csv"))]
    if sens:
        s = pd.read_csv(os.path.join(T, "sensitivity", f"backtest_results_{sens[0]}.csv"))
        s = s[s.alpha == 0.01].set_index("model").reindex(ORDER)
        L += ["**ADANIENT sensitivity run** (data from 4 Jun 2015, the day after the suspected corporate action; genuine "
              "crash days of 2023-2024 kept). 99% VaR breach rates over the same test window: "
              + ", ".join(f"{m} {pct(s.loc[m, 'exc_rate'])}" for m in ORDER) + ".", "",
              "ADANIENT is a crash-prone stock, not a data problem; it is reported here so that excluding it from the "
              "balanced panel does not hide how the models behave on such a stock.", ""]

    L += ["## Sources", "",
          "- outputs/tables/summary_*.csv, backtest_results_*.csv, diebold_mariano_*.csv, diebold_mariano_pinball_*.csv",
          "- outputs/tables/diag_feature_ranges_summary.csv, outputs/tables/validation/variant_selection.csv, selected_variant.json",
          "- outputs/tables/breach_days_summary_price.csv, outputs/tables/exclusion_review.csv, outputs/tables/sensitivity/",
          "- config/universe.csv, config/universe_excluded.csv, data/frozen/manifest.csv"]
    open(os.path.join(ROOT, "report", "first_results.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("Wrote report/first_results.md")


if __name__ == "__main__":
    main()
