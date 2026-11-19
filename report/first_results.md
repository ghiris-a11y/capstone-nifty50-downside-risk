# First full-panel results (working draft)

Status: Dr. Pardeshi's approval of the balanced panel and the November 2026 window is **pending**. These are working results for discussion, not report conclusions.

Every number below is read from files in `outputs/tables/` (listed under Sources).

## Setup

- Panel: 41 Nifty 50 stocks with full history from 2015 (config/universe.csv); 9 candidates excluded (config/universe_excluded.csv).
- Frozen snapshot: 2026-11-18 10:07 UTC, data 2015-01-01 to 2026-11-17, SHA-256 hashes in data/frozen/manifest.csv.
- Test window: 2024-01-01 to 2026-11-17 (708-710 trading days per stock). Train to 2021-12-31, validation 2022-2023.
- Feature sets are named by what they contain. Macro series (repo rate, CPI, IIP) are **not yet included**; the official files have not been supplied.

## 1. Breach rates and backtests (price/volume features for the ML models)

Pass shares are the percentage of the stocks with p > 0.05. Basel zones apply to 99% VaR only and must be read with Kupiec: the traffic light penalises too many breaches, not too few. Lower FZ0 and pinball are better.

| Model | Exc. 95% (nominal 5%) | Exc. 99% (nominal 1%) | Kupiec pass 95% | Kupiec pass 99% | Christoffersen CC pass 99% | Basel Green (99%) | Mean FZ0 95% | Median FZ0 95% (stocks) | Pinball 99% (x10,000) |
|---|---|---|---|---|---|---|---|---|---|
| GARCH-normal | 3.88% | 1.33% | 76% | 83% | 100% | 84% | -3.3566 | -3.3758 | 5.810 |
| GARCH-t | 4.48% | 0.87% | 83% | 95% | 100% | 96% | -3.3622 | -3.3844 | 5.813 |
| EGARCH-normal | 3.75% | 1.31% | 63% | 83% | 93% | 83% | -3.3571 | -3.3740 | 5.845 |
| EGARCH-t | 4.38% | 0.88% | 88% | 100% | 98% | 96% | -3.3641 | -3.3853 | 5.865 |
| GJR-normal | 3.72% | 1.30% | 59% | 83% | 98% | 85% | -3.3540 | -3.3753 | 5.823 |
| GJR-t | 4.37% | 0.84% | 88% | 98% | 100% | 96% | -3.3604 | -3.3861 | 5.855 |
| HistSim250 | 6.21% | 1.69% | 78% | 63% | 76% | 63% | -3.3005 | -3.3277 | 6.214 |
| XGBoost | 6.58% | 1.64% | 54% | 68% | 71% | 68% | -3.3188 | -3.3144 | 6.093 |
| RandomForest | 6.09% | 1.35% | 71% | 80% | 83% | 82% | -3.3496 | -3.3707 | 5.884 |
| MLP | 5.67% | 1.20% | 80% | 68% | 85% | 82% | -3.2941 | -3.3227 | 6.128 |

**What this means.** At 99%, the breach rates closest to the nominal 1% were EGARCH-t (0.88%), GARCH-t (0.87%), GJR-t (0.84%). The ML models breached XGBoost 1.64%, RandomForest 1.35%, MLP 1.20% of days at 99%. A breach rate above nominal means a desk using that model would hold too little capital or margin on the worst days; below nominal means it would tie up more capital than needed.

## 2. Diebold-Mariano tests: ML models against each GARCH model (pairs = 6 GARCH models x stocks)

Feature set `price` (price/volume only); 246 pairs per ML model:

| ML model | FZ0 95%: GARCH lower / ML lower / no diff | Pinball 95%: GARCH lower / ML lower / no diff | Pinball 99%: GARCH lower / ML lower / no diff |
|---|---|---|---|
| XGBoost | 31 / 1 / 214 | 28 / 0 / 218 | 17 / 5 / 224 |
| RandomForest | 12 / 1 / 233 | 2 / 11 / 233 | 14 / 10 / 222 |
| MLP | 47 / 0 / 199 | 56 / 0 / 190 | 45 / 3 / 198 |

Feature set `price_vixlevel` (price/volume + India VIX level); 246 pairs per ML model:

| ML model | FZ0 95%: GARCH lower / ML lower / no diff | Pinball 95%: GARCH lower / ML lower / no diff | Pinball 99%: GARCH lower / ML lower / no diff |
|---|---|---|---|
| XGBoost | 51 / 9 / 186 | 44 / 12 / 190 | 30 / 0 / 216 |
| RandomForest | 13 / 1 / 232 | 0 / 10 / 236 | 17 / 8 / 221 |
| MLP | 57 / 1 / 188 | 34 / 0 / 212 | 25 / 0 / 221 |

Feature set `price_vixrel` (price/volume + VIX relative to its 60-day mean); 246 pairs per ML model:

| ML model | FZ0 95%: GARCH lower / ML lower / no diff | Pinball 95%: GARCH lower / ML lower / no diff | Pinball 99%: GARCH lower / ML lower / no diff |
|---|---|---|---|
| XGBoost | 25 / 2 / 219 | 18 / 9 / 219 | 13 / 2 / 231 |
| RandomForest | 0 / 7 / 239 | 3 / 15 / 228 | 15 / 10 / 221 |
| MLP | 47 / 3 / 196 | 46 / 4 / 196 | 26 / 0 / 220 |

**What this means.** Across the three ML models (price set, FZ0 95%), GARCH had significantly lower loss in 90 pairs, ML in 2, and 646 pairs showed no significant difference at the 5% level. A breach rate further from nominal does not by itself mean a significantly worse forecast on these loss functions; the test results should be quoted alongside the breach rates.

## 3. XGBoost 'no-risk' days and the effect on mean FZ0

A no-risk day is a day on which XGBoost's forecast lower-tail quantile was at or above zero, so VaR hit its floor (0.0001%). FZ0 is unbounded on such days if a loss follows, so the mean can be dominated by a single day; the median across stocks is reported next to it.

| Feature set | Level | XGBoost no-risk days (all stocks) | XGBoost mean FZ0 | XGBoost median FZ0 (stocks) |
|---|---|---|---|---|
| price | 95% | 19 | -3.3188 | -3.3144 |
| price | 99% | 20 | 28.9606 | -2.8156 |
| price_vixlevel | 95% | 34 | -3.3040 | -3.3373 |
| price_vixlevel | 99% | 50 | 29.0809 | -2.7206 |
| price_vixrel | 95% | 31 | -3.3319 | -3.3238 |
| price_vixrel | 99% | 10 | 28.9592 | -2.7793 |
| price_fxchg | 95% | 37 | -3.3198 | -3.3257 |
| price_fxchg | 99% | 20 | -2.7460 | -2.7404 |
| price_vixrel_fxchg | 95% | 11 | -3.3348 | -3.3403 |
| price_vixrel_fxchg | 99% | 9 | -2.7396 | -2.7685 |

## 4. ML models by feature set (test window)

GARCH and historical simulation do not use these features, so their rows are identical across sets.

| Feature set | Contains | Model | Exc. 95% | Exc. 99% | Kupiec pass 99% | Pinball vs price (95%+99%) |
|---|---|---|---|---|---|---|
| price | price/volume only | XGBoost | 6.58% | 1.64% | 68% | 1.000 |
| price | price/volume only | RandomForest | 6.09% | 1.35% | 80% | 1.000 |
| price | price/volume only | MLP | 5.67% | 1.20% | 68% | 1.000 |
| price_vixlevel | price/volume + India VIX level | XGBoost | 7.24% | 1.88% | 61% | 1.015 |
| price_vixlevel | price/volume + India VIX level | RandomForest | 6.56% | 1.71% | 63% | 1.010 |
| price_vixlevel | price/volume + India VIX level | MLP | 6.25% | 1.37% | 73% | 0.997 |
| price_vixrel | price/volume + VIX relative to its 60-day mean | XGBoost | 6.46% | 1.62% | 63% | 1.000 |
| price_vixrel | price/volume + VIX relative to its 60-day mean | RandomForest | 5.64% | 1.30% | 80% | 0.999 |
| price_vixrel | price/volume + VIX relative to its 60-day mean | MLP | 5.66% | 1.25% | 76% | 0.991 |
| price_fxchg | price/volume + USD/INR changes | XGBoost | 6.71% | 1.54% | 66% | 0.996 |
| price_fxchg | price/volume + USD/INR changes | RandomForest | 6.06% | 1.35% | 78% | 1.002 |
| price_fxchg | price/volume + USD/INR changes | MLP | 5.99% | 1.30% | 88% | 1.001 |
| price_vixrel_fxchg | price/volume + VIX relative + USD/INR changes | XGBoost | 6.52% | 1.54% | 63% | 0.997 |
| price_vixrel_fxchg | price/volume + VIX relative + USD/INR changes | RandomForest | 5.75% | 1.30% | 73% | 0.999 |
| price_vixrel_fxchg | price/volume + VIX relative + USD/INR changes | MLP | 5.35% | 1.20% | 71% | 1.016 |

For reference, the earlier run labelled `price_vix_macro`, which actually contained VIX level + USD/INR level (no repo rate, CPI or IIP) and predates the XGBoost ES floor, gave 99% breach rates of XGBoost 2.30%, RandomForest 2.07%, MLP 2.91% (outputs/tables/superseded/pre_es_floor_2026-11-18/).

## 5. Why did market features change the ML results? (diagnosis)

**Feature ranges.** Share of test days on which a feature lies outside the range of the data the final models were fitted on (2015-2023), median across stocks:

| Feature | Share of test days outside fitted range | Fitted range (median) | Test range (median) |
|---|---|---|---|
| usdinr | 64.3% | 62.06 to 85.19 | 82.3 to 96.88 |
| vix | 3.4% | 0.1014 to 0.8361 | 0.0915 to 0.2789 |
| rv_x_vix | 0.4% | 0.0007414 to 0.04446 | 0.0006798 to 0.006422 |
| vix_rel60 | 0.0% | -0.3759 to 2.544 | -0.3244 to 0.891 |
| usdinr_ret1 | 0.0% | -0.02312 to 0.0264 | -0.02301 to 0.02181 |
| usdinr_ret21 | 0.0% | -0.05426 to 0.07208 | -0.03231 to 0.0419 |

**Validation window versus test window.** Pinball loss relative to the price-only set (below 1 = the features helped). Validation: models trained on 2015-2019, calibrated on 2020-2021, evaluated on 2022-2023.

| Variant | Model | Validation pinball vs price (2022-23) | Test pinball vs price (2024-26) | Validation exc. 99% | Test exc. 99% |
|---|---|---|---|---|---|
| price_vixlevel | XGBoost | 0.988 | 1.015 | 1.89% | 1.88% |
| price_vixlevel | RandomForest | 0.973 | 1.010 | 0.53% | 1.71% |
| price_vixlevel | MLP | 0.932 | 0.997 | 0.83% | 1.37% |
| price_vixrel | XGBoost | 0.989 | 1.000 | 1.70% | 1.62% |
| price_vixrel | RandomForest | 0.991 | 0.999 | 0.47% | 1.30% |
| price_vixrel | MLP | 0.921 | 0.991 | 0.74% | 1.25% |
| price_fxchg | XGBoost | 0.997 | 0.996 | 1.81% | 1.54% |
| price_fxchg | RandomForest | 1.003 | 1.002 | 0.47% | 1.35% |
| price_fxchg | MLP | 0.952 | 1.001 | 0.61% | 1.30% |
| price_vixrel_fxchg | XGBoost | 0.988 | 0.997 | 1.76% | 1.54% |
| price_vixrel_fxchg | RandomForest | 0.997 | 0.999 | 0.45% | 1.30% |
| price_vixrel_fxchg | MLP | 0.930 | 1.016 | 0.77% | 1.20% |

Variant chosen on the validation window only (rule and timestamp in outputs/tables/validation/selected_variant.json, created 2026-11-19 04:04:33 UTC, before the test rerun): overall `price_vixlevel`, stationary `price_vixrel`.

**What this means.** The USD/INR level was outside its fitted range on most test days (64%); tree models cannot extrapolate beyond the values they were fitted on, so poor results with that feature are consistent with a range shift. The VIX level was outside its range on only 3.4% of test days, so range shift does not explain the VIX result. In 4 of 12 model-variant cases the features lowered pinball loss on the validation window (2022-23) but raised it on the test window (2024-26): the value of these features changed between periods. Overfitting was not tested directly (for example by comparing in-sample and out-of-sample loss), so the report should not attribute the ML results to overfitting on this evidence.

## 6. Do breaches cluster on market-wide stress days? (99% VaR, price set)

Stress day = Nifty 50 one-day log return of -2% or worse, defined in advance: 11 of 710 test days (1.5%).

| Model | Breaches (all stocks) | Share on stress days | Max in one day | Days with 10+ stocks breaching | Top days |
|---|---|---|---|---|---|
| GARCH-normal | 387 | 20.2% | 23 | 5 | 2024-06-04 23 (Nifty -6.1%); 2025-02-28 12 (Nifty -1.9%); 2025-04-07 11 (Nifty -3.3%) |
| GARCH-t | 252 | 20.6% | 22 | 2 | 2024-06-04 22 (Nifty -6.1%); 2025-04-07 10 (Nifty -3.3%); 2024-03-13 8 (Nifty -1.5%) |
| EGARCH-normal | 382 | 18.3% | 23 | 4 | 2024-06-04 23 (Nifty -6.1%); 2025-04-07 11 (Nifty -3.3%); 2025-02-28 10 (Nifty -1.9%) |
| EGARCH-t | 257 | 21.4% | 22 | 2 | 2024-06-04 22 (Nifty -6.1%); 2025-04-07 10 (Nifty -3.3%); 2024-03-13 8 (Nifty -1.5%) |
| GJR-normal | 377 | 19.1% | 23 | 4 | 2024-06-04 23 (Nifty -6.1%); 2024-08-05 10 (Nifty -2.7%); 2025-02-28 10 (Nifty -1.9%) |
| GJR-t | 243 | 21.4% | 22 | 2 | 2024-06-04 22 (Nifty -6.1%); 2025-04-07 10 (Nifty -3.3%); 2025-02-28 8 (Nifty -1.9%) |
| HistSim250 | 492 | 20.5% | 23 | 8 | 2024-06-04 23 (Nifty -6.1%); 2024-08-05 15 (Nifty -2.7%); 2024-03-13 15 (Nifty -1.5%) |
| XGBoost | 476 | 16.2% | 22 | 4 | 2024-06-04 22 (Nifty -6.1%); 2025-04-07 11 (Nifty -3.3%); 2024-03-13 10 (Nifty -1.5%) |
| RandomForest | 393 | 19.3% | 22 | 4 | 2024-06-04 22 (Nifty -6.1%); 2025-04-07 13 (Nifty -3.3%); 2024-10-03 12 (Nifty -2.1%) |
| MLP | 350 | 18.0% | 21 | 1 | 2024-06-04 21 (Nifty -6.1%); 2025-02-28 9 (Nifty -1.9%); 2025-04-07 9 (Nifty -3.3%) |

**What this means.** If breaches were spread evenly, about 1.5% would fall on stress days. A much higher share means breaches arrive together across many stocks on the same day, which is what matters for a portfolio or a clearing house: losses that hit many positions at once.

## 7. The three stocks excluded as suspected unadjusted corporate actions

| Stock | Date | Move | Nifty | Assessment | Note |
|---|---|---|---|---|---|
| TRENT.NS | 2026-01-01 | -40.12% | 0.06% | unadjusted corporate action (level persists, no rebound, Nifty flat) |  |
| ADANIENT.NS | 2015-06-03 | -49.02% | -1.24% | unadjusted corporate action (level persists, no rebound, Nifty flat) | consistent with the 2015 demerger of Adani Transmission from Adani Enterprises [UNVERIFIED] |
| ADANIENT.NS | 2017-04-26 | -23.50% | 0.49% | unclassified: needs NSE corporate-action check |  |
| ADANIENT.NS | 2019-05-20 | 24.19% | 3.63% | genuine move (market-wide day) |  |
| ADANIENT.NS | 2020-08-25 | 21.24% | 0.05% | unclassified: needs NSE corporate-action check |  |
| ADANIENT.NS | 2023-01-27 | -20.48% | -1.62% | genuine move (documented news) | Hindenburg Research report (25 Jan 2023) sell-off: genuine news-driven move |
| ADANIENT.NS | 2023-02-01 | -33.12% | -0.26% | genuine move (documented news) | Hindenburg sell-off and withdrawal of the follow-on public offer: genuine move |
| ADANIENT.NS | 2023-02-02 | -31.06% | -0.03% | genuine move (documented news) | Hindenburg sell-off continued: genuine move |
| ADANIENT.NS | 2024-06-04 | -21.46% | -6.11% | genuine move (market-wide day) | general-election result day (market-wide sell-off): genuine move |
| ADANIENT.NS | 2024-11-21 | -25.63% | -0.72% | genuine move (documented news) | US indictment news involving Adani group: genuine move |
| TMPV.NS | 2025-10-14 | -51.34% | -0.32% | unadjusted corporate action (level persists, no rebound, Nifty flat) | Tata Motors demerger ex-date (commercial-vehicle business split off); company announcement |

Rule: excluded if a one-day move of 35% or more occurred while the Nifty moved less than 3% (moves that triggered exclusion are those with |move| >= 35%). Event notes come from general knowledge and need a cited source (NSE corporate-action records or news) before they appear in the report.

**ADANIENT sensitivity run** (data from 4 Jun 2015, the day after the suspected corporate action; genuine crash days of 2023-2024 kept). 99% VaR breach rates over the same test window: GARCH-normal 0.71%, GARCH-t 0.56%, EGARCH-normal 0.71%, EGARCH-t 0.56%, GJR-normal 0.71%, GJR-t 0.56%, HistSim250 1.41%, XGBoost 0.56%, RandomForest 0.56%, MLP 0.71%.

ADANIENT is a crash-prone stock, not a data problem; it is reported here so that excluding it from the balanced panel does not hide how the models behave on such a stock.

## Sources

- outputs/tables/summary_*.csv, backtest_results_*.csv, diebold_mariano_*.csv, diebold_mariano_pinball_*.csv
- outputs/tables/diag_feature_ranges_summary.csv, outputs/tables/validation/variant_selection.csv, selected_variant.json
- outputs/tables/breach_days_summary_price.csv, outputs/tables/exclusion_review.csv, outputs/tables/sensitivity/
- config/universe.csv, config/universe_excluded.csv, data/frozen/manifest.csv
