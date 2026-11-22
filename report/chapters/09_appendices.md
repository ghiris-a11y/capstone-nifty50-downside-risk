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

The code and data pipeline are in the public repository github.com/ghiris-a11y/capstone-nifty50-downside-risk. The main pipeline is nifty50_var_pipeline.py; scripts in src/ build the universe, freeze and validate the data, make the figures, export the dashboard data and compute every number in this report (src/report_numbers.py). The GitHub Action in .github/workflows/daily_update.yml runs each weekday at 13:30 UTC (7:00 PM IST): it downloads the new day's prices, validates them, recomputes a next-day GJR-t VaR and ES for every stock, commits only the live data folders and redeploys the dashboard to GitHub Pages at ghiris-a11y.github.io/capstone-nifty50-downside-risk. Its layout takes ideas from two Figma Community files, the Trading Stock Market Dashboard Platform UI Kit (https://www.figma.com/design/3c5zWpbNciVkRL6YMIsbgg/) and the Minimal & modern report template for brand insights and marketing dashboards (https://www.figma.com/design/o8Yeuw8XFrj9Oxt2TkYOLt/): layout ideas only, no assets copied; the licence on the two Community pages was not checked. The dashboard text was written for non-specialist readers and scored between grade {{fk_min}} and {{fk_max}} on the Flesch-Kincaid scale across its {{n_tabs}} tabs. The six screenshots below were captured from the live site at phone layout (480 pixels wide, at four times the screen resolution). Each is cropped to one element of a tab and printed at 14.6 cm wide; the smallest text in each crop prints at 10 pt or more (src/report_screens.py logs the size). A full desktop screen shrunk to page width would print its text at about 6 pt.

[[FIG:dash_numbers|report/figures/dashboard/app_start_numbers.png|Dashboard, Start here: the one-line answer and the key numbers|Live dashboard, captured with Playwright (src/report_screens.py)|Phone screenshot of the Start here tab: an "In one line" card saying the classic statistics models stayed closest to the expected loss limits, and four number cards for the closest breach rate, the share of stocks passing the check, the comparisons that could be luck and the misses on market-wide bad days.|14.6]]

[[MEANS]] A reader who sees only the first screen gets the answer and the four numbers behind it, each with a one-line explanation.

[[FIG:dash_actions|report/figures/dashboard/app_start_actions.png|Dashboard, Start here: "What a firm should do" (first three of five cards)|Live dashboard, captured with Playwright (src/report_screens.py)|Phone screenshot of recommendation cards, each naming the user (bank risk desk, broker margin team, portfolio manager), the action and the number from the study that supports it.|14.6]]

[[MEANS]] The dashboard carries the Chapter 6 recommendations to the people who would act on them, with the supporting number on each card.

[[FIG:dash_beaten|report/figures/dashboard/app_models_beaten.png|Dashboard, Model comparison: how often each model's forecast was beaten (chart of the "How often each model was beaten" card)|Live dashboard, captured with Playwright (src/report_screens.py)|Phone screenshot of a horizontal bar chart of breaches per 100 days for each model, with a dashed ideal line at 1 and good, caution and poor labels with icons in a column to the right.|14.6]]

[[MEANS]] Plain labels and icons, not only colour, show which models were beaten too often; the value labels sit in their own column so the ideal line never crosses them.

[[FIG:dash_fig14|report/figures/dashboard/app_regimes_fig14.png|Dashboard, Calm vs stressed days: share of each model's beaten days that fell on market-wide bad days (chart of the Figure 14 card)|Live dashboard, captured with Playwright (src/report_screens.py)|Phone screenshot of a bar chart of the share of beaten days on market-wide bad days for each model, all around a fifth, with the share of all days that were bad days labelled above the plot.|14.6]]

[[MEANS]] The chart that supports the stress-day cushion in Section 6.4 is the same one a risk committee sees on the dashboard.

[[FIG:dash_fig3|report/figures/dashboard/app_stock_fig3.png|Dashboard, One stock up close: Reliance Industries, daily return against the GJR-t and XGBoost likely worst daily loss (chart of the Figure 3 card)|Live dashboard, captured with Playwright (src/report_screens.py)|Phone screenshot of a line chart of Reliance daily returns with two forecast lines below them, beaten days marked with crosses and triangles, and a dashed line at the 7 October 2026 rate rise.|14.6]]

[[MEANS]] Any user can see, stock by stock, the days on which each model's forecast was beaten.

[[FIG:dash_live|report/figures/dashboard/app_live_table.png|Dashboard, Daily example: the banner and the top of the next-day table (the text between them is left out; the dashed line marks the break; on a phone the table scrolls sideways to more columns)|Live dashboard, captured with Playwright (src/report_screens.py)|Two stacked phone screenshots: an amber banner saying "Daily example only. This is not the report's results. It updates each weekday evening.", a dashed break, and the top of a table of next-day worst-loss estimates by stock.|14.6]]

[[MEANS]] The daily example shows the recommended model running every evening; it is clearly labelled as separate from the frozen results in this report.
