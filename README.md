# Nifty 50 Downside Risk: GARCH vs Machine Learning

MBA Business Analytics capstone (ITM Skills University). It compares GARCH, EGARCH and GJR-GARCH models (Normal and Student-t) with XGBoost, Random Forest and MLP. Each model forecasts one-day-ahead 95% and 99% Value-at-Risk (VaR) and Expected Shortfall (ES) for a balanced panel of 40–45 Nifty 50 stocks from 2015 to 2026.

| Split | Period |
|---|---|
| Train | 2015 – 2021 |
| Validation | 2022 – 2023 |
| Test | 2024-01-01 – Nov 2026 (includes the 7 Oct 2026 RBI repo hike to 5.50%) |

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
