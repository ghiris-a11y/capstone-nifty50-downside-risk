# CHAPTER 2: LITERATURE REVIEW

The review is organised by theme and kept short, as the study's weight lies in the analysis. Only sources whose details were verified against the publisher's DOI record or the official web page are cited.

## 2.1 Measuring downside risk: VaR and Expected Shortfall

Value-at-Risk is the loss that should not be exceeded on a given share of days, for example 99 days out of 100. It is easy to explain, but it says nothing about how bad a loss is once the threshold is crossed, and it is not always sub-additive, so a diversified portfolio can appear riskier than its parts (Artzner et al., 1999). Expected Shortfall, the average loss on the days beyond VaR, fixes both problems and is a coherent risk measure (Acerbi & Tasche, 2002). This is why the Basel Committee's market-risk standard measures capital with ES while keeping a 99% VaR backtest to check models (BCBS, 2019).

Backtesting compares forecasts with what happened. Kupiec (1995) tests whether VaR is breached as often as it should be; Christoffersen (1998) adds a test of whether breaches arrive independently or in clusters. The Basel traffic-light approach turns the number of 99% breaches in 250 days into green, amber and red zones (BCBS, 1996). Because ES on its own cannot be backtested with a simple scoring function, Fissler and Ziegel (2016) showed that VaR and ES are jointly elicitable; their FZ0 loss, used by Patton et al. (2019), scores a VaR-ES pair together. Nolde and Ziegel (2017) set out the consequences for banking regulation. Quantile (pinball) loss, from quantile regression (Koenker & Bassett, 1978), scores VaR alone. Diebold and Mariano (1995) provide the standard test of whether one forecast's average loss is significantly lower than another's.

## 2.2 GARCH-family volatility models

Bollerslev's (1986) GARCH model forecasts tomorrow's variance from recent squared returns and yesterday's variance, capturing volatility clustering with very few parameters. Nelson's (1991) EGARCH models the log of variance and lets negative shocks raise volatility more than positive ones; the GJR-GARCH model of Glosten et al. (1993) does the same with an extra term for negative returns. Combined with fat-tailed Student-t errors, these models remain the industry baseline for one-day VaR. Filtered historical simulation (Barone-Adesi et al., 1999) combines a volatility forecast with the empirical distribution of standardised returns, an idea this study uses for two of the machine-learning models.

## 2.3 Machine-learning approaches

Random Forests average many decision trees grown on resampled data (Breiman, 2001); XGBoost builds trees one after another, each correcting the previous ones, with regularisation to limit over-fitting (Chen & Guestrin, 2016). Both can be trained with a quantile loss so that they forecast VaR directly. Behera et al. (2023) used machine-learning regressions to forecast returns for mean-VaR portfolio optimisation across the Bombay, Tokyo and Shanghai exchanges and found AdaBoost the best of the models they compared. Buczynski and Chlebus (2023) proposed GARCHNet, a neural network built around a GARCH structure for VaR forecasting, and reported competitive results against classical models. Xu et al. (2024) combined GARCH with neural networks in a GARCH-informed neural network. Sahiner et al. (2023) compared artificial neural networks with GARCH-type models for ten Asian markets and found that the advantage of neural networks depended on the market and the horizon. To interpret tree-based models, SHAP values attribute each forecast to its inputs (Lundberg & Lee, 2017).

## 2.4 India VIX and macroeconomic drivers

Chandra and Thenmozhi (2015) showed that the India VIX has an asymmetric relationship with Nifty returns, rising more after falls than it falls after rises, and discussed its use in risk management. This motivates using the VIX as an input. Macroeconomic variables such as the repo rate, inflation and industrial production change slowly and are released with a lag; this study includes them in the design with release lags, but the official series were not yet available for the reported results (Chapter 1, Scope).

## 2.5 Research gap

{{tab:gap}} summarises the gaps that this study addresses.

[[MDTABLE:gap|Research gaps and how this study addresses them|Author's synthesis of Sections 2.1 to 2.4]]
| Gap in the literature | How this study addresses it |
|---|---|
| Comparisons are mostly at index level or for developed markets | Stock-level results for a balanced panel of Nifty 50 stocks |
| Usually one GARCH model against one ML model | Six GARCH variants, three ML models and a benchmark, on identical data |
| Accuracy judged by volatility errors, not by VaR and ES | Kupiec, Christoffersen, Basel zones, FZ0 and pinball losses, Diebold-Mariano tests |
| Value of India VIX and macro inputs rarely isolated | Labelled input sets, chosen on a validation window before the test |
| Averages hide behaviour in stress | Results by India VIX quartile and on market-wide stress days |
| ML studies often shuffle time-series data | Strict time order; features at day t use data up to t-1 |

## 2.6 Research questions, objectives and hypotheses

**Research questions.**

1. RQ1: Do machine-learning models forecast one-day 95% and 99% VaR with breach rates closer to the nominal level than GARCH-family models?
2. RQ2: Do machine-learning models give significantly better joint VaR and ES forecasts than GARCH-family models?
3. RQ3: Does the comparison change between calm and stressed markets?
4. RQ4: Do India VIX and macroeconomic inputs improve machine-learning forecasts over price and volume inputs alone?

**Objectives.** To forecast one-day VaR and ES for each stock with ten models; to backtest every forecast with the tests regulators use; to test whether differences are significant; to examine performance by market regime and on stress days; to measure the value of market inputs; and to turn the findings into recommendations for specific users.

**Hypotheses.**

- H1: Machine-learning models give 99% VaR breach rates closer to nominal than GARCH models.
- H2: Machine-learning models have significantly lower joint VaR-ES loss (FZ0) than GARCH models.
- H3: Any machine-learning advantage is larger when the India VIX is high.
- H4: India VIX and macroeconomic inputs improve machine-learning forecasts over price and volume inputs.
