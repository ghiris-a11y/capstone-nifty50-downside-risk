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

## 6.3 Where machine learning did not help, and its role

The machine-learning models we tested did not help with the main job. At 99% they were breached more often than nominal (XGBoost {{exc99_xgb}}, Random Forest {{exc99_rf}}, MLP {{exc99_mlp}}, against {{exc99_gjrt}} for GJR-t), they set aside less money on average (Rs {{buf_mlfam}} crore per Rs 100 crore for the three ML models, against Rs {{buf_tfam}} crore for the Student-t GARCH models; {{tab:buffers}}), and where joint loss differed significantly GARCH was better in {{dm_g}} pairs against {{dm_m}}. Adding the India VIX did not bring them closer to the nominal rate (Section 5.9). The recommendation is therefore not to use them for limits, margins or capital.

Machine learning should not be discarded altogether, but its role should match the evidence. Random Forest was competitive for 95% VaR (significantly better than GARCH in {{dmp95_m_rf}} pairs and worse in {{dmp95_g_rf}} on pinball loss), so it can serve as a challenger model for internal 95% limits. Any ML model used should be refitted regularly (in this study it was fitted once), screened for "no-risk" forecasts, and restricted to inputs that stay within the range seen in training; the USD/INR level, for example, was outside that range on {{out_usdinr}} of test days.

## 6.4 Stress-day cushion and an India VIX alert

{{tab:cushion}} shows why a separate stress rule is needed and how large it would have to be.

[[TABLE:cushion|cushion]]

[[MEANS]] On market-wide stress days ({{st_obs}} stock-days) GJR-t was breached on {{st_br_gjrt}} of stock-days, against {{ns_br_gjrt}} on other days. To keep stress-day breaches to 1%, the forecast would have needed to be about {{st_mult99}} times larger on those days, and the average loss beyond VaR on a stress-day breach was {{st_excess}} of the position. By contrast, a high India VIX the day before did not signal more breaches: on days after the VIX closed above {{vix_q4_edge}} (the top quarter of test days), GJR-t's breach rate was {{br_q4_gjrt}}, against {{br_q13_gjrt}} on other days.

The rule that follows from the data has two parts:

- **Stress add-on (margins and limits).** Hold a standing stress buffer, sized as a market-fall scenario of about {{st_mult99}} times the normal 99% VaR, for the positions most exposed to a market-wide fall. It should not be switched on and off by a forecast, because stress days are not known in advance.
- **India VIX alert (monitoring, not margins).** When the India VIX closes above {{vix_q4_edge}}, the risk desk reviews concentrated positions and checks that the stress buffer is in place the next morning. Because the high-VIX breach rate was close to the normal rate, the VIX should trigger a review, not an automatic increase in margins.

## 6.5 Sector margins

Section 5.10 showed that the typical one-day 99% VaR ranged from {{sec_low_var}} for {{sec_low}} to {{sec_high_var}} for {{sec_high}}. A single margin or limit rate for all large caps would over-charge the steadier sectors and under-charge the volatile ones. The recommended rule is a sector floor (the sector's median VaR) that a stock's own GJR-t VaR can raise but not lower. Sectors with only one or two stocks in the panel, such as {{sec_high}} ({{sec_high_n}} stock), should be reviewed stock by stock rather than given a sector rate.

## 6.6 Expected benefits

The benefits below are computed from the outputs, with the assumptions stated. {{tab:buffers}} shows the money each model would set aside for one bad day.

[[TABLE:buffers|buffers]]

[[MEANS]] The Student-t GARCH models set aside about Rs {{buf_tfam}} crore for every Rs 100 crore held, the machine-learning models about Rs {{buf_mlfam}} crore. The ML models look cheaper only because they set aside less, and they were breached more often for exactly that reason; the saving is not a real gain.

Assumptions: one-day horizon; a position held equally in each stock; 250 trading days a year; buffers are the average 99% VaR over the test window, not a regulatory capital charge (which would apply multipliers and a 10-day horizon).

- **Fewer breaches.** Replacing XGBoost with GJR-t would avoid about {{gap_xgb_gjrt_yr}} 99% breaches per stock per year (difference in breach rates × 250 trading days), or about {{gap_xgb_gjrt_panel}} across a {{n_stocks}}-stock book. Against Random Forest the saving is about {{gap_rf_gjrt_yr}} per stock per year.
- **Capital and margin sizing.** The average one-day 99% VaR from GJR-t across the panel was {{avg_var99}}, which means a buffer of about ₹{{buffer_100cr}} crore for every ₹100 crore held in a single stock (range {{avg_var99_min}} to {{avg_var99_max}} by stock). This is the scale of money a too-low forecast leaves uncovered, and a too-high one ties up.
- **Clustered losses covered.** A stress add-on targets the {{stress_share_days}} of days that carried about a fifth of all breaches ({{stress_gjrt}} for GJR-t), so a small, rarely used buffer covers a large share of the shortfalls.

## 6.7 30/60/90-day implementation roadmap

{{fig:roadmap}} and {{tab:roadmap}} show a 90-day rollout followed by regular reviews.

[[FIG:roadmap|report/figures/v_roadmap.png|Implementation roadmap for the recommended risk process|Author's recommendation|Five boxes in sequence: month 1 data checks, month 2 shadow run of GJR-t, month 3 backtest and go-live with a stress add-on, quarterly re-validation and yearly review of ML challengers.]]

[[MDTABLE:roadmap|30/60/90-day implementation plan|Author's recommendation, based on Chapters 5 and 6]]
| Period | Actions | Done when |
|---|---|---|
| Days 1-30 | Freeze a data snapshot; validate prices; set up the daily GJR-t VaR and ES run and the dashboard | Daily run completes unattended for 20 trading days |
| Days 31-60 | Run GJR-t in shadow beside the current method; set sector floors; agree the stress buffer and the India VIX alert level | Monthly breach report reviewed by the risk committee |
| Days 61-90 | Backtest the shadow period (breach count, misses in a row, FZ0); go live for limits and margins with the stress buffer | Breach rate within the Kupiec range; sign-off by model-risk review |
| Every month | Count breaches across stocks; flag days with many stocks breached together | Report filed |
| Every quarter / year | Re-validate the models; test any machine-learning challenger against GJR-t on the same backtests | Challenger adopted only if it passes every test and is significantly better |

[[MEANS]] Running the new model in parallel with the existing one for a month before switching lets a desk see real breaches and margin changes without risk, and the quarterly and yearly reviews keep the model from drifting as markets and interest rates change.

## 6.8 Feasibility and viability

{{tab:feas}} assesses the recommended set-up on cost, skills, compute, governance, regulatory fit and risks.

[[MDTABLE:feas|Feasibility and viability of the recommended approach|data/logs/run.log, data/logs/run_test_rerun.log, .github/workflows/daily_update.yml, requirements.txt]]
| Dimension | Assessment |
|---|---|
| Data cost | Free daily prices (Yahoo Finance) for research; a production desk would switch to licensed exchange data, with the same pipeline |
| Skills | One analyst with Python; GARCH models are standard in the open-source arch package |
| Compute | About {{sec_per_stock}} seconds per stock for all ten models over the test window on a laptop; about {{min_per_set}} minutes for the full panel using {{n_jobs}} parallel workers; the daily GJR-t update runs in a free GitHub Action |
| Governance and explainability | GARCH parameters have a clear meaning (persistence, asymmetry, tail thickness) and can be reviewed by a model-risk committee; ML models need SHAP-type explanations |
| Regulatory fit | 99% VaR backtests and Basel traffic-light zones are the tests banks report; GARCH-t passed them most often; ES is reported alongside VaR, as the Basel market-risk framework expects |

[[MEANS]] The recommended set-up is cheap to run and easy to govern. The main cost is not computing power but discipline: monthly backtests, a stress add-on and a clear rule that challenger models must earn their place.

## 6.9 Risks and mitigations

{{tab:risks}} lists the main risks of the recommended set-up, the evidence for each in this study and a control for it.

[[MDTABLE:risks|Risks of the recommended approach and how to reduce them|Author's assessment, based on Chapter 5]]
| Risk | Evidence in this study | Mitigation |
|---|---|---|
| Many stocks lose together on one day | {{stress_gjrt}} of GJR-t breaches fell on {{stress_share_days}} of days | Standing stress buffer (Section 6.4); monthly cluster report |
| Losses on very bad days exceed the ES forecast | Actual/forecast ES above 1 for {{n_es_above1}} of {{n_models}} models | Prudence margin on ES; report ES with VaR |
| A machine-learning model forecasts no risk | XGBoost did so on {{norisk99_xgb}} stock-days at 99% | Floor check before any ML forecast is used; ML only as a challenger |
| Inputs move outside the range seen in training | USD/INR level out of range on {{out_usdinr}} of test days | Use changes, not levels; range checks in the daily run |
| Errors in free price data | {{n_excl_ca}} stocks excluded for suspected corporate-action errors | Licensed exchange data in production; daily validation and logging |
| Regime change, for example a rate cycle | Only {{ph_days}} trading days after the 7 October 2026 hike | Quarterly re-validation; review after each MPC decision |
| Over-reliance on one model | All results come from one test window | Keep a challenger model and the historical-simulation benchmark in the monthly report |

[[MEANS]] None of these risks is a reason to delay. Each has a low-cost control, and most are already built into the daily pipeline and the dashboard.
