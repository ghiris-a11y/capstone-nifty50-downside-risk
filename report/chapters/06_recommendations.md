# CHAPTER 6: RECOMMENDATIONS

Every recommendation follows from Chapter 5. The central finding is that the machine-learning models we tested did not do better than the classic models. The Student-t GARCH models stay the default; machine learning gets a limited challenger role.

## 6.1 Decision table by user

[[FIG:decision|report/figures/v_decision_table.png|Recommendation decision table: user, recommended approach, evidence, expected benefit and viability|Author's recommendations; evidence from outputs/tables/summary_price.csv, diebold_mariano_price.csv, breach_days_summary_price.csv and outputs/tables/report/sector_summary_price.csv|Table graphic with five rows (bank market-risk desk, broker margin team, portfolio manager, retail or fintech app, exchange or regulator) and columns for approach, evidence, expected benefit and viability.]]

[[MEANS]] {{fig:decision}} gives every user the same core model, a Student-t GARCH forecast, because it was the most reliable on every test. What differs is the add-on: a stress buffer for brokers, sector limits for fund managers, plain words for apps and cross-stock monitoring for the exchange.

## 6.2 Where machine learning did not help

The machine-learning models we tested did not help with the main job. They missed more often at 99% (XGBoost {{exc99_xgb}} against {{exc99_gjrt}} for GJR-t). They also set aside less money: Rs {{buf_mlfam}} crore per Rs 100 crore, against Rs {{buf_tfam}} crore for the Student-t GARCH models. They should not set limits, margins or capital. Interest-rate data did not help either: adding repo-rate changes moved every ML model further from 1% (Section 5.8), so a rate feed is not worth buying for this purpose. Random Forest may serve as a challenger for internal 95% limits. It must then be refitted regularly, screened for zero-risk forecasts and given inputs that stay within their training range.

## 6.3 Stress-day cushion and an India VIX alert

[[TABLE:cushion|cushion]]

[[MEANS]] {{tab:cushion}} shows that on market-wide fall days GJR-t missed on {{st_br_gjrt}} of stock-days, against {{ns_br_gjrt}} on other days. Covering those days to the 1% standard would need about {{st_mult99}} times the normal VaR. A high India VIX the day before did not signal more misses ({{br_q4_gjrt}} against {{br_q13_gjrt}}).

The rule that follows has two parts:

- **Stress buffer (margins and limits).** Hold a standing buffer sized as a market-fall scenario of about {{st_mult99}} times normal 99% VaR for the positions most exposed. Keep it in place, because fall days cannot be forecast.
- **India VIX alert (monitoring).** When the VIX closes above {{vix_q4_edge}}, review concentrated positions next morning. It should trigger a review, not an automatic margin increase.

## 6.4 Sector margins

Set a sector floor equal to the sector's median 99% VaR, which a stock's own GJR-t VaR can raise but not lower. Review one-stock sectors stock by stock.

## 6.5 Expected benefits

[[TABLE:buffers|buffers]]

[[MEANS]] {{tab:buffers}} shows the money each model sets aside for one bad day. The ML models look cheaper only because they set aside less, and they missed more often for exactly that reason. Using GJR-t instead of XGBoost would avoid about {{gap_xgb_gjrt_panel}} misses a year across {{n_stocks}} stocks.

Assumptions: one-day horizon; equal positions in each stock; 250 trading days a year. The buffer is the average 99% VaR over the test, not a regulatory capital charge, which adds multipliers and a 10-day horizon.

## 6.6 30/60/90-day plan

[[MDTABLE:roadmap|30/60/90-day implementation plan|Author's recommendation, based on Chapters 5 and 6]]
| Period | Actions | Done when |
|---|---|---|
| Days 1-30 | Freeze data; validate prices; start the daily GJR-t run and dashboard | 20 trading days run unattended |
| Days 31-60 | Run GJR-t beside the current method; set sector floors; agree the stress buffer and VIX alert | Risk committee reviews the first monthly report |
| Days 61-90 | Backtest the trial period; go live with the stress buffer | Miss test passed; model-risk sign-off |
| Every month | Count misses; flag days with many stocks missing together | Report filed |
| Every quarter / year | Re-validate; test any ML challenger on the same tests | Challenger adopted only if better on every test |

[[MEANS]] {{tab:roadmap}} lets a desk see real misses and margin changes for a month before switching. Regular reviews then stop the model drifting as markets change.

## 6.7 Feasibility and viability

[[MDTABLE:feas|Feasibility and viability of the recommended approach|data/logs/run.log, data/logs/run_test_rerun.log, .github/workflows/daily_update.yml, requirements.txt]]
| Area | Assessment |
|---|---|
| Data cost | Free daily prices for research; licensed exchange data in production, same pipeline |
| Skills | One Python analyst; GARCH is in the open-source arch package |
| Compute | About {{sec_per_stock}} seconds per stock for all ten models; {{min_per_set}} minutes for the panel on {{n_jobs}} workers; daily run in a free GitHub Action |
| Governance | GARCH settings have clear meanings a model-risk committee can review; ML needs SHAP explanations |
| Regulatory fit | 99% VaR backtests and Basel zones are what banks report; Student-t GARCH passed them most often |

[[MEANS]] {{tab:feas}} shows the set-up is cheap and easy to govern. The real cost is discipline: monthly backtests, a stress buffer and a rule that challengers must earn their place.

## 6.8 Risks and mitigations

[[MDTABLE:risks|Risks of the recommended approach and how to reduce them|Author's assessment, based on Chapter 5]]
| Risk | Evidence | Mitigation |
|---|---|---|
| Many stocks fall together | {{stress_gjrt}} of GJR-t misses on {{stress_share_days}} of days | Standing stress buffer; monthly cluster report |
| Worst-day losses exceed ES | ES ratio above 1 for {{n_es_above1}} of {{n_models}} models | Prudence margin on ES |
| An ML model forecasts no risk | XGBoost: {{norisk99_xgb}} stock-days | Zero-risk check; ML only as challenger |
| Inputs leave their training range | USD/INR level: {{out_usdinr}} of days | Use changes, not levels; daily range check |
| Errors in free price data | {{n_excl_ca}} stocks excluded | Licensed data; daily validation |
| Rate-cycle change | {{ph_days}} days after the hike; rate inputs did not help | Review misses after each policy meeting |
| Reliance on one model | One test window | Keep a challenger and the benchmark |

[[MEANS]] {{tab:risks}} shows each risk has a low-cost control. Most controls are already built into the daily pipeline and the dashboard.

## 6.9 Monthly monitoring scorecard

[[TABLE:kpis|kpis]]

[[MEANS]] {{tab:kpis}} gives a risk committee a short monthly checklist. GJR-t had about {{gjrt_breaches_yr}} misses per stock per year against an ideal of {{ideal_yr}}, so most months should show few alerts. When one appears, the cluster and stress rows show whether the model or the market is the cause.

## 6.10 The decision dashboard

Live dashboard: [https://ghiris-a11y.github.io/capstone-nifty50-downside-risk/](https://ghiris-a11y.github.io/capstone-nifty50-downside-risk/)

[[IMG:report/figures/dashboard/qr_dashboard.png|3|QR code linking to the live dashboard]]

The dashboard turns this chapter into a daily tool, refreshed every weekday evening. Its first screen, {{fig:desk_start}}, gives the one-line answer, the key numbers and "What a firm should do" cards.


[[FIG:desk_start|report/figures/dashboard/desk_start.png|Dashboard, Start here tab on a desktop screen (tab content)|Live dashboard, captured with Playwright (src/report_screens.py)|Desktop screenshot of the dashboard content area with the masthead, the question as the page title, a draft-results banner, the one-line answer and the first key-number cards.|15.5]]

[[SHOWS]] Each morning a risk manager opens Start here for the answer and the action cards. The Daily example tab then lists tomorrow's likely worst loss for each stock, sorted from largest. Calm vs stressed days shows whether misses are bunching, and One stock up close checks a single position before a limit is changed.
