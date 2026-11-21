# PROGRESS

Last updated: 2026-11-21. Read this file to resume work in a fresh session.

## Done
- P1-P4: pipeline, frozen snapshot, test-window rerun (41 stocks x 5 feature sets), first_results.md.
- P5 figures, P6 dashboard on GitHub Pages: https://ghiris-a11y.github.io/capstone-nifty50-downside-risk/
- Dashboard plain-language rewrite (commit 6c38c94). Label list: `frontend/LABEL_CHANGES.md`. Readability: Flesch-Kincaid grade 2.9-4.1 per tab (`src/dashboard_check.py`).
- Phase 2 report (commit a0436d3):
  - chapter sources in `report/chapters/`; numbers come from `src/report_numbers.py` and are logged in `outputs/tables/report/report_numbers.csv`
  - build: `python src/report_numbers.py`, `python src/make_report_visuals.py`, `python src/build_report.py`, `python src/export_pdf.py`, `python src/report_pages.py --pages 37,48,61`
  - outputs: `report/Phase2_Report.docx` and `.pdf` (62 pages). These stay local and are git-ignored because they carry the ITM logo.
  - QA: `report/qa_phase2.md`, `report/page_check.md`
- 2026-11-21: the daily Action's deploy failed on a temporary GitHub artifact-API error ("Fetching artifact metadata failed"); the update job and upload were fine. Added one automatic deploy retry after 90 s to `.github/workflows/daily_update.yml`.

## Open items (need the user)
- Dashboard screenshots in Appendix G print small (about 6-7 pt text). Option: re-capture zoomed crops.
- Citations: RBI primary statement for the 7 Oct 2026 repo hike (currently SCC Online); Ali & Dembo (2025); the [UNVERIFIED] papers in `report/chapters/sources.md` stay uncited until links are supplied.
- Guide designation on the cover is "HoD BTech" (copied from Phase 1); confirm.
- Node 20 deprecation warning on actions/configure-pages@v5 and deploy-pages@v4: harmless for now; upgrade once GitHub publishes Node 24 versions.

## Next phase (not started)
- P10 QA: exact-match rerun on 2 tickers, check the manifest hashes in `data/frozen/`, write QA_report.md.
