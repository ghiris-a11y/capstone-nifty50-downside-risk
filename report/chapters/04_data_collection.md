# CHAPTER 4: DATA COLLECTION

## 4.1 Type of data and sources

All data are secondary, daily and numeric; prices come from Yahoo Finance (2026). No questionnaire was used (Appendix A). {{tab:sources}} lists each series and its use.

[[MDTABLE:sources|Data sources|Author's compilation; access dates in report/chapters/sources.md]]
| Data | Symbol | Source | Use |
|---|---|---|---|
| Daily close and volume, {{n_stocks}} stocks | TICKER.NS | Yahoo Finance | Returns, inputs, backtests |
| Nifty 50 index | ^NSEI | Yahoo Finance | Market context, fall days |
| India VIX | ^INDIAVIX | Yahoo Finance | Input, calm and stressed days |
| USD/INR | INR=X | Yahoo Finance | Input (labelled sets) |
| Index members, December 2025 | Nifty 50 list | NSE | Population |
| Repo rate | Handbook Table 43; policy releases | RBI | Input (one labelled set) |
| CPI, IIP | Monthly releases | MoSPI | Left out on purpose |

## 4.2 Data pipeline

{{fig:pipeline}} shows the path from sources to report and dashboard. The research data were frozen on {{snapshot}} into {{n_frozen_files}} read-only files with SHA-256 hashes. A GitHub Action adds each weekday's prices to a separate live file and updates the dashboard; only derived numbers are published.

[[FIG:pipeline|report/figures/redrawn/image6.png|Data pipeline from sources to the frozen snapshot, the daily GitHub Action and the dashboard|Author's design; implemented in src/ and .github/workflows/daily_update.yml|Diagram with sources, validation and frozen snapshot in the top row, live files, GitHub Action and research run in the middle row, and the dashboard at the bottom.|15.5]]

[[MEANS]] Anyone with the code and the frozen files gets the same numbers, and the recommended model can run daily at almost no cost.

## 4.3 Sample selection

{{fig:funnel}} shows how {{n_cand}} index members became the {{n_stocks}}-stock panel.

[[FIG:funnel|report/figures/redrawn/image7.png|Sample selection funnel from 50 constituents to the 41-stock balanced panel|config/nifty50_dec2025_candidates.csv, config/universe.csv, config/universe_excluded.csv|Funnel showing 50 constituents, 44 with full history after removing 6 later listings, and 41 after removing 3 suspected corporate-action errors.|15.5]]

[[MEANS]] Every model sees the same years, and falls caused by data errors are not counted as real losses.

## 4.4 Return statistics

[[TABLE:desc_panel|desc_panel]]

[[MEANS]] {{tab:desc_panel}} shows quiet days are the norm ({{pooled_small}} moved under 2%), but fat tails mean bell-curve models will understate big losses. Appendix C gives the figures by sector.

## 4.5 The market in the test years

Each stock has {{rows_per_stock}} daily rows from {{data_first}} to {{data_last}}. The test window holds {{test_days_min}} to {{test_days_max}} trading days per stock, {{test_obs}} stock-days in all, so the analysis pools stocks.

[[FIG:market|outputs/figures/print/fig01_market_context.png|Nifty 50 cumulative log return since January 2015 and the India VIX percentile, 2015 to 2026|outputs/figures/fig01_market_context (src/make_figures.py); frozen snapshot|Line chart of the Nifty 50 cumulative return rising from 2015 to 2026 with the India VIX percentile in amber; the test window from 2024 is shaded and the 7 October 2026 repo hike is marked with a dashed line.]]

[[MEANS]] {{fig:market}} shows a rising but uneven market. The India VIX peaked at about {{vix_test_max}} points in the test years, against {{vix_fit_max}} earlier, so the test covers normal to moderately stressed markets, not a 2020-style crisis.
