# CHAPTER 5: DATA ANALYSIS AND INTERPRETATION

Every number in this chapter is read from outputs/ by src/report_numbers.py. Unless stated otherwise, the machine-learning (ML) models use price and volume inputs only.

## 5.1 Data cleaning

[[TABLE:cleaning|cleaning]]

[[MEANS]] {{tab:cleaning}} shows the data needed little repair. The one real issue was {{zero_vol_rows}} zero-volume placeholder rows from Yahoo Finance, which were removed and logged. A desk using free data should run the same daily checks before trusting any forecast.

## 5.2 What the GARCH models learned

[[TABLE:garch|garch]]

[[MEANS]] {{tab:garch}} carries three messages for risk. Volatility lasts (median persistence {{pers_med}} for GJR-t), so one bad day raises risk for weeks. Bad news matters more than good news for {{gjr_gamma_pos}} of {{n_stocks}} stocks ({{gjr_gamma_sig}} significant), and tails are fat (median Student-t degrees of freedom {{nu_med}}). A Student-t model fitted best for {{aic_tshare}} stocks, which hints at the results below.

## 5.3 How often were the forecasts beaten?

[[FIG:exc|report/figures/v_exc_rate_ideal.png|Miss rate of each model against the ideal, 99% and 95% VaR, all stocks|outputs/tables/summary_price.csv|Two horizontal bar charts of breach rates by model with dashed ideal lines at 1% and 5%; GARCH-t models sit just below 1% and ML models above it.]]

[[MEANS]] {{fig:exc}} shows the Student-t GARCH models just under the 1% ideal at 99%, so they hold slightly more margin than needed. Every ML model sat above it, so a desk using one would hold too little on the worst days. XGBoost would miss about {{gap_xgb_gjrt_yr}} more times per stock per year than GJR-t.

[[TABLE:bt|bt]]

[[MEANS]] {{tab:bt}} confirms the picture with the formal tests. GJR-t passed the miss-frequency test for {{kup99_gjrt}} of stocks and stayed in the Basel green zone in {{green_gjrt}} of blocks, against {{kup99_xgb}} and {{green_xgb}} for XGBoost. For a bank, leaving the green zone raises its capital multiplier, so this gap has a direct cost.

The Basel share counts complete 250-day blocks from the start of the test. Each stock has {{basel_blocks}} blocks, the last ending on {{basel_last_cov}}, so a stock's share can only be {{basel_values}}. The last {{basel_uncov_min}} to {{basel_uncov_max}} days per stock, including the October 2026 hike, are covered by the other tests but not by the Basel share. Appendix B gives the other test results.

[[FIG:heat|outputs/figures/print/fig04_exception_heatmap_99.png|99% miss rate by stock and model; white is the ideal 1%, orange above and purple below|outputs/tables/backtest_results_price.csv (src/make_figures.py)|Heatmap with ten models as rows and 41 stocks as columns in two panels; ML rows contain more orange cells, GARCH-t rows more purple cells.]]

[[MEANS]] {{fig:heat}} shows the ML problem is broad, not caused by a few hard stocks. XGBoost was above 1% for {{above1_xgb}} of {{n_stocks}} stocks, GJR-t for {{above1_gjrt}}. A firm should not expect stock-by-stock tuning to rescue the ML models.

[[FIG:rel|outputs/figures/print/fig03_var_vs_returns_RELIANCE.png|Reliance Industries: daily returns with the 99% VaR of GJR-t and XGBoost, and misses|outputs/tables/by_ticker/price/RELIANCE.NS__daily.parquet (src/make_figures.py)|Line chart of Reliance daily returns with two VaR lines below; triangles and crosses mark misses.]]

[[MEANS]] {{fig:rel}} shows one stock day by day. Over {{rel_days}} days about {{exp_breaches_stock}} misses would be ideal; GJR-t missed {{rel_gjrt}} times and XGBoost {{rel_xgb}}. The GJR-t limit widens fast after a big fall and then eases, which is how a desk wants a limit to behave.

## 5.4 How big were the losses on the worst days?

[[FIG:es|outputs/figures/print/fig08_es_calibration.png|Real loss on miss days divided by forecast ES (1 = exact), 95% and 99%|outputs/tables/backtest_results_price.csv (src/make_figures.py)|Two panels of box plots, 95% and 99%, of the ratio of actual to forecast ES per stock for each model, with a dashed line at 1.]]

[[MEANS]] {{fig:es}} shows that at 99%, {{n_es_above1}} of {{n_models}} models under-forecast the average loss on the worst days. The gap was small for the Student-t models (GJR-t {{es99_gjrt}}) and larger for the Normal ones (GJR-normal {{es99_gjrn}}). Banks and brokers should treat ES as a floor and add a prudence margin.

## 5.5 Is the difference real, or just luck?

[[FIG:dm|report/figures/v_dm_bar.png|Diebold-Mariano tests on the FZ0 score (95%): each ML model against each GARCH model on every stock|outputs/tables/diebold_mariano_price.csv; outputs/tables/report/dm_fz0_95_counts.csv|Stacked horizontal bars for XGBoost, Random Forest and MLP showing GARCH significantly better, ML significantly better and no significant difference; grey dominates and red is much larger than blue.]]

[[MEANS]] In {{fig:dm}}, {{dm_n}} of {{dm_total}} comparisons ({{dm_none_share}}) showed no real difference. Where a gap was real, GARCH was better {{dm_g}} times and ML {{dm_m}} times. Nothing here justifies replacing GARCH with ML.

[[TABLE:dm|dm]]

[[MEANS]] {{tab:dm}} adds the score for the loss limit alone (pinball score). Random Forest was competitive at 95%, better than GARCH in {{dmp95_m_rf}} pairs and worse in {{dmp95_g_rf}}. A firm could use it as a challenger for internal 95% limits only.

One caution applies to all average scores. XGBoost forecast "no risk" on {{norisk99_xgb}} stock-days at 99%. On {{nr_date}}, for {{nr_stock}}, its loss limit sat at zero, so an ordinary loss of {{nr_ret}} became a miss while GJR-t's limit was {{nr_gjrt_var}}. That one day lifted {{nr_stock}}'s mean 99% FZ0 score to {{nr_fz0}}, against a median of {{nr_fz0med}}. The counts above, not the means, are the fair guide.

## 5.6 Calm versus stressed markets

[[FIG:vix|outputs/figures/print/fig05_vix_quartiles_fz0.png|FZ0 score by quarter of the previous day's India VIX (mean across stocks, ±1 standard error)|outputs/tables/regime_results_price.csv (src/make_figures.py)|Dot plot of mean FZ0 by model in four VIX quartiles; losses rise from the calm to the stressed quartile and GARCH dots sit below ML dots in the stressed quartile.]]

[[MEANS]] {{fig:vix}} shows every model doing worse when the market was nervous ({{q4_worse_all}} models). In the most fearful quarter the best score came from {{q4_best}} (GJR-t {{q4_gjrt}}, XGBoost {{q4_xgb}}). ML did not pull ahead in stress, so a desk gains nothing by switching models when the VIX rises.

[[TABLE:regime|regime]]

[[MEANS]] {{tab:regime}} gives the scores behind the chart (lower is better). Every model scores worse on fearful days than on calm ones. Stress planning therefore matters more than switching models.

## 5.7 Do bad days come together?

[[FIG:stress|report/figures/v_stress_share.png|Share of 99% misses that fell on market-wide fall days (Nifty 50 down 2% or more)|outputs/tables/breach_days_summary_price.csv|Bar chart of the share of breaches on stress days for each model, all between about 16% and 21%, far above a dashed line at 1.5% showing the share of days that were stress days.]]

[[MEANS]] {{fig:stress}} shows that market-wide fall days were {{stress_days}} of {{mkt_days}} test days, yet they held {{stress_min}} to {{stress_max}} of each model's misses. No model avoids this. Clearing corporations and funds need a separate buffer for these days.

[[TABLE:stress|stress]]

[[MEANS]] {{tab:stress}} shows the clustering is shared by every model. On {{worst_date}} the Nifty 50 fell {{worst_nifty}} and {{worst_n}} of {{n_stocks}} stocks missed their GJR-t limit together. Brokers should expect margin calls to arrive in bunches on such days.

[[FIG:byday|outputs/figures/print/fig13_breaches_by_day.png|Number of stocks missing their 99% VaR on each day, GJR-t and XGBoost; triangles mark market-wide fall days|outputs/tables/breach_days_price.csv (src/make_figures.py)|Two bar charts over 2024 to 2026 of the number of stocks breaching on each day; tall bars line up with stress-day triangles, the tallest on 4 June 2024.]]

[[MEANS]] {{fig:byday}} shows the tall bars lining up with market-wide fall days for both models. A one-stock limit cannot see this shared shock. Portfolio and exchange risk teams should add a market-wide scenario on top of stock-level VaR.

## 5.8 Do extra market inputs help the ML models?

The India VIX level moved XGBoost's 99% forecast more than any other input ({{shap_top_bp}} basis points on average, SHAP values). A big effect is not the same as a better forecast, which {{tab:sets}} tests.

[[TABLE:sets|sets]]

[[MEANS]] Adding the VIX level moved every ML model's 99% miss rate further from 1% (XGBoost {{vix_exc99_xgb}}). The inputs helped on the validation years but hurt on the test years in {{flip}} of {{flip_of}} cases. A firm should not pay for extra inputs until they prove their value out of sample.

[[TABLE:ranges|ranges]]

[[MEANS]] {{tab:ranges}} gives one reason. The USD/INR level was outside its training range on {{out_usdinr}} of test days, and tree models cannot extrapolate. Any input used in production needs a daily range check.

## 5.9 Sector differences

[[FIG:sector|outputs/figures/print/fig09_sector_var.png|Average one-day 99% VaR from GJR-t by sector (one point per stock)|outputs/tables/by_ticker/price/*__daily.parquet (src/make_figures.py)|Box plots of average 99% VaR by sector, from FMCG at the low end to Services and Capital Goods at the high end, with Financial Services showing the widest spread.]]

[[MEANS]] {{fig:sector}} shows the typical 99% loss limit ranging from {{sec_low_var}} for {{sec_low}} to {{sec_high_var}} for {{sec_high}} ({{sec_high_n}} stock). One margin rate for all large caps would over-charge steady stocks and under-charge volatile ones. XGBoost missed more often than GJR-t in {{sec_xgb_worse}} of {{n_sec}} sectors.

## 5.10 Robustness checks

- Adani Enterprises was excluded for a 2015 price error, so it was run separately with its later crashes kept. Its 99% miss rates were {{adani_gjrt}} for GJR-t, {{adani_xgb}} for XGBoost and {{adani_hs}} for historical simulation.
- XGBoost's ES method understates true ES by at most {{es_bias_max}} in a check against known distributions, too little to change any conclusion.
- A rerun of two stocks from the frozen data reproduced the backtests exactly (QA_report.md).

## 5.11 Hypotheses and findings

[[TABLE:hyp|hyp]]

[[MEANS]] {{tab:hyp}} gives the decisions: H1 {{h1}}, H2 {{h2}}, H3 {{h3}}, H4 {{h4}}. The data give no reason to move loss limits or margins from the Student-t GARCH models to the machine-learning models we tested.

[[TABLE:findings|findings]]

[[MEANS]] {{tab:findings}} links each finding to an action in Chapter 6. The biggest remaining risk is not the choice of model but market-wide fall days.
