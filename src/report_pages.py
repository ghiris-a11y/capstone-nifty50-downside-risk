"""Page check for report/Phase2_Report.pdf: page count per chapter, figures and tables per chapter, and PNG previews of
chosen pages.

  python src/report_pages.py [--pages 31,52,70]   ->  report/page_check.md, report/page_previews/page_<n>.png
"""
import argparse
import json
import os
import re

import fitz

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, "report", "Phase2_Report.pdf")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="")
    a = ap.parse_args()
    doc = fitz.open(PDF)
    reg = json.load(open(os.path.join(ROOT, "report", "build_registry.json"), encoding="utf-8"))
    starts = {}
    for i, page in enumerate(doc):
        top = " ".join(page.get_text().split())[:120]
        m = re.search(r"CHAPTER (\d+):", top)
        if m and "TABLE OF CONTENTS" not in top and "LIST OF" not in top and int(m.group(1)) not in starts:
            # a chapter page starts with its heading (the contents pages list several chapters on one page)
            if len(re.findall(r"CHAPTER \d+:", page.get_text())) == 1:
                starts[int(m.group(1))] = i
    order = sorted(starts)
    rows, body = [], 0
    for k, ch in enumerate(order):
        end = starts[order[k + 1]] if k + 1 < len(order) else len(doc)
        n = end - starts[ch]
        body += n
        pc = reg["per_chapter"].get(str(ch), {})
        rows.append((ch, starts[ch] + 1, n, pc.get("figures", 0), pc.get("tables", 0)))
    front = starts[order[0]] if order else 0
    lines = ["# Phase 2 report: page check", "", f"Total pages: {len(doc)} (front matter: {front}, chapters 1-9: {body})", "",
             "| Chapter | Starts on PDF page | Pages | Share of chapter pages | Figures | Tables |", "|---|---|---|---|---|---|"]
    lines += [f"| {c} | {s} | {n} | {100 * n / body:.0f}% | {f} | {t} |" for c, s, n, f, t in rows]
    an = sum(n for c, s, n, f, t in rows if c in (5, 6))
    theory = sum(n for c, s, n, f, t in rows if c in (1, 2, 3))
    lines += ["", f"Chapters 5 and 6 (analysis and recommendations): {an} of {body} chapter pages ({100 * an / body:.0f}%); "
              f"Chapters 1-3 (theory and method): {theory} pages ({100 * theory / body:.0f}%)."]
    open(os.path.join(ROOT, "report", "page_check.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    if a.pages:
        out = os.path.join(ROOT, "report", "page_previews")
        os.makedirs(out, exist_ok=True)
        for p in [int(x) for x in a.pages.split(",")]:
            pix = doc[p - 1].get_pixmap(dpi=110)
            pix.save(os.path.join(out, f"page_{p}.png"))
            print("preview", p)


if __name__ == "__main__":
    main()
