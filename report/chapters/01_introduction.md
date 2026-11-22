# CHAPTER 1: INTRODUCTION

## Executive summary

This study asks a practical question: how much could a large Indian stock lose tomorrow, and which method forecasts that loss best? It compares classic models of changing volatility (GARCH, EGARCH and GJR-GARCH) with three machine-learning models (XGBoost, Random Forest and a neural network called MLP). A simple historical method serves as a benchmark.

Each model forecasts two numbers for {{n_stocks}} Nifty 50 stocks every day. The first is the loss limit for 99 of 100 days (99% Value-at-Risk, VaR). The second is the average loss on the worst days (Expected Shortfall, ES). The models learn from 2015 to 2021, choices are made on 2022 and 2023, and all results come from {{test_obs}} unseen stock-days from January 2024 to November 2026.

The classic models with fat-tailed errors came closest to expected. At 99%, {{closest1}}, {{closest2}} and {{closest3}} were beaten on {{closest1_exc}}, {{closest2_exc}} and {{closest3_exc}} of days, against an ideal of 1%. The machine-learning models we tested were beaten more often. Bad days also came together: market-wide fall days were {{stress_share_days}} of days but held {{stress_gjrt}} of GJR-t's misses. Chapter 6 therefore recommends a classic model for limits and margins, plus a buffer for market-wide fall days.

## 1.1 Title of the project

Comparative Predictive Analytics of Downside Risk in NSE Nifty 50 Stocks: Machine Learning vs. GARCH Models Using Secondary Historical and Macroeconomic Data.

## 1.2 Industry overview and market structure

India's shares trade on two national exchanges, the NSE and BSE, under the regulator SEBI. Every trade is guaranteed by a clearing corporation, which carries the risk that a member cannot pay. The Nifty 50 is the NSE's index of fifty large companies (NSE, n.d.-b). The NSE also publishes the India VIX, a "fear gauge" read from option prices (Chandra & Thenmozhi, 2015).

{{fig:market_structure}} shows where a one-day loss forecast is used. Clearing corporations set margins from a VaR-based charge (NSE, n.d.-a). Funds use it for position limits, and banks hold capital against market risk under Basel rules (Basel Committee on Banking Supervision [BCBS], 2019).

[[FIG:market_structure|report/figures/v_market_structure.png|Indian equity market structure and the uses of VaR and Expected Shortfall|Author's diagram based on NSE (n.d.-a) and BCBS (2019)|Diagram showing SEBI and RBI at the top, NSE and NSE Clearing below them, four groups of market participants, and four uses of VaR and ES: margins, limits, capital and investor communication.]]

[[MEANS]] A loss forecast decides how much cash a broker collects, how large a fund's positions can be and how much capital a bank holds. Too low, and the firm is short on the worst days. Too high, and money sits idle.

## 1.3 How daily returns behave

Three features shape every model here. Very large moves happen more often than a bell curve suggests (fat tails), so the study includes Student-t versions of each GARCH model. Calm and turbulent spells each tend to last (Bollerslev, 1986). Bad news raises volatility more than good news, which EGARCH and GJR-GARCH allow for (Nelson, 1991; Glosten et al., 1993). In this data the typical stock had an excess kurtosis of {{kurt_med}}, far from the zero of a bell curve.

## 1.4 Macroeconomic context

On 7 October 2026 the RBI's Monetary Policy Committee raised the repo rate by 25 basis points to 5.50%. It also moved its stance to calibrated tightening (Reserve Bank of India, 2026a, 2026b). Chapter 5 reports the weeks after the hike separately. The data end on {{data_last}}, so the next policy meeting, on 2 to 4 December 2026, is not covered (Reserve Bank of India, 2026a).

## 1.5 SWOT of downside-risk management in Indian equities

{{fig:swot}} sums up the position of a firm that wants to manage the downside of Indian large caps.

[[FIG:swot|report/figures/v_swot.png|SWOT analysis of downside-risk management in Indian equities|Author's analysis; the strength and threat items that refer to this study come from Chapter 5|Two-by-two grid of strengths, weaknesses, opportunities and threats for downside-risk management in Indian equities.]]

[[MEANS]] The opportunity is a cheap daily risk process built on free data. The main threat is the day many stocks fall together. A firm should build the process and plan for those days.

## 1.6 Problem statement

Risk teams can choose between well-known statistical models and newer machine-learning methods. A wrong choice is costly either way: forecasts that are too low cause margin shortfalls, and forecasts that are too high lock up money. Most published comparisons use indices or developed markets, and judge volatility rather than VaR and ES. This study asks which approach gives more reliable one-day VaR and ES for individual Nifty 50 stocks, in calm and stressed markets.

## 1.7 Scope

- {{n_stocks}} Nifty 50 stocks with daily prices from January 2015 to {{data_last}} ({{n_excl}} candidates excluded; see Chapter 4).
- One-day horizon; 95% and 99% VaR and ES, shown as positive loss numbers.
- Secondary data only; no questionnaire.
- Training 2015 to 2021, validation 2022 to 2023, test 1 January 2024 to {{data_last}}.
- Inputs: market data (prices, volume, India VIX and USD/INR). Price rises (CPI) and factory output (IIP) were left out on purpose: they come monthly, late and are later revised.
- Live dashboard: [https://ghiris-a11y.github.io/capstone-nifty50-downside-risk/](https://ghiris-a11y.github.io/capstone-nifty50-downside-risk/)
