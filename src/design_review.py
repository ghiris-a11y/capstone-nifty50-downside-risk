"""Design and mobile review of every dashboard tab.

Viewports: 1440 desktop, phones 360 / 390 / 414 / 480 portrait and 844x390 landscape; engines: Chromium (Edge) and
WebKit (Safari engine). Full-page screenshots go to design/review/<engine>_<width>_<tab>.png (Chromium only, unless
--shots all). Per tab and viewport it prints problems only:
  overflow      horizontal page overflow in px
  clipped       text cut off by its own box
  badPlots      Plotly charts that did not draw
  legend        a chart legend overlapping the plot area
  annOut        annotation text outside its chart
  tap           tap targets under 40x40 px (nav links, pills, menu button, selects)
  smallBody     body text under 14 px (captions marked text-xs / 13 px are excluded)
  smallChart    chart text under 11 px
and checks that the phone menu drawer opens, navigates and closes.

  python src/design_review.py [--url ...] [--tabs start,stock] [--views 390,844x390] [--engines chromium,webkit]
"""
import argparse
import os

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABS = [("start", "#/"), ("overview", "#/overview"), ("models", "#/models"), ("regimes", "#/regimes"), ("stock", "#/stock"),
        ("features", "#/features"), ("live", "#/live"), ("glossary", "#/glossary"), ("about", "#/about")]
VIEWS = ["1440", "360", "390", "414", "480", "844x390"]

CHECK = r"""() => {
  const R = (e) => e.getBoundingClientRect();
  const visible = (e) => { const r = R(e); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden' && !e.closest('details:not([open]) > :not(summary)'); };
  const out = {overflow: document.documentElement.scrollWidth - window.innerWidth, clipped: [], badPlots: 0, plots: 0,
               legend: [], annOut: [], tap: [], smallBody: [], smallChart: []};
  document.querySelectorAll('main h1, main h2, main h3, main p, main button, main a, main label, header *, nav a').forEach(e => {
    if (!visible(e) || e.closest('.js-plotly-plot') || e.closest('table')) return;
    if (e.scrollWidth > e.clientWidth + 2 && getComputedStyle(e).overflowX !== 'visible') out.clipped.push(e.innerText.slice(0, 40));
  });
  document.querySelectorAll('.js-plotly-plot').forEach((p, i) => {
    if (!visible(p)) return;
    out.plots++;
    if (!p.querySelector('.main-svg')) { out.badPlots++; return; }
    const pr = R(p);
    const lg = p.querySelector('.legend'), drag = [...p.querySelectorAll('.nsewdrag')];
    if (lg && drag.length) {
      const l = R(lg);
      if (drag.some(d => { const a = R(d); return l.left < a.right - 2 && l.right > a.left + 2 && l.top < a.bottom - 2 && l.bottom > a.top + 2; }))
        out.legend.push(i);
    }
    p.querySelectorAll('.annotation-text, .annotation text').forEach(a => {
      const r = R(a); if (!r.width) return;
      if (r.left < pr.left - 1 || r.right > pr.right + 1 || r.top < pr.top - 1) out.annOut.push(a.textContent.slice(0, 30));
    });
    p.parentElement.querySelectorAll(':scope > svg text').forEach(a => {   // our arrow-note overlay
      const r = R(a); if (r.left < pr.left - 1 || r.right > pr.right + 1) out.annOut.push(a.textContent.slice(0, 30));
    });
    p.querySelectorAll('.xtitle, .ytitle, .xtick text, .ytick text, .g-xtitle text, .g-ytitle text').forEach(a => {   // axis text cut off
      const r = R(a); if (!r.width || !a.textContent.trim()) return;
      if (r.left < pr.left - 1 || r.right > pr.right + 1 || r.bottom > pr.bottom + 1) out.annOut.push('axis: ' + a.textContent.slice(0, 26));
    });
    p.querySelectorAll('text').forEach(t => {
      const fs = parseFloat(t.style.fontSize || getComputedStyle(t).fontSize);
      if (t.textContent.trim() && fs < 10.95 && R(t).width) out.smallChart.push(`${t.textContent.slice(0, 15)} ${fs}`);
    });
  });
  document.querySelectorAll('nav a, header button, main button, main select, main summary').forEach(e => {
    if (!visible(e)) return;
    const r = R(e); if (r.width < 40 || r.height < 40) out.tap.push(`${(e.innerText || e.getAttribute('aria-label') || e.tagName).trim().slice(0, 20)} ${Math.round(r.width)}x${Math.round(r.height)}`);
  });
  document.querySelectorAll('main p, main li, main td, main dd').forEach(e => {
    if (!visible(e) || e.closest('.js-plotly-plot') || e.closest('.text-xs') || e.matches('.text-xs, [class*="text-[13px]"]') || e.closest('[class*="text-[13px]"]') || e.closest('figcaption')) return;
    if (!e.innerText.trim()) return;
    const fs = parseFloat(getComputedStyle(e).fontSize); if (fs < 13.95) out.smallBody.push(`${e.innerText.slice(0, 25)} ${fs}`);
  });
  return out;
}"""


def drawer_ok(page, url):
    page.goto(url + "#/", wait_until="load")
    page.wait_for_timeout(800)
    btn = page.get_by_role("button", name="Open menu")
    if not btn.is_visible():
        return "no menu button (desktop layout)"
    btn.click()
    link = page.locator("nav a", has_text="Glossary").last
    if not link.is_visible():
        return "FAIL: drawer did not open"
    link.click()
    page.wait_for_timeout(500)
    if "#/glossary" not in page.url:
        return "FAIL: navigation from drawer"
    if page.get_by_role("button", name="Close menu").count() and page.get_by_role("button", name="Close menu").first.is_visible():
        return "FAIL: drawer stayed open"
    return "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:4181/capstone-nifty50-downside-risk/")
    ap.add_argument("--out", default=os.path.join(ROOT, "design", "review"))
    ap.add_argument("--tabs", default="")
    ap.add_argument("--views", default=",".join(VIEWS))
    ap.add_argument("--engines", default="chromium,webkit")
    ap.add_argument("--shots", default="chromium", help="engines to screenshot: chromium, all or none")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    tabs = [t for t in TABS if not a.tabs or t[0] in a.tabs.split(",")]
    problems = 0
    with sync_playwright() as p:
        for eng in a.engines.split(","):
            br = p.chromium.launch(channel="msedge") if eng == "chromium" else p.webkit.launch()
            for v in a.views.split(","):
                w, h = (int(x) for x in v.split("x")) if "x" in v else (int(v), 900)
                page = br.new_page(viewport={"width": w, "height": h}, is_mobile=False)
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
                if w < 1024:
                    print(f"{eng} {v} drawer: {drawer_ok(page, a.url)}", flush=True)
                for name, frag in tabs:
                    page.goto(a.url + frag, wait_until="load")
                    page.wait_for_function("!document.body.innerText.includes('Loading')", timeout=90000)
                    page.wait_for_timeout(2500)
                    r = page.evaluate(CHECK)
                    if a.shots == "all" or a.shots == eng:
                        page.screenshot(path=os.path.join(a.out, f"{eng}_{v}_{name}.png"), full_page=True)
                    bad = {k: r[k] for k in ("overflow", "clipped", "badPlots", "legend", "annOut", "tap", "smallBody", "smallChart") if r[k]}
                    if errors:
                        bad["errors"] = errors[:2]
                    problems += bool(bad)
                    print(f"{eng} {v} {name:9s} plots {r['plots']} " + ("OK" if not bad else str({k: (x[:4] if isinstance(x, list) else x) for k, x in bad.items()})), flush=True)
                    errors.clear()
                page.close()
            br.close()
    print(f"tabs with problems: {problems}")


if __name__ == "__main__":
    main()
