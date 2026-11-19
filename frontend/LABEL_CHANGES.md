# Dashboard label changes (plain-language rewrite)

Audience: non-technical readers. The technical name is kept in a small "Technical term" line, an info tooltip,
a "Technical note" under each chart, or a "For experts" section. Numbers in titles and findings are computed from
`public/data/*.json` at run time; none are typed in.

## Tabs and page furniture
| Old | New |
|---|---|
| (none) | **Start here** (new tab, `#/`) |
| Overview (`#/`) | Results at a glance (`#/overview`) |
| Model comparison | Model comparison (unchanged) |
| Regimes & stress | Calm vs stressed days |
| Stock drill-down | One stock up close |
| Feature importance | What drives the forecasts |
| Live risk | Daily example |
| (none) | **Glossary** (new tab) |
| About | About & limits |
| Nifty 50 Downside Risk: GARCH vs Machine Learning | How much could a big Indian stock lose tomorrow? |
| One-day 95% and 99% Value-at-Risk and Expected Shortfall for 41 Nifty 50 stocks. MBA Business Analytics capstone, ITM Skills University. | Classic models against machine learning, tested on 41 big stocks. A student project at ITM Skills University. |
| Working results. Guide approval … pending. Repo rate, CPI and IIP not yet included … | Draft results: our project guide has not yet approved them. The models do not yet use interest rates, price rises or factory output. |
| Frozen research snapshot … · live data as of … · Data: Yahoo Finance (derived values only) | Locked data copy … · daily example up to … · Data: Yahoo Finance (only returns and risk numbers are shown, no prices) |

## Terms
| Old | New (technical term kept beside it) |
|---|---|
| VaR / Value-at-Risk | Likely worst daily loss |
| 95% / 99% | 19 out of 20 days / 99 out of 100 days |
| Expected Shortfall (ES) | Average loss on the very bad days |
| Breach / exception | Day the loss was bigger than the forecast ("beaten") |
| Breach rate vs nominal | How often forecasts were beaten (ideal: 1 in 100 days) |
| Kupiec pass | Did forecasts fail too often? |
| Christoffersen CC pass | Did failures come in clusters? |
| Basel Green share | Regulator-style safety check (green = pass) |
| FZ0 / pinball loss | Overall forecast quality score (lower is better) |
| Diebold-Mariano | Is the difference real, or just luck? |
| GARCH significantly lower loss / ML significantly lower loss / No significant difference | GARCH really better / Machine learning really better / Could be luck (no real difference) |
| India VIX | Market fear gauge (India VIX) |
| Market-stress day (Nifty <= -2%) | Market-wide bad day (Nifty fell 2% or more) |
| No-risk days | XGBoost sometimes saw no risk / "no-risk" days |
| Feature set for the ML models | Inputs used by the machine-learning models |
| VaR level (99% / 95%) | Likely worst daily loss: which level? (99 out of 100 days / 19 out of 20 days) |
| Model A / Model B | First model / Second model |
| Actual daily return | Real daily return |
| `<model>` 99% VaR (as return) | `<model>` likely worst daily loss |
| `<model>` breach (n) | `<model>`: loss bigger than forecast (n days) |
| Daily log return (%) | Daily return (%) |
| Model names (GARCH-t, XGBoost, …) | Names kept, with a line underneath: "Classic statistics model · allows for extreme days", "Machine-learning model that learns from data · boosted decision trees", etc. |
| Feature codes (vix, rv_20, ret_l1, …) | Plain input names (Market fear gauge (VIX) level, Size of swings over the last 20 days, Return yesterday, …) |

## Overview cards ("Results at a glance")
| Old | New |
|---|---|
| Closest to nominal 1% (99% VaR) | Closest to expected (99 out of 100 days) |
| Lowest median joint VaR-ES loss (FZ0, 95%) | moved to For experts |
| Kupiec pass rate at 99% (share of stocks) | shown as good / caution / poor badges on the "How often were forecasts beaten" chart |
| Basel Green share (99% only) | Regulator-style safety check (green = pass) |
| Diebold-Mariano (FZ0 95%, ML vs each GARCH model, per stock) | Is the difference real, or just luck? |
| XGBoost no-risk days | XGBoost sometimes saw no risk |
| Breaches on market-stress days (99%) | Bad days come together |
| Backtest summary table | For experts: full backtest summary table |

## Chart titles (each now states the finding, adds "How to read this" and "What this means")
| Figure | Old title | New title (numbers filled from data) |
|---|---|---|
| New | — | `<model>` came closest to the ideal of 1 in 100 days (… days in 100) |
| 1 | Nifty 50 cumulative return and India VIX percentile, 2015-2026 | The models were judged on 2024 to 2026 (shaded), which includes the October 2026 rate rise |
| 2 | Distribution of daily log returns by stock, test window | On …% of stock-days the price moved less than 2% either way; big moves were rare |
| 3 | RELIANCE.NS: 99% VaR forecast against actual returns, with breaches | Reliance: GJR-t was beaten on … days and XGBoost on … (99 out of 100 days) |
| 4 | 99% VaR breach rate by stock and model | GJR-t was beaten too often on … of 41 stocks; XGBoost on … of 41 |
| 5 | Joint VaR-ES loss by India VIX quartile | Every model found the most fearful days hardest to forecast |
| 6 | XGBoost 99% VaR: feature importance | Market fear gauge (VIX) level had the biggest effect on XGBoost's forecast |
| 7 | 99% VaR backtests per stock: Kupiec against Christoffersen | …% of classic-model results passed both checks, against …% for machine learning |
| 8 | Expected Shortfall calibration: realised tail loss over forecast ES | On the very bad days, real losses were … times the GJR-t forecast and … times the XGBoost forecast |
| 9 | Average 99% VaR by sector | … stocks had the biggest likely worst daily loss; … the smallest |
| 10 | Models ordered by closeness of the 99% breach rate to nominal | moved to For experts (replaced on the main screen by the new bar chart) |
| 11 | Joint VaR-ES loss (FZ0): mean versus median across stocks | A few "no-risk" days made XGBoost's average score look much worse than its typical score |
| 12 | GARCH significantly better in 90 pairs, ML in 2, no difference in 646 | GARCH was really better in 90 comparisons, machine learning in 2; the other 646 could be luck |
| 13 | Breaches by day across the 41 stocks (99% VaR) | On the worst day (2024-06-04), 22 of 41 stocks lost more than the GJR-t forecast |
| 14 | Breaches concentrate on market-wide stress days | Market-wide bad days were 1.5% of days but held 21.4% of GJR-t's beaten days |

## Live tab
| Old | New |
|---|---|
| Latest one-day risk (live extension) | Daily example: next day's likely worst loss for each stock, under a banner "Daily example only. This is not the report's results." |
| Last return, 1-day volatility, Tail index (nu), VaR 95%, ES 95%, VaR 99%, ES 99% | Worst loss (99 of 100 days), Very bad days (99 of 100), Worst loss (19 of 20 days); full technical table under For experts |
| Sort by var 99 / es 99 / … | Sort by Worst loss (99 of 100 days) / Very bad days (99 of 100) / … |

## Moved behind "For experts"
Full backtest table and technical cards, Figure 10 table, Diebold-Mariano counts for every input set, breach-clustering
table, per-stock backtest table, ML results by input set, validation-window selection, feature-range table, full
live table, technical method list, excluded stocks and the review of large one-day moves.
