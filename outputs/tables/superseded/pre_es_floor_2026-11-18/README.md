# Superseded: full-panel results before the XGBoost ES floor (run of 18 Nov 2026)

Kept for the record; not used for report numbers. Replaced by the rerun of 19 Nov 2026 in `outputs/tables/`.

Why superseded: `xgb_quantile` floored ES at the *unfloored* VaR, so on days when XGBoost's level-alpha
quantile was positive (a "no-risk" forecast) ES could fall below VaR. Fixed on 19 Nov 2026
(`var_f = np.maximum(var, 1e-6); out[a] = (var_f, np.maximum(es, var_f))`). Non-XGBoost numbers are unaffected.

What each label actually contained:

| File label | Features |
|---|---|
| `price` | price/volume features only |
| `price_vix` | price/volume + India VIX level (`vix`, `vix_chg`, `rv_x_vix`) |
| `price_vix_macro` | price/volume + VIX level + USD/INR level (`usdinr`, `usdinr_chg`). Repo rate, CPI and IIP were **not** included (files not supplied), despite the label. |
