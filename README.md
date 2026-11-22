# Nifty 50 Downside Risk: GARCH vs Machine Learning

MBA Business Analytics capstone (ITM Skills University). It compares GARCH, EGARCH and GJR-GARCH models (Normal and Student-t) with XGBoost, Random Forest and MLP. Each model forecasts one-day-ahead 95% and 99% Value-at-Risk (VaR) and Expected Shortfall (ES) for a balanced panel of 40–45 Nifty 50 stocks from 2015 to 2026.

| Split | Period |
|---|---|
| Train | 2015 – 2021 |
| Validation | 2022 – 2023 |
| Test | 2024-01-01 – Nov 2026 (includes the 7 Oct 2026 RBI repo hike to 5.50%) |

Dashboard (planned, GitHub Pages): https://ghiris-a11y.github.io/capstone-nifty50-downside-risk/

Project rules are in [CLAUDE.md](CLAUDE.md). The phased work plan is in [PROJECT_PLAN.md](PROJECT_PLAN.md).

## Setup (Windows)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest -q
```

On macOS or Linux, activate with `source .venv/bin/activate`.

## Folder layout

```
config/            universe.csv (final tickers, sector, listing date)
data/raw/          downloaded source files (not committed)
data/frozen/       hashed snapshot used for all report numbers (never overwritten)
data/live/         daily feed written by the GitHub Action
data/processed/    intermediate files
data/logs/         download, validation and run logs
src/               data, figure and dashboard-export scripts
frontend/          React + TypeScript + Vite + Tailwind dashboard (GitHub Pages)
outputs/           tables/, figures/, models/ (models not committed), live/
report/            chapters/, figures/, template/ (template kept local only)
tests/             pytest suite
```

## Reproducibility

- Seeds are fixed at 42, and package versions are pinned in `requirements.txt`.
- All report numbers come from `data/frozen/`, which has SHA-256 hashes in its manifest.
- The live feed in `data/live/` only drives the dashboard's "Live risk" tab.

## Data pipeline (how the report numbers are produced)

```powershell
python src/build_universe.py --end 2026-11-18      # config/universe.csv (41 stocks) + universe_excluded.csv
python src/download_history.py --end 2026-11-18    # data/frozen/*.parquet + manifest.csv (read-only, never overwritten)
python src/validate_data.py                        # data/logs/validation_report.md
python nifty50_var_pipeline.py --tickers-file config/universe.csv --features price+vix `
       --test-end 2026-11-18 --frozen --n-jobs 8 --out-dir outputs/tables
```

The pipeline writes one result file per stock to `outputs/tables/by_ticker/<features>/` and skips stocks that
already have results, so an interrupted run resumes where it stopped (`--no-resume` forces a recompute).
The frozen parquet files are kept off GitHub (Yahoo terms); `data/frozen/manifest.csv` holds their SHA-256 hashes.
Macro data: see `data/raw/templates/README.md`.

## Daily live update (GitHub Action)

`.github/workflows/daily_update.yml` runs `src/update_data.py` at 13:30 UTC (7:00 PM IST) Monday to Friday. It
appends validated new prices to `data/live/prices_live.csv`, recomputes one-day 95%/99% VaR and ES per stock
(GJR-GARCH(1,1) Student-t, last 1,500 days) in `outputs/live/latest_risk.csv`, and commits `data/live/`,
`data/logs/` and `outputs/live/` back to the repository. It never touches `data/frozen/`.

**Run it manually:** on GitHub open the repository, click **Actions**, choose **Daily data update**, click
**Run workflow**, keep branch `main` and confirm. A green tick means success.

**When it fails:** GitHub emails the repository owner. Open the failed run, then read
`data/logs/update_log.csv` (one line per ticker and check). Typical causes: a Yahoo outage (rerun later), or a
one-day move above 20% placed in `data/live/quarantine.csv` (check whether it is a split or a genuine move;
if genuine, append the row to `prices_live.csv` by hand and rerun).

Run locally: `pip install -r requirements-live.txt` then `python src/update_data.py`. Before 16:30 IST,
today's partial prices are skipped. The committed live file keeps only `date, ticker, adj_close` for the last
1,600 trading days per symbol (what the Action needs); no other price fields are stored.

## Figures and dashboard

```powershell
python src/make_figures.py            # outputs/figures/*.png (300 DPI) + *.html + captions.md
python src/export_dashboard_json.py   # frontend/public/data/*.json (derived data only: returns, VaR/ES, test results)
cd frontend
npm ci
npm run dev       # local development server
npm run build     # type-check + production build into frontend/dist
npm run preview   # serve the production build locally
```

Regenerate both after any model rerun (for example after the macro data are added), then commit
`outputs/figures` and `frontend/public/data`.

**Live site:** https://ghiris-a11y.github.io/capstone-nifty50-downside-risk/

**GitHub Pages setup (one time):** repository **Settings → Pages → Build and deployment → Source: GitHub Actions**
(do not pick a suggested Jekyll or Static HTML workflow). The `deploy` job of `daily_update.yml` builds
`frontend/dist` and publishes it with `actions/upload-pages-artifact` and `actions/deploy-pages` after every daily
update, and whenever dashboard code is pushed. The Action never commits dashboard files: live risk JSON is
regenerated inside the build. The app uses `HashRouter` and relative `./data/...` paths, and Vite `base` is
`/capstone-nifty50-downside-risk/`.

**Design credits.** The dashboard layout (side menu, KPI card row, stock list and table, chart cards led by a big
number with a short note) borrows ideas from two Figma Community files:
[Trading Stock Market Dashboard Platform UI Kit](https://www.figma.com/design/3c5zWpbNciVkRL6YMIsbgg/) and
[Minimal & modern report template for brand insights and marketing dashboards](https://www.figma.com/design/o8Yeuw8XFrj9Oxt2TkYOLt/).
No images, logos, brand names or text were copied. Figma Community files are usually shared under CC BY 4.0; the
licence notes on the two pages could not be opened, so this is not yet checked. Reference screenshots are in
`design/figma/`, and notes are in `design/figma_notes.md`. Font: Inter (bundled with `@fontsource/inter`, SIL Open
Font License).

## Phase 2 report (Word and PDF)

Every number in the report is a `{{key}}` placeholder in `report/chapters/*.md`, filled from `outputs/` by
`src/report_numbers.py` (each key, value and source file is listed in `outputs/tables/report/report_numbers.csv`).

```
python src/garch_estimates.py            # GARCH parameters at the test start -> outputs/tables/garch_params_teststart.csv
python src/make_figures.py --print       # print-size figures (15.6 cm, text >= 10 pt) -> outputs/figures/print/
python src/make_report_visuals.py        # diagrams and extra charts -> report/figures/
python src/dashboard_check.py --screens-only --url https://ghiris-a11y.github.io/capstone-nifty50-downside-risk/ --out report/figures/dashboard
python src/build_report.py               # report/Phase2_Report.docx + report/qa_phase2.md
python src/export_pdf.py                 # Word (Windows): update contents lists, export tagged PDF with bookmarks
python src/report_pages.py --pages 37,48,61   # page count per chapter (report/page_check.md) and page previews
```

The .docx and .pdf carry the ITM logo and stay local (see .gitignore). `src/dashboard_check.py` also measures the
dashboard's Flesch-Kincaid grade and checks phone, laptop and projector widths (`outputs/dashboard_check/readability.json`).
