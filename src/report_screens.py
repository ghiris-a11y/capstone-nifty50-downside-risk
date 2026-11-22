"""Dashboard screenshots for Appendix G of the Phase 2 report, sized so the printed text is at least 10 pt.

Captured from the live site at phone layout (viewport 480 x 900, below the 640 px tablet breakpoint) with device scale
factor 4. Each shot is cropped to one element's box on a tab, ending at the last block boundary that still fits one
report page. The report prints every shot at 14.6 cm wide, so 1 CSS px = 14.6 / (crop width) cm; the smallest text in
each crop (HTML and chart text) is measured and its printed size logged. It must be at least 10 pt.

  python src/report_screens.py [--url https://ghiris-a11y.github.io/capstone-nifty50-downside-risk/]
  -> report/figures/dashboard/app_<name>.png and report/figures/dashboard/app_sizes.json
"""
import argparse
import json
import os

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEW_W = 480
PRINT_CM = 14.6
MAX_IMG_CM = 20.5   # image height that leaves room for the caption, source line and "What this means" box
MAX_CM = {"start_numbers": 21.6}  # the Key numbers block needs slightly more; its caption and box are short
PAD = 4

# name, route, JS function of <main> returning [start element, element whose bottom ends the crop]
ANCHORS = [
    ("start_numbers", "#/", "(m) => [m.firstElementChild, [...m.querySelectorAll('section')].find(s => s.querySelector('h2')?.innerText.trim() === 'Key numbers')]"),
    ("start_actions", "#/", "(m) => { const s = [...m.querySelectorAll('section')].find(s => s.querySelector('h2')?.innerText.trim() === 'What a firm should do'); return [s, s]; }"),
    # chart cards are taller than one page at the 10-pt scale, so these crops hold the chart itself; the report caption
    # gives the card's title
    ("models_beaten", "#/models", "(m) => { const p = [...m.querySelectorAll('figure')].find(f => /How often each model was beaten/i.test(f.innerText)).querySelector('.js-plotly-plot'); return [p, p]; }"),
    ("regimes_fig14", "#/regimes", "(m) => { const p = [...m.querySelectorAll('figure')].find(f => f.innerText.trim().startsWith('Figure 14')).querySelector('.js-plotly-plot'); return [p, p]; }"),
    ("stock_fig3", "#/stock", "(m) => { const p = [...m.querySelectorAll('figure')].find(f => f.innerText.trim().startsWith('Figure 3')).querySelector('.js-plotly-plot'); return [p, p]; }"),
    # the Daily example page is two shots stacked: the amber banner, then the top of the table (the text between is
    # left out and the break is marked with a dashed line)
    ("live_banner", "#/live", "(m) => [m.firstElementChild, m.firstElementChild]"),
    ("live_tabletop", "#/live", "(m) => { const t = m.querySelector('table').parentElement; return [t, t]; }"),
]

JS_BOX = """([pick, budgetCm, printCm, pad]) => {
  const main = document.querySelector('main');
  const [start, end] = eval(pick)(main);
  const R = (e) => e.getBoundingClientRect();
  const top = (e) => R(e).top + window.scrollY, bottom = (e) => R(e).bottom + window.scrollY;
  const x0 = Math.min(R(start).left, R(end).left), x1 = Math.max(R(start).right, R(end).right);
  const budget = budgetCm * (x1 - x0 + 2 * pad) / printCm - 2 * pad;   // CSS px that fit one page at the printed width
  const y0 = top(start), limit = Math.min(bottom(end), y0 + budget);
  // end at the last block boundary that fits (never cut through a block, text line or table row)
  const ends = [...main.querySelectorAll('*')].filter(e => R(e).height > 12 && !e.closest('svg') && !e.closest('.js-plotly-plot'))
    .map(bottom).filter(b => b > y0 + 40 && b <= limit + 0.5);
  const y1 = Math.max(...ends);
  // smallest visible text inside the crop (HTML text and chart text)
  let small = 99, what = '';
  const inside = (r) => r.width > 0 && r.top + window.scrollY >= y0 - 1 && r.bottom + window.scrollY <= y1 + 1 && r.left >= x0 - 1 && r.right <= x1 + 1;
  main.querySelectorAll('*').forEach(e => {
    const own = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (!own || !inside(R(e))) return;
    const cs = getComputedStyle(e);
    if (cs.visibility === 'hidden' || cs.display === 'none') return;
    const fs = parseFloat(e.style.fontSize || cs.fontSize);
    if (fs < small) { small = fs; what = e.textContent.trim().slice(0, 30); }
  });
  return {x0, x1, y0, y1, small, what, cut: y1 < bottom(end) - 1};
}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="https://ghiris-a11y.github.io/capstone-nifty50-downside-risk/")
    ap.add_argument("--out", default=os.path.join(ROOT, "report", "figures", "dashboard"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    info, ok = {}, True
    with sync_playwright() as p:
        br = p.chromium.launch(channel="msedge")
        page = br.new_page(viewport={"width": VIEW_W, "height": 900}, device_scale_factor=4)
        for name, frag, pick in ANCHORS:
            page.goto(a.url + frag, wait_until="load")
            page.wait_for_function("!document.body.innerText.includes('Loading')", timeout=90000)
            page.wait_for_timeout(3500)
            b = page.evaluate(JS_BOX, [pick, MAX_CM.get(name, MAX_IMG_CM), PRINT_CM, PAD])
            clip = dict(x=b["x0"] - PAD, y=b["y0"] - PAD, width=b["x1"] - b["x0"] + 2 * PAD, height=b["y1"] - b["y0"] + 2 * PAD)
            page.screenshot(path=os.path.join(a.out, f"app_{name}.png"), clip=clip, full_page=True)
            px_per_cm = clip["width"] / PRINT_CM
            pt = b["small"] / px_per_cm / 0.03528
            info[name] = dict(css_w=round(clip["width"]), css_h=round(clip["height"]), print_w_cm=PRINT_CM,
                              print_h_cm=round(clip["height"] / px_per_cm, 1), smallest_px=b["small"], smallest_text=b["what"],
                              smallest_pt=round(pt, 1), cut_before_end=b["cut"])
            ok &= pt >= 10
            print(name, info[name], flush=True)
        br.close()
    # stack the two Daily example pieces into one image: banner, dashed break, table top (fits the page budget)
    from PIL import Image, ImageDraw
    top_im = Image.open(os.path.join(a.out, "app_live_banner.png")).convert("RGB")
    tab_im = Image.open(os.path.join(a.out, "app_live_tabletop.png")).convert("RGB")
    gap = 24 * 4
    max_h = int(MAX_IMG_CM * tab_im.width / PRINT_CM)
    tab_im = tab_im.crop((0, 0, tab_im.width, min(tab_im.height, max_h - top_im.height - gap)))
    out = Image.new("RGB", (max(top_im.width, tab_im.width), top_im.height + gap + tab_im.height), "white")
    out.paste(top_im, (0, 0)); out.paste(tab_im, (0, top_im.height + gap))
    dr = ImageDraw.Draw(out)
    for x in range(0, out.width, 40):
        dr.line([(x, top_im.height + gap // 2), (x + 20, top_im.height + gap // 2)], fill=(150, 150, 150), width=4)
    out.save(os.path.join(a.out, "app_live_table.png"), dpi=(300, 300))
    info["live_table"] = dict(stacked=["live_banner", "live_tabletop"], print_h_cm=round(out.height / (out.width / PRINT_CM), 1))
    json.dump(info, open(os.path.join(a.out, "app_sizes.json"), "w"), indent=1)
    print("all smallest text at least 10 pt" if ok else "SOME TEXT BELOW 10 PT: crop tighter")


if __name__ == "__main__":
    main()
