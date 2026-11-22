# CHAPTER 9: APPENDICES

## Key terms

{{tab:terms}} explains each technical term in plain words.

[[MDTABLE:terms|Key terms used in this report|Author's definitions]]
| Term | Plain meaning |
|---|---|
| VaR (Value-at-Risk), 99% | Loss limit for 99 of 100 days: the loss a position should not exceed on 99 days out of 100 |
| VaR, 95% | Loss limit for 19 of 20 days |
| ES (Expected Shortfall) | Average loss on the worst days, beyond the loss limit |
| Miss (breach, exception) | A day on which the real loss was bigger than the loss limit |
| Miss rate | Share of days with a miss; ideal 1% at 99% and 5% at 95% |
| Kupiec test | Test of whether misses are too frequent (or too rare) |
| Christoffersen test | Test of whether misses come in clusters |
| Basel green zone | Four or fewer 99% misses in 250 days: the zone banks aim for |
| FZ0 score | Score for the loss limit and the worst-day average together; lower is better |
| Pinball score | Score for the loss limit alone; lower is better |
| Diebold-Mariano test | Test of whether one model's average score is really lower, or the gap could be luck |
| GARCH, EGARCH, GJR-GARCH | Classic models of changing volatility; EGARCH and GJR let bad news count more |
| Normal / Student-t errors | Bell-curve tails / fatter tails that allow more extreme days |
| XGBoost, Random Forest, MLP | The machine-learning models we tested: boosted trees, averaged trees, a small neural network |
| Historical simulation | Benchmark that uses the last 250 days as the forecast |
| India VIX | The market "fear gauge" read from option prices |
| Market-wide fall day | A day the Nifty 50 fell 2% or more |
| SHAP value | How much each input moved a tree model's forecast |

## Appendix A: Questionnaire

Not applicable. The study uses secondary market data only; no survey, interview or questionnaire was used.

## Appendix B: Backtest detail and results by stock

[[TABLE:bt_extra|bt_extra]]

[[TABLE:perstock_compact|perstock_compact]]

{{tab:bt_extra}} adds the measures not shown in Chapter 5; {{tab:perstock_compact}} summarises the stocks. XGBoost's mean FZ0 score at 99% is pulled up by its zero-risk days (Section 5.5). Full per-stock results: [backtest_results_price.csv](https://github.com/ghiris-a11y/capstone-nifty50-downside-risk/blob/main/outputs/tables/backtest_results_price.csv)

## Appendix C: Return statistics by sector

[[TABLE:desc_sector|desc_sector]]

{{tab:desc_sector}} groups the stocks by sector. Full statistics by stock: [descriptive_test_returns.csv](https://github.com/ghiris-a11y/capstone-nifty50-downside-risk/blob/main/outputs/tables/report/descriptive_test_returns.csv)

## Appendix D: GARCH estimates

[[TABLE:garch_compact|garch_compact]]

{{tab:garch_compact}} shows the spread of GJR-t estimates across stocks. Full estimates for all six models: [garch_params_teststart.csv](https://github.com/ghiris-a11y/capstone-nifty50-downside-risk/blob/main/outputs/tables/garch_params_teststart.csv)

## Appendix E: Model settings

[[MDTABLE:hyper|Model settings (fixed in advance; not tuned on the test window)|nifty50_var_pipeline.py]]
| Model | Settings |
|---|---|
| GARCH, EGARCH, GJR-GARCH | Constant mean; p = 1, q = 1 (o = 1 for EGARCH and GJR); Normal or Student-t errors; refit every 20 trading days |
| XGBoost | Quantile loss; 300 trees, depth 3, learning rate 0.03, subsample 0.8, column sample 0.8, L2 penalty 5; six quantiles per level |
| Random Forest | 300 trees, depth 6, at least 20 observations per leaf, half the inputs per split; predicts the absolute return |
| MLP | Two hidden layers (64 and 32 units), ReLU, Adam, L2 penalty 0.001, early stopping on 15% of the training data, up to 300 iterations |
| Historical simulation | Quantile and tail mean of the last 250 returns |
| All models | Random seed 42; inputs for day t use data up to t-1 |

{{tab:hyper}} lists every setting.

## Appendix F: Variable dictionary

[[MDTABLE:vars|Variable dictionary|nifty50_var_pipeline.py (build_features)]]
| Variable | Definition | Set |
|---|---|---|
| ret_l1, ret_l2, ret_l5, ret_l10, ret_l20 | Daily log return 1, 2, 5, 10 and 20 trading days before the forecast day | Price/volume |
| abs_ret, neg_ret | Size of yesterday's return; yesterday's fall (zero if positive) | Price/volume |
| rv_10, rv_20, rv_60 | Volatility over the last 10, 20 and 60 days | Price/volume |
| mdd_60 | Fall of the cumulative return from its 60-day high | Price/volume |
| vol_chg_5, vol_chg_20 | Change in log volume over 5 and 20 days | Price/volume |
| vix, vix_chg, rv_x_vix | India VIX level, its daily change, and volatility times VIX | VIX level |
| vix_rel60, vix_rel60_chg | VIX relative to its 60-day mean, and its change | VIX relative |
| usdinr_ret1, usdinr_ret21 | One-day and 21-day change in USD/INR | USD/INR changes |

{{tab:vars}} defines every machine-learning input.

## Appendix G: Code, daily update and dashboard

Live dashboard: [https://ghiris-a11y.github.io/capstone-nifty50-downside-risk/](https://ghiris-a11y.github.io/capstone-nifty50-downside-risk/)

Code and data: [https://github.com/ghiris-a11y/capstone-nifty50-downside-risk](https://github.com/ghiris-a11y/capstone-nifty50-downside-risk)

The main pipeline is nifty50_var_pipeline.py; scripts in src/ build every number and figure in this report. A GitHub Action runs each weekday at 7:00 PM IST. It downloads the day's prices, checks them, recomputes a next-day GJR-t VaR and ES for every stock and updates the dashboard. The dashboard text scored grade {{fk_min}} to {{fk_max}} on the Flesch-Kincaid scale across its {{n_tabs}} tabs. Its layout borrows ideas from two Figma Community files, the [Trading Stock Market Dashboard Platform UI Kit](https://www.figma.com/design/3c5zWpbNciVkRL6YMIsbgg/) and the [Minimal & modern report template](https://www.figma.com/design/o8Yeuw8XFrj9Oxt2TkYOLt/). Only layout ideas were used and no assets were copied; the licence on the two Community pages was not checked.

The figures below show the first screen of five more tabs on a desktop (1,100 by 700 pixels), cropped to the content area with the side menu removed, two to a page. The last figure shows the same dashboard on a phone.


[[FIG:desk_overview|report/figures/dashboard/desk_overview.png|Dashboard, Results at a glance tab on a desktop screen (content area)|Live dashboard, captured with Playwright (src/report_screens.py)|Desktop screenshot of the Results at a glance tab with the one-line answer, input and level selectors, and summary cards.|15.5]]

[[SHOWS]] One screen with the headline numbers for any input set and level, for a manager who has two minutes.

[[FIG:desk_models|report/figures/dashboard/desk_models.png|Dashboard, Model comparison tab on a desktop screen (content area)|Live dashboard, captured with Playwright (src/report_screens.py)|Desktop screenshot of the Model comparison tab with the one-line answer and the top of the chart of how often each model was beaten.|15.5]]

[[SHOWS]] How often each model was beaten, with good, caution and poor labels; the basis for choosing the model.

[[FIG:desk_regimes|report/figures/dashboard/desk_regimes.png|Dashboard, Calm vs stressed days tab on a desktop screen (content area)|Live dashboard, captured with Playwright (src/report_screens.py)|Desktop screenshot of the Calm vs stressed days tab with the one-line answer and the market context chart.|15.5]]

[[SHOWS]] When the models fail: on market-wide fall days, the case for the stress buffer.

[[FIG:desk_stock|report/figures/dashboard/desk_stock.png|Dashboard, One stock up close tab on a desktop screen (content area)|Live dashboard, captured with Playwright (src/report_screens.py)|Desktop screenshot of the stock tab with selectors for stock, two models and level, time-range buttons and the stocks-to-watch list.|15.5]]

[[SHOWS]] Any stock and two models, day by day, before a position limit is changed.

[[FIG:desk_live|report/figures/dashboard/desk_live.png|Dashboard, Daily example tab on a desktop screen (live extension, not the report's results)|Live dashboard, captured with Playwright (src/report_screens.py)|Desktop screenshot of the Daily example tab with an amber banner saying it is not the report's results and the table of next-day worst-loss estimates by stock.|15.5]]

[[SHOWS]] Tomorrow's likely worst loss for each stock, updated every weekday evening and clearly marked as separate from the report's frozen results.


[[PHONES:phones|report/figures/dashboard/phone_start.png|report/figures/dashboard/phone_models.png|report/figures/dashboard/phone_live.png|The same dashboard on a phone: Start here, Model comparison and Daily example|Live dashboard, captured with Playwright (src/report_screens.py)|Three phone screenshots side by side showing the first screen of the Start here, Model comparison and Daily example tabs, each with a menu button at the top.]]

[[MEANS]] {{fig:phones}} shows the same tabs on a phone, with the menu folded behind a button. A manager can check tomorrow's limits from anywhere.
