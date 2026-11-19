"""Dashboard readability and layout check (Playwright + textstat).

For every tab it collects the text a reader sees on the main screen (expert sections, tables, charts and the small
"Technical term" lines are excluded), computes the Flesch-Kincaid grade, lists sentences above grade 9, checks for
horizontal overflow at phone (390x844), laptop (1600x900) and projector (1920x1080) widths, records console errors,
and saves screenshots. Uses the installed Microsoft Edge (channel="msedge"), so no browser download is needed.

  python src/dashboard_check.py --url http://localhost:4173/capstone-nifty50-downside-risk/ --out outputs/dashboard_check
  python src/dashboard_check.py --screens-only --out report/figures/dashboard   (1600x900 screenshots for the report)
"""
import argparse
import json
import os
import re

import textstat
from playwright.sync_api import sync_playwright

TABS = [("start", "#/"), ("overview", "#/overview"), ("models", "#/models"), ("regimes", "#/regimes"), ("stock", "#/stock"),
        ("features", "#/features"), ("live", "#/live"), ("glossary", "#/glossary"), ("about", "#/about")]
SIZES = {"phone": (390, 844), "laptop": (1600, 900), "projector": (1920, 1080)}

JS_TEXT = r"""() => {
  const main = document.querySelector('main').cloneNode(true);
  main.querySelectorAll('details, table, .js-plotly-plot, select, svg, .text-xs, button').forEach(e => e.remove());
  const blocks = [];
  main.querySelectorAll('h2, h3, p, li, dt, dd, label, .text-lg').forEach(e => {
    if (e.querySelector('p, li, h3')) return;   // leaf text blocks only
    const t = e.innerText.replace(/\s+/g, ' ').trim();
    if (t) blocks.push(t);
  });
  const header = document.querySelector('header p').innerText;
  return [header, ...new Set(blocks)];
}"""


def sentences(blocks):
    out = []
    for b in blocks:
        b = b if re.search(r"[.!?]$", b) else b + "."
        out += [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9“])", b) if s.strip()]
    return out


def wait_ready(page):
    page.wait_for_load_state("networkidle")
    page.wait_for_function("!document.body.innerText.includes('Loading')", timeout=60000)
    page.wait_for_timeout(1500)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:4173/capstone-nifty50-downside-risk/")
    ap.add_argument("--out", default="outputs/dashboard_check")
    ap.add_argument("--screens-only", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    report = {"url": a.url, "tabs": {}}
    with sync_playwright() as p:
        br = p.chromium.launch(channel="msedge")
        sizes = {"laptop": SIZES["laptop"]} if a.screens_only else SIZES
        for size, (w, h) in sizes.items():
            page = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=2 if a.screens_only else 1)
            errors = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            for name, frag in TABS:
                page.goto(a.url + frag)
                wait_ready(page)
                over = page.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")
                if a.screens_only:
                    page.screenshot(path=os.path.join(a.out, f"{name}.png"))
                    continue
                page.screenshot(path=os.path.join(a.out, f"{size}_{name}.png"), full_page=size == "phone")
                tab = report["tabs"].setdefault(name, {})
                tab[f"overflow_px_{size}"] = over
                if size == "laptop":
                    blocks = page.evaluate(JS_TEXT)
                    text = " ".join(sentences(blocks))
                    tab["fk_grade"] = round(textstat.flesch_kincaid_grade(text), 1)
                    tab["flesch_reading_ease"] = round(textstat.flesch_reading_ease(text), 1)
                    tab["words"] = textstat.lexicon_count(text)
                    tab["above_9"] = [s for s in sentences(blocks)
                                      if textstat.lexicon_count(s) >= 6 and textstat.flesch_kincaid_grade(s) > 9]
                tab.setdefault("console_errors", [])
                tab["console_errors"] += [e for e in errors if e not in tab["console_errors"]]
                errors.clear()
            page.close()
        br.close()
    if not a.screens_only:
        all_text = []
        json.dump(report, open(os.path.join(a.out, "readability.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        for k, v in report["tabs"].items():
            print(f"{k:10s} FK {v['fk_grade']:5} ease {v['flesch_reading_ease']:5} words {v['words']:4} "
                  f"overflow phone/laptop/projector {v['overflow_px_phone']}/{v['overflow_px_laptop']}/{v['overflow_px_projector']} "
                  f"errors {len(v['console_errors'])} above9 {len(v['above_9'])}")
            for s in v["above_9"]:
                print("    >9:", s)
            for e in v["console_errors"]:
                print("    ERR:", e[:200])


if __name__ == "__main__":
    main()
