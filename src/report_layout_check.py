"""Layout checks on the built report (run after src/export_pdf.py).

1. Page fill: share of the usable page height that carries content; pages under 40% are listed (chapter ends, the
   cover and front matter are marked, as they may be short by design).
2. Split words in tables: every word of every table cell in the DOCX must appear unbroken in the PDF text. A word that
   Word broke across two lines shows up only as fragments; any such word fails the check (exit code 1).
3. Links: clickable link annotations in the PDF that point to the live dashboard and to GitHub.

  python src/report_layout_check.py   -> report/layout_check.md
"""
import os
import re
import sys

import fitz
from docx import Document

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, "report", "Phase2_Report.pdf")
DOCX = os.path.join(ROOT, "report", "Phase2_Report.docx")
DASH = "https://ghiris-a11y.github.io/capstone-nifty50-downside-risk/"


def page_fill(page):
    h = page.rect.height
    top, bottom = 2.3 / 2.54 * 72, h - 2.3 / 2.54 * 72
    ys = []
    for b in page.get_text("dict")["blocks"]:
        x0, y0, x1, y1 = b["bbox"]
        if y0 > bottom - 2:   # footer (page number)
            continue
        if b.get("type") == 0 and not "".join(s["text"] for l in b["lines"] for s in l["spans"]).strip():
            continue
        ys.append((y0, y1))
    for img in page.get_image_info():
        ys.append((img["bbox"][1], img["bbox"][3]))
    for d in page.get_drawings():   # table borders and shading
        r = d["rect"]
        if r.y1 < bottom - 2 and r.height < h * 0.9:
            ys.append((r.y0, r.y1))
    if not ys:
        return 0.0
    used = max(y1 for _, y1 in ys) - top
    return max(0.0, min(1.0, used / (bottom - top)))


def main():
    doc = fitz.open(PDF)
    lines = ["# Report layout check", ""]
    # 1 fill
    starts = set()
    for i, p in enumerate(doc):
        head = " ".join(p.get_text().split())[:200]
        if re.search(r"^(\d+ )?CHAPTER \d+:", head) and "TABLE OF CONTENTS" not in head and "LIST OF" not in head:
            starts.add(i)
    low = []
    for i, p in enumerate(doc):
        f = page_fill(p)
        if f < 0.40:
            note = "cover" if i == 0 else "front matter" if i < min(starts or {0}) else "chapter end" if (i + 1) in starts or i == len(doc) - 1 else "CHECK"
            low.append((i + 1, round(100 * f), note))
    lines += ["## Pages under 40% filled", "", "| Page | Fill | Note |", "|---|---|---|"] + [f"| {a} | {b}% | {c} |" for a, b, c in low] + [""]
    # 2 split words in tables
    pdf_words = set()
    for p in doc:
        for w in p.get_text("words"):
            pdf_words.add(w[4])
    pdf_text = " ".join(" ".join(p.get_text().split()) for p in doc)
    d = Document(DOCX)
    split = []
    for ti, t in enumerate(d.tables):
        if len(t.columns) < 2:   # 'What this means' boxes are prose: a break at a hyphen there is normal
            continue
        for row in t.rows:
            for c in row.cells:
                for tok in re.findall(r"[^\s/]+", c.text.replace("‑", "-")):
                    tok = tok.strip(".,;:()\"'")
                    if len(tok) < 3:
                        continue
                    if tok in pdf_words or any(tok in w for w in pdf_words):
                        continue
                    alt = tok.replace("-", "‑")
                    if alt in pdf_text or tok in pdf_text:
                        continue
                    split.append((ti + 1, tok))
    split = sorted(set(split))
    lines += [f"## Words split across lines in tables: {len(split)}", ""] + [f"- table {a}: `{b}`" for a, b in split[:40]] + [""]
    # 3 links
    links = [(i + 1, l.get("uri", "")) for i, p in enumerate(doc) for l in p.get_links() if l.get("uri")]
    dash = [pg for pg, u in links if u.startswith(DASH)]
    gh = [pg for pg, u in links if "github.com/ghiris-a11y" in u]
    lines += ["## Clickable links in the PDF", "", f"- Dashboard link on pages: {dash or 'none'}", f"- GitHub links on pages: {gh or 'none'}",
              f"- All link annotations: {len(links)}", ""]
    open(os.path.join(ROOT, "report", "layout_check.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(1 if split else 0)


if __name__ == "__main__":
    main()
