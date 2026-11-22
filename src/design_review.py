"""Design review screenshots of every dashboard tab at desktop (1440 px) and phone (480 px) width.

Saves full-page screenshots to design/review/<width>_<tab>.png and prints, per tab: horizontal overflow, console
errors, empty cards, text clipped by its box, and Plotly charts that failed to draw.

  python src/design_review.py [--url http://localhost:4181/capstone-nifty50-downside-risk/] [--tabs start,stock]
"""
import argparse
import os

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABS = [("start", "#/"), ("overview", "#/overview"), ("models", "#/models"), ("regimes", "#/regimes"), ("stock", "#/stock"),
        ("features", "#/features"), ("live", "#/live"), ("glossary", "#/glossary"), ("about", "#/about")]
CHECK = r"""() => {
  const out = {overflow: document.documentElement.scrollWidth - window.innerWidth, empty: 0, clipped: [], plots: 0, badPlots: 0};
  document.querySelectorAll('.card').forEach(c => { if (!c.innerText.trim() && !c.querySelector('svg, canvas')) out.empty++; });
  document.querySelectorAll('h1, h2, h3, p, td, th, button, a, label').forEach(e => {
    if (e.closest('.js-plotly-plot') || e.closest('table')) return;
    if (e.scrollWidth > e.clientWidth + 2 && getComputedStyle(e).overflowX !== 'visible') out.clipped.push(e.innerText.slice(0, 50));
  });
  document.querySelectorAll('.js-plotly-plot').forEach(p => { out.plots++; if (!p.querySelector('.main-svg')) out.badPlots++; });
  return out;
}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:4181/capstone-nifty50-downside-risk/")
    ap.add_argument("--out", default=os.path.join(ROOT, "design", "review"))
    ap.add_argument("--tabs", default="")
    ap.add_argument("--widths", default="1440,480")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    tabs = [t for t in TABS if not a.tabs or t[0] in a.tabs.split(",")]
    with sync_playwright() as p:
        br = p.chromium.launch(channel="msedge")
        for w in [int(x) for x in a.widths.split(",")]:
            page = br.new_page(viewport={"width": w, "height": 900})
            errors = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            for name, frag in tabs:
                page.goto(a.url + frag, wait_until="load")
                page.wait_for_function("!document.body.innerText.includes('Loading')", timeout=90000)
                page.wait_for_timeout(2500)
                r = page.evaluate(CHECK)
                page.screenshot(path=os.path.join(a.out, f"{w}_{name}.png"), full_page=True)
                print(f"{w} {name:9s} overflow {r['overflow']} empty {r['empty']} plots {r['plots']} bad {r['badPlots']} "
                      f"clipped {r['clipped'][:3]} errors {errors[:2]}", flush=True)
                errors.clear()
            page.close()
        br.close()


if __name__ == "__main__":
    main()
