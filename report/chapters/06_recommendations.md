# CHAPTER 6: RECOMMENDATIONS

The recommendations follow only from the results in Chapter 5. The central finding is that machine learning did not outperform the classic models for this task: the GARCH models with Student-t errors were closest to the expected breach frequency and, where differences were significant, had lower loss. The recommendations therefore keep those models as the default and give machine learning a controlled, secondary role.

## 6.1 Decision table by user

{{fig:decision}} sets out, for five types of user, the recommended approach, the evidence behind it, the expected benefit and how viable it is.

[[FIG:decision|report/figures/v_decision_table.png|Recommendation decision table: user, recommended approach, evidence, expected benefit and viability|Author's recommendations; evidence from outputs/tables/summary_price.csv, diebold_mariano_price.csv, breach_days_summary_price.csv and outputs/tables/report/sector_summary_price.csv|Table graphic with five rows (bank market-risk desk, broker margin team, portfolio manager, retail or fintech app, exchange or regulator) and columns for approach, evidence, expected benefit and viability.]]

[[MEANS]] Every user gets the same core model, a GARCH-t forecast, because it was the most reliable across all the checks. What differs is what each user adds on top: a stress buffer for brokers, sector limits for fund managers, plain-language display for apps and cross-stock monitoring for the exchange.

### 6.1.1 Bank market-risk desk

Use GJR-GARCH-t or EGARCH-t for one-day 99% VaR and ES, re-estimated at least monthly. In the test, GJR-t was breached on {{exc99_gjrt}} of days, passed the Kupiec test for {{kup99_gjrt}} of stocks and was in the Basel green zone in {{green_gjrt}} of windows. A bank in the amber or red zone pays a higher capital multiplier, so staying green has a direct cost benefit. Because every model under-forecast ES on the very bad days (Section 5.5), add a margin of prudence to ES rather than treating it as exact.

### 6.1.2 Broker margin team

Use a GARCH-t daily VaR as the base margin and add a rule-based stress add-on when the market falls sharply. {{stress_gjrt}} of GJR-t breaches fell on the {{stress_share_days}} of days when the Nifty 50 fell 2% or more, and on the worst day {{worst_n}} of {{n_stocks}} stocks breached at once. Margin shortfalls are therefore concentrated on a handful of days, which is where the add-on is needed.

### 6.1.3 Portfolio manager

Set position limits from each stock's GJR-t VaR rather than a single rule for all large caps. The typical forecast one-day 99% loss ranged from {{sec_low_var}} ({{sec_low}}) to {{sec_high_var}} ({{sec_high}}). Limits that follow each stock's risk let a fund hold more of its steadier stocks without taking on more total risk.

### 6.1.4 Retail or fintech app

Show the GJR-t "likely worst daily loss" for the next day in plain words, refreshed every evening. The project's GitHub Action and dashboard do this automatically at almost no cost (Appendix G), and the dashboard text scored between grade {{fk_min}} and {{fk_max}} on the Flesch-Kincaid scale across its tabs (outputs/dashboard_check/readability.json). Investors who see "on a bad day you could lose about ₹{{buffer_100cr}} on every ₹100 held" can size positions sensibly.

### 6.1.5 Exchange or regulator

Monitor breach clustering across stocks, not only stock by stock, and require any ML risk model to pass the same backtests as a GARCH model, including a check that it never forecasts zero risk. XGBoost forecast no risk on {{norisk99_xgb}} stock-days at 99% (Section 5.6), a failure mode that standard averages can hide.

## 6.2 Which model for which situation

{{fig:flow}} turns the recommendations into a simple decision path.

[[FIG:flow|report/figures/v_model_flow.png|Which model for which situation: a decision flow for one-day VaR and ES|Author's recommendations based on Chapter 5|Decision flow starting from the need for a one-day VaR, branching on regulatory use to GJR-GARCH-t or a GARCH-t default with ML challengers, then branching on whether the market is falling sharply to a stress buffer or normal use.]]

[[MEANS]] The path is deliberately short. For any regulatory or money-setting use, a GARCH-t model is the answer; ML models can be shown as challengers for internal views, and only after passing the same tests. The second question, whether the whole market is falling, matters more for losses than the choice between models.

## 6.3 Role for machine learning

Machine learning should not be discarded, but its role should match the evidence. Random Forest was competitive for 95% VaR (significantly better than GARCH in {{dmp95_m_rf}} pairs and worse in {{dmp95_g_rf}} on pinball loss), so it can serve as a challenger model for internal 95% limits. Any ML model used should be refitted regularly (in this study it was fitted once), screened for "no-risk" forecasts, and restricted to inputs that stay within the range seen in training; the USD/INR level, for example, was outside that range on {{out_usdinr}} of test days.

## 6.4 Feasibility and viability

{{tab:feas}} assesses the recommended set-up on cost, skills, compute, governance, regulatory fit and risks.

[[MDTABLE:feas|Feasibility and viability of the recommended approach|data/logs/run.log, data/logs/run_test_rerun.log, .github/workflows/daily_update.yml, requirements.txt]]
| Dimension | Assessment |
|---|---|
| Data cost | Free daily prices (Yahoo Finance) for research; a production desk would switch to licensed exchange data, with the same pipeline |
| Skills | One analyst with Python; GARCH models are standard in the open-source arch package |
| Compute | About {{sec_per_stock}} seconds per stock for all ten models over the test window on a laptop; about {{min_per_set}} minutes for the full panel using {{n_jobs}} parallel workers; the daily GJR-t update runs in a free GitHub Action |
| Governance and explainability | GARCH parameters have a clear meaning (persistence, asymmetry, tail thickness) and can be reviewed by a model-risk committee; ML models need SHAP-type explanations |
| Regulatory fit | 99% VaR backtests and Basel traffic-light zones are the tests banks report; GARCH-t passed them most often |
| Risks | Common shocks across stocks; data errors in free sources; changes in the rate regime; over-reliance on any single model |

[[MEANS]] The recommended set-up is cheap to run and easy to govern. The main cost is not computing power but discipline: monthly backtests, a stress add-on and a clear rule that challenger models must earn their place.

## 6.5 Expected benefits

The benefits below are computed from the outputs, with the assumptions stated.

- **Fewer breaches.** Replacing XGBoost with GJR-t would avoid about {{gap_xgb_gjrt_yr}} 99% breaches per stock per year (difference in breach rates × 250 trading days), or about {{gap_xgb_gjrt_panel}} across a {{n_stocks}}-stock book. Against Random Forest the saving is about {{gap_rf_gjrt_yr}} per stock per year.
- **Capital and margin sizing.** The average one-day 99% VaR from GJR-t across the panel was {{avg_var99}}, which means a buffer of about ₹{{buffer_100cr}} crore for every ₹100 crore held in a single stock (range {{avg_var99_min}} to {{avg_var99_max}} by stock). This is the scale of money a too-low forecast leaves uncovered, and a too-high one ties up.
- **Clustered losses covered.** A stress add-on targets the {{stress_share_days}} of days that carried about a fifth of all breaches ({{stress_gjrt}} for GJR-t), so a small, rarely used buffer covers a large share of the shortfalls.

## 6.6 Implementation roadmap

{{fig:roadmap}} shows a three-month rollout followed by regular reviews.

[[FIG:roadmap|report/figures/v_roadmap.png|Implementation roadmap for the recommended risk process|Author's recommendation|Five boxes in sequence: month 1 data checks, month 2 shadow run of GJR-t, month 3 backtest and go-live with a stress add-on, quarterly re-validation and yearly review of ML challengers.]]

[[MEANS]] Running the new model in parallel with the existing one for a month before switching lets a desk see real breaches and margin changes without risk, and the quarterly and yearly reviews keep the model from drifting as markets and interest rates change.
