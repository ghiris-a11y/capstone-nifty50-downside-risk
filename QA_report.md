# QA report (P10 final QA)

Run on 2026-11-22 14:22 by src/qa_final.py.

## 1. Tests

- pytest -q: 25 passed, 14 warnings in 13.48s
- python nifty50_var_pipeline.py --demo: exit code 0

## 2. Frozen snapshot

- Manifest: 44 files, snapshot 2026-11-18 10:07 UTC; SHA-256 mismatches: none.
- Commits that touched data/frozen: 2: 5aca39b 2026-11-18 P2 frozen 41-stock panel, P3 daily GitHub Action, P4 parallel resumable pipeline; ae8071c 2026-11-18 Scaffold project structure (P0): folders, pinned requirements, README, smoke tests
- Uncommitted changes in data/frozen: none.

## 3. Exact-match rerun (2 tickers, label price, from data/frozen)

Command: `python nifty50_var_pipeline.py --tickers RELIANCE.NS,INFY.NS --features price --label price --frozen --test-end 2026-11-18 --out-dir <scratch> --n-jobs 2` (same settings as the logged run in data/logs/run_test_rerun.log; results written outside outputs/).

| File | Byte-identical | Largest numeric difference | Text columns identical | Significance decisions changed |
|---|---|---|---|---|
| INFY.NS__backtest.csv | yes | 0.0e+00 | yes |  |
| INFY.NS__daily.parquet | no | 2.8e-17 | yes |  |
| INFY.NS__dm.csv | no | 2.2e-16 | yes | 0 |
| INFY.NS__dm_pinball.csv | no | 4.4e-16 | yes | 0 |
| INFY.NS__regime.csv | yes | 0.0e+00 | yes |  |
| RELIANCE.NS__backtest.csv | yes | 0.0e+00 | yes |  |
| RELIANCE.NS__daily.parquet | no | 2.1e-17 | yes |  |
| RELIANCE.NS__dm.csv | no | 2.2e-16 | yes | 0 |
| RELIANCE.NS__dm_pinball.csv | no | 2.8e-16 | yes | 0 |
| RELIANCE.NS__regime.csv | yes | 0.0e+00 | yes |  |

Backtest and regime files (breaches, coverage tests, Basel shares, FZ0 by regime) are byte-identical. Daily VaR/ES and Diebold-Mariano files differ only by floating-point rounding (at most a few times 1e-16), with no change in any breach or any 5% decision.

- data/logs/macro_skipped.log: 2 line(s); last: `2026-11-22 14:12:13.561123 skipped data\raw\repo_rate.csv: blank or unverified rows`. The unverified repo-rate file was skipped for each rerun ticker, as designed; no reported result uses it.

## 4. Tickers and fits

- Test days per ticker: 708 to 710; tickers with fewer than 500: none.
- Stock-days with a missing or non-finite VaR in the reported (price) results: 0.
- Failed tickers in the logged test-window runs: 41 merged, 0 failed, 41 merged, 0 failed, 41 merged, 0 failed, 41 merged, 0 failed, 41 merged, 0 failed, 1 merged, 0 failed, 1 merged, 0 failed.

## 5. GitHub Action

- Last scheduled run: 44820066066 on 2026-11-20T21:24:39Z: failure.
- Last push run: 45003956887 on 2026-11-22T08:41:09Z: success.
- Failing job `deploy`, step(s) ['Deploy to GitHub Pages']. Log lines: `Error: No artifacts named "github-pages" were found for this workflow run. Ensure artifacts are uploaded with actions/upload-artifact@v4 or later.` / `Error: No artifacts named "github-pages" were found for this workflow run. Ensure artifacts are uploaded with actions/upload-artifact@v4 or later.` / `Fetching artifact metadata failed. Is githubstatus.com reporting issues with API requests, Pages, or Actions? Please re-run the deployment at a later time.`
- Cause and fix: GitHub's artifact service failed briefly after a successful update and upload (the update job passed). Fix already in place: .github/workflows/daily_update.yml retries the deploy once after 90 s (commit 1286f40, after this run). Every push deploy since then has succeeded; the next scheduled run (Monday) will confirm the retry path.

## 6. Numbers and references

- outputs/tables/report/report_numbers.csv: 373 numbers, 0 without a source file.
- Report build QA (report/qa_phase2.md): Placeholders filled: 162 distinct numbers, each traced to a file in outputs/ (outputs/tables/report/report_numbers.csv); Unresolved placeholders: none; [FILL] / [UNVERIFIED] markers in printed text: none; Figures or tables never referenced in the text: none; Missing image files: none
- References in Chapter 8: 29 entries (20 with a DOI); [UNVERIFIED] markers in the reference list: 0. Verification log: report/chapters/sources.md.

## 7. Template

- Certificate page: none; acknowledgement page: none.

