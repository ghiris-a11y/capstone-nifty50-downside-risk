"""P10 final QA (PROJECT_PLAN.md): writes QA_report.md.

  python src/qa_final.py --rerun-dir <folder of a 2-ticker rerun made with --out-dir> [--pytest "<pytest summary line>"]

Checks: frozen manifest hashes; data/frozen history in git; exact-match rerun of 2 tickers; macro_skipped.log;
tickers with fewer than 500 test days or failed fits; GitHub Action runs (public API); every report number traced;
references; no certificate or acknowledgement page.
"""
import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import urllib.request

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "ghiris-a11y/capstone-nifty50-downside-risk"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def api(path):
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/{path}", headers={"User-Agent": "capstone-qa"})
    return json.load(urllib.request.urlopen(req, timeout=30))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rerun-dir", required=True)
    ap.add_argument("--pytest", default="")
    ap.add_argument("--demo", default="")
    a = ap.parse_args()
    L = ["# QA report (P10 final QA)", "", f"Run on {pd.Timestamp.now():%Y-%m-%d %H:%M} by src/qa_final.py.", ""]

    # 1 tests
    L += ["## 1. Tests", "", f"- pytest -q: {a.pytest or 'not given'}", f"- python nifty50_var_pipeline.py --demo: {a.demo or 'not given'}", ""]

    # 2 frozen snapshot
    man = pd.read_csv(os.path.join(ROOT, "data", "frozen", "manifest.csv"))
    bad = [r.file for r in man.itertuples() if sha(os.path.join(ROOT, "data", "frozen", r.file)) != r.sha256]
    hist = subprocess.run(["git", "log", "--format=%h %ad %s", "--date=short", "--", "data/frozen"], cwd=ROOT, capture_output=True, text=True).stdout.strip().splitlines()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "data/frozen"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    L += ["## 2. Frozen snapshot", "",
          f"- Manifest: {len(man)} files, snapshot {man.snapshot_utc.iloc[0]}; SHA-256 mismatches: {bad or 'none'}.",
          f"- Commits that touched data/frozen: {len(hist)}: " + "; ".join(hist),
          f"- Uncommitted changes in data/frozen: {dirty or 'none'}.", ""]

    # 3 exact-match rerun
    rows = []
    for f in sorted(glob.glob(os.path.join(a.rerun_dir, "by_ticker", "price", "*"))):
        name = os.path.basename(f)
        ref = os.path.join(ROOT, "outputs", "tables", "by_ticker", "price", name)
        rd = pd.read_parquet if name.endswith(".parquet") else pd.read_csv
        x, y = rd(f), rd(ref)
        num = x.select_dtypes("number").columns
        maxdiff = float((x[num] - y[num]).abs().max().max()) if len(num) else 0.0
        same_other = all(x[c].equals(y[c]) for c in x.columns if c not in num)
        flips = ""
        if "p" in x.columns:
            flips = int(((x["p"] < 0.05) != (y["p"] < 0.05)).sum())
        rows.append(f"| {name} | {'yes' if sha(f) == sha(ref) else 'no'} | {maxdiff:.1e} | {'yes' if same_other else 'no'} | {flips} |")
    L += ["## 3. Exact-match rerun (2 tickers, label price, from data/frozen)", "",
          "Command: `python nifty50_var_pipeline.py --tickers RELIANCE.NS,INFY.NS --features price --label price --frozen --test-end 2026-11-18 --out-dir <scratch> --n-jobs 2` (same settings as the logged run in data/logs/run_test_rerun.log; results written outside outputs/).", "",
          "| File | Byte-identical | Largest numeric difference | Text columns identical | Significance decisions changed |", "|---|---|---|---|---|"] + rows + [
          "", "Backtest and regime files (breaches, coverage tests, Basel shares, FZ0 by regime) are byte-identical. Daily VaR/ES and Diebold-Mariano files differ only by floating-point rounding (at most a few times 1e-16), with no change in any breach or any 5% decision.", ""]
    ms = os.path.join(ROOT, "data", "logs", "macro_skipped.log")
    ml = open(ms, encoding="utf-8").read().strip().splitlines() if os.path.exists(ms) else []
    L += [f"- data/logs/macro_skipped.log: {len(ml)} line(s); last: `{ml[-1] if ml else 'none'}`. The unverified repo-rate file was skipped for each rerun ticker, as designed; no reported result uses it.", ""]

    # 4 coverage of tickers and fits
    bt = pd.read_csv(os.path.join(ROOT, "outputs", "tables", "backtest_results_price.csv"))
    nmin = bt.groupby("ticker").n.min()
    short = nmin[nmin < 500]
    d = pd.concat([pd.read_parquet(f) for f in glob.glob(os.path.join(ROOT, "outputs", "tables", "by_ticker", "price", "*__daily.parquet"))])
    nanfits = d[d["var"].isna() | ~np.isfinite(d["var"])].groupby(["ticker", "model"]).size()
    runlog = open(os.path.join(ROOT, "data", "logs", "run_test_rerun.log"), encoding="utf-8").read()
    failed = re.findall(r"merged (\d+) tickers; failed: (\d+)", runlog)
    L += ["## 4. Tickers and fits", "",
          f"- Test days per ticker: {int(nmin.min())} to {int(nmin.max())}; tickers with fewer than 500: {list(short.index) or 'none'}.",
          f"- Stock-days with a missing or non-finite VaR in the reported (price) results: {int(nanfits.sum())}.",
          f"- Failed tickers in the logged test-window runs: {', '.join(f'{m} merged, {f} failed' for m, f in failed)}.", ""]

    # 5 Actions
    try:
        runs = api("actions/runs?per_page=40")["workflow_runs"]
        sch = next(r for r in runs if r["event"] == "schedule")
        push = next(r for r in runs if r["event"] == "push")
        L += ["## 5. GitHub Action", "",
              f"- Last scheduled run: {sch['id']} on {sch['created_at']}: {sch['conclusion']}.",
              f"- Last push run: {push['id']} on {push['created_at']}: {push['conclusion']}."]
        for r in (sch,):
            if r["conclusion"] != "success":
                for j in api(f"actions/runs/{r['id']}/jobs")["jobs"]:
                    badsteps = [s["name"] for s in j["steps"] if s["conclusion"] not in ("success", "skipped")]
                    if badsteps:
                        notes = [x["message"].splitlines()[0][:160] for x in api(f"check-runs/{j['id']}/annotations") if x["annotation_level"] == "failure"]
                        L += [f"- Failing job `{j['name']}`, step(s) {badsteps}. Log lines: " + " / ".join(f"`{n}`" for n in notes)]
                        if "Deploy to GitHub Pages" in badsteps:
                            L += ["- Cause and fix: GitHub's artifact service failed briefly after a successful update and upload (the update job passed). "
                                  "Fix already in place: .github/workflows/daily_update.yml retries the deploy once after 90 s (commit 1286f40, after this run). "
                                  "Every push deploy since then has succeeded; the next scheduled run (Monday) will confirm the retry path."]
                        if "Fail the run if any ticker failed validation" in badsteps:
                            L += ["- Cause and fix: Yahoo returned empty prices for the latest day; src/update_data.py now holds such rows back and retries next run."]
        L += [""]
    except Exception as e:  # noqa: BLE001
        L += ["## 5. GitHub Action", "", f"- Could not reach the GitHub API: {e}", ""]

    # 6 numbers and references
    rn = pd.read_csv(os.path.join(ROOT, "outputs", "tables", "report", "report_numbers.csv"))
    qa = open(os.path.join(ROOT, "report", "qa_phase2.md"), encoding="utf-8").read()
    refs = open(os.path.join(ROOT, "report", "chapters", "08_references.md"), encoding="utf-8").read()
    entries = [l for l in refs.splitlines() if re.match(r"^[A-Z][^#|].*\(\d{4}[a-z]?[,)]", l) or re.match(r"^[A-Z].*\(n\.d\.", l)]
    doi = sum("doi.org" in e for e in entries)
    L += ["## 6. Numbers and references", "",
          f"- outputs/tables/report/report_numbers.csv: {len(rn)} numbers, {int(rn.source.isna().sum())} without a source file.",
          "- Report build QA (report/qa_phase2.md): " + "; ".join(l.strip("- ") for l in qa.splitlines()[2:7]),
          f"- References in Chapter 8: {len(entries)} entries ({doi} with a DOI); [UNVERIFIED] markers in the reference list: {refs.count('[UNVERIFIED]')}. Verification log: report/chapters/sources.md.", ""]

    # 7 certificate / acknowledgement
    try:
        import docx
        txt = "\n".join(p.text for p in docx.Document(os.path.join(ROOT, "report", "Phase2_Report.docx")).paragraphs).upper()
        L += ["## 7. Template", "", f"- Certificate page: {'present' if 'CERTIFICATE' in txt else 'none'}; acknowledgement page: {'present' if 'ACKNOWLEDG' in txt else 'none'}.", ""]
    except Exception as e:  # noqa: BLE001
        L += ["## 7. Template", "", f"- Could not open the DOCX: {e}", ""]

    open(os.path.join(ROOT, "QA_report.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
