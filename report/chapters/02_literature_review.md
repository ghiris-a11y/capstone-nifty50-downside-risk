# CHAPTER 2: LITERATURE REVIEW

Only sources checked against the publisher's DOI record or the official web page are cited.

## 2.1 Loss limits and how to check them

The loss limit for 99 of 100 days (VaR) is easy to explain, but it says nothing about how bad a loss is beyond the limit (Artzner et al., 1999). The average loss on the worst days (ES) fills that gap (Acerbi & Tasche, 2002), and Basel rules now set bank capital with ES while checking 99% VaR (BCBS, 2019). The test of whether misses are too frequent comes from Kupiec (1995); the test of whether misses come in clusters comes from Christoffersen (1998). The Basel traffic light sorts the number of 99% misses in 250 days into green, amber and red zones (BCBS, 1996). VaR and ES can be scored together with one number (Fissler & Ziegel, 2016; Nolde & Ziegel, 2017); this study uses the FZ0 score of Patton et al. (2019). The pinball score rates VaR alone (Koenker & Bassett, 1978), and the Diebold-Mariano test checks whether one model's average score is really lower than another's (Diebold & Mariano, 1995).

## 2.2 Classic volatility models

GARCH forecasts tomorrow's volatility from recent returns and yesterday's volatility (Bollerslev, 1986). EGARCH and GJR-GARCH let bad news raise volatility more than good news (Nelson, 1991; Glosten et al., 1993). With fat-tailed Student-t errors they remain the industry baseline for one-day VaR, including for Indian stocks (Ali & Dembo, 2025, a preprint not yet peer reviewed). Filtered historical simulation joins a volatility forecast with past standardised returns (Barone-Adesi et al., 1999); two of the machine-learning models here use it.

## 2.3 Machine-learning models

Random Forests average many decision trees (Breiman, 2001). XGBoost adds trees one at a time, each fixing the last one's errors (Chen & Guestrin, 2016). Behera et al. (2023) used such models for VaR-based portfolios on three Asian exchanges. Buczynski and Chlebus (2023) built a GARCH-shaped neural network for VaR, and Xu et al. (2024) mixed GARCH with neural networks. Sahiner et al. (2023) found that neural networks beat GARCH in some Asian markets and horizons but not others. SHAP values show which inputs drive a tree model's forecast (Lundberg & Lee, 2017).

## 2.4 India VIX

The India VIX rises more after market falls than it drops after rises (Chandra & Thenmozhi, 2015). This makes it a natural candidate input for risk forecasts.

## 2.5 Research gap

[[MDTABLE:gap|Research gaps and how this study addresses them|Author's synthesis of Sections 2.1 to 2.4]]
| Gap in the literature | How this study addresses it |
|---|---|
| Mostly index-level or developed-market studies | Stock-level results for {{n_stocks}} Nifty 50 stocks |
| Usually one GARCH model against one ML model | Six GARCH models, three ML models and a benchmark on the same data |
| Judged on volatility errors, not on VaR and ES | Miss-frequency and clustering tests, Basel zones, FZ0 and pinball scores |
| Value of extra inputs rarely tested on its own | Labelled input sets, chosen on a validation window before the test |
| Averages hide behaviour on bad days | Results by India VIX level and on market-wide fall days |

{{tab:gap}} sums up the gaps this study fills.

## 2.6 Research questions and hypotheses

1. RQ1: Do the machine-learning models give 99% VaR miss rates closer to 1% than the GARCH models?
2. RQ2: Do they give significantly better VaR and ES forecasts together (FZ0 score)?
3. RQ3: Does the answer change between calm and stressed markets?
4. RQ4: Do extra market inputs improve the machine-learning forecasts?

The matching hypotheses say the ML models do better. H1: their 99% miss rates are closer to 1%. H2: their FZ0 score is significantly lower. H3: any ML advantage is larger when the India VIX is high. H4: extra inputs improve ML forecasts. The objective is to turn the answers into clear rules for risk desks, brokers, fund managers and regulators.
