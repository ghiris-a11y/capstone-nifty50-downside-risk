# CHAPTER 4: DATA COLLECTION

## 4.1 Type of data and sources

All data are secondary, daily and numeric. No questionnaire was used (Appendix A). {{tab:sources}} lists each series and its use.

[[MDTABLE:sources|Data sources|Author's compilation; access dates in report/chapters/sources.md]]
| Data | Symbol | Source | Use |
|---|---|---|---|
| Daily close and volume, {{n_stocks}} stocks | TICKER.NS | Yahoo Finance | Returns, inputs, backtests |
| Nifty 50 index | ^NSEI | Yahoo Finance | Market context, fall days |
| India VIX | ^INDIAVIX | Yahoo Finance | Input, calm and stressed days |
| USD/INR | INR=X | Yahoo Finance | Input (labelled sets) |
| Index members, December 2025 | Nifty 50 list | NSE | Population |
| CPI, IIP | Monthly releases | MoSPI | Left out on purpose |

## 4.2 Data pipeline

{{fig:pipeline}} shows the path from sources to report and dashboard. Downloads wait between requests, retry and log every failure. The research data were frozen on {{snapshot}} into {{n_frozen_files}} read-only files with SHA-256 hashes. A GitHub Action adds each weekday's prices to a separate live file and updates the dashboard; only derived numbers are published.

[[FIG:pipeline|report/figures/v_pipeline.png|Data pipeline from sources to the frozen snapshot, the daily GitHub Action and the dashboard|Author's design; implemented in src/ and .github/workflows/daily_update.yml|Diagram with sources, validation and frozen snapshot in the top row, live files, GitHub Action and research run in the middle row, and the dashboard at the bottom.]]

[[MEANS]] Anyone with the code and the frozen files gets the same numbers. The daily Action shows the recommended model can run unattended at almost no cost.

## 4.3 Sample selection

{{fig:funnel}} shows how {{n_cand}} index members became the {{n_stocks}}-stock panel.

[[FIG:funnel|report/figures/v_funnel.png|Sample selection funnel from 50 constituents to the 41-stock balanced panel|config/nifty50_dec2025_candidates.csv, config/universe.csv, config/universe_excluded.csv|Funnel showing 50 constituents, 44 with full history after removing 6 later listings, and 41 after removing 3 suspected corporate-action errors.]]

[[MEANS]] Later listings were left out only so that every model sees the same years. The price-error exclusions remove falls that were data artefacts, not real losses.

## 4.4 The market in the test years

Each stock has {{rows_per_stock}} daily rows from {{data_first}} to {{data_last}}. The test window holds {{test_days_min}} to {{test_days_max}} trading days per stock, {{test_obs}} stock-days in all. At 99%, a good model should be beaten about {{exp_breaches_stock}} times per stock, so one stock alone says little and the analysis pools stocks.

[[FIG:market|outputs/figures/print/fig01_market_context.png|Nifty 50 cumulative log return since January 2015 and the India VIX percentile, 2015 to 2026|outputs/figures/fig01_market_context (src/make_figures.py); frozen snapshot|Line chart of the Nifty 50 cumulative return rising from 2015 to 2026 with the India VIX percentile in amber; the test window from 2024 is shaded and the 7 October 2026 repo hike is marked with a dashed line.]]

[[MEANS]] {{fig:market}} shows a rising but uneven market. The India VIX peaked at about {{vix_test_max}} points in the test years, against {{vix_fit_max}} in the fitting years. The test therefore checks normal to moderately stressed markets, not a 2020-style crisis.

## 4.5 Return statistics

[[TABLE:desc_panel|desc_panel]]

[[MEANS]] {{tab:desc_panel}} shows that {{pooled_small}} of stock-days moved by less than 2%, yet every stock had rare big falls. With fat tails and negative skew in {{n_negskew}} of {{n_stocks}} stocks, bell-curve models will understate big losses. Appendix C gives the figures by sector.
