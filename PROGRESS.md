# PROGRESS

Last updated: 2026-11-22 (dashboard redesign). Read this file (and CLAUDE.md, PROJECT_PLAN.md) to resume work in a fresh session.

## Status by phase (PROJECT_PLAN.md section 3)

| Phase | Prompts | Status |
|---|---|---|
| A Pilot and approval | P0, P1 | Pilot done. Guide approval of the results is still pending: the dashboard banner says "Draft results". |
| B Data, frozen snapshot, Action | P2, P3 | Done. 41-stock panel; `data/frozen/` hashed; daily Action runs on weekdays at 13:30 UTC. |
| C Full run | P4 | Done for price, VIX and USD/INR feature sets (41 stocks x 5 labelled sets). **Macro set (repo, CPI, IIP) not run**: the files are not yet verified. |
| D Figures, dashboard, chapters | P5, P6, P7, P8 | Done. Dashboard: https://ghiris-a11y.github.io/capstone-nifty50-downside-risk/ (redesigned 2026-11-22: sidebar shell, Inter, story chart cards; plain-language labels unchanged, see `frontend/LABEL_CHANGES.md`; Flesch-Kincaid grade 3.2-4.0). |
| E Assembly and QA | P9, P10 | P9 done: `report/Phase2_Report.docx` and `.pdf`, 66 pages, local only (ITM logo). **P10 final QA not started.** |

## Report build (in order; use `.venv\Scripts\python.exe`)
1. `src/report_numbers.py` (every number, logged in `outputs/tables/report/report_numbers.csv`)
2. `src/make_report_visuals.py` (diagrams in `report/figures/`)
3. `src/report_screens.py` (Appendix G dashboard crops, from the live site)
4. `src/build_report.py` (DOCX and `report/qa_phase2.md`)
5. `src/export_pdf.py` (Word via pywin32; updates the contents lists; about 60 s)
6. `src/report_pages.py --pages 37,48,63` (`report/page_check.md` and previews in `report/page_previews/`)

QA on 2026-11-22: 142 numbers traced to `outputs/`; nothing unresolved; no [FILL] or [UNVERIFIED] in the printed text; every figure and table is referenced; pytest 22 passed; demo exit 0.
Pages: Chapters 5-6 have 27 of 58 chapter pages (47%); Chapters 1-3 have 11 (19%); Appendices 10.

## Log
- 2026-11-19: dashboard plain-language rewrite (6c38c94).
- 2026-11-21: Phase 2 report committed (ee738f0). Deploy retry added to the Action after GitHub's temporary artifact-API failure (1286f40); redeploy verified.
- 2026-11-22:
  - `data/raw/repo_rate.csv` prefilled from RBI releases (64cf944). All rows are UNVERIFIED; 15 rows have an RBI URL and value, 13 are blank with a note.
  - RBI (2026a, 2026b) cited for the 5.50% hike and the calibrated-tightening stance in Chapters 1 and 5, replacing SCC Online. Ali & Dembo (2025) cited in Chapter 2 as a non-peer-reviewed preprint. Data cut-off line added in Chapter 1: the next MPC meeting (2-4 Dec 2026) is after the cut-off (e1ade21).
  - Appendix G screenshots retaken (3929e9b): phone layout 480 px, device scale 2, one block per tab, printed at 14.6 cm, smallest text (11 px chart labels) at 10 pt, one figure per page with its box.

- 2026-11-22 (later):
  - `load_macro` now skips any macro file with blank or non-VERIFIED rows and logs it to `data/logs/macro_skipped.log` (e4c1059). Tests are in `tests/test_macro_guard.py` (25 tests pass).
  - Dashboard redesign (a427bcc). Layout ideas come from two Figma Community files; notes are in `design/figma_notes.md`. The reference PNGs are kept local and git-ignored.
  - Review screenshots at 1440 and 480 px: `python src/design_review.py` (needs `npm run preview` on port 4181) writes to `design/review/`.
  - Three flaws fixed: the phone axis title, the stress-days label, and the ideal line through the value labels.

## Open items (need the user)
1. **repo_rate.csv:** check each row against the RBI page and fill the 13 blank rows (Database on Indian Economy, or the RBI press releases). Then set status to VERIFIED.
   - Warning: the pipeline reads this file whenever it exists (`load_macro`). The template README says a partial file must not be used.
   - Do not run the macro feature set until every row is filled and verified.
   - CPI and IIP files are still missing (MoSPI).
2. **Guide approval** of the draft results, and of the cover designation "HoD BTech" (copied from Phase 1).
3. **[UNVERIFIED] papers** in `report/chapters/sources.md` stay uncited until links are supplied.
4. **Figma licences:** confirm the licence on each Community page (assumed CC BY 4.0; credited on the About tab and in the README).
   - Remaining minor chart crowding at phone width comes from the exported figures (Fig 2 stock names, Fig 4 and Fig 9 x labels).
   - **Appendix G screenshots** in the report show the old design. To refresh them, run `src/report_screens.py`, `src/build_report.py`, `src/export_pdf.py`, and check the crops: the crop start texts may need updating.
5. **Node 20 deprecation warning** on configure-pages@v5 and deploy-pages@v4: upgrade when Node 24 versions exist.

## Next phases
1. **P10 final QA** (no user input needed). Steps:
   - pytest;
   - exact-match rerun on 2 tickers from `data/frozen/`;
   - verify the manifest hashes and that `data/frozen/` is unchanged in git history;
   - check the Action's last run;
   - list tickers with fewer than 500 test days or failed fits;
   - confirm at least 10 verified references and no certificate or acknowledgement page;
   - write `QA_report.md`.
2. **Macro feature set**, once the repo, CPI and IIP files are verified.
   - Run the price+VIX+macro set on the test window; this adds results.
   - Update Chapter 5 sections 5.9-5.10 and H4 (currently "rejected for India VIX; macro not yet tested").
   - Needs the user's go-ahead because it changes the reported results.
3. **Final proofread and submission:**
   - the guide's comments;
   - the viva questions in PROJECT_PLAN.md section 7;
   - submit the PDF.
