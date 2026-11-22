"""Dashboard screenshots for Appendix G of the Phase 2 report, sized so the printed text is at least 10 pt.

Captured at phone layout (viewport 480 x 900, below the dashboard's 640 px tablet breakpoint; device scale factor 2)
and cropped to one block of main content per tab. Rule used: the smallest text on screen is the 11 px chart text,
so a crop may hold at most 11 / 0.3528 = 31.2 CSS px per printed cm. A 454 px wide crop therefore prints at
about 14.5 cm, and one report page (20.5 cm of image height, leaving room for the caption and the "What this means" box) holds
at most about 639 CSS px of page height.
A desktop capture cannot meet the rule: its content is about 1,246 px wide, so 17 px body text would print at
about 6 pt on a 15 cm figure.

  python src/report_screens.py [--url https://ghiris-a11y.github.io/capstone-nifty50-downside-risk/]
  -> report/figures/dashboard/phone_<tab>.png and report/figures/dashboard/phone_sizes.json (printed width in cm
     and the printed point size of 11 px and 17 px text, read by src/build_report.py)
"""
import argparse
import json
import os

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEW_W = 480
PX_PER_CM = 11 / 0.3528          # 11 px text prints at 10 pt
MAX_IMG_CM = 20.5                # image height that fits one page with its caption, source line and "What this means" box
BUDGET = MAX_IMG_CM * PX_PER_CM  # CSS px of page height per screenshot
PAD = 4
# (name, route, text the crop starts at; None = first block under the tabs; '|plot' = start at the chart in that block,
#  when title + chart would not fit; the report caption then carries the finding title)
TABS = [("start", "#/", None),
        ("models", "#/models", "EGARCH-t came closest"),
        ("regimes", "#/regimes", "Figure 14.|plot"),
        ("stock", "#/stock", "Reliance Industries: forecast against real loss|plot"),
        ("live", "#/live", None)]

JS_BOX = """([startText, budget]) => {
  const main = document.querySelector('main');
  const all = [...main.querySelectorAll('*')].filter(e => e.getBoundingClientRect().height > 20);
  let start = main.firstElementChild, plot = null;
  if (startText) {
    const [txt, mode] = startText.split('|');
    const hits = all.filter(e => (e.innerText || '').trim().startsWith(txt));
    start = hits[hits.length - 1];   // innermost element whose text starts there
    if (mode === 'plot') start = plot = start.closest('figure, section').querySelector('.js-plotly-plot');
  }
  const y0 = start.getBoundingClientRect().top + window.scrollY;
  // end at the last block boundary that fits the budget (never cut through a block)
  const ends = all.map(e => e.getBoundingClientRect().bottom + window.scrollY).filter(b => b > y0 + 150 && b <= y0 + budget);
  let y1 = Math.max(...ends);
  if (plot && plot.getBoundingClientRect().bottom + window.scrollY <= y0 + budget) y1 = plot.getBoundingClientRect().bottom + window.scrollY;  // end with the chart
  const kids = [...main.children].map(c => c.getBoundingClientRect());
  return {x0: Math.min(...kids.map(k => k.left)), x1: Math.max(...kids.map(k => k.right)), y0, y1};
}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="https://ghiris-a11y.github.io/capstone-nifty50-downside-risk/")
    ap.add_argument("--out", default=os.path.join(ROOT, "report", "figures", "dashboard"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    info = {}
    with sync_playwright() as p:
        br = p.chromium.launch(channel="msedge")
        page = br.new_page(viewport={"width": VIEW_W, "height": 900}, device_scale_factor=2)
        for name, frag, start in TABS:
            page.goto(a.url + frag, wait_until="load")
            page.wait_for_function("!document.body.innerText.includes('Loading')", timeout=60000)
            page.wait_for_timeout(3000)
            b = page.evaluate(JS_BOX, [start, BUDGET - 2 * PAD])
            clip = dict(x=b["x0"] - PAD, y=b["y0"] - PAD, width=b["x1"] - b["x0"] + 2 * PAD, height=b["y1"] - b["y0"] + 2 * PAD)
            page.screenshot(path=os.path.join(a.out, f"phone_{name}.png"), clip=clip, full_page=True)
            w_cm = clip["width"] / PX_PER_CM
            info[name] = dict(css_w=round(clip["width"]), css_h=round(clip["height"]), print_w_cm=round(w_cm, 2),
                              print_h_cm=round(clip["height"] / PX_PER_CM, 1),
                              pt_11px=round(11 / PX_PER_CM / 0.03528, 1), pt_17px=round(17 / PX_PER_CM / 0.03528, 1))
            print(name, info[name], flush=True)
        br.close()
    json.dump(info, open(os.path.join(a.out, "phone_sizes.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
