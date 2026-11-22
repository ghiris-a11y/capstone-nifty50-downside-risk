# CHAPTER 3: RESEARCH METHODOLOGY

## 3.1 Research design

The study is quantitative and uses past data only. It works like a forecasting contest that mirrors a risk desk. Each evening every model uses only what is known that day to forecast the next day's VaR and ES. The forecast is then compared with what happened. The unit of analysis is one stock on one day.

## 3.2 Sampling

The population is the fifty Nifty 50 stocks of December 2025. The sample is purposive: it keeps every stock with daily prices since January 2015, so all models are judged on the same days (a balanced panel). Rules set before any model was run removed later listings and suspected price errors. The final sample is {{n_stocks}} stocks from {{n_sectors}} sectors. The panel keeps only firms that survived, so results describe established large caps.

## 3.3 Time windows

{{fig:timeline}} shows the split. GARCH models are re-estimated every 20 trading days on all earlier data. The machine-learning models are fitted once on 2015 to 2023. The extra-input sets were chosen on 2022 to 2023 and the choice was recorded on {{sel_time}} UTC, before any test result existed. Nothing is shuffled across the three periods; the only random split is the MLP's 15% early-stopping sample inside the training years.

[[FIG:timeline|report/figures/v_timeline.png|Train, validation and test windows, with the 7 October 2026 repo hike marked|Author's design; dates from the pipeline configuration and outputs/tables/validation/selected_variant.json|Timeline from 2015 to 2026 with training, validation and test bars for the main study and a second row for the feature-choice protocol; a dashed line marks the RBI repo hike on 7 October 2026.]]

[[MEANS]] The test years were never used to tune anything. The results therefore preview how each model would behave in real use.

## 3.4 Models and inputs

- **Six GARCH models:** GARCH, EGARCH and GJR-GARCH, each with Normal or Student-t errors.
- **XGBoost:** forecasts the loss limit directly, plus five deeper points whose average gives ES.
- **Random Forest and MLP:** forecast the size of tomorrow's move; past forecast errors then give VaR and ES (filtered historical simulation).
- **Benchmark:** the loss limit and worst-day average of the last 250 days (historical simulation).

The machine-learning inputs are past returns, recent volatility, recent falls and volume changes. Labelled sets add the India VIX or USD/INR changes. One more set adds the change in the RBI repo rate over 21 and 63 trading days. Each rate change is dated on the day the RBI announced it, from a file checked row by row against RBI Handbook Table 43 and the policy releases (Reserve Bank of India, 2025). The program refuses to use any rate file with a blank or unchecked row. Every input for day t uses data up to day t-1 only, and random seeds are fixed at 42.

## 3.5 How the forecasts are judged

- Miss rate: the share of days the loss exceeded VaR (ideal 5% at 95% and 1% at 99%).
- Test of whether misses are too frequent (Kupiec test) and whether they come in clusters (Christoffersen test), per stock, at the 5% level.
- Basel green zone, for 99% VaR only: the share of 250-day blocks with four or fewer misses.
- Score for loss limit and worst-day loss together (FZ0 score), and a score for the loss limit alone (pinball score); lower is better.
- Diebold-Mariano test: is one model's average score really lower, or could the gap be luck?
- Splits by the previous day's India VIX and by market-wide fall days (Nifty 50 down 2% or more).

## 3.6 Techniques and why they were chosen

[[FIG:techniques|report/figures/v_techniques.png|Techniques used in the study, why they were chosen and what they answer|Author's design|Table-style graphic with three columns: technique, reason for choosing it, and the research question it answers, for ten techniques from GARCH models to SHAP values.]]

{{fig:techniques}} links each technique to the question it answers.

## 3.7 Changes from the Phase 1 plan

{{tab:changes}} lists each change, checked against the code.

[[MDTABLE:changes|Changes from the Phase 1 plan|nifty50_var_pipeline.py, config/universe.csv, src/, frontend/]]
| Area | Phase 1 plan | As built | Reason |
|---|---|---|---|
| Sample | All {{n_cand}} stocks | {{n_stocks}}-stock balanced panel | {{n_excl_late}} later listings, {{n_excl_ca}} price errors removed |
| Test window | Shorter | To {{data_last}} | Covers the October 2026 hike |
| ML target | Rolling quantile | Next-day return; historical simulation as benchmark | VaR must cover the real return |
| Basel zones | 95% and 99% | 99% only | The traffic light is defined at 99% |
| Inputs | Indicators, Nifty lags, return × repo term | Not built; labelled input sets | Small, testable input sets |
| Scoring | Classifiers; RMSE, MAE | Quantile and volatility models; pinball, FZ0 | VaR and ES are tail measures |
| Tuning | Cross-validation; AIC/BIC choice | Fixed settings; all six GARCH reported | No tuning on shuffled data |
| MLP | Dropout | L2 penalty | scikit-learn's MLP has no dropout |
| GARCH refit | Quarterly | Every 20 trading days | Closer to desk practice |
| Deep learning | LSTM | Not done | Simpler ML did not beat GARCH |
| Dashboard | Power BI | React site on GitHub Pages | Free, public, updated daily |
| Monthly data | CPI and IIP | Left out on purpose | Monthly, late and revised |
| Exchange rate | Not specified | USD/INR from Yahoo Finance | Same source as prices |

[[MEANS]] Every change keeps the contest fair and closer to how a desk works. None was made after seeing test results.
