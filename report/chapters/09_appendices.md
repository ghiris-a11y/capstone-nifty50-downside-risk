# CHAPTER 9: APPENDICES

## Appendix A: Questionnaire

Not applicable. The study uses secondary data only (daily market prices and index levels); no survey, interview or questionnaire was used.

## Appendix B: Results by stock

{{tab:perstock}} gives the 99% VaR breach rate for every stock and the main models.

[[TABLE:perstock|perstock]]

## Appendix C: Descriptive statistics by stock

{{tab:desc_stock}} gives the test-window return statistics for each stock.

[[TABLE:desc_stock|desc_stock]]

## Appendix D: GARCH estimates by stock

{{tab:garch_stock}} gives the GJR-GARCH-t estimates for each stock at the start of the test window.

[[TABLE:garch_stock|garch_stock]]

## Appendix E: Model settings (hyperparameters)

{{tab:hyper}} lists the fixed settings of every model.

[[MDTABLE:hyper|Model settings used in nifty50_var_pipeline.py (fixed in advance; not tuned on the test window)|nifty50_var_pipeline.py]]
| Model | Settings |
|---|---|
| GARCH, EGARCH, GJR-GARCH | Constant mean; p = 1, q = 1 (o = 1 for EGARCH and GJR); Normal or Student-t errors; re-estimated every 20 trading days on all past data |
| XGBoost | Quantile loss; 300 trees, depth 3, learning rate 0.03, subsample 0.8, column sample 0.8, L2 penalty 5; six quantiles per level |
| Random Forest | 300 trees, depth 6, at least 20 observations per leaf, half the inputs per split; predicts the absolute return |
| MLP | Two hidden layers (64 and 32 units), ReLU, Adam, L2 penalty 0.001, early stopping on 15% of the training data, up to 300 iterations |
| Historical simulation | Empirical quantile and tail mean of the last 250 returns |
| All models | Random seed 42; inputs at day t use data up to t-1 |

## Appendix F: Variable dictionary

{{tab:vars}} defines every input used by the machine-learning models.

[[MDTABLE:vars|Variable dictionary|nifty50_var_pipeline.py (build_features)]]
| Variable | Definition | Set |
|---|---|---|
| ret_l1, ret_l2, ret_l5, ret_l10, ret_l20 | Daily log return 1, 2, 5, 10 and 20 trading days before the forecast day | Price/volume |
| abs_ret, neg_ret | Size of yesterday's return; yesterday's fall (zero if positive) | Price/volume |
| rv_10, rv_20, rv_60 | Realised volatility over 10, 20 and 60 days | Price/volume |
| mdd_60 | Current fall of the cumulative return from its 60-day high | Price/volume |
| vol_chg_5, vol_chg_20 | Change in log volume over 5 and 20 days | Price/volume |
| vix, vix_chg, rv_x_vix | India VIX level, its daily change, and realised volatility times VIX | VIX level |
| vix_rel60, vix_rel60_chg | VIX relative to its 60-day mean, and its change | VIX relative |
| usdinr_ret1, usdinr_ret21 | One-day and 21-day change in USD/INR | USD/INR changes |
| VaR, ES | One-day loss forecasts at 95% and 99%, positive numbers | Outputs |

## Appendix G: Code, GitHub Action and dashboard

The code and data pipeline are in the public repository github.com/ghiris-a11y/capstone-nifty50-downside-risk. The main pipeline is nifty50_var_pipeline.py; scripts in src/ build the universe, freeze and validate the data, make the figures, export the dashboard data and compute every number in this report (src/report_numbers.py). The GitHub Action in .github/workflows/daily_update.yml runs each weekday at 13:30 UTC (7:00 PM IST): it downloads the new day's prices, validates them, recomputes a next-day GJR-t VaR and ES for every stock, commits only the live data folders and redeploys the dashboard to GitHub Pages at ghiris-a11y.github.io/capstone-nifty50-downside-risk. Its layout takes ideas from two Figma Community files, the Trading Stock Market Dashboard Platform UI Kit (https://www.figma.com/design/3c5zWpbNciVkRL6YMIsbgg/) and the Minimal & modern report template for brand insights and marketing dashboards (https://www.figma.com/design/o8Yeuw8XFrj9Oxt2TkYOLt/): layout ideas only, no assets copied; the licence on the two Community pages was not checked. The dashboard text was written for non-specialist readers and scored between grade {{fk_min}} and {{fk_max}} on the Flesch-Kincaid scale across its {{n_tabs}} tabs. The screenshots below were captured from the live site at phone layout (480 pixels wide, at twice the screen resolution) and each is cropped to one block of a tab. They are printed at 14.6 cm wide so that the smallest text on screen, the chart labels, prints at about 10 pt; a full desktop screen shrunk to page width would print its text at about 6 pt.

[[FIG:dash_start|report/figures/dashboard/phone_start.png|Dashboard: Start here tab (top of the page)|Live dashboard, captured with Playwright (src/report_screens.py)|Phone-width screenshot of the Start here tab: a one-line takeaway, the research question and the first of three key-finding cards.|14.6]]

[[MEANS]] The first screen answers the study's question in one line and three findings, so a reader who goes no further still gets the result.

[[FIG:dash_models|report/figures/dashboard/phone_models.png|Dashboard: Model comparison tab (how often each model's forecast was beaten)|Live dashboard, captured with Playwright (src/report_screens.py)|Phone-width screenshot of the Model comparison tab: a finding title, a how-to-read line and a bar chart of breaches per 100 days for each model with an ideal line at 1 and good, caution and poor badges shown with icons.|14.6]]

[[MEANS]] The model comparison uses plain labels ("how often forecasts were beaten") with the technical term kept beside them, and icons as well as colour for good, caution and poor.

[[FIG:dash_regimes|report/figures/dashboard/phone_regimes.png|Dashboard: Calm vs stressed days tab (share of beaten days on market-wide bad days)|Live dashboard, captured with Playwright (src/report_screens.py)|Phone-width screenshot of a chart on the Calm vs stressed days tab: bars for the share of each model's beaten days that fell on market-wide bad days.|14.6]]

[[MEANS]] The regime tab shows when models fail, which is the question a risk committee asks after a bad day.

[[FIG:dash_stock|report/figures/dashboard/phone_stock.png|Dashboard: One stock up close tab (Reliance Industries)|Live dashboard, captured with Playwright (src/report_screens.py)|Phone-width screenshot of the chart on the stock tab for Reliance Industries: the daily return with two models' likely worst daily loss lines, beaten days marked with crosses and the 7 October 2026 rate rise as a dashed line.|14.6]]

[[MEANS]] Any user can pick a stock and two models and see the forecast against what really happened, day by day.

[[FIG:dash_live|report/figures/dashboard/phone_live.png|Dashboard: Daily example tab (live extension, not the report's results)|Live dashboard, captured with Playwright (src/report_screens.py)|Phone-width screenshot of the Daily example tab: an amber banner saying it is a daily example and not the report's results, a one-line takeaway and the start of the next-day worst-loss table.|14.6]]

[[MEANS]] The daily example shows the recommended model running in production every evening; it is clearly labelled as separate from the frozen results in this report.
