# Pilot results summary: GARCH vs ML downside risk (3 stocks)

Every number below is read from the files listed under Sources. Nothing was typed in by hand.

## Setup
- Stocks: RELIANCE.NS, HDFCBANK.NS, INFY.NS
- Features: price+vix (macro variables not yet available)
- Data: from 2015-01-01 to 2026-11-17 (last complete close; the run on 18 Nov 2026 excluded the open trading day)
- Train: to 2021-12-31 | Validation: to 2023-12-31 | Test: 2024-01-01 to 2026-11-17 (709 test days per stock)
- Models: GARCH, EGARCH, GJR-GARCH (Normal and Student-t, refit every 20 days); XGBoost (quantile), Random Forest and MLP (volatility + filtered historical simulation); benchmark: rolling 250-day historical simulation
- Seed 42; pipeline runtime for 3 stocks: 75.2 s

## Results by model (mean over the 3 stocks)
Pass counts are the number of stocks with p > 0.05. Basel zones apply to 99% VaR only. Lower pinball and FZ0 are better.

| Model | Family | Exc. rate 95% (nominal 5%) | Exc. rate 99% (nominal 1%) | Kupiec pass 95% | Kupiec pass 99% | Christoffersen CC pass 95% | Christoffersen CC pass 99% | Basel Green share (99%) | Pinball 95% | Pinball 99% | FZ0 95% | FZ0 99% |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GARCH-normal | GARCH | 4.70% | 1.69% | 3/3 | 1/3 | 3/3 | 3/3 | 67% | 0.0017 | 0.0005 | -3.4025 | -2.8387 |
| GARCH-t | GARCH | 5.41% | 1.22% | 3/3 | 3/3 | 3/3 | 3/3 | 100% | 0.0017 | 0.0005 | -3.4062 | -2.9237 |
| EGARCH-normal | GARCH | 4.33% | 1.55% | 3/3 | 3/3 | 3/3 | 3/3 | 50% | 0.0017 | 0.0005 | -3.4048 | -2.8274 |
| EGARCH-t | GARCH | 5.17% | 1.08% | 3/3 | 3/3 | 2/3 | 3/3 | 100% | 0.0017 | 0.0005 | -3.4059 | -2.8938 |
| GJR-normal | GARCH | 4.42% | 1.69% | 3/3 | 1/3 | 3/3 | 3/3 | 67% | 0.0017 | 0.0005 | -3.3967 | -2.8243 |
| GJR-t | GARCH | 5.31% | 1.03% | 3/3 | 3/3 | 3/3 | 3/3 | 100% | 0.0017 | 0.0005 | -3.4000 | -2.8983 |
| HistSim250 | Benchmark | 6.68% | 1.69% | 1/3 | 2/3 | 2/3 | 3/3 | 67% | 0.0017 | 0.0006 | -3.3366 | -2.7674 |
| XGBoost | ML | 1.13% | 0.28% | 0/3 | 1/3 | 0/3 | 1/3 | 100% | 0.0020 | 0.0007 | -3.2076 | -2.7244 |
| RandomForest | ML | 6.58% | 1.83% | 2/3 | 0/3 | 2/3 | 3/3 | 67% | 0.0017 | 0.0005 | -3.3975 | -2.8953 |
| MLP | ML | 5.45% | 1.08% | 3/3 | 3/3 | 2/3 | 3/3 | 100% | 0.0017 | 0.0006 | -3.2191 | -2.5694 |

## Mean FZ0 loss at 95% by India VIX quartile (previous day's VIX; lower is better)

| Model | Q1 calm | Q2 | Q3 | Q4 stressed |
|---|---|---|---|---|
| GARCH-normal | -3.5906 | -3.2420 | -3.5013 | -3.2765 |
| GARCH-t | -3.5898 | -3.2527 | -3.5041 | -3.2785 |
| EGARCH-normal | -3.5926 | -3.2635 | -3.5024 | -3.2612 |
| EGARCH-t | -3.5934 | -3.2658 | -3.4985 | -3.2662 |
| GJR-normal | -3.5952 | -3.2411 | -3.4963 | -3.2545 |
| GJR-t | -3.5977 | -3.2409 | -3.4954 | -3.2663 |
| HistSim250 | -3.5428 | -3.2576 | -3.4408 | -3.1051 |
| XGBoost | -3.2920 | -3.1681 | -3.2776 | -3.0929 |
| RandomForest | -3.5230 | -3.2099 | -3.5383 | -3.3199 |
| MLP | -3.5736 | -2.6079 | -3.5086 | -3.1894 |

## From the 7 Oct 2026 repo hike to 2026-11-17 (28 trading days x 3 stocks)

| Model | Exceptions 95% (of 84) | Exceptions 99% (of 84) |
|---|---|---|
| GARCH-normal | 3 (3.57%) | 0 (0.00%) |
| GARCH-t | 4 (4.76%) | 0 (0.00%) |
| EGARCH-normal | 2 (2.38%) | 0 (0.00%) |
| EGARCH-t | 3 (3.57%) | 0 (0.00%) |
| GJR-normal | 3 (3.57%) | 0 (0.00%) |
| GJR-t | 4 (4.76%) | 0 (0.00%) |
| HistSim250 | 4 (4.76%) | 0 (0.00%) |
| XGBoost | 1 (1.19%) | 0 (0.00%) |
| RandomForest | 6 (7.14%) | 2 (2.38%) |
| MLP | 4 (4.76%) | 1 (1.19%) |

The window is too short for formal tests: with 84 observations, about 0.8 exceptions are expected at 99%.

## Observations
1. Fat tails matter at 99%. The Student-t GARCH models had 99% exception rates closest to the nominal 1% (GARCH-t 1.22%; EGARCH-t 1.08%; GJR-t 1.03%), passed Kupiec in 3/3 stocks and had a Basel Green share of 100%. The Normal versions breached more often (GARCH-normal 1.69%; EGARCH-normal 1.55%; GJR-normal 1.69%); their Green share was 50%, 67%.
2. XGBoost was far too conservative. Its exception rate was 1.13% at 95% (nominal 5%) and 0.28% at 99% (nominal 1%), and it passed Kupiec at 95% in 0/3 stocks. On the 95% joint VaR-ES loss (FZ0), the Diebold-Mariano test found GARCH significantly better than XGBoost in 18 of 18 GARCH-stock pairs (5% level). Its Basel Green share was 100% only because the traffic light penalises too many breaches, not too few. In business terms, it would set capital and margins too high.
3. MLP and Random Forest were not significantly different from any GARCH model on 95% FZ0 (Diebold-Mariano: no significant difference in 18 of 18 pairs for MLP and 18 of 18 for Random Forest). MLP's 99% exception rate was 1.08%; Random Forest's was 1.83% and it passed Kupiec at 99% in 0/3 stocks.
4. On the joint VaR-ES loss (FZ0, lower is better) the lowest mean was GARCH-t at 95% (-3.4062) and GARCH-t at 99% (-2.9237). In the highest India VIX quartile the lowest mean 95% FZ0 was RandomForest (-3.3199) against -3.2785 for the best GARCH model (GARCH-t). This regime split is descriptive only and was not significance-tested in the pilot.
5. The rolling 250-day historical-simulation benchmark breached 6.68% of days at 95% and passed Kupiec at 95% in 1/3 stocks; the weakest GARCH-family model passed Kupiec at 95% in 3/3 stocks. In this pilot the volatility-updating models tracked risk better than the fixed-window rule.

## Problems found
- Data: Yahoo returned zero-volume placeholder rows for all 3 stocks on 2025-03-18, 2026-01-15. They were dropped and logged in data/logs/dropped_rows.csv (6 rows). A check on 18 Nov 2026 found a Nifty 50 (^NSEI) row for 2025-03-18 but none for 2026-01-15, so the first looks like a real trading day with a missing stock price and the second like a market holiday. Confirm against NSE in P2.
- Reproducibility: Yahoo's adjusted closes differ by up to about 5e-7 (relative) between downloads, which changed a few XGBoost and Random Forest exceptions between otherwise identical runs. The pilot now reads one hashed snapshot (data/processed/pilot_snapshot/manifest.csv); the full study must use the frozen snapshot in data/frozen/.
- Largest one-day move in the pilot test window: RELIANCE.NS on 2026-11-02, log return 10.97%. It is below the 20% quarantine threshold but should be checked against the NSE bhavcopy before the full run.
- Exception rates far from nominal: XGBoost (1.13% at 95%, 0.28% at 99%). Its tail-quantile set-up needs review before the full run.
- GARCH fits: 0 failed fits were logged in the pilot runs.
- Basel Green share is computed from only 2 non-overlapping 250-day windows per stock, so each stock can only score 0%, 50% or 100%.
- Macro variables (repo rate, CPI, IIP) are not in the pilot because the official series are not yet filled in; the pilot uses price + India VIX features.

## Caution
Three stocks are a pilot, not a conclusion. Results can change on the full 40-45 stock panel.

## Sources
- outputs/summary_price_vix.csv, outputs/backtest_results_price_vix.csv, outputs/regime_results_price_vix.csv, outputs/diebold_mariano_price_vix.csv
- outputs/tables/pilot_model_summary_price_vix.csv, pilot_fz0_by_vix_quartile_price_vix.csv, pilot_post_hike_price_vix.csv, pilot_dm_ml_vs_garch_price_vix.csv, pilot_meta_price_vix.csv, pilot_daily_forecasts_price_vix.csv
- data/logs/dropped_rows.csv, data/logs/pilot_run_*.log, data/processed/pilot_snapshot/manifest.csv
