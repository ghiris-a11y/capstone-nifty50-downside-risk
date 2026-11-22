"""Plain-English check of the report body text, per chapter: average and longest sentence (words), sentences over 30
words, Flesch reading ease, and banned jargon words. Placeholders are filled from src/report_numbers.py so numbers
count as words; tables, figure markup and headings are left out.

  python src/report_readability.py [--save before|after]   -> report/readability_<tag>.json and a printed table
"""
import argparse
import glob
import json
import os
import re
import sys

import textstat

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
BANNED = ["elicitab", "semiparametric", "heteroskedastic", "heteroscedastic", "operationalis", "operationaliz", "leverage"]


def body(text, N):
    out = []
    for line in text.split("\n"):
        s = line.strip()
        if not s or s.startswith(("#", "|", "[[FIG", "[[TABLE", "[[MDTABLE", "[[IMG", "[[LANDSCAPE", "[[PORTRAIT", "[[PAGEBREAK", "[[PHONES", "[[DESKTOP")):
            continue
        s = s.replace("[[MEANS]]", "").replace("[[SHOWS]]", "")
        s = re.sub(r"\{\{(fig|tab):[^}]+\}\}", "Figure 1", s)
        s = re.sub(r"\{\{([^}]+)\}\}", lambda m: N.get(m.group(1), ("0",))[0], s)
        s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1", s)   # links
        s = re.sub(r"https?://\S+", "link", s)
        s = re.sub(r"[*`]", "", s)
        s = re.sub(r"^(- |\d+\. )", "", s)
        if not re.search(r"[.!?]$", s):
            s += "."
        out.append(s)
    return " ".join(out)


def sentences(t):
    # split on sentence ends, but not inside numbers such as 0.88 or abbreviations like "e.g."
    return [s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9“\"(])", t) if s.strip()]


def stats(text):
    ss = sentences(text)
    lens = [len(s.split()) for s in ss]
    return dict(sentences=len(ss), avg_words=round(sum(lens) / max(len(lens), 1), 1), max_words=max(lens or [0]),
                over_30=sum(l > 30 for l in lens), reading_ease=round(textstat.flesch_reading_ease(text), 1),
                banned=[b for b in BANNED if b in text.lower()],
                longest=[s[:140] for s, l in sorted(zip(ss, lens), key=lambda x: -x[1]) if l > 30][:5])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", default="")
    a = ap.parse_args()
    from report_numbers import build
    N, _ = build()
    res = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "report", "chapters", "0[1-79]_*.md"))):
        ch = os.path.basename(f)[:2]
        res[ch] = stats(body(open(f, encoding="utf-8").read(), N))
    print(f"{'Ch':3} {'sent':>5} {'avg':>5} {'max':>4} {'>30':>4} {'ease':>6}  banned")
    for ch, r in res.items():
        print(f"{ch:3} {r['sentences']:5} {r['avg_words']:5} {r['max_words']:4} {r['over_30']:4} {r['reading_ease']:6}  {r['banned']}")
    if a.save:
        json.dump(res, open(os.path.join(ROOT, "report", f"readability_{a.save}.json"), "w", encoding="utf-8"), indent=1)
    return res


if __name__ == "__main__":
    main()
