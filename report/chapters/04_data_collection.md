# CHAPTER 4: DATA COLLECTION

## 4.1 Type of data

All data are secondary, daily and quantitative. No primary data were collected, so no questionnaire was used (see Appendix A).

## 4.2 Data sources

{{tab:sources}} lists every data series, where it comes from and how it is used.

[[MDTABLE:sources|Data sources|Author's compilation; access dates in report/chapters/sources.md]]
| Data | Symbol or series | Source | Use |
|---|---|---|---|
| Adjusted daily close and volume, 41 stocks | TICKER.NS | Yahoo Finance | Returns, features, backtests |
| Nifty 50 index | ^NSEI | Yahoo Finance | Market context, stress days |
| India VIX | ^INDIAVIX | Yahoo Finance | Feature, regimes |
| USD/INR exchange rate | INR=X | Yahoo Finance | Feature (labelled variants) |
| Index constituents, December 2025 | Nifty 50 list | NSE | Population for sampling |
| Repo rate | Monetary policy press releases | RBI | Prepared in data/raw/repo_rate.csv; not used, because not every row is verified |
| CPI, IIP | Monthly releases | MoSPI | Excluded by design (monthly, released late, revised) |

## 4.3 Data pipeline

{{fig:pipeline}} shows how data move from the sources to the report and the dashboard. Every download waits between requests, retries with back-off and logs failures. The research data were frozen on {{snapshot}} into read-only files with SHA-256 hashes ({{n_frozen_files}} files), and every number in this report comes from that snapshot. A separate GitHub Action runs each weekday at 13:30 UTC (7:00 PM IST), adds the new day's prices to a live file, recomputes a next-day GJR-t VaR and ES for each stock, and rebuilds the public dashboard. Only derived values (returns, VaR, ES and test results) are published; raw prices are not.

[[FIG:pipeline|report/figures/v_pipeline.png|Data pipeline from sources to the frozen snapshot, the daily GitHub Action and the dashboard|Author's design; implemented in src/ and .github/workflows/daily_update.yml|Diagram with sources, validation and frozen snapshot in the top row, live files, GitHub Action and research run in the middle row, and the dashboard at the bottom.]]

[[MEANS]] The frozen snapshot makes every result repeatable: anyone with the code and the snapshot gets the same numbers. The daily Action shows that the recommended model can run unattended at almost no cost.

## 4.4 Sample selection

{{fig:funnel}} shows how the {{n_cand}} index constituents became the {{n_stocks}}-stock panel; {{tab:excluded}} lists each excluded stock and the reason.

[[FIG:funnel|report/figures/v_funnel.png|Sample selection funnel from 50 constituents to the 41-stock balanced panel|config/nifty50_dec2025_candidates.csv, config/universe.csv, config/universe_excluded.csv|Funnel showing 50 constituents, 44 with full history after removing 6 later listings, and 41 after removing 3 suspected corporate-action errors.]]

[[TABLE:excluded|excluded]]

[[MEANS]] The six later listings are excluded only because the models need the same years of history. The three corporate-action exclusions remove price drops that are artefacts of the free data, not real losses. One of them, Adani Enterprises, also had genuine crashes; a separate sensitivity run (Chapter 5) shows that excluding it does not hide how the models behave on a crash-prone stock.

## 4.5 Dataset description

Each stock has {{rows_per_stock}} daily rows from {{data_first}} to {{data_last}}. The test window holds between {{test_days_min}} and {{test_days_max}} trading days per stock, {{test_obs}} stock-days in total. At 99%, a well-calibrated model should therefore be breached about {{exp_breaches_stock}} times per stock over the test window, which is why single-stock tests have limited power and the analysis focuses on results across all stocks.

{{fig:market}} places the test window in the context of the whole period.

[[FIG:market|outputs/figures/print/fig01_market_context.png|Nifty 50 cumulative log return since January 2015 and the India VIX percentile, 2015 to 2026|outputs/figures/fig01_market_context (src/make_figures.py); frozen snapshot|Line chart of the Nifty 50 cumulative return rising from 2015 to 2026 with the India VIX percentile in amber; the test window from 2024 is shaded and the 7 October 2026 repo hike is marked with a dashed line.]]

[[MEANS]] The models were tested on a rising but uneven market. The India VIX never reached the extremes of earlier years in the test window (its highest level was about {{vix_test_max}} points, against {{vix_fit_max}} in the fitting years), so the test is a fair check of normal-to-moderately-stressed conditions rather than of a crisis like 2020.

## 4.6 Descriptive statistics

{{tab:desc_panel}} summarises daily returns in the test window, and {{fig:dist}} shows the distribution for every stock. Appendix C gives the statistics by stock.

[[TABLE:desc_panel|desc_panel]]

[[FIG:dist|outputs/figures/print/fig02_return_distributions.png|Distribution of daily log returns by stock, test window (tails clipped at ±8%)|outputs/figures/fig02_return_distributions (src/make_figures.py)|Grid of 41 small histograms, one per stock, each peaked around zero with long thin tails.]]

[[MEANS]] On {{pooled_small}} of stock-days the price moved by less than 2% either way, but every stock had rare large moves, and the worst single day in the sample was {{worst_day_ret}} ({{worst_day_stock}}). Fat tails (median excess kurtosis {{kurt_med}}) and negative skew in {{n_negskew}} of {{n_stocks}} stocks mean that a bell-curve model will understate how often big losses occur, which is exactly what the Normal versions of the GARCH models show in Chapter 5.
