# CHAPTER 5: DATA ANALYSIS AND INTERPRETATION

All numbers in this chapter are read from files in outputs/ by src/report_numbers.py; the source of each table and figure is given under it. Unless stated otherwise, the machine-learning (ML) models use price and volume inputs only, which is the baseline set; Section 5.9 compares the other input sets.

## 5.1 Data cleaning and preprocessing

{{tab:cleaning}} records every cleaning step applied to the {{n_stocks}}-stock panel and its result.

[[TABLE:cleaning|cleaning]]

[[MEANS]] The data needed little repair: no missing or duplicate rows, and every file matched its hash. The main issue was {{zero_vol_rows}} placeholder rows with zero volume that Yahoo Finance inserts on some holidays; left in, they would create fake zero returns and impossible volume features, so they were removed and logged rather than silently dropped.

## 5.2 Statistical analysis: model estimates

{{tab:garch}} shows the GARCH parameters estimated on 2015 to 2023, the fit each model starts the test window with (later refits every 20 days are not stored).

[[TABLE:garch|garch]]

[[MEANS]] Three facts matter for risk. Volatility is very persistent (median persistence {{pers_med}} for GJR-t), so a turbulent day raises risk for weeks, not just for the next day. Bad news matters more than good news: the GJR asymmetry term was positive for {{gjr_gamma_pos}} of {{n_stocks}} stocks and significant at 5% for {{gjr_gamma_sig}}. And tails are fat: the median Student-t degrees of freedom is {{nu_med}}, far from the bell curve. By the Akaike criterion a Student-t model fitted best for {{aic_tshare}} of {{n_stocks}} stocks (EGARCH-t for {{aic_egarcht}}), which anticipates the backtest results below. The ML settings (number of trees, depth, network layers) are fixed values listed in Appendix E; they were not tuned on the test window.

## 5.3 How often were the forecasts beaten? VaR backtests

{{fig:exc}} compares each model's breach rate with the ideal, and {{tab:bt99}} and {{tab:bt95}} give the full backtest results.

[[FIG:exc|report/figures/v_exc_rate_ideal.png|Breach rate of each model against the ideal, 99% and 95% VaR, all stocks|outputs/tables/summary_price.csv|Two horizontal bar charts of breach rates by model with dashed ideal lines at 1% and 5%; GARCH-t models sit just below 1% and ML models above it.]]

[[MEANS]] At 99%, the three classic models with Student-t errors were closest to the nominal 1%: {{closest1}} {{closest1_exc}}, {{closest2}} {{closest2_exc}} and {{closest3}} {{closest3_exc}}. They were slightly conservative, so a desk using them would hold a little more margin than strictly needed. Every ML model was breached more often than 1% (XGBoost {{exc99_xgb}}, Random Forest {{exc99_rf}}, MLP {{exc99_mlp}}), as were the Normal GARCH models and historical simulation, so a desk using them would hold too little on the worst days. Over a year, XGBoost would be breached about {{gap_xgb_gjrt_yr}} more times per stock than GJR-t, or about {{gap_xgb_gjrt_panel}} more breaches across the whole panel.

[[TABLE:bt99|bt99]]

[[MEANS]] The tests confirm the breach rates. GJR-t passed the Kupiec test for {{kup99_gjrt}} of stocks and stayed in the Basel green zone in {{green_gjrt}} of 250-day windows; XGBoost passed Kupiec for {{kup99_xgb}} and was green in {{green_xgb}}. For a bank, falling out of the green zone means a higher capital multiplier, so this gap is a direct cost. The Basel zones penalise too many breaches, not too few, so the slight conservatism of the t-models does not count against them.

[[TABLE:bt95|bt95]]

[[MEANS]] At 95% the picture is the same in direction: the t-models were slightly conservative ({{exc95_gjrt}} for GJR-t against 5%) and the ML models were breached more often than nominal (XGBoost {{exc95_xgb}}). The Normal GARCH models over-forecast risk at 95% but under-forecast it at 99%, the classic sign of a bell curve fitted to fat-tailed data.

{{fig:heat}} shows the 99% breach rate for every stock and model.

[[FIG:heat|outputs/figures/print/fig04_exception_heatmap_99.png|99% VaR breach rate by stock and model; white is the nominal 1%, orange above and purple below|outputs/tables/backtest_results_price.csv (src/make_figures.py)|Heatmap with ten models as rows and 41 stocks as columns in two panels; ML rows contain more orange cells, GARCH-t rows more purple cells.]]

[[MEANS]] The breach rate was above 1% for {{abovegrid_garch}} of GARCH stock-model cells and {{abovegrid_ml}} of ML cells; GJR-t was above 1% for {{above1_gjrt}} of {{n_stocks}} stocks and XGBoost for {{above1_xgb}}. The problem with the ML models is therefore broad, not driven by one or two difficult stocks.

{{fig:kc}} plots, for each stock and model, the Kupiec and Christoffersen independence p-values.

[[FIG:kc|outputs/figures/print/fig07_kupiec_vs_christoffersen.png|99% VaR backtests per stock: Kupiec against Christoffersen independence p-values (dashed lines = 5% significance)|outputs/tables/backtest_results_price.csv (src/make_figures.py)|Scatter of p-values with one point per stock and model; most points lie above and to the right of the 5% lines; many points overlap because p-values take a limited set of values.]]

[[MEANS]] {{bothpass_garch}} of GARCH stock-model results passed both tests, against {{bothpass_ml}} of ML results. Failing the first test means the wrong amount of margin; failing the second means failures come in runs, when a firm can least absorb them. Many points overlap because with about {{exp_breaches_stock}} expected breaches per stock the p-values can only take a few values.

{{fig:board}} ranks the models by how close their 99% breach rate is to 1% and lists the other measures alongside.

[[FIG:board|outputs/figures/print/fig10_leaderboard.png|Models ordered by closeness of the 99% breach rate to nominal (not a ranking of overall quality)|outputs/tables/summary_price.csv (src/make_figures.py)|Table graphic with ten models in rows and columns for distance from 1%, breach rates, pass rates, Basel green share, FZ0 and ES ratio; GARCH rows shaded red and ML rows blue.]]

[[MEANS]] The ordering is by breach rate only. The t-models lead on every column a regulator looks at, but the ordering alone does not prove that one model's overall forecasts are better; Section 5.6 tests that directly.

## 5.4 One stock up close

{{fig:rel}} shows Reliance Industries as an example of what the forecasts look like day by day.

[[FIG:rel|outputs/figures/print/fig03_var_vs_returns_RELIANCE.png|Reliance Industries: daily returns with the 99% VaR of GJR-t and XGBoost, and breaches|outputs/tables/by_ticker/price/RELIANCE.NS__daily.parquet (src/make_figures.py)|Line chart of Reliance daily returns with two VaR lines below; triangles and crosses mark breaches.]]

[[MEANS]] Over {{rel_days}} test days about {{exp_breaches_stock}} breaches would be ideal; GJR-t was breached {{rel_gjrt}} times and XGBoost {{rel_xgb}} times. The GJR-t line widens quickly after large falls and then decays, which is the volatility clustering shown in Section 5.2.

## 5.5 How big were the losses on the very bad days? Expected Shortfall

{{fig:es}} compares the realised average loss on breach days with the forecast ES on those days.

[[FIG:es|outputs/figures/print/fig08_es_calibration.png|Expected Shortfall calibration: realised loss on breach days over forecast ES (1 = exact)|outputs/tables/backtest_results_price.csv (src/make_figures.py)|Two panels of box plots, 95% and 99%, of the ratio of actual to forecast ES per stock for each model, with a dashed line at 1.]]

[[MEANS]] At 99%, the average ratio was above 1 for {{n_es_above1}} of {{n_models}} models: on the very bad days, every model under-forecast the size of the loss somewhat. The gap was small for the t-models (GJR-t {{es99_gjrt}}, GARCH-t {{es99_garcht}}) and largest for the Normal models (EGARCH-normal {{es99_egarchn}}, GJR-normal {{es99_gjrn}}). XGBoost's ratio ({{es99_xgb}}) is closer to 1; this may partly reflect its higher breach rate, since a model breached more often includes milder losses among its breach days. A risk team should treat ES forecasts as a floor, not a ceiling.

## 5.6 Is the difference real, or just luck? Joint loss and significance tests

{{fig:dm}} counts the Diebold-Mariano results on the FZ0 loss, and {{tab:dm}} adds the pinball-loss tests.

[[FIG:dm|report/figures/v_dm_bar.png|Diebold-Mariano tests on FZ0 (95%): each ML model against each of the six GARCH models for every stock|outputs/tables/diebold_mariano_price.csv; outputs/tables/report/dm_fz0_95_counts.csv|Stacked horizontal bars for XGBoost, Random Forest and MLP showing GARCH significantly better, ML significantly better and no significant difference; grey dominates and red is much larger than blue.]]

[[MEANS]] Of {{dm_total}} comparisons, GARCH had significantly lower loss in {{dm_g}}, ML in {{dm_m}}, and {{dm_n}} ({{dm_none_share}}) showed no significant difference. Most gaps in overall quality are therefore too small to be sure about with about three years of data, but where a gap is real it almost always favours GARCH. There is no evidence here that would justify replacing GARCH with ML.

[[TABLE:dm|dm]]

[[MEANS]] The pinball tests give the same direction for VaR alone: GARCH was significantly better in {{dmp95_g}} pairs at 95% and {{dmp99_g}} at 99%, against {{dmp95_m}} and {{dmp99_m}} for ML. The exception is Random Forest at 95% pinball, where it was significantly better than GARCH in {{dmp95_m_rf}} pairs and worse in {{dmp95_g_rf}}: for the 95% VaR alone, Random Forest is competitive. MLP was the weakest ML model ({{dm_g_mlp}} pairs in favour of GARCH and {{dm_m_mlp}} in favour of MLP on FZ0).

{{fig:fz}} contrasts the mean and median FZ0 loss, and {{tab:norisk}} explains the gap for XGBoost.

[[FIG:fz|outputs/figures/print/fig11_fz0_mean_median.png|Joint VaR-ES loss (FZ0): mean (open) and median (filled) across stocks, 95% and 99%|outputs/tables/summary_price.csv (src/make_figures.py)|Dot plot of mean and median FZ0 loss by model for 95% and 99%; XGBoost's 99% mean is off the scale and annotated.]]

[[TABLE:norisk|norisk]]

[[MEANS]] XGBoost's mean 99% FZ0 is {{fz99_xgb}}, against a median of {{fzmed99_xgb}}. The cause is "no-risk" days: on {{norisk99_xgb}} stock-days at 99% XGBoost forecast a lower-tail quantile at or above zero, so its VaR fell to the floor and any loss counted as a breach. {{fig:lt}} shows the decisive case.

[[FIG:lt|report/figures/v_lt_norisk.png|Larsen & Toubro: the XGBoost no-risk day and its effect on the 99% FZ0 loss|outputs/tables/by_ticker/price/LT.NS__daily.parquet; outputs/tables/backtest_results_price.csv|Line chart around April 2025 of L&T returns with GJR-t and XGBoost 99% VaR; on 16 April 2025 the XGBoost VaR rises to zero and a small loss becomes a breach, annotated.]]

[[MEANS]] On {{nr_date}}, XGBoost's 99% VaR for {{nr_stock}} sat at its floor, so an ordinary loss of {{nr_ret}} became {{nr_breach}}, while GJR-t's VaR that day was {{nr_gjrt_var}}. FZ0 punishes a forecast of no risk very heavily, and this single day lifted {{nr_stock}}'s mean 99% FZ0 to {{nr_fz0}}, against a median of {{nr_fz0med}}. For a business user the lesson is plain: a model that can ever say "no risk" for a large-cap stock is not safe for margins or limits, however good its average looks on other days.

## 5.7 Calm versus stressed markets

{{fig:vix}} and {{tab:regime}} show the FZ0 loss in each quartile of the previous day's India VIX.

[[FIG:vix|outputs/figures/print/fig05_vix_quartiles_fz0.png|Joint VaR-ES loss by previous-day India VIX quartile (mean across stocks, ±1 standard error)|outputs/tables/regime_results_price.csv (src/make_figures.py)|Dot plot of mean FZ0 by model in four VIX quartiles; losses rise from the calm to the stressed quartile and GARCH dots sit below ML dots in the stressed quartile.]]

[[TABLE:regime|regime]]

[[MEANS]] Loss was higher in the most fearful quartile than in the calmest for {{q4_worse_all}} models, so every model found stressed days harder. In the stressed quartile the lowest loss came from {{q4_best}} (GJR-t {{q4_gjrt}}, XGBoost {{q4_xgb}}). The hope that ML would pull ahead when markets are fearful is not supported by these results.

{{tab:posthike}} reports the weeks after the RBI repo hike of 7 October 2026.

[[TABLE:posthike|posthike]]

[[MEANS]] The post-hike period is only {{ph_days}} trading days ({{ph_obs}} stock-days, about {{ph_exp}} expected breaches at 99%), too short for firm conclusions. Breaches were rare for every model (GJR-t {{ph_gjrt}}, XGBoost {{ph_xgb}}); the rate rise did not cause a burst of model failures in these weeks.

## 5.8 Do bad days come together?

{{fig:stress}} and {{tab:stress}} show how many breaches fell on market-wide stress days, and {{fig:byday}} shows breaches day by day.

[[FIG:stress|report/figures/v_stress_share.png|Share of 99% VaR breaches that fell on market-wide stress days (Nifty 50 down 2% or more)|outputs/tables/breach_days_summary_price.csv|Bar chart of the share of breaches on stress days for each model, all between about 16% and 21%, far above a dashed line at 1.5% showing the share of days that were stress days.]]

[[MEANS]] Stress days were only {{stress_days}} of {{mkt_days}} test days ({{stress_share_days}}), yet they carried between {{stress_min}} and {{stress_max}} of each model's breaches ({{stress_gjrt}} for GJR-t, {{stress_xgb}} for XGBoost). No model, classic or ML, avoids this. For a portfolio or a clearing corporation this is the risk that matters: many positions lose more than forecast on the same day.

[[TABLE:stress|stress]]

[[FIG:byday|outputs/figures/print/fig13_breaches_by_day.png|Number of stocks breaching 99% VaR on each day, GJR-t and XGBoost; triangles mark stress days|outputs/tables/breach_days_price.csv (src/make_figures.py)|Two bar charts over 2024 to 2026 of the number of stocks breaching on each day; tall bars line up with stress-day triangles, the tallest on 4 June 2024.]]

[[MEANS]] On the worst day, {{worst_date}}, the Nifty 50 fell {{worst_nifty}} and {{worst_n}} of {{n_stocks}} stocks breached their GJR-t VaR at once. A one-stock VaR cannot see this kind of common shock; a separate stress buffer for market-wide fall days is needed whichever model is used.

## 5.9 Do market inputs help the ML models?

{{fig:shap}} shows which inputs move XGBoost's 99% forecast when the India VIX is added.

[[FIG:shap|outputs/figures/print/fig06_xgb_shap_importance.png|XGBoost 99% VaR: mean absolute SHAP contribution of each input (price/volume + India VIX level set; mean over 41 stocks)|outputs/tables/xgb_shap_importance_price_vixlevel_summary.csv (src/make_figures.py)|Horizontal bar chart of SHAP importance; the India VIX level is the longest bar, followed by the 20-day volume change.]]

[[MEANS]] The VIX level ({{shap_top}}) had the largest effect on the forecast, {{shap_top_bp}} basis points on average, ahead of {{shap_2nd}} ({{shap_2nd_bp}}). Having a large effect is not the same as improving the forecast, which {{tab:sets}} tests.

[[TABLE:sets|sets]]

[[MEANS]] Adding the VIX level moved every ML model's 99% breach rate further from 1% (XGBoost {{vix_exc99_xgb}}, Random Forest {{vix_exc99_rf}}, MLP {{vix_exc99_mlp}}), and the pinball ratio was close to 1 for all sets. In the test years, these market inputs did not make the ML forecasts more reliable.

{{tab:valtest}} compares the validation window, where the input sets were chosen, with the test window.

[[TABLE:valtest|valtest]]

[[MEANS]] The VIX-level set was chosen fairly, on the validation window only ({{sel_overall}}), where it lowered pinball loss. In {{flip}} of {{flip_of}} model-and-set cases the inputs helped on validation but hurt on test: their value changed between periods. {{tab:ranges}} offers one reason.

[[TABLE:ranges|ranges]]

[[MEANS]] The USD/INR level was outside the range seen in fitting on {{out_usdinr}} of test days, and tree models cannot extrapolate beyond the values they were trained on; using it as a level is unsafe. The VIX level was outside its range on only {{out_vix}} of days, so range shift does not explain the VIX result. Over-fitting was not tested directly, so it is not claimed as the cause. The repo rate, CPI and IIP could not be tested because the official files were not yet supplied.

## 5.10 Sector differences

{{fig:sector}} and {{tab:sector}} show how the forecast risk differs by sector.

[[FIG:sector|outputs/figures/print/fig09_sector_var.png|Average one-day 99% VaR from GJR-t by sector (each point is one stock, test window)|outputs/tables/by_ticker/price/*__daily.parquet (src/make_figures.py)|Box plots of average 99% VaR by sector, from FMCG at the low end to Services and Capital Goods at the high end, with Financial Services showing the widest spread.]]

[[TABLE:sector|sector]]

[[MEANS]] The typical forecast one-day 99% loss ranged from {{sec_low_var}} for {{sec_low}} to {{sec_high_var}} for {{sec_high}} (a sector with {{sec_high_n}} stock in the panel); across all stocks the average was {{avg_var99}}. A single margin rate or position limit for all large caps would therefore over-charge defensive stocks and under-charge volatile ones. XGBoost's 99% breach rate was higher than GJR-t's in {{sec_xgb_worse}} of {{n_sec}} sectors.

## 5.11 Robustness checks

- **Excluded crash-prone stock.** Adani Enterprises was excluded for a suspected corporate action in 2015 but also had genuine crashes in 2023 and 2024. Run separately from June 2015 with those crashes kept, its 99% breach rates were {{adani_gjrt}} for GJR-t, {{adani_xgb}} for XGBoost and {{adani_hs}} for historical simulation, so the exclusion does not hide a model failure on a crash-prone stock.
- **XGBoost ES approximation.** ES for XGBoost is the mean of five deeper quantiles. A check against known distributions found this understates true ES by at most {{es_bias_max}} (outputs/tables/xgb_es_approx_bias.csv), too little to change the conclusions.
- **Frozen data.** All results come from the hashed snapshot, with fixed seeds, so a rerun on the snapshot should reproduce them; an exact-match rerun on sample stocks is part of the final quality check.

## 5.12 Hypotheses and findings

{{tab:hyp}} sets out each hypothesis, the evidence and the decision, applied mechanically to the results above.

[[TABLE:hyp|hyp]]

**Interpretation and findings.**

1. GARCH-family models with Student-t errors gave the most reliable one-day VaR for Nifty 50 stocks in 2024 to 2026: breach rates closest to nominal, the highest Kupiec and Basel green shares, and significantly lower joint loss wherever a difference was significant.
2. The ML models were breached more often than nominal at both levels. Their overall loss was mostly not significantly different from GARCH, and where it was, GARCH was better far more often.
3. A forecast of "no risk" by XGBoost on a few stock-days is a model-risk issue on its own, not just a statistical curiosity.
4. Every model under-forecast losses on market-wide stress days; breaches cluster across stocks.
5. The India VIX moved the ML forecasts a lot but did not improve them in the test years; USD/INR as a level is unsafe because of range shift.
6. Risk differs widely by sector, so limits should differ too.
