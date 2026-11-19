"""P5: report and dashboard figures, generated from outputs only.

Each fig_* function returns a Plotly figure (reused by src/export_dashboard_json.py). Running this file
writes PNG (300 DPI equivalent) + interactive HTML to outputs/figures/ and factual captions to
outputs/figures/captions.md. All plotted data are derived (returns, VaR/ES, test results, cumulative
returns, VIX percentile); no raw OHLCV price levels are plotted.

Colours: GARCH = red palette, ML = blue palette, benchmark = grey, warnings/markers = amber.
ML results use the price/volume feature set unless a figure says otherwise. Regenerate after any rerun:
  python src/make_figures.py
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from yahoo import file_name  # noqa: E402

T = os.path.join(ROOT, "outputs", "tables")
FIG = os.path.join(ROOT, "outputs", "figures")
LABEL = "price"
GARCH = ["GARCH-normal", "GARCH-t", "EGARCH-normal", "EGARCH-t", "GJR-normal", "GJR-t"]
ML = ["XGBoost", "RandomForest", "MLP"]
ORDER = GARCH + ["HistSim250"] + ML
COL = {"GARCH-normal": "#fcae91", "GARCH-t": "#fb6a4a", "EGARCH-normal": "#ef3b2c", "EGARCH-t": "#cb181d",
       "GJR-normal": "#a50f15", "GJR-t": "#67000d", "HistSim250": "#7f7f7f",
       "XGBoost": "#08519c", "RandomForest": "#3182bd", "MLP": "#6baed6"}
AMBER = "#d18f00"
HIKE = "2026-10-07"
FONT = dict(family="Times New Roman, serif", size=14)
NOTE = "ML models: price/volume features. Test window 2024-01-01 to 2026-11-17, 41 stocks."


def style(fig, title, h=560, w=1100, subtitle=None):
    text = title + (f"<br><sup>{subtitle}</sup>" if subtitle else "")
    fig.update_layout(title=dict(text=text, x=0.01), font=FONT, template="simple_white", height=h, width=w,
                      margin=dict(t=95 if subtitle else 80, l=70, r=30, b=150),
                      legend=dict(orientation="h", y=-0.32, yanchor="top"))
    return fig


def rd(name):
    return pd.read_csv(os.path.join(T, name))


def daily(label=LABEL):
    files = glob.glob(os.path.join(T, "by_ticker", label, "*__daily.parquet"))
    d = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    d["date"] = pd.to_datetime(d["date"])
    return d


def frozen_close(sym):
    return pd.read_parquet(os.path.join(ROOT, "data", "frozen", file_name(sym)))["Close"]


# ------------------------------------------------------------------ figures
def fig_market_context():
    n = frozen_close("^NSEI")
    v = frozen_close("^INDIAVIX")
    cum = 100 * (np.log(n) - np.log(n.iloc[0]))
    pct_rank = 100 * v.rank(pct=True)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_scatter(x=cum.index, y=cum, name="Nifty 50 cumulative log return (%)", line=dict(color="#333333", width=1.4))
    fig.add_scatter(x=pct_rank.index, y=pct_rank, name="India VIX percentile (0-100, 2015-2026)",
                    line=dict(color=AMBER, width=0.8), opacity=0.7, secondary_y=True)
    fig.add_vrect(x0="2024-01-01", x1=str(n.index.max().date()), fillcolor="#bdbdbd", opacity=0.15, line_width=0,
                  annotation_text="Test window", annotation_position="top left")
    fig.add_vline(x=pd.Timestamp(HIKE).timestamp() * 1000, line_dash="dash", line_color=AMBER, line_width=2,
                  annotation_text="RBI repo hike to 5.50% (7 Oct 2026)", annotation_position="bottom left")
    fig.update_yaxes(title_text="Cumulative log return since 1 Jan 2015 (%)", secondary_y=False)
    fig.update_yaxes(title_text="India VIX percentile", range=[0, 100], secondary_y=True)
    fig.update_xaxes(title_text="Date")
    return style(fig, "Nifty 50 cumulative return and India VIX percentile, 2015-2026")


def fig_return_distributions():
    d = daily()
    d = d[(d.model == "GJR-t") & (d.alpha == 0.01)]
    stocks = sorted(d.ticker.unique())
    cols = 7
    rows = int(np.ceil(len(stocks) / cols))
    fig = make_subplots(rows=rows, cols=cols, subplot_titles=[s.replace(".NS", "") for s in stocks],
                        shared_xaxes=True, vertical_spacing=0.04, horizontal_spacing=0.02)
    bins = np.linspace(-0.08, 0.08, 33)
    centers = 100 * (bins[:-1] + bins[1:]) / 2
    for i, s in enumerate(stocks):
        r = d.loc[d.ticker == s, "ret"].clip(-0.08, 0.08)
        cnt, _ = np.histogram(r, bins=bins)
        fig.add_bar(x=centers, y=cnt, marker_color="#636363", showlegend=False, row=i // cols + 1, col=i % cols + 1)
    fig.update_annotations(font_size=10)
    fig.update_yaxes(showticklabels=False)
    fig.update_xaxes(tickvals=[-5, 0, 5], tickfont=dict(size=10))
    return style(fig, "Distribution of daily log returns by stock, test window (%; tails clipped at +/-8%)", h=900)


def fig_var_vs_returns(ticker="RELIANCE.NS", models=("GJR-t", "XGBoost"), alpha=0.01, d=None):
    d = daily() if d is None else d
    d = d[(d.ticker == ticker) & (d.alpha == alpha)]
    base = d[d.model == models[0]].sort_values("date")
    fig = go.Figure()
    fig.add_scatter(x=base.date, y=100 * base.ret, mode="lines", name="Actual daily return", line=dict(color="#4d4d4d", width=1))
    for m in models:
        s = d[d.model == m].sort_values("date")
        fig.add_scatter(x=s.date, y=-100 * s["var"], mode="lines", name=f"{m} {int((1 - alpha) * 100)}% VaR (as return)",
                        line=dict(color=COL[m], width=1.8))
    marks = {"XGBoost": dict(symbol="x-thin-open", size=13, color=COL["XGBoost"], line=dict(width=2.5, color=COL["XGBoost"])),
             "GJR-t": dict(symbol="triangle-down", size=11, color=COL["GJR-t"], line=dict(width=1, color="white"))}
    for m in sorted(models, key=lambda x: x in GARCH):  # GARCH markers drawn last (on top)
        b = d[(d.model == m) & (d.exception == 1)]
        fig.add_scatter(x=b.date, y=100 * b.ret, mode="markers", name=f"{m} breach ({len(b)})",
                        marker=marks.get(m, dict(size=9, color=COL[m])))
    fig.add_vline(x=pd.Timestamp(HIKE).timestamp() * 1000, line_dash="dash", line_color=AMBER, line_width=2)
    fig.update_xaxes(title_text="Date"); fig.update_yaxes(title_text="Daily log return (%)")
    return style(fig, f"{ticker}: {int((1 - alpha) * 100)}% VaR forecast against actual returns, with breaches")


def fig_exception_heatmap():
    b = rd(f"backtest_results_{LABEL}.csv")
    b = b[b.alpha == 0.01]
    p = b.pivot(index="ticker", columns="model", values="exc_rate")[ORDER] * 100
    p.index = [i.replace(".NS", "") for i in p.index]
    fig = go.Figure(go.Heatmap(z=p.values, x=p.columns, y=p.index, colorscale="PuOr_r", zmid=1.0,
                               colorbar=dict(title="Breach rate (%)"),
                               hovertemplate="%{y} | %{x}: %{z:.2f}%<extra></extra>"))
    fig.update_xaxes(title_text="Model", tickangle=-35); fig.update_yaxes(title_text="Stock", autorange="reversed")
    return style(fig, "99% VaR breach rate by stock and model (nominal 1%; orange above, purple below)", h=1000, w=900)


def fig_vix_quartiles():
    r = rd(f"regime_results_{LABEL}.csv")
    g = r.groupby(["model", "regime"])["mean_fz0"].agg(["mean", "std", "count"]).reset_index()
    g["se"] = g["std"] / np.sqrt(g["count"])
    fig = go.Figure()
    for m in ORDER:
        s = g[g.model == m].set_index("regime").reindex(["Q1 calm", "Q2", "Q3", "Q4 stressed"])
        fig.add_bar(x=s.index, y=s["mean"], name=m, marker_color=COL[m], error_y=dict(type="data", array=s["se"]))
    fig.update_layout(barmode="group")
    fig.update_xaxes(title_text="Previous-day India VIX quartile (test window)")
    fig.update_yaxes(title_text="Mean FZ0 loss, 95% VaR/ES (lower is better)")
    return style(fig, "Joint VaR-ES loss by India VIX quartile (mean across stocks; bars = +/-1 standard error)")


def fig_shap():
    s = rd("xgb_shap_importance_price_vixlevel_summary.csv").sort_values("mean")
    fig = go.Figure(go.Bar(x=1e4 * s["mean"], y=s["feature"], orientation="h", marker_color=COL["XGBoost"],
                           error_x=dict(type="data", array=1e4 * s["std"] / np.sqrt(s["count"]))))
    fig.update_xaxes(title_text="Mean |SHAP| contribution to the 1% quantile forecast (basis points of return)")
    fig.update_yaxes(title_text="Feature")
    return style(fig, "XGBoost 99% VaR: feature importance (price/volume + India VIX level set; mean over 41 stocks)", h=640)


def fig_kupiec_christoffersen():
    b = rd(f"backtest_results_{LABEL}.csv")
    b = b[b.alpha == 0.01]
    fig = go.Figure()
    for m in ORDER:
        s = b[b.model == m]
        fig.add_scatter(x=s.kupiec_p, y=s.ind_p, mode="markers", name=m, text=s.ticker,
                        marker=dict(color=COL[m], size=7, opacity=0.75),
                        hovertemplate="%{text}<br>Kupiec p=%{x:.3f}<br>Independence p=%{y:.3f}<extra>" + m + "</extra>")
    for ax in ("x", "y"):
        fig.add_shape(type="line", **({"x0": 0.05, "x1": 0.05, "y0": 0, "y1": 1} if ax == "x" else {"x0": 0, "x1": 1, "y0": 0.05, "y1": 0.05}),
                      line=dict(color=AMBER, dash="dash"))
    fig.update_xaxes(title_text="Kupiec unconditional coverage p-value", range=[0, 1])
    fig.update_yaxes(title_text="Christoffersen independence p-value", range=[0, 1])
    return style(fig, "99% VaR backtests per stock: Kupiec against Christoffersen (dashed line = 5% significance)", h=650, w=900)


def fig_es_calibration():
    b = rd(f"backtest_results_{LABEL}.csv")
    fig = make_subplots(rows=1, cols=2, subplot_titles=("95% ES", "99% ES"), shared_yaxes=True)
    for c, a in enumerate((0.05, 0.01), 1):
        for m in ORDER:
            s = b[(b.model == m) & (b.alpha == a)]
            fig.add_box(y=s.actual_over_expected_es, name=m, marker_color=COL[m], showlegend=False, row=1, col=c)
        fig.add_hline(y=1, line_dash="dash", line_color=AMBER, row=1, col=c)
    fig.update_yaxes(title_text="Actual / forecast ES on breach days", row=1, col=1)
    fig.update_xaxes(tickangle=-40)
    return style(fig, "Expected Shortfall calibration: realised tail loss over forecast ES (1 = exact; above 1 = ES too low)")


def fig_sector_var():
    d = daily()
    d = d[(d.model == "GJR-t") & (d.alpha == 0.01)]
    sec = pd.read_csv(os.path.join(ROOT, "config", "universe.csv")).set_index("ticker")["sector"]
    s = d.groupby("ticker")["var"].mean().mul(100).rename("var").to_frame().join(sec)
    order = s.groupby("sector")["var"].median().sort_values().index
    fig = go.Figure()
    for sc in order:
        g = s[s.sector == sc]
        fig.add_box(y=g["var"], name=sc, boxpoints="all", jitter=0.3, marker_color=COL["GJR-t"], line_color=COL["GJR-t"],
                    text=[i.replace(".NS", "") for i in g.index], showlegend=False)
    fig.update_yaxes(title_text="Average one-day 99% VaR, GJR-GARCH-t (% of position)")
    fig.update_xaxes(tickangle=-30)
    return style(fig, "Average 99% VaR by sector (each point is one stock, test window)", h=620)


def fig_leaderboard():
    s = rd(f"summary_{LABEL}.csv").set_index(["model", "alpha"])
    rows = []
    for m in ORDER:
        r5, r1 = s.loc[(m, 0.05)], s.loc[(m, 0.01)]
        rows.append([m, abs(r1.exc_rate - 0.01) * 100, r1.exc_rate * 100, r5.exc_rate * 100, r1.pass_kupiec * 100,
                     r1.pass_cc * 100, r1.green99 * 100, r5.fz0, r5.fz0_median_stocks, r1.es_ratio])
    t = pd.DataFrame(rows, columns=["Model", "Distance from 1% (pp)", "Breach 99% (%)", "Breach 95% (%)",
                                    "Kupiec pass 99% (%)", "CC pass 99% (%)", "Basel Green (%)",
                                    "Mean FZ0 95%", "Median FZ0 95%", "ES ratio 99%"]).sort_values("Distance from 1% (pp)")
    fmt = ["", ".2f", ".2f", ".2f", ".0f", ".0f", ".0f", ".4f", ".4f", ".3f"]
    cells = [t[c] if f == "" else [format(v, f) for v in t[c]] for c, f in zip(t.columns, fmt)]
    fig = go.Figure(go.Table(header=dict(values=list(t.columns), fill_color="#f0f0f0", font=dict(size=12)),
                             cells=dict(values=cells, font=dict(size=12),
                                        fill_color=[[("#fee0d2" if m in GARCH else "#deebf7" if m in ML else "#f0f0f0")
                                                     for m in t.Model]])))
    return style(fig, "Models ordered by closeness of the 99% breach rate to nominal (not a ranking of overall quality)", h=520)


def fig_fz0_mean_median():
    s = rd(f"summary_{LABEL}.csv").set_index(["model", "alpha"])
    fig = make_subplots(rows=1, cols=2, subplot_titles=("95% VaR/ES", "99% VaR/ES"))
    for c, a in enumerate((0.05, 0.01), 1):
        med = np.array([s.loc[(m, a), "fz0_median_stocks"] for m in ORDER])
        mean = np.array([s.loc[(m, a), "fz0"] for m in ORDER])
        lo, hi = min(med.min(), np.sort(mean)[0]) - 0.03, med.max() + 0.08  # zoom on the bulk of the values
        off = mean > hi
        fig.add_scatter(x=ORDER, y=np.where(off, np.nan, mean), mode="markers", name="Mean across stocks",
                        marker=dict(symbol="circle-open", size=13, color=[COL[m] for m in ORDER], line=dict(width=2)),
                        showlegend=c == 1, row=1, col=c)
        fig.add_scatter(x=ORDER, y=med, mode="markers", name="Median across stocks",
                        marker=dict(symbol="circle", size=10, color=[COL[m] for m in ORDER]), showlegend=c == 1, row=1, col=c)
        for m, v in zip(np.array(ORDER)[off], mean[off]):
            fig.add_annotation(x=m, y=hi, text=f"mean {v:.2f}<br>(off scale)", showarrow=True, arrowhead=2, ay=-30,
                               font=dict(color=AMBER, size=11), row=1, col=c)
        fig.update_yaxes(range=[lo, hi + 0.05], row=1, col=c)
    n99 = int(s.loc[("XGBoost", 0.01), "norisk_days"]); n95 = int(s.loc[("XGBoost", 0.05), "norisk_days"])
    fig.update_yaxes(title_text="FZ0 loss (lower is better)", row=1, col=1)
    fig.update_xaxes(tickangle=-40)
    return style(fig, "Joint VaR-ES loss (FZ0): mean (open) versus median (filled) across stocks",
                 subtitle=f"XGBoost 'no-risk' days (forecast quantile at or above zero): {n95} at 95%, {n99} at 99%, all stocks; "
                          "one such day can dominate the mean")


def dm_counts(dm):
    d = dm.copy()
    flip = d.model_a.isin(GARCH) & d.model_b.isin(ML)
    d.loc[flip, ["model_a", "model_b"]] = d.loc[flip, ["model_b", "model_a"]].values
    d.loc[flip, "dm_stat"] = -d.loc[flip, "dm_stat"]
    d = d[d.model_a.isin(ML) & d.model_b.isin(GARCH)]
    return pd.DataFrame([dict(model=m, garch=int(((g.p < 0.05) & (g.dm_stat > 0)).sum()),
                              ml=int(((g.p < 0.05) & (g.dm_stat < 0)).sum()), none=int((g.p >= 0.05).sum()))
                         for m, g in d.groupby("model_a")]).set_index("model").reindex(ML)


def fig_dm_summary():
    c = dm_counts(rd(f"diebold_mariano_{LABEL}.csv"))
    tot = c.sum()
    fig = go.Figure()
    fig.add_bar(y=c.index, x=c.garch, name="GARCH significantly lower loss", orientation="h", marker_color=COL["GJR-t"])
    fig.add_bar(y=c.index, x=c.ml, name="ML significantly lower loss", orientation="h", marker_color=COL["XGBoost"])
    fig.add_bar(y=c.index, x=c.none, name="No significant difference", orientation="h", marker_color="#d9d9d9")
    fig.update_layout(barmode="stack")
    fig.update_xaxes(title_text="Number of (GARCH model x stock) pairs, Diebold-Mariano test at 5%, FZ0 95%")
    return style(fig, f"GARCH significantly better in {int(tot.garch)} pairs, ML in {int(tot.ml)}, "
                      f"no difference in {int(tot.none)}", h=420)


def fig_breaches_by_day(models=("GJR-t", "XGBoost")):
    b = rd(f"breach_days_{LABEL}.csv")
    b["date"] = pd.to_datetime(b["date"])
    b = b[b.alpha == 0.01]
    fig = make_subplots(rows=len(models), cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        subplot_titles=[f"{m}: number of stocks breaching 99% VaR" for m in models])
    st = b[(b.model == models[0]) & b.stress_day]
    for i, m in enumerate(models, 1):
        s = b[b.model == m].sort_values("date")
        fig.add_bar(x=s.date, y=s.breaches, name=m, marker_color=COL[m], marker_line_width=0, row=i, col=1)
        fig.add_scatter(x=st.date, y=[-1.5] * len(st), mode="markers", name="Market-stress day (Nifty <= -2%)",
                        marker=dict(symbol="triangle-up", size=9, color=AMBER), showlegend=i == 1, row=i, col=1)
        fig.update_yaxes(title_text="Stocks (of 41)", range=[-3, 24], row=i, col=1)
    fig.update_xaxes(title_text="Date", row=len(models), col=1)
    return style(fig, "Breaches by day across the 41 stocks (99% VaR)", h=650)


def fig_stress_share():
    s = rd(f"breach_days_summary_{LABEL}.csv")
    s = s[s.alpha == 0.01].set_index("model").reindex(ORDER)
    base = 100 * s.share_of_days_stress.iloc[0]
    fig = go.Figure(go.Bar(x=ORDER, y=100 * s.share_of_breaches_on_stress_days, marker_color=[COL[m] for m in ORDER],
                           text=[f"{v:.1f}%" for v in 100 * s.share_of_breaches_on_stress_days], textposition="outside"))
    fig.add_hline(y=base, line_dash="dash", line_color=AMBER, annotation_text=f"Share of test days that are stress days: {base:.1f}%",
                  annotation_position="top left")
    fig.update_yaxes(title_text="Share of 99% breaches on stress days (%)"); fig.update_xaxes(tickangle=-35)
    return style(fig, "Breaches concentrate on market-wide stress days (Nifty one-day fall of 2% or more)")


FIGURES = {
    "fig01_market_context": fig_market_context, "fig02_return_distributions": fig_return_distributions,
    "fig03_var_vs_returns_RELIANCE": fig_var_vs_returns, "fig04_exception_heatmap_99": fig_exception_heatmap,
    "fig05_vix_quartiles_fz0": fig_vix_quartiles, "fig06_xgb_shap_importance": fig_shap,
    "fig07_kupiec_vs_christoffersen": fig_kupiec_christoffersen, "fig08_es_calibration": fig_es_calibration,
    "fig09_sector_var": fig_sector_var, "fig10_leaderboard": fig_leaderboard,
    "fig11_fz0_mean_median": fig_fz0_mean_median, "fig12_dm_summary": fig_dm_summary,
    "fig13_breaches_by_day": fig_breaches_by_day, "fig14_stress_share": fig_stress_share,
}


def captions():
    s = rd(f"summary_{LABEL}.csv").set_index(["model", "alpha"])
    b = rd(f"backtest_results_{LABEL}.csv")
    c = dm_counts(rd(f"diebold_mariano_{LABEL}.csv")).sum()
    bd = rd(f"breach_days_summary_{LABEL}.csv").set_index(["model", "alpha"])
    sh = rd("xgb_shap_importance_price_vixlevel_summary.csv")
    closest = sorted(ORDER, key=lambda m: abs(s.loc[(m, 0.01), "exc_rate"] - 0.01))[:3]
    rel = daily()
    rel = rel[(rel.ticker == "RELIANCE.NS") & (rel.alpha == 0.01)]
    p = lambda v: f"{100 * v:.2f}%"
    return {
        "fig01_market_context": "Nifty 50 cumulative log return since 1 January 2015 and the percentile of the India VIX within 2015-2026. "
                                "The shaded area is the test window; the dashed line marks the RBI repo hike of 7 October 2026.",
        "fig02_return_distributions": f"Histograms of daily log returns for each of the {b.ticker.nunique()} stocks over the test window "
                                      "(bins of 0.5 percentage points; returns beyond +/-8% are placed in the end bins).",
        "fig03_var_vs_returns_RELIANCE": f"RELIANCE.NS daily returns with the 99% VaR of GJR-GARCH-t and XGBoost (price/volume features). "
                                         f"Breaches: GJR-t {int(rel[rel.model == 'GJR-t'].exception.sum())}, XGBoost {int(rel[rel.model == 'XGBoost'].exception.sum())} "
                                         f"of {rel[rel.model == 'GJR-t'].shape[0]} days.",
        "fig04_exception_heatmap_99": "99% VaR breach rate for each stock and model; the colour scale is centred on the nominal 1%.",
        "fig05_vix_quartiles_fz0": "Mean FZ0 loss (95% VaR and ES) in each quartile of the previous day's India VIX, averaged across stocks; "
                                   "error bars are one standard error across stocks. Lower is better.",
        "fig06_xgb_shap_importance": f"Mean absolute SHAP contribution of each feature to XGBoost's 1% quantile forecast (feature set "
                                     f"price/volume + India VIX level), averaged over 41 stocks; the largest is {sh.iloc[0].feature}.",
        "fig07_kupiec_vs_christoffersen": "Kupiec (unconditional coverage) and Christoffersen (independence) p-values for 99% VaR, one point per "
                                          "stock and model; points left of or below the dashed lines fail the test at 5%.",
        "fig08_es_calibration": "Ratio of the realised average loss on breach days to the average forecast ES on those days, per stock; "
                                "1 means the ES forecast matched realised tail losses.",
        "fig09_sector_var": "Average one-day 99% VaR from GJR-GARCH-t over the test window for each stock, grouped by sector.",
        "fig10_leaderboard": f"Models ordered by the distance of the 99% breach rate from 1%. Closest to nominal: "
                             + ", ".join(f"{m} ({p(s.loc[(m, 0.01), 'exc_rate'])})" for m in closest)
                             + ". The ordering is by breach rate only; it is not a ranking of overall forecast quality.",
        "fig11_fz0_mean_median": f"Mean and median FZ0 across stocks. XGBoost had {int(s.loc[('XGBoost', 0.05), 'norisk_days'])} no-risk days "
                                 f"at 95% and {int(s.loc[('XGBoost', 0.01), 'norisk_days'])} at 99% (forecast quantile at or above zero); "
                                 f"its mean 99% FZ0 is {s.loc[('XGBoost', 0.01), 'fz0']:.4f} against a median of "
                                 f"{s.loc[('XGBoost', 0.01), 'fz0_median_stocks']:.4f}.",
        "fig12_dm_summary": f"Diebold-Mariano tests on FZ0 (95%) between each ML model and each of the six GARCH models for every stock: "
                            f"GARCH significantly better in {int(c.garch)} pairs, ML in {int(c.ml)}, no difference in {int(c['none'])}.",
        "fig13_breaches_by_day": "Number of stocks whose return breached the 99% VaR on each day, for GJR-GARCH-t and XGBoost; triangles mark "
                                 "days on which the Nifty 50 fell 2% or more.",
        "fig14_stress_share": f"Share of all 99% breaches that occurred on market-stress days; stress days are "
                              f"{100 * bd.share_of_days_stress.iloc[0]:.1f}% of test days. GJR-t: "
                              f"{100 * bd.loc[('GJR-t', 0.01), 'share_of_breaches_on_stress_days']:.1f}%, XGBoost: "
                              f"{100 * bd.loc[('XGBoost', 0.01), 'share_of_breaches_on_stress_days']:.1f}%.",
    }


def main():
    os.makedirs(FIG, exist_ok=True)
    caps = captions()
    lines = ["# Figure captions (generated from outputs by src/make_figures.py)", "", NOTE, ""]
    for i, (name, fn) in enumerate(FIGURES.items(), 1):
        fig = fn()
        fig.write_html(os.path.join(FIG, f"{name}.html"), include_plotlyjs="cdn")
        fig.write_image(os.path.join(FIG, f"{name}.png"), scale=300 / 96)
        lines += [f"**{name}.** {caps[name]}", ""]
        print("wrote", name)
    open(os.path.join(FIG, "captions.md"), "w", encoding="utf-8").write("\n".join(lines))


if __name__ == "__main__":
    main()
