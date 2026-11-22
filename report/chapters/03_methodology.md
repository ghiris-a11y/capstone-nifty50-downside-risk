# CHAPTER 3: RESEARCH METHODOLOGY

## 3.1 Research design

The study is quantitative, empirical and ex post. It is designed as a forecasting competition that mirrors how a risk desk works: each model is fitted on past data only, it forecasts the next day's VaR and ES, and the forecast is later compared with what actually happened. The unit of analysis is a stock-day. {{fig:method_flow}} shows the seven stages, which follow the flowchart planned in Phase 1 (Appendix C of that report).

[[FIG:method_flow|report/figures/v_method_flow.png|Research methodology flowchart|Author's design; implemented in nifty50_var_pipeline.py|Flowchart of seven stages from data acquisition through cleaning, feature engineering, GARCH modelling, ML modelling, backtesting and visualisation, with a feedback loop from evaluation to feature selection on the validation window.]]

[[MEANS]] Every forecast is made the way it would have been made in real time, so the results show what a desk would actually have experienced, not what a model can explain after the fact.

## 3.2 Sampling technique and sample size

The sampling technique is purposive: the population is the fifty Nifty 50 constituents in December 2025, and the sample keeps every stock with a complete daily history from January 2015, so that all models are judged on the same days (a balanced panel). Stocks listed later, or whose price history showed a suspected unadjusted corporate action, were excluded by rules set before any model was run. The final sample is N = {{n_stocks}} stocks from {{n_sectors}} sectors (Chapter 4 gives the selection funnel). A balanced panel has a known bias: it keeps only firms that survived and stayed in the index, so results describe established large caps.

## 3.3 Training, validation and test windows

{{fig:timeline}} shows the time split. Models are trained on 2015 to 2021 and validated on 2022 to 2023; the test window, from 1 January 2024 to {{data_last}}, is never used for any choice. GARCH models are re-estimated every 20 trading days on all data up to that point; the machine-learning models are fitted once on 2015 to 2023 and then forecast the whole test window. To choose which market inputs the machine-learning models should use, a separate protocol trains on 2015 to 2019, calibrates on 2020 to 2021 and evaluates on 2022 to 2023; the choice was recorded on {{sel_time}} UTC, before the test results were produced.

[[FIG:timeline|report/figures/v_timeline.png|Train, validation and test windows, with the 7 October 2026 repo hike marked|Author's design; dates from the pipeline configuration and outputs/tables/validation/selected_variant.json|Timeline from 2015 to 2026 with training, validation and test bars for the main study and a second row for the feature-choice protocol; a dashed line marks the RBI repo hike on 7 October 2026.]]

[[MEANS]] Because the test years were never used to tune anything, the results are an honest preview of how each model would behave going forward. The price of this honesty is that the machine-learning models are not refitted during the test, which Chapter 7 lists as a limitation.

## 3.4 Models

- **GARCH family (six models).** GARCH(1,1), EGARCH(1,1) and GJR-GARCH(1,1), each with Normal and Student-t errors and a constant mean, estimated on percentage log returns.
- **XGBoost quantile regression.** Six quantiles are forecast for each level (the VaR quantile and five deeper quantiles); VaR is the level quantile and ES is the mean of the deeper ones, with VaR floored at a tiny positive number and ES never below VaR.
- **Random Forest and MLP.** Each forecasts the size of the next day's return; standardised validation residuals then give VaR and ES by filtered historical simulation.
- **Historical simulation (benchmark).** The empirical quantile and tail mean of the last 250 returns.

Inputs for the machine-learning models are lagged returns, realised volatility over 10, 20 and 60 days, recent drawdown and volume changes, and, in labelled variants, the India VIX and the USD/INR exchange rate. Every input at day t uses information up to day t-1 only. Random seeds are fixed at 42.

The inputs are market data only. CPI and IIP are excluded by design: they are monthly, released weeks late and revised afterwards, the pipeline has no stationary CPI feature, and they carry little information at a one-day horizon. The pipeline can add repo-rate changes over 21 and 63 days as a labelled input set; the repo-rate file dates each change on the RBI announcement date (lag 0). That file is not yet fully verified, and the loader skips any macro file with a blank or unverified row and records the skip in data/logs/macro_skipped.log, so no reported result uses it.

## 3.5 Evaluation

Breach rates are compared with the nominal 5% and 1%. Kupiec and Christoffersen tests are applied per stock at the 5% significance level. Basel traffic-light zones are reported for 99% VaR only, as the share of non-overlapping 250-day windows with four or fewer breaches. Forecast quality is scored with FZ0 (VaR and ES together) and pinball loss (VaR), and Diebold-Mariano tests with a five-lag long-run variance compare each machine-learning model with each GARCH model, stock by stock. Results are also split by quartile of the previous day's India VIX and by market-wide stress days, defined in advance as days on which the Nifty 50 fell 2% or more.

## 3.6 Techniques and why they were chosen

{{fig:techniques}} lists every technique, why it was chosen and which question it answers.

[[FIG:techniques|report/figures/v_techniques.png|Techniques used in the study, why they were chosen and what they answer|Author's design|Table-style graphic with three columns: technique, reason for choosing it, and the research question it answers, for ten techniques from GARCH models to SHAP values.]]

[[MEANS]] Each test answers a question a risk manager would ask: does the model fail too often, do failures bunch together, would a regulator accept it, and is any advantage real or luck.
