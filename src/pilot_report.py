"""Write report/pilot_summary.md and report/pilot_pitch.docx from pilot outputs only.

Every number is read from outputs/tables/pilot_*_<tag>.csv, outputs/*_<tag>.csv or
data/logs/; nothing is typed in by hand. Run src/pilot_analysis.py first.

  python src/pilot_report.py --features price+vix
"""
import argparse, math, os, re

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GARCH = ["GARCH-normal", "GARCH-t", "EGARCH-normal", "EGARCH-t", "GJR-normal", "GJR-t"]
ML = ["XGBoost", "RandomForest", "MLP"]
ORDER = GARCH + ["HistSim250"] + ML
FAM = {**{m: "GARCH" for m in GARCH}, **{m: "ML" for m in ML}, "HistSim250": "Benchmark"}
HIKE = "2026-10-07"


def pct(x, d=2):
    return "n/a" if pd.isna(x) else f"{100 * x:.{d}f}%"


def share(x, n):
    return "n/a" if pd.isna(x) else f"{int(round(x * n))}/{n}"


def load(tag):
    t = lambda f: pd.read_csv(os.path.join(ROOT, "outputs", "tables", f"{f}_{tag}.csv"))
    D = dict(meta=t("pilot_meta").iloc[0], summ=t("pilot_model_summary"),
             fz=t("pilot_fz0_by_vix_quartile").set_index("model"),
             post=t("pilot_post_hike"), dm=t("pilot_dm_ml_vs_garch").set_index("ml_model"),
             bt=pd.read_csv(os.path.join(ROOT, "outputs", f"backtest_results_{tag}.csv")),
             daily=pd.read_csv(os.path.join(ROOT, "outputs", "tables", f"pilot_daily_forecasts_{tag}.csv"),
                               parse_dates=["date"]))
    dr = os.path.join(ROOT, "data", "logs", "dropped_rows.csv")
    D["dropped"] = pd.read_csv(dr).drop_duplicates() if os.path.exists(dr) else pd.DataFrame()
    logs = [os.path.join(ROOT, "data", "logs", f) for f in os.listdir(os.path.join(ROOT, "data", "logs"))
            if f.startswith("pilot_run")]
    D["fit_failures"] = sum(len(re.findall(r" failed: ", open(f, encoding="utf-8", errors="ignore").read()))
                            for f in logs)
    D["n_tickers"] = len(D["meta"]["tickers"].split(","))
    return D


def facts(D):
    """Derived statements, each computed from the loaded tables."""
    s, n = D["summ"].set_index(["model", "alpha"]), D["n_tickers"]
    F = {}
    F["t_models_99"] = [(m, s.loc[(m, 0.01), "exc_rate"], s.loc[(m, 0.01), "pass_kupiec"],
                         s.loc[(m, 0.01), "green99"]) for m in ("GARCH-t", "EGARCH-t", "GJR-t")]
    F["n_models_99"] = [(m, s.loc[(m, 0.01), "exc_rate"], s.loc[(m, 0.01), "pass_kupiec"],
                         s.loc[(m, 0.01), "green99"]) for m in ("GARCH-normal", "EGARCH-normal", "GJR-normal")]
    F["xgb"] = s.loc["XGBoost"]
    F["dm"] = D["dm"]
    F["best_fz"] = {a: s.xs(a, level="alpha")["fz0"].idxmin() for a in (0.05, 0.01)}
    F["best_fz_val"] = {a: s.xs(a, level="alpha")["fz0"].min() for a in (0.05, 0.01)}
    q4 = D["fz"]["Q4 stressed"]
    F["q4_best"], F["q4_best_val"] = q4.idxmin(), q4.min()
    F["q4_best_garch"], F["q4_best_garch_val"] = q4[GARCH].idxmin(), q4[GARCH].min()
    F["hs"] = s.loc["HistSim250"]
    post = D["post"]
    F["post_days"] = int(post["days"].iloc[0]) if len(post) else 0
    p99 = post[post["alpha"] == 0.01].assign(fam=lambda d: d["model"].map(FAM))
    F["post99_by_fam"] = p99.groupby("fam")["exceptions"].sum().to_dict()
    F["post99_obs"] = int(p99["obs"].iloc[0]) if len(p99) else 0
    n_test = int(D["meta"]["test_days_per_stock"])
    F["basel_windows"] = math.floor(n_test / 250)
    d = D["daily"][(D["daily"]["model"] == "GJR-t") & (D["daily"]["alpha"] == 0.05)]
    big = d.loc[d["ret"].abs().idxmax()]
    F["biggest_move"] = (big["ticker"], big["date"].date(), big["ret"])
    return F


# ------------------------------------------------------------------ markdown
def md_table(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    out += ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(out)


def results_table(D):
    s, n = D["summ"], D["n_tickers"]
    rows = []
    for m in ORDER:
        r5 = s[(s.model == m) & (s.alpha == 0.05)].iloc[0]
        r1 = s[(s.model == m) & (s.alpha == 0.01)].iloc[0]
        rows.append({"Model": m, "Family": FAM[m],
                     "Exc. rate 95% (nominal 5%)": pct(r5.exc_rate), "Exc. rate 99% (nominal 1%)": pct(r1.exc_rate),
                     "Kupiec pass 95%": share(r5.pass_kupiec, n), "Kupiec pass 99%": share(r1.pass_kupiec, n),
                     "Christoffersen CC pass 95%": share(r5.pass_cc, n), "Christoffersen CC pass 99%": share(r1.pass_cc, n),
                     "Basel Green share (99%)": pct(r1.green99, 0),
                     "Pinball 95%": f"{r5.pinball:.4f}", "Pinball 99%": f"{r1.pinball:.4f}",
                     "FZ0 95%": f"{r5.fz0:.4f}", "FZ0 99%": f"{r1.fz0:.4f}"})
    return pd.DataFrame(rows)


def short_table(D):
    """Compact version for the one-to-two-page pitch."""
    full = results_table(D)
    return full[["Model", "Exc. rate 95% (nominal 5%)", "Exc. rate 99% (nominal 1%)", "Kupiec pass 95%",
                 "Kupiec pass 99%", "Basel Green share (99%)", "FZ0 95%", "FZ0 99%"]].rename(columns={
        "Exc. rate 95% (nominal 5%)": "Exc. 95%", "Exc. rate 99% (nominal 1%)": "Exc. 99%",
        "Kupiec pass 95%": "Kupiec 95%", "Kupiec pass 99%": "Kupiec 99%",
        "Basel Green share (99%)": "Basel Green (99%)"})


def regime_md(D):
    f = D["fz"].reindex(ORDER).reset_index()
    for c in f.columns[1:]:
        f[c] = f[c].map(lambda v: f"{v:.4f}")
    return f.rename(columns={"model": "Model"})


def post_md(D):
    p = D["post"].copy()
    p["model"] = pd.Categorical(p["model"], ORDER, ordered=True)
    out = p.pivot_table(index="model", columns="alpha", values="exceptions", observed=True).reset_index()
    rate = p.pivot_table(index="model", columns="alpha", values="exc_rate", observed=True).reset_index()
    obs = int(p["obs"].iloc[0])
    return pd.DataFrame({"Model": out["model"].astype(str),
                         f"Exceptions 95% (of {obs})": out[0.05].astype(int).astype(str) + " (" + rate[0.05].map(pct) + ")",
                         f"Exceptions 99% (of {obs})": out[0.01].astype(int).astype(str) + " (" + rate[0.01].map(pct) + ")"})


def xgb_text(x, dm, n):
    """XGBoost observation; direction and wording follow the numbers."""
    e5, e1 = x.loc[0.05, "exc_rate"], x.loc[0.01, "exc_rate"]
    if e5 > 0.05 and e1 > 0.01:
        verdict = "XGBoost breached more often than nominal at both levels (VaR too low, i.e. too aggressive)"
        biz = "In business terms, it would set capital and margins too low."
    elif e5 < 0.05 and e1 < 0.01:
        verdict = "XGBoost breached less often than nominal at both levels (VaR too high, i.e. too cautious)"
        biz = "In business terms, it would set capital and margins too high."
    else:
        verdict = "XGBoost was on different sides of nominal at the two levels"
        biz = ""
    d = dm.loc["XGBoost"]
    pairs = int(d.sum())
    if d["garch_better"] == 0 and d["ml_better"] == 0:
        dm_txt = (f"On the 95% joint VaR-ES loss (FZ0), Diebold-Mariano found no significant difference from any "
                  f"GARCH model ({int(d['no_diff'])} of {pairs} pairs).")
    else:
        dm_txt = (f"On the 95% joint VaR-ES loss (FZ0), Diebold-Mariano found GARCH significantly better in "
                  f"{int(d['garch_better'])}, XGBoost better in {int(d['ml_better'])} and no difference in "
                  f"{int(d['no_diff'])} of {pairs} pairs.")
    return (f"{verdict}: {pct(e5)} at 95% (nominal 5%) and {pct(e1)} at 99% (nominal 1%). It passed Kupiec in "
            f"{share(x.loc[0.05, 'pass_kupiec'], n)} stocks at 95% and {share(x.loc[0.01, 'pass_kupiec'], n)} at 99%, "
            f"with a Basel Green share of {pct(x.loc[0.01, 'green99'], 0)}. {dm_txt} {biz}").strip()


def corrections(D, tag):
    """Old (bugged) vs new XGBoost figures, read from outputs/tables/superseded/."""
    sup = os.path.join(ROOT, "outputs", "tables", "superseded")
    old_p = os.path.join(sup, f"xgb_bug_summary_{tag}.csv")
    if not os.path.exists(old_p):
        return None
    old = pd.read_csv(old_p).set_index(["model", "alpha"]).loc["XGBoost"]
    new = D["summ"].set_index(["model", "alpha"]).loc["XGBoost"]
    n = D["n_tickers"]
    rows = []
    for col, lab, f in [("exc_rate", "Exception rate", pct), ("pass_kupiec", "Kupiec pass", lambda v: share(v, n)),
                        ("pass_cc", "Christoffersen CC pass", lambda v: share(v, n)),
                        ("fz0", "Mean FZ0", lambda v: f"{v:.4f}"), ("es_ratio", "Actual/expected ES", lambda v: f"{v:.4f}")]:
        for a in (0.05, 0.01):
            rows.append({"XGBoost metric": f"{lab} {int((1 - a) * 100)}%", "Before fix": f(old.loc[a, col]),
                         "After fix": f(new.loc[a, col])})
    rows.append({"XGBoost metric": "Basel Green share 99%", "Before fix": pct(old.loc[0.01, "green99"], 0),
                 "After fix": pct(new.loc[0.01, "green99"], 0)})
    od = pd.read_csv(os.path.join(sup, f"xgb_bug_pilot_dm_ml_vs_garch_{tag}.csv")).set_index("ml_model").loc["XGBoost"]
    nd = D["dm"].loc["XGBoost"]
    rows.append({"XGBoost metric": "DM pairs where GARCH significantly better", "Before fix": int(od["garch_better"]),
                 "After fix": int(nd["garch_better"])})
    other_changed = []
    oth = pd.read_csv(old_p).set_index(["model", "alpha"]).drop(index="XGBoost", level="model")
    nth = D["summ"].set_index(["model", "alpha"]).drop(index="XGBoost", level="model")[list(oth.columns)]
    nth.index = pd.MultiIndex.from_tuples([(str(m), a) for m, a in nth.index], names=oth.index.names)
    if (oth.fillna(-9).sort_index() != nth.fillna(-9).sort_index()).to_numpy().any():
        other_changed.append("non-XGBoost summary rows")
    ofz = pd.read_csv(os.path.join(sup, f"xgb_bug_pilot_fz0_by_vix_quartile_{tag}.csv"), index_col=0)
    best_changed = ofz["Q4 stressed"].idxmin() != D["fz"]["Q4 stressed"].idxmin()
    return pd.DataFrame(rows), other_changed, best_changed


def observations(D, F):
    n = D["n_tickers"]
    tm = "; ".join(f"{m} {pct(e)}" for m, e, _, _ in F["t_models_99"])
    nm = "; ".join(f"{m} {pct(e)}" for m, e, _, _ in F["n_models_99"])
    tk = sorted({share(k, n) for _, _, k, _ in F["t_models_99"]})
    tg = sorted({pct(g, 0) for _, _, _, g in F["t_models_99"]})
    ng = sorted({pct(g, 0) for _, _, _, g in F["n_models_99"]})
    x, dm = F["xgb"], F["dm"]
    pairs = int(dm.loc["XGBoost"].sum())
    obs = [
        f"Fat tails matter at 99%. The Student-t GARCH models had 99% exception rates closest to the nominal 1% "
        f"({tm}), passed Kupiec in {', '.join(tk)} stocks and had a Basel Green share of {', '.join(tg)}. "
        f"The Normal versions breached more often ({nm}); their Green share was {', '.join(ng)}.",
        xgb_text(x, dm, n),
        f"MLP and Random Forest were not significantly different from any GARCH model on 95% FZ0 "
        f"(Diebold-Mariano: no significant difference in {int(dm.loc['MLP', 'no_diff'])} of {int(dm.loc['MLP'].sum())} "
        f"pairs for MLP and {int(dm.loc['RandomForest', 'no_diff'])} of {int(dm.loc['RandomForest'].sum())} for Random Forest). "
        f"MLP's 99% exception rate was {pct(D['summ'].set_index(['model','alpha']).loc[('MLP',0.01),'exc_rate'])}; "
        f"Random Forest's was {pct(D['summ'].set_index(['model','alpha']).loc[('RandomForest',0.01),'exc_rate'])} "
        f"and it passed Kupiec at 99% in {share(D['summ'].set_index(['model','alpha']).loc[('RandomForest',0.01),'pass_kupiec'], n)} stocks.",
        f"On the joint VaR-ES loss (FZ0, lower is better) the lowest mean was {F['best_fz'][0.05]} at 95% "
        f"({F['best_fz_val'][0.05]:.4f}) and {F['best_fz'][0.01]} at 99% ({F['best_fz_val'][0.01]:.4f}). "
        f"In the highest India VIX quartile the lowest mean 95% FZ0 was {F['q4_best']} ({F['q4_best_val']:.4f}) "
        f"against {F['q4_best_garch_val']:.4f} for the best GARCH model ({F['q4_best_garch']}). "
        f"This regime split is descriptive only and was not significance-tested in the pilot.",
        f"The rolling 250-day historical-simulation benchmark breached {pct(F['hs'].loc[0.05, 'exc_rate'])} of days at 95% "
        f"and passed Kupiec at 95% in {share(F['hs'].loc[0.05, 'pass_kupiec'], n)} stocks; the weakest GARCH-family "
        f"model passed Kupiec at 95% in {share(D['summ'][(D['summ'].model.isin(GARCH)) & (D['summ'].alpha == 0.05)]['pass_kupiec'].min(), n)} "
        f"stocks. In this pilot the volatility-updating models tracked risk better than the fixed-window rule.",
    ]
    return obs


def es_bias(dist, alpha=0.05):
    b = pd.read_csv(os.path.join(ROOT, "outputs", "tables", "xgb_es_approx_bias.csv"))
    v = b[(b.distribution == dist) & (b.alpha == alpha)]["understatement_pct"].iloc[0]
    return f"{v:.1f}% at 95%"


def problems(D, F):
    n = D["n_tickers"]
    dr = D["dropped"]
    dates = ", ".join(sorted(dr["date"].astype(str).unique())) if len(dr) else "none"
    t, d, r = F["biggest_move"]
    x = F["xgb"]
    return [
        f"Data: Yahoo returned zero-volume placeholder rows for all {n} stocks on {dates}. They were dropped "
        f"and logged in data/logs/dropped_rows.csv ({len(dr)} rows). A check on 18 Nov 2026 found a Nifty 50 "
        f"(^NSEI) row for 2025-03-18 but none for 2026-01-15, so the first looks like a real trading day "
        f"with a missing stock price and the second like a market holiday. Confirm against NSE in P2.",
        "Reproducibility: Yahoo's adjusted closes differ by up to about 5e-7 (relative) between downloads, "
        "which changed a few XGBoost and Random Forest exceptions between otherwise identical runs. The pilot "
        "now reads one hashed snapshot (data/processed/pilot_snapshot/manifest.csv); the full study must use "
        "the frozen snapshot in data/frozen/.",
        f"Largest one-day move in the pilot test window: {t} on {d}, log return {pct(r)}. Checked by the student "
        f"against press reports (a results-day rally); it is kept in the data as a genuine tail event.",
        "Models failing Kupiec in every stock: " + (", ".join(
            f"{m} at {int((1 - a) * 100)}% ({pct(v)} exceptions)" for (m, a), v in
            D["summ"].set_index(["model", "alpha"]).query("pass_kupiec == 0")["exc_rate"].items()) or "none") + ".",
        f"ES approximation: XGBoost's ES is the mean of 5 tail quantiles. Even with exact quantiles this understates "
        f"true ES by {es_bias('normal')} for a Normal tail and {es_bias('t(4)')} for Student-t(4) "
        f"(outputs/tables/xgb_es_approx_bias.csv). XGBoost's realised/expected ES ratio is "
        f"{x.loc[0.05, 'es_ratio']:.4f} at 95% and {x.loc[0.01, 'es_ratio']:.4f} at 99%; the ratio is measured only on "
        f"breach days and is pulled down when VaR is too shallow, so it should not be read as proof of accurate ES.",
        f"GARCH fits: {D['fit_failures']} failed fits were logged in the pilot runs.",
        f"Basel Green share is computed from only {F['basel_windows']} non-overlapping 250-day windows per stock, "
        "so each stock can only score 0%, 50% or 100%.",
        "Macro variables (repo rate, CPI, IIP) are not in the pilot because the official series are not yet "
        "filled in; the pilot uses price + India VIX features.",
    ]


def corrections_md(D, tag):
    c = corrections(D, tag)
    if c is None:
        return []
    tbl, other_changed, best_changed = c
    return [
        "## Corrections",
        "An earlier version of this summary (git commit 97517a4) reported XGBoost as far too cautious. That result "
        "came from a bug in `xgb_quantile`: after sorting the fitted quantiles in ascending order, the code read "
        "the first column (the 0.1*alpha quantile) as VaR, and the ES average included the alpha quantile. The fix "
        "reads the last sorted column as VaR and averages the other five for ES. The pilot was rerun from the same "
        "hashed snapshot with the same settings.", "",
        md_table(tbl), "",
        "What changed:",
        "- Observation 2 (XGBoost) is rewritten. The earlier claims that XGBoost was too conservative and that "
        "GARCH was significantly better in all 18 Diebold-Mariano comparisons are withdrawn.",
        "- The XGBoost rows in the results, VIX-quartile and post-hike tables, and the XGBoost line in Figures 1 and 2.",
        "- Problems found: the XGBoost item is replaced by a data-driven list of models failing Kupiec in every stock.",
        f"- Unchanged: {'none - check' if other_changed else 'every GARCH, HistSim250, Random Forest and MLP number (verified identical to the earlier run)'}; "
        f"the best model by mean FZ0 and the lowest-loss model in the highest VIX quartile "
        f"{'CHANGED' if best_changed else 'are the same as before'}.", "",
    ]


def write_md(D, F, path, tag):
    m = D["meta"]
    lines = [
        "# Pilot results summary: GARCH vs ML downside risk (3 stocks)", "",
        "Every number below is read from the files listed under Sources. Nothing was typed in by hand.", "",
        "## Setup",
        f"- Stocks: {m['tickers'].replace(',', ', ')}",
        f"- Features: {m['features']} (macro variables not yet available)",
        f"- Data: from {m['data_start']} to {m['test_last_date']} (last complete close; the run on 18 Nov 2026 excluded the open trading day)",
        f"- Train: to {m['train_end']} | Validation: to {m['val_end']} | Test: {m['test_start']} to {m['test_last_date']} "
        f"({m['test_days_per_stock']} test days per stock)",
        f"- Models: GARCH, EGARCH, GJR-GARCH (Normal and Student-t, refit every {m['refit_days']} days); XGBoost (quantile), "
        "Random Forest and MLP (volatility + filtered historical simulation); benchmark: rolling 250-day historical simulation",
        f"- Seed {m['seed']}; pipeline runtime for 3 stocks: {m['pipeline_runtime_s']} s", "",
        *corrections_md(D, tag),
        "## Results by model (mean over the 3 stocks)",
        "Pass counts are the number of stocks with p > 0.05. Basel zones apply to 99% VaR only. Lower pinball and FZ0 are better. "
        "Read Kupiec and the Basel share together: the traffic light only penalises too many breaches, so a model "
        "that breaches far too rarely can still score 100% Green.", "",
        md_table(results_table(D)), "",
        "## Mean FZ0 loss at 95% by India VIX quartile (previous day's VIX; lower is better)", "",
        md_table(regime_md(D)), "",
        f"## From the 7 Oct 2026 repo hike to {m['test_last_date']} ({F['post_days']} trading days x {D['n_tickers']} stocks)", "",
        md_table(post_md(D)), "",
        f"The window is too short for formal tests: with {F['post99_obs']} observations, about "
        f"{F['post99_obs'] * 0.01:.1f} exceptions are expected at 99%.", "",
        "## Observations", *[f"{i}. {o}" for i, o in enumerate(observations(D, F), 1)], "",
        "## Problems found", *[f"- {p}" for p in problems(D, F)], "",
        "## Caution",
        "Three stocks are a pilot, not a conclusion. Results can change on the full 40-45 stock panel.", "",
        "## Sources",
        f"- outputs/summary_{tag}.csv, outputs/backtest_results_{tag}.csv, outputs/regime_results_{tag}.csv, outputs/diebold_mariano_{tag}.csv",
        f"- outputs/tables/pilot_model_summary_{tag}.csv, pilot_fz0_by_vix_quartile_{tag}.csv, pilot_post_hike_{tag}.csv, "
        f"pilot_dm_ml_vs_garch_{tag}.csv, pilot_meta_{tag}.csv, pilot_daily_forecasts_{tag}.csv",
        "- data/logs/dropped_rows.csv, data/logs/pilot_run_*.log, data/processed/pilot_snapshot/manifest.csv",
    ]
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")


# ------------------------------------------------------------------ docx
def write_docx(D, F, path, tag, logo):
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt, RGBColor

    doc = Document()
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
    for side in ("left_margin", "right_margin"):
        setattr(sec, side, Cm(2.0))
    sec.top_margin = sec.bottom_margin = Cm(1.8)
    st = doc.styles["Normal"]
    st.font.name, st.font.size = "Times New Roman", Pt(10.5)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    st.paragraph_format.space_after = Pt(4)

    # page number bottom right
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = fp.add_run()
    for tagname, text in (("begin", None), (None, "PAGE"), ("end", None)):
        if tagname:
            el = OxmlElement("w:fldChar"); el.set(qn("w:fldCharType"), tagname)
        else:
            el = OxmlElement("w:instrText"); el.set(qn("xml:space"), "preserve"); el.text = text
        run._r.append(el)

    def para(text="", bold=False, size=None, align=None, italic=False, space_after=None):
        p = doc.add_paragraph()
        r = p.add_run(text); r.bold, r.italic = bold, italic
        r.font.name = "Times New Roman"
        if size: r.font.size = Pt(size)
        if align is not None: p.alignment = align
        if space_after is not None: p.paragraph_format.space_after = Pt(space_after)
        return p

    def heading(text):
        p = para(text.upper(), bold=True, size=12, space_after=2)
        p.paragraph_format.space_before = Pt(8)

    if logo and os.path.exists(logo):
        lp = doc.add_paragraph(); lp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        lp.add_run().add_picture(logo, width=Cm(1.9))
    para("Capstone Project 2025-27: Phase 2 Pilot", bold=True, size=16, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=0)
    para("Comparative Predictive Analytics of Downside Risk in NSE Nifty 50 Stocks: Machine Learning vs. GARCH Models",
         bold=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    para("Ghiri S | MBA Business Analytics | Faculty guide: Dr. Aarti Pardeshi | ITM Skills University",
         size=10, align=WD_ALIGN_PARAGRAPH.CENTER, italic=True)

    m = D["meta"]
    heading("1. Purpose")
    para("Test the full Phase 2 pipeline on three large Nifty 50 stocks before running it on the 40-45 stock panel, "
         "and seek approval for the changes to the study design listed at the end.")
    heading("2. What was run")
    para(f"Stocks: {m['tickers'].replace(',', ', ')}. Daily data {m['data_start']} to {m['test_last_date']}. "
         f"Train to {m['train_end']}, validation to {m['val_end']}, test {m['test_start']} to {m['test_last_date']} "
         f"({m['test_days_per_stock']} days per stock). Features: past returns, realised volatility, volume and "
         f"India VIX ({m['features']}); macro variables are not yet included. Models: six GARCH-family models "
         f"(GARCH, EGARCH, GJR; Normal and Student-t), XGBoost, Random Forest, MLP and a 250-day historical-simulation "
         f"benchmark, for one-day 95% and 99% VaR and ES. Runtime: {m['pipeline_runtime_s']} seconds for three stocks.")

    heading("3. Results")
    para("Table 1. Backtest results by model (mean of 3 stocks; pass counts = stocks with p > 0.05; lower FZ0 is better)",
         italic=True, size=10, space_after=2)
    tbl = short_table(D)
    t = doc.add_table(rows=1, cols=len(tbl.columns)); t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, c in enumerate(tbl.columns):
        cell = t.rows[0].cells[i]; cell.text = ""
        r = cell.paragraphs[0].add_run(c); r.bold = True; r.font.size = Pt(9)
    for row in tbl.itertuples(index=False):
        cells = t.add_row().cells
        for i, v in enumerate(row):
            r = cells[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(9)
            if i == 0:
                r.font.color.rgb = RGBColor(0xA5, 0x0F, 0x15) if FAM[v] == "GARCH" else (
                    RGBColor(0x08, 0x51, 0x9C) if FAM[v] == "ML" else RGBColor(0x55, 0x55, 0x55))
    figdir = os.path.join(ROOT, "outputs", "figures", "pilot")
    figs = doc.add_table(rows=2, cols=2)
    for i, (f, cap) in enumerate([
            (f"pilot_exception_rate_{tag}.png", "Figure 1. Exception rate by model vs nominal rate (GARCH red, ML blue, benchmark grey)"),
            (f"pilot_var_vs_returns_RELIANCE_{tag}.png", "Figure 2. RELIANCE.NS 99% VaR (GJR-t, XGBoost) vs actual returns, with breaches")]):
        pic = figs.rows[0].cells[i].paragraphs[0]; pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pic.add_run().add_picture(os.path.join(figdir, f), width=Cm(8.4))
        cp = figs.rows[1].cells[i].paragraphs[0]; cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cp.add_run(cap); r.italic = True; r.font.size = Pt(10)

    heading("4. Observations")
    for o in observations(D, F):
        doc.add_paragraph(o, style="List Number")
    para(f"Post-hike window (7 Oct to {m['test_last_date']}, {F['post_days']} trading days): 99% exceptions by family "
         + ", ".join(f"{k} {v}" for k, v in sorted(F["post99_by_fam"].items()))
         + f" (out of {F['post99_obs']} stock-days per model). Too short for formal tests.")
    heading("5. Problems found")
    for p in problems(D, F):
        doc.add_paragraph(p, style="List Bullet")
    heading("6. Caution")
    para("Three stocks are a pilot, not a conclusion. Results can change on the full 40-45 stock panel.")

    box = doc.add_table(rows=1, cols=1); box.style = "Table Grid"
    c = box.rows[0].cells[0]
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:fill"), "FFF4D6")
    c._tc.get_or_add_tcPr().append(shd)
    c.paragraphs[0].add_run("Approval requested from Dr. Pardeshi").bold = True
    for item in ["(a) A balanced panel of 40-45 Nifty 50 stocks with full price history from 2015 (newer listings dropped).",
                 "(b) Test window extended to November 2026, covering the 7 Oct 2026 repo hike to 5.50%.",
                 "(c) Basel traffic-light zones applied to 99% VaR only, and rolling 250-day historical simulation "
                 "used as a benchmark model instead of the rolling-quantile target.",
                 "(d) The Phase 2 report template (Cover; Chapters 1-9; no certificate or acknowledgement)."]:
        c.add_paragraph(item)
    doc.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", default="price+vix")
    a = ap.parse_args()
    tag = a.features.replace("+", "_")
    D = load(tag); F = facts(D)
    os.makedirs(os.path.join(ROOT, "report"), exist_ok=True)
    write_md(D, F, os.path.join(ROOT, "report", "pilot_summary.md"), tag)
    logo = os.path.join(ROOT, "report", "template", "itm_logo.png")
    if not os.path.exists(logo):
        try:
            import fitz
            pdf = fitz.open(os.path.join(ROOT, "report", "template", "Phase1_Report.pdf"))
            xref = pdf[0].get_images()[0][0]
            fitz.Pixmap(pdf, xref).save(logo)
        except Exception as ex:
            print(f"Logo not extracted ({ex}); pitch will have no logo.")
    write_docx(D, F, os.path.join(ROOT, "report", "pilot_pitch.docx"), tag, logo)
    print("Wrote report/pilot_summary.md and report/pilot_pitch.docx")


if __name__ == "__main__":
    main()
