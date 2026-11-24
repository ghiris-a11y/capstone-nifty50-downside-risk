"""Redraw the report's diagram figures with measured text: wrapped inside boxes, centred, no overflow."""
from PIL import Image, ImageDraw, ImageFont

DPI = 300
F = "/usr/share/fonts/truetype/liberation/LiberationSerif-%s.ttf"
def font(px, bold=False): return ImageFont.truetype(F % ("Bold" if bold else "Regular"), px)
PT = lambda pt: round(pt * DPI / 72)          # point size -> pixels at 300 dpi
CM = lambda cm: round(cm / 2.54 * DPI)

C = dict(  # fill, border
    red=("#FDE0D2", "#A50F15"), blue=("#DEEBF7", "#08519C"), grey=("#F0F0F0", "#444444"),
    white=("#FFFFFF", "#444444"), amber=("#FDF0D0", "#C98A00"), head=("#333333", "#333333"),
    lgrey=("#F7F7F7", "#BBBBBB"), cell=("#FFFFFF", "#BBBBBB"))
TXT = "#111111"
PAD = 20

def wrap(d, text, f, width):
    out = []
    for para in text.split("\n"):
        line = ""
        for w in para.split(" "):
            t = (line + " " + w).strip()
            if d.textlength(t, font=f) <= width or not line:
                line = t
            else:
                out.append(line); line = w
        out.append(line)
    return out

def block(d, title, body, width, ft, fb, align="center", bullets=False):
    """Return list of (text, font, x_offset) lines and total height for a box of inner width."""
    lines = []
    if title:
        for l in wrap(d, title, ft, width): lines.append((l, ft, 0))
    if body:
        if bullets:
            ind = d.textlength("•  ", font=fb)
            for item in body:
                for k, l in enumerate(wrap(d, item, fb, width - ind)):
                    lines.append((("•  " if k == 0 else "") + l, fb, 0 if k == 0 else ind))
        else:
            for l in wrap(d, body, fb, width): lines.append((l, fb, 0))
    lh = lambda f: round(f.size * 1.22)
    gap = round(fb.size * 0.35) if title and body else 0
    h = sum(lh(f) for _, f, _ in lines) + gap
    return lines, h, lh, gap

def draw_box(d, x, y, w, h, title, body, style, ft, fb, align="center", bullets=False, radius=18, title_color=None):
    fill, edge = C[style]
    d.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=fill, outline=edge, width=5)
    lines, th, lh, gap = block(d, title, body, w - 2 * PAD, ft, fb, align, bullets)
    cy = y + (h - th) / 2
    first_body = True
    for i, (l, f, xo) in enumerate(lines):
        if f is fb and title and first_body:
            cy += gap; first_body = False
        tw = d.textlength(l, font=f)
        tx = x + (w - tw) / 2 if align == "center" else x + PAD + xo
        d.text((tx, cy), l, font=f, fill=(title_color if (f is ft and title_color) else TXT))
        cy += lh(f)

def need_h(d, title, body, w, ft, fb, bullets=False):
    return block(d, title, body, w - 2 * PAD, ft, fb, bullets=bullets)[1] + 2 * PAD + 10

def arrow(d, p0, p1, color="#333333", width=6, head=22):
    import math
    d.line([p0, p1], fill=color, width=width)
    a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    l, r = a + math.radians(152), a - math.radians(152)
    d.polygon([p1, (p1[0] + head * math.cos(l), p1[1] + head * math.sin(l)),
               (p1[0] + head * math.cos(r), p1[1] + head * math.sin(r))], fill=color)

def canvas(wcm, hpx):
    im = Image.new("RGB", (CM(wcm), hpx), "white")
    return im, ImageDraw.Draw(im)

def save(im, path):
    im.save(path, dpi=(DPI, DPI)); print(path, im.size, round(im.size[0] / DPI * 2.54, 2), "x", round(im.size[1] / DPI * 2.54, 2), "cm")

W = 15.5  # cm, printed width

# ---------------------------------------------------------------- Figure 1.1 market structure
def fig11(path):
    ft, fb, fl = font(PT(11), True), font(PT(10)), font(PT(11), True)
    im, d = canvas(W, 4000); Wp = im.size[0]
    gx = 50; w2 = (Wp - gx) // 2; y = 6
    top = [("SEBI", "Securities market regulator. Sets risk rules for exchanges, clearing corporations, brokers and funds."),
           ("RBI", "Central bank. Sets the repo rate (raised to 5.50% on 7 October 2026) and supervises banks.")]
    mid = [("NSE", "Exchange. Runs trading; publishes the Nifty 50 index and the India VIX (expected volatility)."),
           ("NSE Clearing", "Clearing corporation. Guarantees trades and collects margin from members every day.")]
    def row2(items, style, y):
        h = max(need_h(d, t, b, w2, ft, fb) for t, b in items)
        for k, (t, b) in enumerate(items): draw_box(d, 3 + k * (w2 + gx), y, w2 - 6, h, t, b, style, ft, fb)
        return h
    h = row2(top, "grey", y)
    for k in range(2):
        cx = 3 + k * (w2 + gx) + w2 // 2; arrow(d, (cx, y + h + 4), (cx, y + h + 56))
    y += h + 64
    h = row2(mid, "white", y)
    arrow(d, (w2 - 3, y + h // 2), (w2 + gx + 3, y + h // 2))
    y += h + 30
    def label(t, y, color=TXT):
        tw = d.textlength(t, font=fl); d.text(((Wp - tw) / 2, y), t, font=fl, fill=color); return fl.size + 24
    y += label("Market participants", y)
    gx4 = 34; w4 = (Wp - 3 * gx4) // 4
    parts = ["Brokers and trading members", "Mutual funds and FPIs", "Bank treasury desks", "Retail investors (demat accounts)"]
    h = max(need_h(d, None, p, w4, ft, fb) for p in parts)
    for k, p in enumerate(parts): draw_box(d, 3 + k * (w4 + gx4), y, w4 - 6, h, None, p, "white", ft, fb)
    for k in range(4):
        cx = 3 + k * (w4 + gx4) + w4 // 2; arrow(d, (cx, y + h + 4), (cx, y + h + 50), color="#A50F15")
    y += h + 62
    y += label("How VaR and Expected Shortfall are used", y, "#A50F15")
    uses = [("Margins", "Clearing corporations set initial margin from a VaR-type estimate of a one-day loss."),
            ("Limits", "Brokers and funds cap positions so the likely worst daily loss stays inside a budget."),
            ("Capital", "Banks hold market-risk capital; Basel rules use ES and backtest 99% VaR."),
            ("Investor view", "Apps and funds show risk to clients in simple terms.")]
    h = max(need_h(d, t, b, w4, ft, fb) for t, b in uses)
    for k, (t, b) in enumerate(uses): draw_box(d, 3 + k * (w4 + gx4), y, w4 - 6, h, t, b, "red", ft, fb)
    y += h + 8
    save(im.crop((0, 0, Wp, y)), path)

# ---------------------------------------------------------------- Figure 1.2 SWOT
def fig12(path):
    ft, fb = font(PT(11), True), font(PT(10))
    im, d = canvas(W, 4000); Wp = im.size[0]; g = 40; w2 = (Wp - g) // 2
    q = [("Strengths", "red", ["Deep, liquid large-cap market with daily index and India VIX data",
                                "Established VaR-based margin and risk framework",
                                "Free daily data allow transparent, repeatable models",
                                "In this study, GARCH-t models stayed close to the 1% breach target"]),
         ("Weaknesses", "grey", ["Free data are unofficial; some corporate actions are unadjusted",
                                  "Newer large firms have short histories",
                                  "ML risk models are harder to explain and need refitting",
                                  "Single-stock backtests have few breaches, so low power"]),
         ("Opportunities", "blue", ["Growing retail base needs simple daily risk signals",
                                     "Low-cost automated daily risk pipelines (as built here)",
                                     "Stress add-ons for market-wide fall days",
                                     "Use ML as a challenger model under strict backtests"]),
         ("Threats", "amber", ["Market-wide shock days when many stocks breach together",
                                "Interest-rate regime change (repo hike, Oct 2026)",
                                "Inputs drifting outside the range a model was fitted on",
                                "Over-trusting a model that once forecast no risk"])]
    h = max(need_h(d, t, b, w2, ft, fb, bullets=True) for t, _, b in q)
    y = 4
    for k, (t, s, b) in enumerate(q):
        x = 3 + (k % 2) * (w2 + g); yy = y + (k // 2) * (h + g)
        # title centred, bullets left-aligned: draw box then title then bullets
        fill, edge = C[s]
        d.rounded_rectangle([x, yy, x + w2 - 6, yy + h], radius=18, fill=fill, outline=edge, width=5)
        tw = d.textlength(t, font=ft); ty = yy + PAD
        d.text((x + (w2 - 6 - tw) / 2, ty), t, font=ft, fill=TXT)
        lines, _, lh, _ = block(d, None, b, w2 - 6 - 2 * PAD, ft, fb, bullets=True)
        cy = ty + round(ft.size * 1.22) + round(fb.size * 0.35)
        for l, f, xo in lines:
            d.text((x + PAD + xo, cy), l, font=f, fill=TXT); cy += lh(f)
    save(im.crop((0, 0, Wp, y + 2 * h + g + 8)), path)

# ---------------------------------------------------------------- Figure 3.1 timeline (matplotlib)
def fig31(path):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt, matplotlib.dates as md
    from matplotlib import font_manager
    for s in ("Regular", "Bold"): font_manager.fontManager.addfont(F % s)
    plt.rcParams.update({"font.family": "Liberation Serif", "font.size": 11})
    D = lambda s: md.datestr2num(s)
    fig, ax = plt.subplots(figsize=(W / 2.54, 5.2 / 2.54), dpi=DPI)
    rows = {"Main study": [("Train", "2015-01-01", "2022-01-01", "#FDE0D2"), ("Validation", "2022-01-01", "2024-01-01", "#FDF0D0"),
                           ("Test", "2024-01-01", "2026-11-18", "#DEEBF7")],
            "Feature choice": [("Train", "2015-01-01", "2020-01-01", "#FDE0D2"), ("Calibrate", "2020-01-01", "2022-01-01", "#F0F0F0"),
                               ("Evaluate", "2022-01-01", "2024-01-01", "#FDF0D0")]}
    for i, (name, segs) in enumerate(rows.items()):
        yv = 1 - i
        for lab, a, b, col in segs:
            ax.barh(yv, D(b) - D(a), left=D(a), height=0.55, color=col, edgecolor="#333333", linewidth=1)
            ax.text((D(a) + D(b)) / 2, yv, lab, ha="center", va="center", fontsize=11)
    hk = D("2026-10-07")
    ax.axvline(hk, color="#C98A00", ls="--", lw=1.6)
    ax.annotate("RBI repo hike to 5.50%, 7 Oct 2026", xy=(hk, 1.32), xytext=(D("2025-12-01"), 1.62),
                ha="right", va="center", fontsize=10, color="#7A5200",
                arrowprops=dict(arrowstyle="->", color="#7A5200", lw=1))
    ax.set_yticks([1, 0]); ax.set_yticklabels(list(rows)); ax.set_ylim(-0.5, 1.85)
    ax.set_xlim(D("2015-01-01"), D("2027-03-01"))
    ax.xaxis.set_major_locator(md.YearLocator(2)); ax.xaxis.set_major_formatter(md.DateFormatter("%Y"))
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout(pad=0.3); fig.savefig(path, dpi=DPI); plt.close(fig)
    im = Image.open(path); print(path, im.size)

# ---------------------------------------------------------------- tables drawn as figures (3.2 and 6.1)
def table_fig(path, head, rows, widths_frac, styles, bold_first=False, fs=10):
    fh, fb, fbb = font(PT(fs), True), font(PT(fs)), font(PT(fs), True)
    im, d = canvas(W, 6000); Wp = im.size[0]; g = 8
    ws = [round((Wp - g * (len(head) - 1)) * f) for f in widths_frac]
    ws[-1] = Wp - g * (len(head) - 1) - sum(ws[:-1])
    def row(cells, y, stys, fonts, mind=0):
        h = max(mind, max(block(d, None, c, w - 2 * PAD, fonts[i], fonts[i])[1] for i, (c, w) in enumerate(zip(cells, ws))) + 2 * PAD)
        x = 0
        for i, (c, w) in enumerate(zip(cells, ws)):
            fill, edge = C[stys[i]]
            d.rectangle([x, y, x + w - 1, y + h], fill=fill, outline=edge, width=3)
            lines, th, lh, _ = block(d, None, c, w - 2 * PAD, fonts[i], fonts[i])
            cy = y + (h - th) / 2
            for l, f, _ in lines:
                tx = x + (w - d.textlength(l, font=f)) / 2 if stys[i] == "head" else x + PAD
                d.text((tx, cy), l, font=f, fill="white" if stys[i] == "head" else TXT); cy += lh(f)
            x += w + g
        return h
    y = 0
    y += row(head, y, ["head"] * len(head), [fh] * len(head)) + g
    for r, st in zip(rows, styles):
        fonts = [fbb if (bold_first and i == 0) else fb for i in range(len(r))]
        y += row(r, y, st, fonts) + g
    save(im.crop((0, 0, Wp, y - g + 2)), path)

def fig32(path):
    head = ["Technique", "Why it was chosen", "What it answers"]
    R = [("red", "GARCH, EGARCH, GJR-GARCH (Normal and Student-t)", "Standard volatility models; EGARCH/GJR add the leverage effect, t adds fat tails", "Do classic models give well-calibrated VaR and ES?"),
         ("blue", "XGBoost quantile regression", "Learns the tail quantile directly from many inputs; non-linear", "Can ML forecast the loss quantile better?"),
         ("blue", "Random Forest and MLP + filtered historical simulation", "Learn volatility from inputs; residual quantiles give VaR and ES", "Does flexible volatility modelling help?"),
         ("grey", "250-day historical simulation", "Simple industry benchmark with no model", "Baseline any model must beat"),
         ("amber", "Kupiec and Christoffersen tests", "Standard VaR backtests: frequency and clustering of breaches", "Do forecasts fail too often, or in bunches?"),
         ("amber", "Basel traffic light (99% only)", "The regulator's backtest zones for 99% VaR", "Would a bank model stay in the green zone?"),
         ("amber", "FZ0 and pinball losses", "Proper scoring rules for VaR and ES together", "Which forecasts are best overall?"),
         ("amber", "Diebold-Mariano test", "Tests whether a loss difference is larger than chance", "Is a model's advantage real?"),
         ("amber", "India VIX quartiles, stress days", "Splits results by market mood and by market-wide falls", "When do models fail?"),
         ("blue", "SHAP values", "Shows which inputs drive the ML forecast", "Can ML forecasts be explained?")]
    table_fig(path, head, [r[1:] for r in R], [0.33, 0.37, 0.30], [[r[0], "cell", "cell"] for r in R])

def fig61(path):
    head = ["User", "Approach", "Evidence (this study)", "Expected benefit", "Viability"]
    R = [("Bank market-risk desk", "GJR-GARCH-t (or EGARCH-t) for 99% VaR and ES; ML only as a challenger", "GJR-t breach rate 0.84%, Kupiec pass 98%, Basel Green 96%; DM: GARCH better 90, ML 2", "About 2.0 fewer breaches per stock per year than XGBoost", "High: open-source, minutes per day"),
         ("Broker margin team", "GARCH-t daily VaR plus a stress add-on for market-wide fall days", "21.4% of GJR-t breaches fell on 1.5% of days (Nifty down 2%+)", "Fewer margin shortfalls on the days that matter most", "High: rule-based add-on"),
         ("Portfolio manager", "Per-stock GJR-t VaR, with sector-based limits", "Median average 99% VaR from 3.51% (FMCG) to 6.03% (Services)", "Risk budgets that match each stock's real risk", "High: uses existing data"),
         ("Retail or fintech app", "Show the GJR-t 'likely worst daily loss' in plain words, refreshed daily", "Daily Action and dashboard run unattended; dashboard text at Flesch-Kincaid grade 3.0-4.0", "Investors understand downside before they trade", "High: low cost, static hosting"),
         ("Exchange or regulator", "Monitor breach clustering across stocks; require ML risk models to pass the same backtests", "Up to 22 of 41 stocks breached on one day; XGBoost had 20 no-risk stock-days at 99%", "Early warning of system-wide stress; safer model approvals", "Medium: needs data sharing")]
    table_fig(path, head, R, [0.15, 0.24, 0.25, 0.19, 0.17], [["lgrey", "red", "cell", "cell", "amber"]] * len(R), bold_first=True, fs=9.5)

# ---------------------------------------------------------------- Figure 4.1 pipeline
def fig41(path):
    ft, fb, fs = font(PT(11), True), font(PT(10)), font(PT(9.5))
    im, d = canvas(W, 4000); Wp = im.size[0]; g = 90; w3 = (Wp - 2 * g) // 3
    xs = [3 + k * (w3 + g) for k in range(3)]
    r1 = [("Sources", "Yahoo Finance: 41 stocks, Nifty 50, India VIX, USD/INR. NSE: index constituents. RBI: repo rate (verified).", "grey"),
          ("Validation", "Hashes, gaps, zero-volume rows, corporate-action rule; failures logged", "white"),
          ("Frozen snapshot", "Read-only parquet files with SHA-256 hashes (2026-11-18 10:07 UTC); source of all report numbers", "red")]
    r2 = [("Live files", "data/live, outputs/live (derived values only, no raw prices published)", "blue"),
          ("GitHub Action", "Weekdays 13:30 UTC (7:00 PM IST): new prices, checks, GJR-t next-day VaR and ES", "blue"),
          ("Research run", "nifty50_var_pipeline.py: 10 models, backtests, tables and figures", "red")]
    y1 = 4; h1 = max(need_h(d, t, b, w3, ft, fb) for t, b, _ in r1)
    for x, (t, b, s) in zip(xs, r1): draw_box(d, x, y1, w3, h1, t, b, s, ft, fb)
    arrow(d, (xs[0] + w3 + 6, y1 + h1 // 2), (xs[1] - 8, y1 + h1 // 2))
    arrow(d, (xs[1] + w3 + 6, y1 + h1 // 2), (xs[2] - 8, y1 + h1 // 2))
    y2 = y1 + h1 + 90; h2 = max(need_h(d, t, b, w3, ft, fb) for t, b, _ in r2)
    for x, (t, b, s) in zip(xs, r2): draw_box(d, x, y2, w3, h2, t, b, s, ft, fb)
    blue, red = "#08519C", "#A50F15"
    arrow(d, (xs[0] + w3 // 2, y1 + h1 + 6), (xs[0] + w3 // 2, y2 - 8), color=blue)
    d.text((xs[0] + w3 // 2 + 18, y1 + h1 + 30), "daily refresh", font=fs, fill=blue)
    arrow(d, (xs[2] + w3 // 2, y1 + h1 + 6), (xs[2] + w3 // 2, y2 - 8))
    arrow(d, (xs[1] - 6, y2 + h2 // 2), (xs[0] + w3 + 8, y2 + h2 // 2), color=blue)
    wd = round(Wp * 0.62); xd = (Wp - wd) // 2; y3 = y2 + h2 + 80
    dt, db = "Dashboard", "Static React site on GitHub Pages: plain-language findings, charts, stock drill-down and the daily example; rebuilt after every update"
    h3 = need_h(d, dt, db, wd, ft, fb)
    draw_box(d, xd, y3, wd, h3, dt, db, "amber", ft, fb)
    arrow(d, (xs[0] + w3 // 2, y2 + h2 + 6), (xd + 60, y3 - 8), color=blue)
    arrow(d, (xs[2] + w3 // 2, y2 + h2 + 6), (xd + wd - 60, y3 - 8), color=red)
    save(im.crop((0, 0, Wp, y3 + h3 + 8)), path)

# ---------------------------------------------------------------- Figure 4.2 funnel
def fig42(path):
    fb, fs = font(PT(11)), font(PT(10))
    im, d = canvas(W, 3000); Wp = im.size[0]
    boxes = [("50 Nifty 50 constituents (December 2025 list)", "grey", 0.62),
             ("44 with a full price history from January 2015", "grey", 0.54),
             ("41 stocks in the balanced panel", "red", 0.46)]
    notes = [("− 6 listed after 15 Jan 2015: ETERNAL, HDFCLIFE, INDIGO, JIOFIN, MAXHEALTH, SBILIFE", "#555555"),
             ("− 3 suspected unadjusted corporate actions: ADANIENT, TMPV, TRENT", "#7A5200")]
    cx = round(Wp * 0.33); bh = 150; gap = 190; y = 4
    for k, (t, s, f) in enumerate(boxes):
        w = round(Wp * f); x = max(3, cx - w // 2)
        draw_box(d, x, y, w, bh, None, t, s, fb, fb)
        if k < 2:
            arrow(d, (cx, y + bh + 6), (cx, y + bh + gap - 8))
            lines = wrap(d, notes[k][0], fs, Wp - cx - 60)
            ty = y + bh + gap / 2 - len(lines) * fs.size * 0.62
            for l in lines:
                d.text((cx + 34, ty), l, font=fs, fill=notes[k][1]); ty += round(fs.size * 1.22)
        y += bh + gap
    save(im.crop((0, 0, Wp, y - gap + 8)), path)

if __name__ == "__main__":
    import sys
    out = sys.argv[1]
    fig11(f"{out}/image2.png"); fig12(f"{out}/image3.png"); fig31(f"{out}/image4.png")
    fig32(f"{out}/image5.png"); fig41(f"{out}/image6.png"); fig42(f"{out}/image7.png"); fig61(f"{out}/image18.png")
