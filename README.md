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
today's partial prices are skipped.
