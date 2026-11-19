"""SHAP feature importance for the XGBoost 99% VaR model (input to figure 6).

For each stock: fit the XGBoost quantile model at q = 0.01 exactly as xgb_quantile() does (same
hyperparameters, fitted on train + validation), then compute exact Tree SHAP contributions on the test
window with XGBoost's built-in pred_contribs. Importance = mean |SHAP| per feature (in return units).
Feature set: price_vixlevel (selected on the validation window; outputs/tables/validation/selected_variant.json).

Writes outputs/tables/xgb_shap_importance_price_vixlevel.csv (stock x feature) and *_summary.csv.
"""
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import nifty50_var_pipeline as p  # noqa: E402

FEATURES, LABEL, Q = "price+vix", "price_vixlevel", 0.01


def main(test_end="2026-11-18"):
    import xgboost as xgb
    os.chdir(ROOT)
    p.FROZEN_DIR = os.path.join("data", "frozen")
    uni = pd.read_csv(os.path.join("config", "universe.csv"))
    vix = p.load_series("^INDIAVIX", "2015-01-01", test_end)
    rows = []
    for t in uni["ticker"]:
        px = p.load_prices(t, "2015-01-01", test_end)
        ret = np.log(px["Close"]).diff().dropna()
        X = p.build_features(ret, vix, None, px["Volume"].reindex(ret.index), FEATURES)
        d = pd.concat([X, ret.rename("y")], axis=1).dropna()
        X, y = d.drop(columns="y"), d["y"]
        tr, va, te = p._split(X, y)
        m = xgb.XGBRegressor(objective="reg:quantileerror", quantile_alpha=Q, n_estimators=300, max_depth=3,
                             learning_rate=0.03, subsample=0.8, colsample_bytree=0.8, reg_lambda=5,
                             random_state=p.SEED, n_jobs=1)
        m.fit(X[tr | va], y[tr | va])
        contrib = m.get_booster().predict(xgb.DMatrix(X[te]), pred_contribs=True)[:, :-1]  # drop bias column
        imp = np.abs(contrib).mean(axis=0)
        for f, v in zip(X.columns, imp):
            rows.append(dict(ticker=t, feature=f, mean_abs_shap=float(v)))
        print(t, "done")
    d = pd.DataFrame(rows)
    d.to_csv(os.path.join("outputs", "tables", f"xgb_shap_importance_{LABEL}.csv"), index=False)
    s = (d.groupby("feature")["mean_abs_shap"].agg(["mean", "median", "std", "count"])
           .sort_values("mean", ascending=False).reset_index())
    s.to_csv(os.path.join("outputs", "tables", f"xgb_shap_importance_{LABEL}_summary.csv"), index=False)
    print(s.round(6).to_string(index=False))


if __name__ == "__main__":
    main()
