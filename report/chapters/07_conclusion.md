# CHAPTER 7: CONCLUSION

## 7.1 Answers to the research questions

- **RQ1.** No. The ML models were breached more often than nominal (99%: XGBoost {{exc99_xgb}}, Random Forest {{exc99_rf}}, MLP {{exc99_mlp}}), while GARCH-t models were closest to 1% ({{closest1}} {{closest1_exc}}, {{closest2}} {{closest2_exc}}, {{closest3}} {{closest3_exc}}). H1 is {{h1}}.
- **RQ2.** No. Most differences in joint VaR-ES loss were not significant ({{dm_n}} of {{dm_total}} pairs); where they were, GARCH was better in {{dm_g}} pairs and ML in {{dm_m}}. H2 is {{h2}}.
- **RQ3.** Every model found stressed days harder, and in the most fearful VIX quartile the lowest loss came from {{q4_best}}; ML did not gain an advantage in stress. H3 is {{h3}}.
- **RQ4.** The India VIX had the largest effect on XGBoost's forecasts but did not bring any ML model closer to the nominal breach rate; macro series could not yet be tested. H4: {{h4}}.

## 7.2 Contribution

The study gives stock-level, out-of-sample evidence for Indian large caps on the measures risk desks actually use, with every number traceable to a frozen, hashed data snapshot and open code. It adds two practical diagnostics that averages hide: the clustering of breaches on market-wide stress days and the "no-risk" forecasts of a quantile-regression ML model. It also delivers a working daily risk pipeline and a plain-language dashboard (Appendix G).

## 7.3 Limitations

- About {{test_days_max}} test days per stock gives about {{exp_breaches_stock}} expected 99% breaches per stock, so single-stock tests have low power.
- The panel keeps only {{n_stocks}} stocks with full history since 2015 (survivorship bias); newer large firms are excluded.
- The ML models were fitted once on 2015 to 2023 and not refitted during the test, while GARCH models were refitted every 20 days; regular refitting might help ML.
- Repo rate, CPI and IIP were not yet included because the official files had not been supplied.
- Yahoo Finance data are unofficial; corporate actions are not always adjusted.
- The test window was calm by the standard of 2020; results may differ in a crisis. Past data do not guarantee future results.
- Guide approval of the panel and the November 2026 window was pending when these results were produced.

## 7.4 Future research

Refit ML models on a rolling basis and compare again; add the RBI and MoSPI macro series with release lags; extend to portfolio-level VaR to measure the clustering effect directly; test hybrid models that feed GARCH volatility into ML; and repeat the study through a high-stress period.
