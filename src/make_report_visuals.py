"""Extra visuals for the Phase 2 report (diagrams and data charts), drawn at true print size.

Every chart reads its data from outputs/ (via src/report_numbers.py or the CSVs directly); diagrams contain no
result numbers except where a number is read from outputs. Width 15.5 cm, Times New Roman, text 10 pt or larger,
300 DPI, GARCH = red, ML = blue, benchmark = grey, warnings = amber.

  python src/make_report_visuals.py      ->  report/figures/*.png
"""
import os
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from report_numbers import GARCH, ML, ORDER, build, daily, rd  # noqa: E402

OUT = os.path.join(ROOT, "report", "figures")
W = 15.5 / 2.54  # inches
COL = {"GARCH-normal": "#fcae91", "GARCH-t": "#fb6a4a", "EGARCH-normal": "#ef3b2c", "EGARCH-t": "#cb181d",
       "GJR-normal": "#a50f15", "GJR-t": "#67000d", "HistSim250": "#7f7f7f",
       "XGBoost": "#08519c", "RandomForest": "#3182bd", "MLP": "#6baed6"}
RED, RED_L, BLUE, BLUE_L, GREY_L, AMBER, AMBER_L = "#a50f15", "#fee0d2", "#08519c", "#deebf7", "#f0f0f0", "#d18f00", "#fdf0d0"
plt.rcParams.update({"font.family": "Times New Roman", "font.size": 10.5, "axes.titlesize": 11, "axes.labelsize": 10.5,
                     "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.dpi": 400})


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, f"{name}.png"), bbox_inches="tight", pad_inches=0.05, facecolor="white")
    plt.close(fig)
    print("wrote", name)


def canvas(h_cm, xmax=100, ymax=None):
    fig = plt.figure(figsize=(W, h_cm / 2.54))
    ax = fig.add_axes([0, 0, 1, 1])
    ymax = ymax or xmax * h_cm / 15.5
    ax.set_xlim(0, xmax); ax.set_ylim(0, ymax); ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, fc="white", ec="#333333", fs=10, title=None, wrap=None, lw=1.0, align="center"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2", fc=fc, ec=ec, lw=lw))
    body = "\n".join(textwrap.fill(t, wrap) if wrap else t for t in text.split("\n")) if text else ""
    if title:
        ax.text(x + w / 2, y + h - 1.2, title, ha="center", va="top", fontsize=fs + 0.5, weight="bold")
        ax.text(x + (w / 2 if align == "center" else 1.5), y + h - 1.2 - 2.9, body, ha=align, va="top", fontsize=fs, linespacing=1.25)
    else:
        ax.text(x + w / 2, y + h / 2, body, ha="center", va="center", fontsize=fs, linespacing=1.25)


def arrow(ax, x0, y0, x1, y1, color="#333333", text=None, lw=1.3, style="-|>"):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle=style, color=color, lw=lw, shrinkA=0, shrinkB=0))
    if text:
        ax.text((x0 + x1) / 2 + 0.8, (y0 + y1) / 2, text, fontsize=10, color=color, va="center")


# ------------------------------------------------------------------ Chapter 1
def market_structure():
    fig, ax = canvas(13.5)
    H = 100 * 13.5 / 15.5
    box(ax, 2, H - 16, 45, 13, "Securities market regulator. Sets risk rules for exchanges, clearing corporations, brokers and funds.",
        fc=GREY_L, title="SEBI", wrap=42)
    box(ax, 53, H - 16, 45, 13, "Central bank. Sets the repo rate (raised to 5.50% on 7 October 2026) and supervises banks.",
        fc=GREY_L, title="RBI", wrap=42)
    box(ax, 2, H - 38, 45, 15, "Exchange. Runs trading; publishes the Nifty 50 index and the India VIX (expected volatility).",
        fc="white", title="NSE", wrap=42)
    box(ax, 53, H - 38, 45, 15, "Clearing corporation. Guarantees trades and collects margin from members every day.",
        fc="white", title="NSE Clearing", wrap=42)
    parts = ["Brokers and\ntrading members", "Mutual funds\nand FPIs", "Bank treasury\ndesks", "Retail investors\n(demat accounts)"]
    for i, p_ in enumerate(parts):
        box(ax, 2 + i * 24.3, H - 55, 21.5, 11, p_, fc="white", fs=10)
    ax.text(50, H - 41.5, "Market participants", ha="center", fontsize=10.5, weight="bold")
    uses = [("Margins", "Clearing corporations set initial margin from a VaR-type estimate of a one-day loss."),
            ("Limits", "Brokers and funds cap positions so the likely worst daily loss stays inside a budget."),
            ("Capital", "Banks hold market-risk capital; Basel rules use ES and backtest 99% VaR."),
            ("Investor view", "Apps and funds show risk to clients in simple terms.")]
    ax.text(50, H - 62.5, "How VaR and Expected Shortfall are used", ha="center", fontsize=10.5, weight="bold", color=RED)
    for i, (t, d) in enumerate(uses):
        box(ax, 2 + i * 24.3, 2, 21.5, H - 68, d, fc=RED_L, ec=RED, title=t, wrap=21, fs=10)
    for x in (24.5, 75.5):
        arrow(ax, x, H - 16.5, x, H - 22.5)
    arrow(ax, 47.5, H - 30, 52.5, H - 30, text=None)
    for i in range(4):
        arrow(ax, 12.75 + i * 24.3, H - 55.5, 12.75 + i * 24.3, H - 59.5, color=RED)
    save(fig, "v_market_structure")


def swot():
    fig, ax = canvas(10.5)
    H = 100 * 10.5 / 15.5
    q = [("Strengths", RED_L, RED, ["Deep, liquid large-cap market with daily index and India VIX data",
                                    "Established VaR-based margin and risk framework",
                                    "Free daily data allow transparent, repeatable models",
                                    "In this study, GARCH-t models stayed close to the 1% breach target"]),
         ("Weaknesses", GREY_L, "#555555", ["Free data are unofficial; some corporate actions are unadjusted",
                                           "Newer large firms have short histories",
                                           "ML risk models are harder to explain and need refitting",
                                           "Single-stock backtests have few breaches, so low power"]),
         ("Opportunities", BLUE_L, BLUE, ["Growing retail base needs simple daily risk signals",
                                         "Low-cost automated daily risk pipelines (as built here)",
                                         "Stress add-ons for market-wide fall days",
                                         "Use ML as a challenger model under strict backtests"]),
         ("Threats", AMBER_L, AMBER, ["Market-wide shock days when many stocks breach together",
                                     "Interest-rate regime change (repo hike, Oct 2026)",
                                     "Inputs drifting outside the range a model was fitted on",
                                     "Over-trusting a model that once forecast no risk"])]
    for i, (t, fc, ec, items) in enumerate(q):
        x = 2 + (i % 2) * 49; y = 2 + (1 - i // 2) * (H / 2 - 1)
        body = "\n".join("• " + textwrap.fill(s, 44, subsequent_indent="   ") for s in items)
        box(ax, x, y, 47, H / 2 - 3, body, fc=fc, ec=ec, title=t, fs=10, align="left", lw=1.4)
    save(fig, "v_swot")


# ------------------------------------------------------------------ Chapter 3
def method_flow():
    fig, ax = canvas(18.5)
    H = 100 * 18.5 / 15.5
    steps = [("1  Data acquisition", "Yahoo Finance daily prices: 41 stocks, Nifty 50, India VIX, USD/INR; frozen, hashed snapshot", GREY_L, "#555555"),
             ("2  Cleaning and validation", "Hash check, gaps, zero-volume rows dropped and logged, corporate-action review", GREY_L, "#555555"),
             ("3  Feature engineering", "Lagged returns, realised volatility, drawdown, volume, VIX, USD/INR; day t uses data up to t-1 only", GREY_L, "#555555"),
             ("4  GARCH modelling", "GARCH, EGARCH, GJR-GARCH × Normal, Student-t; refitted every 20 days", RED_L, RED),
             ("5  ML modelling and benchmark", "XGBoost quantile; Random Forest and MLP + filtered historical simulation; benchmark: 250-day historical simulation", BLUE_L, BLUE),
             ("6  Backtesting and evaluation", "Kupiec, Christoffersen, Basel zones (99%), FZ0 and pinball losses, Diebold-Mariano, VIX regimes", AMBER_L, AMBER),
             ("7  Visualisation and reporting", "Figures, dashboard on GitHub Pages, daily GitHub Action, this report", GREY_L, "#555555")]
    h, gap = 11.6, 3.4
    for i, (t, d, fc, ec) in enumerate(steps):
        y = H - 2 - (i + 1) * h - i * gap
        box(ax, 2, y, 74, h, d, fc=fc, ec=ec, title=t, wrap=70, fs=10)
        if i < len(steps) - 1:
            arrow(ax, 39, y - 0.4, 39, y - gap + 0.4)
    ymid = lambda i: H - 2 - (i + 1) * h - i * gap + h / 2
    ax.plot([76.8, 81, 81], [ymid(5), ymid(5), ymid(2)], color=AMBER, lw=1.3)
    arrow(ax, 81, ymid(2), 76.8, ymid(2), color=AMBER)
    ax.text(82.5, (ymid(5) + ymid(2)) / 2, "Feature sets\nchosen on the\nvalidation\nwindow only\n(2022-23)", fontsize=10, color="#8a5d00", ha="left", va="center")
    save(fig, "v_method_flow")


def timeline():
    fig, ax = plt.subplots(figsize=(W, 6.4 / 2.54))
    t = lambda s: pd.Timestamp(s)
    rows = [("Main study", [("Train", "2015-01-01", "2021-12-31", RED_L), ("Validation", "2022-01-01", "2023-12-31", AMBER_L),
                            ("Test", "2024-01-01", "2026-11-17", BLUE_L)]),
            ("Feature choice", [("Train", "2015-01-01", "2019-12-31", RED_L), ("Calibrate", "2020-01-01", "2021-12-31", GREY_L),
                                ("Evaluate", "2022-01-01", "2023-12-31", AMBER_L)])]
    for i, (name, segs) in enumerate(rows):
        y = 1 - i
        for lab, a, b, c in segs:
            ax.barh(y, (t(b) - t(a)).days, left=t(a), height=0.55, color=c, edgecolor="#333333", lw=0.8)
            ax.text(t(a) + (t(b) - t(a)) / 2, y, lab, ha="center", va="center", fontsize=10)
    ax.axvline(t("2026-10-07"), color=AMBER, ls="--", lw=1.6)
    ax.text(t("2026-10-07"), 1.55, "RBI repo hike\nto 5.50%,\n7 Oct 2026", ha="right", va="bottom", fontsize=10, color="#8a5d00")
    ax.set_yticks([1, 0]); ax.set_yticklabels([r[0] for r in rows])
    ax.set_ylim(-0.6, 2.25)
    ax.xaxis_date()
    ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
    fig.tight_layout()
    save(fig, "v_timeline")


def techniques():
    rows = [("GARCH, EGARCH, GJR-GARCH\n(Normal and Student-t)", "Standard volatility models; EGARCH/GJR add the leverage effect, t adds fat tails", "Do classic models give well-calibrated VaR and ES?", RED_L),
            ("XGBoost quantile regression", "Learns the tail quantile directly from many inputs; non-linear", "Can ML forecast the loss quantile better?", BLUE_L),
            ("Random Forest and MLP +\nfiltered historical simulation", "Learn volatility from inputs; residual quantiles give VaR and ES", "Does flexible volatility modelling help?", BLUE_L),
            ("250-day historical simulation", "Simple industry benchmark with no model", "Baseline any model must beat", GREY_L),
            ("Kupiec and Christoffersen tests", "Standard VaR backtests: frequency and clustering of breaches", "Do forecasts fail too often, or in bunches?", AMBER_L),
            ("Basel traffic light (99% only)", "The regulator's backtest zones for 99% VaR", "Would a bank model stay in the green zone?", AMBER_L),
            ("FZ0 and pinball losses", "Proper scoring rules for VaR and ES together", "Which forecasts are best overall?", AMBER_L),
            ("Diebold-Mariano test", "Tests whether a loss difference is larger than chance", "Is a model's advantage real?", AMBER_L),
            ("India VIX quartiles, stress days", "Splits results by market mood and by market-wide falls", "When do models fail?", AMBER_L),
            ("SHAP values", "Shows which inputs drive the ML forecast", "Can ML forecasts be explained?", BLUE_L)]
    fig, ax = canvas(20)
    H = 100 * 20 / 15.5
    xs, ws = [1, 31, 67], [29, 35, 32]
    for x, w, hd in zip(xs, ws, ["Technique", "Why it was chosen", "What it answers"]):
        ax.add_patch(FancyBboxPatch((x, H - 7), w, 5.5, boxstyle="square,pad=0", fc="#333333", ec="white"))
        ax.text(x + w / 2, H - 4.25, hd, color="white", ha="center", va="center", fontsize=10.5, weight="bold")
    rh = (H - 9) / len(rows)
    for i, (a, b, c, fc) in enumerate(rows):
        y = H - 7.5 - (i + 1) * rh
        for x, w, txt, f_ in zip(xs, ws, [a, b, c], [fc, "white", "white"]):
            ax.add_patch(FancyBboxPatch((x, y), w, rh - 0.5, boxstyle="square,pad=0", fc=f_, ec="#bbbbbb", lw=0.6))
            wrapped = "\n".join(textwrap.fill(s, int(w * 0.85)) for s in txt.split("\n"))
            ax.text(x + 1, y + (rh - 0.5) / 2, wrapped, ha="left", va="center", fontsize=10, linespacing=1.15)
    save(fig, "v_techniques")


# ------------------------------------------------------------------ Chapter 4
def pipeline(N):
    fig, ax = canvas(10.6)
    H = 100 * 10.6 / 15.5
    box(ax, 1, H - 22, 28, 20, "Yahoo Finance: 41 stocks, Nifty 50, India VIX, USD/INR\nNSE: index constituents\nRBI / MoSPI: repo, CPI, IIP (pending)",
        fc=GREY_L, title="Sources", wrap=24)
    box(ax, 36, H - 22, 28, 20, "Hashes, gaps, zero-volume rows, corporate-action rule; failures logged", fc="white", title="Validation", wrap=27)
    box(ax, 71, H - 22, 28, 20, f"Read-only parquet files with SHA-256 hashes ({N['snapshot'][0]}); source of all report numbers", fc=RED_L, ec=RED,
        title="Frozen snapshot", wrap=27)
    arrow(ax, 29.6, H - 12, 35.4, H - 12); arrow(ax, 64.6, H - 12, 70.4, H - 12)
    box(ax, 71, H - 47, 28, 18, "nifty50_var_pipeline.py: 10 models, backtests, tables and figures", fc=RED_L, ec=RED, title="Research run", wrap=27)
    arrow(ax, 85, H - 22.6, 85, H - 28.4)
    box(ax, 36, H - 47, 28, 18, "Weekdays 13:30 UTC (7:00 PM IST): new prices, checks, GJR-t next-day VaR and ES", fc=BLUE_L, ec=BLUE,
        title="GitHub Action", wrap=24)
    box(ax, 1, H - 47, 28, 18, "data/live, outputs/live (derived values only, no raw prices published)", fc=BLUE_L, ec=BLUE, title="Live files", wrap=27)
    arrow(ax, 35.4, H - 38, 29.6, H - 38, color=BLUE)
    arrow(ax, 15, H - 22.6, 15, H - 28.4, color=BLUE)
    ax.text(16, H - 25.5, "daily refresh", fontsize=10, color=BLUE, va="center")
    box(ax, 18, H - 66, 64, 12, "Static React site on GitHub Pages: plain-language findings, charts, stock drill-down and the daily example; "
        "rebuilt after every update", fc=AMBER_L, ec=AMBER, title="Dashboard", wrap=80)
    arrow(ax, 15, H - 47.6, 30, H - 50.4, color=BLUE); arrow(ax, 85, H - 47.6, 70, H - 50.4, color=RED)
    save(fig, "v_pipeline")


def funnel(N):
    exc = pd.read_csv(os.path.join(ROOT, "config", "universe_excluded.csv"))
    late = ", ".join(exc[exc.reason.str.startswith("first price")].ticker.str.replace(".NS", ""))
    ca = ", ".join(exc[exc.reason.str.startswith("suspected")].ticker.str.replace(".NS", ""))
    fig, ax = canvas(10.5)
    H = 100 * 10.5 / 15.5
    levels = [(f"{N['n_cand'][0]} Nifty 50 constituents (December 2025 list)", 90, GREY_L, "#555555"),
              (f"{int(N['n_cand'][0]) - int(N['n_excl_late'][0])} with a full price history from January 2015", 75, GREY_L, "#555555"),
              (f"{N['n_stocks'][0]} stocks in the balanced panel", 60, RED_L, RED)]
    hh = 13
    for i, (t, w, fc, ec) in enumerate(levels):
        y = H - 3 - (i + 1) * hh - i * 7
        box(ax, 50 - w / 2, y, w, hh, t, fc=fc, ec=ec, fs=10.5)
        if i < 2:
            arrow(ax, 50, y - 0.4, 50, y - 6.6)
            note = (f"− {N['n_excl_late'][0]} listed after 15 Jan 2015: {late}" if i == 0 else f"− {N['n_excl_ca'][0]} suspected unadjusted corporate actions: {ca}")
            ax.text(52, y - 3.5, textwrap.fill(note, 62), fontsize=10, color=AMBER if i else "#555555", va="center")
    save(fig, "v_funnel")


# ------------------------------------------------------------------ Chapter 5 data charts
def exc_rate_ideal():
    s = rd("summary_price.csv").set_index(["model", "alpha"])
    fig, axs = plt.subplots(1, 2, figsize=(W, 8.2 / 2.54), sharey=True)
    for ax, a in zip(axs, (0.01, 0.05)):
        vals = [100 * s.loc[(m, a)].exc_rate for m in ORDER]
        ax.barh(range(len(ORDER)), vals, color=[COL[m] for m in ORDER], edgecolor="none")
        ax.axvline(100 * a, color=AMBER, ls="--", lw=1.6, zorder=0)
        ax.text(100 * a, -0.75, f"ideal {100 * a:.0f}%", color="#8a5d00", fontsize=10, ha="center", va="bottom")
        for i, v in enumerate(vals):
            ax.text(v + 0.02 * max(vals), i, f"{v:.2f}", va="center", fontsize=10, bbox=dict(fc="white", ec="none", pad=0.5))
        ax.set_xlim(0, max(vals) * 1.22)
        ax.set_xlabel(f"Breach rate at {'99' if a == 0.01 else '95'}% VaR (%)")
    axs[0].set_yticks(range(len(ORDER))); axs[0].set_yticklabels(ORDER); axs[0].set_ylim(len(ORDER) - 0.5, -1.1)
    fig.tight_layout()
    save(fig, "v_exc_rate_ideal")


def dm_bar():
    c = rd("report/dm_fz0_95_counts.csv").set_index("model")
    fig, ax = plt.subplots(figsize=(W, 5.2 / 2.54))
    left = np.zeros(len(c))
    for col, lab, colr in (("garch_better", "GARCH significantly lower loss", RED), ("ml_better", "ML significantly lower loss", BLUE),
                           ("no_difference", "No significant difference", "#d9d9d9")):
        ax.barh(c.index, c[col], left=left, color=colr, label=lab, edgecolor="white")
        for i, (l, v) in enumerate(zip(left, c[col])):
            if v >= 8:
                ax.text(l + v / 2, i, str(v), ha="center", va="center", fontsize=10, color="white" if col != "no_difference" else "black")
        left += c[col].values
    tot = c.sum()
    ax.set_title(f"All three ML models: GARCH better {tot.garch_better}, ML better {tot.ml_better}, no difference {tot.no_difference}", fontsize=10.5)
    ax.set_xlabel("Pairs (GARCH model × stock), Diebold-Mariano on FZ0 at 95%, 5% level")
    ax.invert_yaxis()
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.38), frameon=False, fontsize=10)
    save(fig, "v_dm_bar")


def stress_share():
    b = rd("breach_days_summary_price.csv")
    b = b[b.alpha == 0.01].set_index("model").reindex(ORDER)
    base = 100 * b.share_of_days_stress.iloc[0]
    fig, ax = plt.subplots(figsize=(W, 7.2 / 2.54))
    v = 100 * b.share_of_breaches_on_stress_days
    ax.bar(range(len(ORDER)), v, color=[COL[m] for m in ORDER])
    for i, x in enumerate(v):
        ax.text(i, x + 0.4, f"{x:.1f}", ha="center", fontsize=10)
    ax.axhline(base, color=AMBER, ls="--", lw=1.6, label=f"Share of test days that were stress days ({base:.1f}%)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.16), frameon=False)
    ax.set_xticks(range(len(ORDER))); ax.set_xticklabels(ORDER, rotation=35, ha="right")
    ax.set_ylabel("Share of 99% breaches\non stress days (%)")
    ax.set_ylim(0, v.max() * 1.12)
    fig.tight_layout()
    save(fig, "v_stress_share")


def lt_case(N):
    d = daily()
    t = N["nr_stock"][0] + ".NS"
    x = d[(d.ticker == t) & (d.alpha == 0.01)]
    xg = x[x.model == "XGBoost"].set_index("date").sort_index()
    gj = x[x.model == "GJR-t"].set_index("date").sort_index()
    day = xg[xg["var"] <= 1e-5].index[0]
    i = xg.index.get_loc(day)
    w = xg.index[max(0, i - 30): i + 31]
    fig, ax = plt.subplots(figsize=(W, 8.4 / 2.54))
    ax.plot(w, 100 * xg.loc[w, "ret"], color="#4d4d4d", lw=1, label=f"{N['nr_stock'][0]} return")
    ax.plot(w, -100 * gj.loc[w, "var"], color=COL["GJR-t"], lw=1.6, label="GJR-t 99% VaR")
    ax.plot(w, -100 * xg.loc[w, "var"], color=COL["XGBoost"], lw=1.6, label="XGBoost 99% VaR")
    ax.axhline(0, color="#999999", lw=0.6)
    ax.scatter([day], [100 * xg.loc[day, "ret"]], s=60, marker="x", color=AMBER, zorder=5, lw=2)
    lo = min(-100 * gj.loc[w, "var"].max(), 100 * xg.loc[w, "ret"].min())
    ax.set_ylim(lo - 5.5, None)
    ax.annotate(f"{N['nr_date'][0]}: XGBoost VaR at its floor (no risk); the loss of {N['nr_ret'][0]}\ncounts as a breach. GJR-t VaR that day: {N['nr_gjrt_var'][0]}",
                xy=(day, 100 * xg.loc[day, "ret"]), xytext=(0.02, 0.04), textcoords="axes fraction", fontsize=10,
                arrowprops=dict(arrowstyle="-|>", color=AMBER), color="#8a5d00", bbox=dict(fc="white", ec=AMBER, pad=2))
    ax.set_ylabel("Daily log return (%)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), fontsize=10, frameon=False, ncol=3)
    import matplotlib.dates as mdates
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    fig.tight_layout()
    save(fig, "v_lt_norisk")


# ------------------------------------------------------------------ Chapter 6
def decision_table(N):
    g = lambda k: N[k][0]
    rows = [("Bank market-risk desk", "GJR-GARCH-t (or EGARCH-t) for 99% VaR and ES; ML only as a challenger",
             f"GJR-t breach rate {g('exc99_gjrt')}, Kupiec pass {g('kup99_gjrt')}, Basel Green {g('green_gjrt')}; DM: GARCH better {g('dm_g')}, ML {g('dm_m')}",
             f"About {g('gap_xgb_gjrt_yr')} fewer breaches per stock per year than XGBoost", "High: open-source, minutes per day"),
            ("Broker margin team", "GARCH-t daily VaR plus a stress add-on for market-wide fall days",
             f"{g('stress_gjrt')} of GJR-t breaches fell on {g('stress_share_days')} of days (Nifty down 2%+)",
             "Fewer margin shortfalls on the days that matter most", "High: rule-based add-on"),
            ("Portfolio manager", "Per-stock GJR-t VaR, with sector-based limits",
             f"Median average 99% VaR from {g('sec_low_var')} ({g('sec_low')}) to {g('sec_high_var')} ({g('sec_high')})",
             "Risk budgets that match each stock's real risk", "High: uses existing data"),
            ("Retail or fintech app", "Show the GJR-t 'likely worst daily loss' in plain words, refreshed daily",
             f"Daily Action and dashboard run unattended; dashboard text at Flesch-Kincaid grade {g('fk_min')}-{g('fk_max')}",
             "Investors understand downside before they trade", "High: low cost, static hosting"),
            ("Exchange or regulator", "Monitor breach clustering across stocks; require ML risk models to pass the same backtests",
             f"Up to {g('maxday_gjrt')} of 41 stocks breached on one day; XGBoost had {g('norisk99_xgb')} no-risk stock-days at 99%",
             "Early warning of system-wide stress; safer model approvals", "Medium: needs data sharing")]
    fig, ax = canvas(16.5)
    H = 100 * 16.5 / 15.5
    xs, ws = [0.5, 14.5, 38, 65, 84], [14, 23.5, 27, 19, 15.5]
    heads = ["User", "Approach", "Evidence (this study)", "Expected benefit", "Viability"]
    for x, w, hd in zip(xs, ws, heads):
        ax.add_patch(FancyBboxPatch((x, H - 7), w - 0.3, 6, boxstyle="square,pad=0", fc="#333333", ec="white"))
        ax.text(x + w / 2, H - 4, hd, color="white", ha="center", va="center", fontsize=10, weight="bold")
    rh = (H - 8) / len(rows)
    for i, r in enumerate(rows):
        y = H - 7.5 - (i + 1) * rh
        for j, (x, w, txt) in enumerate(zip(xs, ws, r)):
            fc = RED_L if j == 1 else (AMBER_L if j == 4 else ("#f7f7f7" if j == 0 else "white"))
            ax.add_patch(FancyBboxPatch((x, y), w - 0.3, rh - 0.5, boxstyle="square,pad=0", fc=fc, ec="#bbbbbb", lw=0.6))
            ax.text(x + 0.8, y + (rh - 0.5) / 2, textwrap.fill(txt, int(w * 0.84)), ha="left", va="center", fontsize=10,
                    weight="bold" if j == 0 else "normal", linespacing=1.15)
    save(fig, "v_decision_table")


def model_flow():
    fig, ax = canvas(12.5)
    H = 100 * 12.5 / 15.5
    box(ax, 30, H - 11, 40, 9, "Need a one-day VaR / ES for a stock or portfolio", fc=GREY_L, fs=10.5, wrap=40)
    box(ax, 30, H - 27, 40, 10, "Used for capital, margin or a regulator?", fc=AMBER_L, ec=AMBER, fs=10.5, wrap=40)
    arrow(ax, 50, H - 11.5, 50, H - 16.5)
    box(ax, 1, H - 47, 40, 14, "GJR-GARCH-t or EGARCH-t; refit at least monthly; backtest every month (Kupiec, Christoffersen, Basel 99%)",
        fc=RED_L, ec=RED, title="Yes", wrap=42, fs=10)
    box(ax, 59, H - 47, 40, 14, "GARCH-t still the default; an ML model may be shown next to it only after it passes the same checks",
        fc=BLUE_L, ec=BLUE, title="No (internal view)", wrap=42, fs=10)
    arrow(ax, 40, H - 27.5, 21, H - 32.5, color=RED); arrow(ax, 60, H - 27.5, 79, H - 32.5, color=BLUE)
    box(ax, 1, H - 63, 98, 10, "Is the market falling sharply (for example the Nifty down 2% or more) or are many stocks breaching at once?",
        fc=AMBER_L, ec=AMBER, fs=10.5, wrap=100)
    arrow(ax, 21, H - 47.5, 30, H - 52.5); arrow(ax, 79, H - 47.5, 70, H - 52.5)
    box(ax, 1, 2, 47, H - 70, "Add a stress buffer on top of VaR; review open positions the same evening", fc="white", ec=AMBER, title="Yes", wrap=48, fs=10)
    box(ax, 52, 2, 47, H - 70, "Use the model VaR and ES as they are; any ML challenger must show zero 'no-risk' days and be refitted regularly",
        fc="white", ec="#555555", title="No", wrap=48, fs=10)
    arrow(ax, 35, H - 63.5, 25, H - 67.5); arrow(ax, 65, H - 63.5, 75, H - 67.5)
    save(fig, "v_model_flow")


def roadmap():
    fig, ax = plt.subplots(figsize=(W, 5.6 / 2.54))
    steps = [("Days 1-30", ["Data checks", "and snapshot", "pipeline"], GREY_L), ("Days 31-60", ["Run GJR-t", "in shadow", "mode"], RED_L),
             ("Days 61-90", ["Backtest;", "go live with", "stress add-on"], RED_L), ("Quarterly", ["Re-validate;", "check", "clustering"], AMBER_L),
             ("Yearly", ["Review ML", "challengers"], BLUE_L)]
    for i, (t, d, c) in enumerate(steps):
        ax.add_patch(FancyBboxPatch((i * 2.05, 0), 1.85, 1.6, boxstyle="round,pad=0.02,rounding_size=0.1", fc=c, ec="#333333", lw=0.9))
        ax.text(i * 2.05 + 0.925, 1.33, t, ha="center", va="center", weight="bold", fontsize=10.5)
        ax.text(i * 2.05 + 0.925, 0.6, chr(10).join(d), ha="center", va="center", fontsize=10, linespacing=1.25)
        if i < len(steps) - 1:
            ax.annotate("", xy=(i * 2.05 + 2.05, 0.8), xytext=(i * 2.05 + 1.85, 0.8), arrowprops=dict(arrowstyle="-|>", lw=1.2))
    ax.set_xlim(-0.05, 10.2); ax.set_ylim(-0.1, 1.7); ax.axis("off")
    save(fig, "v_roadmap")


def main():
    N, _ = build()
    market_structure(); swot(); method_flow(); timeline(); techniques(); pipeline(N); funnel(N)
    exc_rate_ideal(); dm_bar(); stress_share(); lt_case(N); decision_table(N); model_flow(); roadmap()


if __name__ == "__main__":
    main()
