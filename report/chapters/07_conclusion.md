# CHAPTER 7: CONCLUSION

## 7.1 Answers to the research questions

- **RQ1.** No. The machine-learning models we tested missed more often than the 1% ideal (XGBoost {{exc99_xgb}}, Random Forest {{exc99_rf}}, MLP {{exc99_mlp}}). The Student-t GARCH models came closest to expected. H1: {{h1}}.
- **RQ2.** No. Most score gaps could be luck ({{dm_n}} of {{dm_total}} pairs); real gaps favoured GARCH {{dm_g}} times and ML {{dm_m}} times. H2: {{h2}}.
- **RQ3.** No. Every model did worse in nervous markets, and the best score on those days came from {{q4_best}}. H3: {{h3}}.
- **RQ4.** No. The India VIX moved XGBoost's forecasts most but did not bring any ML model closer to 1%. H4: {{h4}}.

## 7.2 Contribution

The study gives stock-level, out-of-sample evidence for Indian large caps on the measures risk desks use. Every number traces to a frozen, hashed data snapshot and open code. It also shows two risks that averages hide: misses bunching on market-wide fall days, and zero-risk forecasts from a machine-learning model. Finally, it delivers a working daily risk pipeline and a plain-language dashboard.

## 7.3 Limitations

- About {{test_days_max}} test days per stock gives about {{exp_breaches_stock}} expected 99% misses each, so single-stock tests are weak.
- Only stocks listed since 2015 are included (survivorship bias).
- The ML models were fitted once; regular refitting might help them.
- Free Yahoo Finance data are unofficial.
- The test years were calm compared with 2020; results may differ in a crisis.
- The project guide had not yet approved the panel and the test window when these results were produced.

## 7.4 Future research

Four extensions would add most. Refit the ML models on a rolling basis. Measure clustering directly with portfolio-level VaR. Test hybrid models that feed GARCH volatility into ML. Repeat the study through a high-stress period.
