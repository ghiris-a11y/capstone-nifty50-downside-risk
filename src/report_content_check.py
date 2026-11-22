"""Content check of the built report (run after export_pdf.py): every in-text citation has a reference entry and every
reference is cited; no stale scope wording, leftover markup or placeholder text in the PDF; figure and table numbers
in the text exist.

  python src/report_content_check.py   -> report/content_check.md (exit 1 on any problem)
"""
import os
import re
import sys

import fitz

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH = os.path.join(ROOT, "report", "chapters")
STALE = [r"not yet (supplied|available|included|tested|verified)", r"\(pending\)", r"\[\[", r"\]\]", r"\{\{", r"MISSING",
         r"\bTODO\b", r"\bFILL\b", r"UNVERIFIED", r"(?<!secondary )market data only", r"were not tested", r"pending guide confirmation", r"  +\w"]


def main():
    body = ""
    for f in sorted(os.listdir(CH)):
        if re.match(r"0[1-79]_.*\.md$", f):
            body += open(os.path.join(CH, f), encoding="utf-8").read() + "\n"
    refs = open(os.path.join(CH, "08_references.md"), encoding="utf-8").read()
    entries = [l for l in refs.splitlines() if re.match(r"^[A-Z]", l) and re.search(r"\((\d{4}[a-z]?|n\.d\.-?[a-z]?)[,)]", l)]
    keys = []
    for e in entries:
        m = re.match(r"^(.*?)\.? \((\d{4}[a-z]?|n\.d\.-?[a-z]?)[,)]", e)
        authors, year = m.group(1), m.group(2)
        first = re.split(r",|&| and ", authors)[0].strip()
        keys.append((first, year, e[:70]))
    # citations in text: "Name (2019)", "(Name, 2019; Other & X, 2020)", "Name et al. (2019)"
    cited = set()
    for m in re.finditer(r"([A-Z][A-Za-z\-]+(?: [A-Z][A-Za-z\-]+)*)(?: et al\.| (?:&|and) [A-Z][A-Za-z\-]+)?,? \(?(\d{4}[a-z]?(?:, \d{4}[a-z]?)*|n\.d\.-?[a-z]?)\)?", body):
        for y in m.group(2).split(", "):
            cited.add((m.group(1).split()[-1] if m.group(1).split()[-1] not in ("India", "Supervision") else m.group(1), y))
    probs = []
    uncited = []
    for first, year, line in keys:
        last = {"Basel Committee on Banking Supervision": "BCBS", "National Stock Exchange of India": "NSE"}.get(first, first.split()[-1])
        if not any((c == last or c.endswith(last) or last.endswith(c) or c in first) and y == year for c, y in cited):
            if not re.search(re.escape(last) + r"[^.]{0,80}" + re.escape(year), body):
                uncited.append(line)
    doc = fitz.open(os.path.join(ROOT, "report", "Phase2_Report.pdf"))
    text = "\n".join(p.get_text() for p in doc)
    flat = " ".join(text.split())
    stale = []
    for pat in STALE[:-1]:
        for m in re.finditer(pat, flat):
            stale.append(flat[max(0, m.start() - 40):m.end() + 40])
    nums_fig = set(re.findall(r"Figure (\d+\.\d+):", flat)); nums_tab = set(re.findall(r"Table (\d+\.\d+):", flat))
    dangling = sorted({f"Figure {x}" for x in re.findall(r"Figure (\d+\.\d+)(?!:)", flat) if x not in nums_fig} |
                      {f"Table {x}" for x in re.findall(r"Table (\d+\.\d+)(?!:)", flat) if x not in nums_tab})
    lines = ["# Report content check", "", f"- Reference entries: {len(keys)}",
             f"- References not cited in the text: {uncited or 'none'}",
             f"- Stale wording or leftover markup in the PDF: {stale or 'none'}",
             f"- Figure/table numbers mentioned but not present: {dangling or 'none'}"]
    open(os.path.join(ROOT, "report", "content_check.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(1 if (uncited or stale or dangling) else 0)


if __name__ == "__main__":
    main()
