# PROGRESS

Last updated: 2026-11-22 (analysis-first report, actionable dashboard, P10 QA). Read this file, CLAUDE.md, PROJECT_PLAN.md and HANDOFF.md to resume in a fresh session.

## Status by phase (PROJECT_PLAN.md section 3)

| Phase | Prompts | Status |
|---|---|---|
| A Pilot and approval | P0, P1 | Pilot done. Guide approval of the results is still pending: the dashboard banner says "Draft results". |
| B Data, frozen snapshot, Action | P2, P3 | Done. 41-stock panel; `data/frozen/` hashed and untouched since P2; daily Action runs on weekdays at 13:30 UTC. |
| C Full run | P4 | Done for 5 labelled market-data sets (price, VIX level, VIX relative, USD/INR changes, both). Interest rates not run, because `data/raw/repo_rate.csv` is not fully verified (Path B). CPI and IIP are excluded by design. |
| D Figures, dashboard, chapters | P5-P8 | Done. Dashboard: https://ghiris-a11y.github.io/capstone-nifty50-downside-risk/ (redesign plus "What a firm should do" cards; mobile-checked in Chromium and WebKit at 360-480 px and in landscape; Flesch-Kincaid grade 3.0-4.0). |
| E Assembly and QA | P9, P10 | Done. `report/Phase2_Report.docx` and `.pdf`: 73 pages, local only (ITM logo). `QA_report.md` is clean. |

## Report build (in order; use `.venv\Scripts\python.exe`)
1. `src/report_numbers.py`: 373 numbers and 23 tables, logged in `outputs/tables/report/report_numbers.csv`.
2. `src/make_report_visuals.py`
3. `src/report_screens.py`: Appendix G, from the live site, 480 px, device scale 4. It logs the smallest printed text (10.8-16.3 pt) to `report/figures/dashboard/app_sizes.json`.
4. `src/build_report.py`: DOCX and `report/qa_phase2.md`.
5. `src/export_pdf.py`
6. `src/report_pages.py --pages 40,47,50,68,69,70,71,72,73`

Pages: front matter 8; chapters 1-9: 65.
- Chapters 5-6: 31 pages, 48% of chapters 1-9, or 61% of chapters 1-7.
- Chapters 1-3: 12 pages, 18% of chapters 1-9.

## Checks
- `python -m pytest -q`: 25 passed.
- `python nifty50_var_pipeline.py --demo`: exit 0.
- `python src/design_review.py --url <live site>`: overflow, clipping, chart drawing, legends, annotations, tap targets of 40 px, body text of 14 px and chart text of 11 px, plus the menu drawer.
- `python src/dashboard_check.py --url ...`: Flesch-Kincaid grade per tab.
- `python src/qa_final.py --rerun-dir <2-ticker rerun>`: writes `QA_report.md`.

## Log
- 2026-11-19: plain-language dashboard (6c38c94).
- 2026-11-21: Phase 2 report (ee738f0); retry added to the deploy step (1286f40).
- 2026-11-22:
  - RBI and Ali & Dembo references (e1ade21); `repo_rate.csv` prefilled, UNVERIFIED (64cf944).
  - Macro guard (e4c1059).
  - Dashboard redesign (a427bcc).
- 2026-11-22, this session:
  - **Path B scope.** The banner keeps only the approval note. The macro note is written by the export script as a grey info line. The report says "market data only; CPI and IIP excluded by design" (e316721).
  - **Start here:** "What a firm should do" cards. **Mobile:** review in Chromium and WebKit, with fixes (6e51b84).
  - **Report Step 5:**
    - Chapter 5: meaning paragraphs after every table and figure, Basel coverage, the DM caveat, and a findings table.
    - Chapter 6: the ML verdict, the stress cushion (x2.75) and the India VIX alert (a high VIX did not predict breaches), sector floors, money set aside per Rs 100 crore, the 30/60/90-day plan, risks (9786f71), and a monitoring scorecard (ce3fd7b).
  - **Report Step 6:** Phase 1 changes table, no-shuffling wording, Kupiec and Christoffersen citations, cover, Figma credit (0781c58).
  - **Step 7:** the Figure 14 label moved above the plot; Tailwind breakpoint order fixed; new Appendix G screenshots (6f288c3).
  - **P10 QA (3b0de80):**
    - the 2-ticker rerun matches (backtest and regime files byte-identical; daily and DM files within 1e-16; no decision changes);
    - manifest hashes match; no ticker has fewer than 500 test days and no fit failed.

## Open items (need the user)
1. **Interest rates.** Verify `data/raw/repo_rate.csv` row by row and fill the 13 blank rows, then set every status to VERIFIED.
   - Only then run Path A (one extra labelled set, `price_vixrel_fxchg_repo`). That needs your go-ahead, because it adds results.
2. **Guide approval** of the results and of the cover designation "HoD BTech" (marked "pending guide confirmation").
3. **Figma licences:** not checked on the Community pages. The credit says so.
4. **Scheduled Action:**
   - the last scheduled run (20 Nov) failed at deploy because of the GitHub artifact API; the deploy retry has been in place since 21 Nov;
   - Monday's run (23 Nov) will be the first scheduled test of the retry.
   - The Node 20 deprecation warning is harmless for now.

## Next phases
1. Final proofread with the guide's comments; viva preparation (PROJECT_PLAN.md section 7); submit the PDF.
2. Optional, after the repo-rate file is verified: Path A run and the post-hike view per model.
