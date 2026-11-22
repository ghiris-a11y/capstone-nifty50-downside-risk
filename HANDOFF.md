# HANDOFF

Short guide for whoever picks this project up next (a person or a fresh Claude Code session). Detailed rules are in CLAUDE.md; the phase plan is in PROJECT_PLAN.md; the running log is in PROGRESS.md.

## 1. What the project is
MBA Business Analytics capstone (ITM Skills University; guide Dr. Aarti Pardeshi; student Ghiri S).
- Compares GARCH, EGARCH and GJR-GARCH (Normal and Student-t) with XGBoost, Random Forest and MLP.
- Measures one-day 95% and 99% VaR and ES on a balanced panel of 41 Nifty 50 stocks.
- Test window: 1 January 2024 to 17 November 2026.

## 2. Where things are
- Pipeline: `nifty50_var_pipeline.py`. Frozen data: `data/frozen/` (hashed, read-only).
- Results: `outputs/tables/`. Report numbers: `outputs/tables/report/report_numbers.csv`.
- Report sources: `report/chapters/*.md`. Build scripts are in `src/` (order in PROGRESS.md).
- Output: `report/Phase2_Report.docx` and `.pdf`, local only because they carry the ITM logo.
- Dashboard: `frontend/` (React and Vite), live at https://ghiris-a11y.github.io/capstone-nifty50-downside-risk/.
- Daily update: `.github/workflows/daily_update.yml` (weekdays at 13:30 UTC; writes only `data/live/`, `data/logs/` and `outputs/live/`).

## 3. How to rebuild
- Report: run the six steps listed in PROGRESS.md.
- Dashboard data: `python src/export_dashboard_json.py`.
- Dashboard: `cd frontend; npm ci; npm run build`.
- Checks: `python -m pytest -q`; `python nifty50_var_pipeline.py --demo`; `python src/design_review.py`; `python src/dashboard_check.py`; `python src/qa_final.py`.

## 4. Rules that matter most
- No number is typed by hand: every number comes from `outputs/` or `data/frozen/` through `src/report_numbers.py` or the dashboard JSON.
- `data/frozen/` is never overwritten.
- Macro files are used only when every row is filled and VERIFIED; `load_macro` skips them otherwise and logs the skip to `data/logs/macro_skipped.log`.
- Wording: "closest to expected", never "wins"; "the machine-learning models we tested".

## 5. Main results (from outputs/; see Chapter 5)
- The Student-t GARCH models came closest to the 1% breach rate at 99%.
- The machine-learning models we tested were breached more often.
- Most Diebold-Mariano gaps were not significant; where they were, almost all favoured GARCH.
- Breaches cluster on market-wide stress days.
- H1 to H3 are rejected. H4 is rejected for India VIX; interest rates, CPI and IIP are outside the scope.

## 6. Known limits
- About 710 test days per stock; survivorship in the balanced panel; Yahoo Finance data.
- Only 28 trading days after the 7 October 2026 repo hike.
- Basel shares cover two 250-day blocks per stock, ending 9 January 2026.

## 7. Status (2026-11-22)

**Done**
- Phases A to E of PROJECT_PLAN.md, including P10 final QA (`QA_report.md`, all checks clean).
- The report has 73 pages:
  - Chapters 5-6 are 31 pages: 48% of chapters 1-9, or 61% of chapters 1-7.
  - Chapters 1-3 are 12 pages (18%).
  - Every number is traced, with no unresolved placeholders and no [FILL] or [UNVERIFIED] in the printed text.
- The dashboard is live, with "What a firm should do" cards, mobile checks passing in Chromium and WebKit, and Flesch-Kincaid grade 4.0 or below on every tab.

**Scope decision (Path B)**
- `data/raw/repo_rate.csv` has 13 blank rows and every row is UNVERIFIED, so no interest-rate run was made.
- The dashboard and report say "market data only; price rises and factory output left out on purpose".

**Waiting on the student or the guide**
1. Verify and complete `repo_rate.csv`. After that, Path A (one extra labelled set, `price_vixrel_fxchg_repo`) can be run with the student's go-ahead.
2. Guide approval of the results and of the cover designation ("HoD BTech", marked "pending guide confirmation").
3. Confirm the Figma Community licences (not checked; the credit says so).
4. The scheduled Action of 20 Nov failed at deploy (GitHub artifact API). The retry fix has been in place since 21 Nov; check that Monday's scheduled run succeeds.

**Next**
- Final proofread with the guide's comments, viva preparation (PROJECT_PLAN.md section 7), then submit the PDF.
