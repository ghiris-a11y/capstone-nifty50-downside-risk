# CHAPTER 1: INTRODUCTION

## Executive summary

This study asks a practical question for anyone who holds large Indian stocks: how much could a position lose tomorrow, and which forecasting method gives the more reliable answer? It compares classic volatility models (GARCH, EGARCH and GJR-GARCH, each with Normal and Student-t errors) with three machine-learning models (XGBoost, Random Forest and a multi-layer perceptron) and a simple historical-simulation benchmark. Each model forecasts the one-day 95% and 99% Value-at-Risk (VaR) and Expected Shortfall (ES) for a balanced panel of {{n_stocks}} Nifty 50 stocks. The models learn from 2015 to 2021, choices are made on 2022 and 2023, and every result comes from {{test_obs}} unseen stock-days between January 2024 and November 2026.

The classic models with fat-tailed errors came closest to the expected loss frequency: at 99% the breach rates of {{closest1}}, {{closest2}} and {{closest3}} were {{closest1_exc}}, {{closest2_exc}} and {{closest3_exc}} against a nominal 1%. The machine-learning models were beaten more often (XGBoost {{exc99_xgb}}, Random Forest {{exc99_rf}}, MLP {{exc99_mlp}}). Where the difference in overall forecast quality was statistically significant, it favoured GARCH in {{dm_g}} stock-model pairs and machine learning in {{dm_m}}; {{dm_n}} pairs showed no significant difference. Breaches came in bunches: market-wide stress days were {{stress_share_days}} of test days but carried {{stress_gjrt}} of GJR-t breaches. The recommendations in Chapter 6 therefore keep GARCH-t models as the default for margins, limits and capital, add a stress buffer for market-wide fall days, and allow machine-learning models only as challengers that pass the same backtests.

## 1.1 Title of the project

Comparative Predictive Analytics of Downside Risk in NSE Nifty 50 Stocks: Machine Learning vs. GARCH Models Using Secondary Historical and Macroeconomic Data.

## 1.2 Industry overview: Indian equity markets

India's equity market is organised around two national exchanges, the National Stock Exchange (NSE) and BSE, under the oversight of the Securities and Exchange Board of India (SEBI). Trading is fully electronic and every trade is guaranteed by a clearing corporation, which stands between buyer and seller and therefore carries the risk that a member cannot pay. The Nifty 50 is the NSE's flagship index of fifty large, liquid companies across the main sectors of the economy; it is the reference point for index funds, derivatives and foreign investors who want exposure to Indian large caps (NSE, n.d.-b). The NSE also publishes the India VIX, a measure of the volatility that option prices imply for the next thirty days, often described as the market's fear gauge (Chandra & Thenmozhi, 2015).

Because so much money is tied to these stocks, the size of a possible one-day loss is a daily business question. A broker must decide how much margin to collect, a fund manager how large a position may be, a bank how much capital to hold, and a retail investor whether a position is affordable. Each of these decisions needs a forecast of the downside, not just of average returns.

## 1.3 Market structure and how risk numbers are used

{{fig:market_structure}} shows the main actors and where a one-day loss forecast enters their decisions. SEBI sets the rules for exchanges, clearing corporations, brokers and funds. The Reserve Bank of India (RBI) sets monetary policy and supervises banks. The NSE runs trading and publishes the Nifty 50 and the India VIX, while its clearing corporation collects margins from members each day. In the cash market, the margin payable is built from a VaR margin, an extreme-loss margin and mark-to-market losses (NSE, n.d.-a). Banks hold capital against market risk under rules from the Basel Committee, which measure risk with Expected Shortfall and backtest 99% VaR forecasts against actual outcomes (Basel Committee on Banking Supervision [BCBS], 2019).

[[FIG:market_structure|report/figures/v_market_structure.png|Indian equity market structure and the uses of VaR and Expected Shortfall|Author's diagram based on NSE (n.d.-a) and BCBS (2019)|Diagram showing SEBI and RBI at the top, NSE and NSE Clearing below them, four groups of market participants, and four uses of VaR and ES: margins, limits, capital and investor communication.]]

[[MEANS]] A one-day loss forecast is not an academic exercise: it sets how much cash a clearing corporation collects, how big a fund's positions can be and how much capital a bank holds. A forecast that is too low leaves these institutions short on the worst days; one that is too high ties up money that could be used elsewhere.

## 1.4 Volatility and risk characteristics

Three features of daily stock returns shape every model in this study. First, returns have fat tails: very large moves happen more often than a bell curve suggests, which is why Student-t versions of the GARCH models are included. Second, volatility clusters: calm and turbulent spells each tend to persist, which GARCH models were built to capture (Bollerslev, 1986). Third, bad news raises volatility more than good news of the same size; EGARCH and GJR-GARCH add this asymmetry (Nelson, 1991; Glosten et al., 1993). Chapter 4 confirms the first feature in this data set: the median stock in the test window had an excess kurtosis of {{kurt_med}}, well above the zero of a normal distribution.

## 1.5 Macroeconomic context

The test window ends shortly after a change in monetary policy. On 7 October 2026 the RBI's Monetary Policy Committee raised the policy repo rate by 25 basis points to 5.50% and moved its stance to calibrated tightening (Reserve Bank of India, 2026a, 2026b). A rate rise can change how investors price risk, so the study reports results for the weeks after the hike separately (Chapter 5), while noting that the period is short. The data used in this report end on {{data_last}}; the next MPC meeting, on 2 to 4 December 2026, falls after this cut-off and is not covered (Reserve Bank of India, 2026a).

## 1.6 SWOT of downside-risk management in Indian equities

{{fig:swot}} summarises the strengths, weaknesses, opportunities and threats for an organisation that wants to forecast and manage the downside of Indian large-cap stocks.

[[FIG:swot|report/figures/v_swot.png|SWOT analysis of downside-risk management in Indian equities|Author's analysis; the strength and threat items that refer to this study come from Chapter 5|Two-by-two grid of strengths, weaknesses, opportunities and threats for downside-risk management in Indian equities.]]

[[MEANS]] The opportunity is a cheap, transparent daily risk process built on free data; the main threat is the day when many stocks fall together. The study is designed around both: it builds such a process and measures how models behave on those days.

## 1.7 Problem statement

Risk teams in India can choose between well-understood statistical models and newer machine-learning methods that promise to use more information, such as the India VIX and exchange rates. The business problem is that a wrong choice is costly in either direction: a model that under-forecasts losses causes margin shortfalls and capital breaches, while one that over-forecasts locks up money. Published comparisons are mostly for index-level data or developed markets, and often judge volatility accuracy rather than the VaR and ES numbers that risk desks actually use. This study therefore asks, for individual Nifty 50 stocks: which approach gives more reliable one-day VaR and ES forecasts, does the answer change in calm and stressed markets, and do market inputs such as the India VIX improve machine-learning forecasts?

## 1.8 Scope

- A balanced panel of {{n_stocks}} Nifty 50 stocks with daily prices from January 2015 to {{data_last}} (Chapter 4 explains the {{n_excl}} exclusions).
- One-day horizon, 95% and 99% VaR and ES, reported as positive loss numbers.
- Secondary data only; no questionnaire or primary survey.
- Training 2015 to 2021, validation 2022 to 2023, test 1 January 2024 to {{data_last}}.
- Inputs are market data only: prices, volume, the India VIX and the USD/INR rate. Interest rates, price rises (CPI) and factory output (IIP) were left out on purpose: the repo rate changes only a few times a year, and CPI and IIP are monthly, released late and later revised, so they carry little information for a one-day forecast. A repo-rate file was prepared from RBI releases but is not yet fully verified, so it was not used.
