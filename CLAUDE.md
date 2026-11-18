# CLAUDE.md — Capstone: Nifty 50 downside risk (GARCH vs ML)

Put this file in the project root. Claude Code reads it at the start of every session.

## Project in one paragraph
MBA Business Analytics capstone (ITM Skills University, guide Dr. Aarti Pardeshi). Compare GARCH / EGARCH / GJR-GARCH (Normal and Student-t) with XGBoost, Random Forest and MLP for one-day-ahead 95% and 99% VaR and Expected Shortfall on a fixed, balanced panel of 40–45 Nifty 50 stocks (full 2015–2026 history). Train 2015-2021, validation 2022-2023, test 2024-01-01 to 2026-11 (extended window includes the Oct 2026 RBI repo hike to 5.50%).

## Hard rules
1. NEVER invent, estimate or hard-code result numbers. Every number in a report, table or chart must come from a file in `outputs/`. If a file is missing, say so and stop.
2. Edit existing files with surgical, additive changes: exact replacement blocks only. No full-file rewrites. No renaming of existing variables, functions, column names or CSV headers unless I ask.
3. Features at day t may use information up to t-1 only. No shuffling, no random k-fold. Macro series use release lags.
4. Basel traffic-light zones apply to 99% VaR only.
5. Fixed seeds (42). Pin versions in requirements.txt. Never overwrite `data/frozen/`; it is a hashed snapshot used for all report numbers. The GitHub Action may write only to `data/live/`, `data/logs/` and `outputs/live/`.
6. Respect data-source terms: delay between requests, retry with backoff, log failures to `data/logs/`, never silently drop rows.
7. Do not fabricate references. If a citation cannot be verified, mark it `[UNVERIFIED]`.
8. After any change, run `pytest -q` and `python nifty50_var_pipeline.py --demo` before saying it works.

## Folder layout
```
capstone_nifty50_downside_risk/
  CLAUDE.md  PROJECT_PLAN.md  requirements.txt  README.md
  nifty50_var_pipeline.py          # main pipeline (do not rewrite)
  config/universe.csv              # final 40-45 tickers + sector + listing date
  data/raw/  data/frozen/  data/live/  data/processed/  data/logs/
  src/  (build_universe.py, download_history.py, validate_data.py, update_data.py, make_figures.py, export_dashboard_json.py)
  frontend/  (React + TS + Vite + Tailwind dashboard; public/data/*.json exported by src/export_dashboard_json.py)
  .github/workflows/daily_update.yml   # cron 13:30 UTC = 7:00 PM IST, Mon-Fri
  outputs/ (tables/, figures/, models/)
  report/ (template/, chapters/, figures/)
  tests/
```

## Conventions
- Python 3.10+, pandas, numpy, scipy, arch, xgboost, scikit-learn, plotly, kaleido, joblib, pyarrow, pytest.
- Colours: GARCH = red palette, ML = blue palette, warnings = amber. Colour-blind safe. Min font 10pt. Export PNG at 300 DPI plus interactive HTML.
- VaR and ES are positive loss numbers (0.025 = 2.5%).
- Tickers use Yahoo format: `RELIANCE.NS`, `HDFCBANK.NS`, `INFY.NS`; index `^NSEI`; VIX `^INDIAVIX`; FX `INR=X`.

## Report rules (teacher's Phase 2 template, same look as Phase 1)
- Order: Cover; 1 Introduction; 2 Literature Review; 3 Research Methodology; 4 Data Collection; 5 Data Analysis and Interpretation; 6 Recommendations; 7 Conclusion; 8 References (minimum 10, APA); 9 Appendices. No certificate, no acknowledgement.
- MBA Business Analytics capstone: weight pages towards analysis, interpretation and actionable business recommendations. Keep theory short.
- After every table or chart add a "What this means" paragraph in business language. Recommendations must follow from the data; if ML lost, say so.
- Appendix questionnaire: not applicable (secondary data); say so.
- Cover details: student Ghiri S, roll no. 021331025144 (Phase 1's cover printed 0211331025144, a typo), MBA Business Analytics, batch 2025-27, guide Dr. Aarti Pardeshi, ITM Skills University / ITM Business School, Kharghar, Navi Mumbai. Phase 2 semester: III unless I say otherwise.
- Dashboard: static React build on GitHub Pages, no backend; HashRouter, Vite base set to the repo name, relative './data/...' fetches.
- Format: Times New Roman, centred bold title page with ITM logo, page numbers bottom right, numbered figures and tables (Figure 5.1, Table 5.1).
