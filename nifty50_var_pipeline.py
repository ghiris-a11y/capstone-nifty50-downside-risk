"""
Capstone Phase 2 pipeline: GARCH vs ML downside risk (VaR / ES) for NSE Nifty 50 stocks.

Usage
-----
  pip install yfinance arch xgboost scikit-learn scipy pandas numpy pyarrow
  python nifty50_var_pipeline.py --demo                 # synthetic smoke test (no internet needed)
  python nifty50_var_pipeline.py --tickers RELIANCE.NS,TCS.NS --features price+vix+macro
  python nifty50_var_pipeline.py --tickers-file tickers.txt --test-end 2026-11-13

Optional macro files (data/raw/): repo_rate.csv, cpi.csv, iip.csv with columns date,value.
USD/INR is downloaded from Yahoo (INR=X).  Outputs go to ./outputs/.

Design (matches Phase 2 report, Chapter 3):
  * Features at day t use information up to t-1 only (shifted by one day); target is return on day t.
  * Train: start..2021-12-31 | Validation: 2022-01-01..2023-12-31 | Test: 2024-01-01..test_end.
  * GARCH / EGARCH / GJR-GARCH, Normal and Student-t, parameters re-estimated every REFIT days.
  * XGBoost: direct quantile regression (pinball loss). Random Forest and MLP: predict volatility,
    then filtered-historical-simulation quantiles from validation standardised residuals.
  * Benchmark: rolling 250-day historical simulation.
  * Tests: Kupiec POF, Christoffersen independence + conditional coverage, Basel zones (99% only),
    pinball loss, Fissler-Ziegel (FZ0) joint VaR-ES loss, Diebold-Mariano.
VaR and ES are reported as positive loss numbers (e.g. 0.025 = 2.5% loss).
"""
import argparse, os, warnings
import numpy as np, pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")
ALPHAS = (0.05, 0.01)
TRAIN_END, VAL_END = "2021-12-31", "2023-12-31"
TEST_START = "2024-01-01"
REFIT = 20
SEED = 42
OUT = "outputs"


# ------------------------------------------------------------------ data
def load_prices(ticker, start="2015-01-01", end=None):
    import yfinance as yf
    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["Close", "Volume"]].dropna()
    bad = df["Volume"] <= 0
    if bad.any() and not ticker.startswith("^") and ticker != "INR=X":
        os.makedirs(os.path.join("data", "logs"), exist_ok=True)
        log = os.path.join("data", "logs", "dropped_rows.csv")
        pd.DataFrame({"ticker": ticker, "date": df.index[bad].date,
                      "reason": "zero volume (Yahoo placeholder)"}).to_csv(
            log, mode="a", header=not os.path.exists(log), index=False)
        df = df[~bad]
    return df


def load_series(ticker, start, end, col="Close"):
    return load_prices(ticker, start, end)[col]


def load_macro(index, start, end, lag_days=None):
    """Forward-filled macro panel on the trading calendar, with release lags."""
    lag_days = lag_days or {"repo_rate": 0, "cpi": 15, "iip": 45}
    m = pd.DataFrame(index=index)
    for name, lag in lag_days.items():
        path = os.path.join("data", "raw", f"{name}.csv")
        if os.path.exists(path):
            s = pd.read_csv(path, parse_dates=["date"]).set_index("date")["value"]
            s.index = s.index + pd.Timedelta(days=lag)  # only known after release
            m[name] = s.reindex(s.index.union(index)).ffill().reindex(index)
    try:
        fx = load_series("INR=X", start, end)
        m["usdinr"] = fx.reindex(index).ffill()
    except Exception:
        pass
    return m


def demo_data(n=2900, seed=SEED):
    """Synthetic GJR-GARCH-like returns, fake VIX and macro: for testing the code only."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-01", periods=n)
    r = np.zeros(n); h = np.full(n, 1e-4)
    for t in range(1, n):
        h[t] = 5e-6 + 0.05 * r[t-1]**2 + 0.08 * (r[t-1] < 0) * r[t-1]**2 + 0.88 * h[t-1]
        r[t] = np.sqrt(h[t]) * rng.standard_t(6) * np.sqrt(4/6)
    vix = pd.Series(100 * np.sqrt(h * 252) * (1 + 0.1 * rng.standard_normal(n)), idx)
    macro = pd.DataFrame({"repo_rate": 5.5 + 0.0 * np.arange(n),
                          "usdinr": 70 + np.cumsum(rng.normal(0, 0.1, n))}, idx)
    return pd.Series(r, idx), vix, macro


# ------------------------------------------------------------------ features
def build_features(ret, vix, macro, volume=None, groups="price+vix+macro"):
    f = pd.DataFrame(index=ret.index)
    for l in (1, 2, 5, 10, 20):
        f[f"ret_l{l}"] = ret.shift(l - 1) if l > 1 else ret
    for w in (10, 20, 60):
        f[f"rv_{w}"] = ret.rolling(w).std()
    f["abs_ret"] = ret.abs()
    f["neg_ret"] = ret.clip(upper=0)
    f["mdd_60"] = (ret.cumsum() - ret.cumsum().rolling(60).max())
    if volume is not None:
        lv = np.log(volume.where(volume > 0)).ffill()
        f["vol_chg_5"] = lv.diff(5)
        f["vol_chg_20"] = lv.diff(20)
    if "vix" in groups and vix is not None:
        f["vix"] = vix.reindex(ret.index).ffill() / 100
        f["vix_chg"] = f["vix"].diff()
        f["rv_x_vix"] = f["rv_20"] * f["vix"]
    if "macro" in groups and macro is not None:
        for c in macro.columns:
            f[c] = macro[c].reindex(ret.index).ffill()
            f[c + "_chg"] = f[c].diff(21)
    return f.shift(1)  # information up to t-1 only


# ------------------------------------------------------------------ GARCH
def garch_forecasts(ret, kind, dist, test_start, refit=REFIT):
    from arch import arch_model
    r = ret * 100
    pos = np.where(r.index >= pd.Timestamp(test_start))[0]
    spec = dict(mean="Constant", dist=dist, p=1, q=1)
    spec.update({"GARCH": dict(vol="GARCH"), "EGARCH": dict(vol="EGARCH", o=1),
                 "GJR": dict(vol="GARCH", o=1)}[kind])
    rows = []
    for s in range(pos[0], len(r), refit):
        e = min(s + refit, len(r))
        res = arch_model(r.iloc[:s], **spec).fit(disp="off", show_warning=False)
        fixed = arch_model(r.iloc[:e], **spec).fix(res.params)
        sig = fixed.conditional_volatility.iloc[s:e].values / 100
        mu = res.params["mu"] / 100
        nu = res.params.get("nu", np.nan)
        for d, sg in zip(r.index[s:e], sig):
            rows.append((d, mu, sg, nu))
    f = pd.DataFrame(rows, columns=["date", "mu", "sig", "nu"]).set_index("date")
    out = {}
    for a in ALPHAS:
        if dist == "normal":
            z = stats.norm.ppf(a)
            var = -(f.mu + f.sig * z)
            es = -(f.mu - f.sig * stats.norm.pdf(z) / a)
        else:
            sc = np.sqrt((f.nu - 2) / f.nu)  # arch's t is unit-variance
            tq = stats.t.ppf(a, f.nu)
            var = -(f.mu + f.sig * sc * tq)
            es = -f.mu + f.sig * sc * (stats.t.pdf(tq, f.nu) / a) * ((f.nu + tq**2) / (f.nu - 1))
        out[a] = (var, es)
    return out


def hist_sim(ret, test_start, window=250):
    out = {}
    for a in ALPHAS:
        var, es = [], []
        for d in ret.index[ret.index >= pd.Timestamp(test_start)]:
            w = ret.loc[:d].iloc[-window - 1:-1]  # strictly past data
            q = w.quantile(a)
            var.append(-q); es.append(-w[w <= q].mean())
        idx = ret.index[ret.index >= pd.Timestamp(test_start)]
        out[a] = (pd.Series(var, idx), pd.Series(es, idx))
    return out


# ------------------------------------------------------------------ ML
def _split(X, y):
    tr = X.index <= TRAIN_END
    va = (X.index > TRAIN_END) & (X.index <= VAL_END)
    te = X.index >= TEST_START
    return tr, va, te


def xgb_quantile(X, y):
    import xgboost as xgb
    tr, va, te = _split(X, y)
    fit = tr | va
    levels = {a: [a] + [a * u for u in (0.1, 0.3, 0.5, 0.7, 0.9)] for a in ALPHAS}
    out = {}
    for a, lv in levels.items():
        preds = []
        for q in lv:
            m = xgb.XGBRegressor(objective="reg:quantileerror", quantile_alpha=q, n_estimators=300,
                                 max_depth=3, learning_rate=0.03, subsample=0.8,
                                 colsample_bytree=0.8, reg_lambda=5, random_state=SEED, n_jobs=1)
            m.fit(X[fit], y[fit])
            preds.append(m.predict(X[te]))
        P = np.sort(np.array(preds).T, axis=1)  # no quantile crossing
        idx = X.index[te]
        var = pd.Series(-P[:, np.where(np.array(lv) == a)[0][0]], idx)
        es = pd.Series(-P[:, 1:].mean(axis=1), idx)  # mean of tail quantiles approximates ES
        out[a] = (np.maximum(var, 1e-6), np.maximum(es, var))
    return out


def vol_scaled(X, y, model):
    """Predict |return| with a tree/NN model, then use FHS quantiles from validation residuals."""
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.neural_network import MLPRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    tr, va, te = _split(X, y)
    if model == "rf":
        m = RandomForestRegressor(n_estimators=300, max_depth=6, min_samples_leaf=20,
                                  max_features=0.5, random_state=SEED, n_jobs=1)
    else:
        m = make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(64, 32), activation="relu", solver="adam",
                          alpha=1e-3, early_stopping=True, validation_fraction=0.15,
                          max_iter=300, random_state=SEED))
    target = y.abs() * 100  # scaled so the MLP trains well
    m.fit(X[tr], target[tr])
    sv = np.maximum(m.predict(X[va]) / 100, 1e-4)
    z = ((y[va] - y[tr].mean()) / sv).values
    m.fit(X[tr | va], target[tr | va])
    st = np.maximum(m.predict(X[te]) / 100, 1e-4)
    mu = y[tr | va].mean()
    idx = X.index[te]
    out = {}
    for a in ALPHAS:
        qz = np.quantile(z, a); ez = z[z <= qz].mean()
        out[a] = (pd.Series(-(mu + st * qz), idx), pd.Series(-(mu + st * ez), idx))
    return out


# ------------------------------------------------------------------ backtests / losses
def kupiec(h, p):
    n, x = len(h), int(h.sum())
    if x in (0, n):
        pi = x / n
        ll1 = 0.0
    else:
        pi = x / n
        ll1 = x * np.log(pi) + (n - x) * np.log(1 - pi)
    ll0 = x * np.log(p) + (n - x) * np.log(1 - p)
    lr = -2 * (ll0 - ll1)
    return lr, 1 - stats.chi2.cdf(lr, 1)


def christoffersen_ind(h):
    h = h.astype(int).values
    a, b = h[:-1], h[1:]
    n00 = ((a == 0) & (b == 0)).sum(); n01 = ((a == 0) & (b == 1)).sum()
    n10 = ((a == 1) & (b == 0)).sum(); n11 = ((a == 1) & (b == 1)).sum()
    def ll(k, n):
        return 0.0 if k in (0, n) else k * np.log(k / n) + (n - k) * np.log(1 - k / n)
    ll_ind = ll(n01, n00 + n01) + ll(n11, n10 + n11)
    pi = (n01 + n11) / max(n00 + n01 + n10 + n11, 1)
    ll_0 = 0.0 if pi in (0, 1) else (n01 + n11) * np.log(pi) + (n00 + n10) * np.log(1 - pi)
    lr = max(-2 * (ll_0 - ll_ind), 0.0)
    return lr, 1 - stats.chi2.cdf(lr, 1)


def basel_green_share(h99):
    """Share of non-overlapping 250-day windows in the Green zone (0-4 exceptions), 99% VaR only."""
    blocks = [h99.iloc[i:i + 250] for i in range(0, len(h99) - 249, 250)]
    if not blocks:
        return np.nan
    return float(np.mean([b.sum() <= 4 for b in blocks]))


def pinball(y, var, a):
    q = -var
    return float(np.mean(np.maximum(a * (y - q), (a - 1) * (y - q))))


def fz0_series(y, var, es, a):
    v, e = -var, -es
    e = np.minimum(e, v - 1e-9)
    return -(1 / (a * e)) * (y <= v) * (v - y) + v / e + np.log(-e) - 1


def dm_test(l1, l2, lag=5):
    d = (l1 - l2).dropna().values
    n = len(d); dm = d - d.mean()
    g0 = dm @ dm / n
    lrv = g0 + 2 * sum((1 - k / (lag + 1)) * (dm[k:] @ dm[:-k]) / n for k in range(1, lag + 1))
    stat = d.mean() / np.sqrt(lrv / n)
    return stat, 2 * (1 - stats.norm.cdf(abs(stat)))


def evaluate(name, ticker, y, fc):
    rows, fz_store = [], {}
    for a, (var, es) in fc.items():
        yy, var, es = y.reindex(var.index), var, es.reindex(var.index)
        h = (yy < -var).astype(int)
        lr_u, p_u = kupiec(h, a)
        lr_i, p_i = christoffersen_ind(h)
        p_cc = 1 - stats.chi2.cdf(lr_u + lr_i, 2)
        tail = yy[h == 1]
        ratio = (-tail.mean() / es[h == 1].mean()) if len(tail) else np.nan
        fz = fz0_series(yy, var, es, a)
        fz_store[a] = fz
        rows.append(dict(ticker=ticker, model=name, alpha=a, n=len(h), exceptions=int(h.sum()),
                         exc_rate=h.mean(), kupiec_p=p_u, ind_p=p_i, cc_p=p_cc,
                         pass_kupiec=p_u > 0.05, pass_cc=p_cc > 0.05,
                         basel_green_share=basel_green_share(h) if a == 0.01 else np.nan,
                         pinball=pinball(yy, var, a), fz0=fz.mean(), actual_over_expected_es=ratio))
    return rows, fz_store


# ------------------------------------------------------------------ main
def run_ticker(ticker, ret, vix, macro, volume, groups):
    X_all = build_features(ret, vix, macro, volume, groups)
    data = pd.concat([X_all, ret.rename("y")], axis=1).dropna()
    X, y = data.drop(columns="y"), data["y"]
    forecasts = {}
    for kind in ("GARCH", "EGARCH", "GJR"):
        for dist in ("normal", "t"):
            try:
                forecasts[f"{kind}-{dist}"] = garch_forecasts(ret, kind, dist, TEST_START)
            except Exception as ex:
                print(f"  {ticker} {kind}-{dist} failed: {ex}")
    forecasts["HistSim250"] = hist_sim(ret, TEST_START)
    forecasts["XGBoost"] = xgb_quantile(X, y)
    forecasts["RandomForest"] = vol_scaled(X, y, "rf")
    forecasts["MLP"] = vol_scaled(X, y, "mlp")
    rows, fz = [], {}
    yt = ret[ret.index >= TEST_START]
    for name, fc in forecasts.items():
        r, f = evaluate(name, ticker, yt, fc)
        rows += r; fz[name] = f
    return pd.DataFrame(rows), fz


def regime_table(ticker, ret, vix, fz_all):
    """Mean FZ0 (95% VaR/ES) by India VIX quartile of the previous day, per model."""
    v = vix.reindex(ret.index).ffill().shift(1)
    v = v[v.index >= TEST_START]
    q = pd.qcut(v, 4, labels=["Q1 calm", "Q2", "Q3", "Q4 stressed"])
    rows = []
    for m, f in fz_all.items():
        s = f[0.05].reindex(q.index)
        for lab, g in s.groupby(q):
            rows.append(dict(ticker=ticker, model=m, regime=lab, mean_fz0=g.mean()))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", default="")
    ap.add_argument("--tickers-file", default="")
    ap.add_argument("--features", default="price+vix+macro", help="price | price+vix | price+vix+macro")
    ap.add_argument("--start", default="2015-01-01")
    ap.add_argument("--test-end", default=None)
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    all_rows, all_reg, dm_rows = [], [], []

    if a.demo:
        ret, vix, macro = demo_data()
        jobs = [("DEMO", ret, vix, macro, None)]
    else:
        tickers = [t.strip() for t in a.tickers.split(",") if t.strip()]
        if a.tickers_file:
            tickers += [l.strip() for l in open(a.tickers_file) if l.strip()]
        vix = load_series("^INDIAVIX", a.start, a.test_end)
        jobs = []
        for t in tickers:
            px = load_prices(t, a.start, a.test_end)
            ret = np.log(px["Close"]).diff().dropna()
            macro = load_macro(ret.index, a.start, a.test_end)
            jobs.append((t, ret, vix, macro, px["Volume"].reindex(ret.index)))

    for t, ret, vix_s, macro, volume in jobs:
        print(f"Running {t} ...")
        res, fz = run_ticker(t, ret, vix_s, macro, volume, a.features)
        all_rows.append(res)
        all_reg.append(regime_table(t, ret, vix_s, fz))
        names = list(fz)
        for i in range(len(names)):          # Diebold-Mariano, 95% joint loss
            for j in range(i + 1, len(names)):
                stat, p = dm_test(fz[names[i]][0.05], fz[names[j]][0.05])
                dm_rows.append(dict(ticker=t, model_a=names[i], model_b=names[j], dm_stat=stat, p=p))

    res = pd.concat(all_rows)
    tag = a.features.replace("+", "_")
    res.to_csv(f"{OUT}/backtest_results_{tag}.csv", index=False)
    pd.concat(all_reg).to_csv(f"{OUT}/regime_results_{tag}.csv", index=False)
    pd.DataFrame(dm_rows).to_csv(f"{OUT}/diebold_mariano_{tag}.csv", index=False)
    summ = (res.groupby(["model", "alpha"])
               .agg(exc_rate=("exc_rate", "mean"), pass_kupiec=("pass_kupiec", "mean"),
                    pass_cc=("pass_cc", "mean"), green99=("basel_green_share", "mean"),
                    pinball=("pinball", "mean"), fz0=("fz0", "mean"),
                    es_ratio=("actual_over_expected_es", "mean")).round(4))
    summ.to_csv(f"{OUT}/summary_{tag}.csv")
    print(summ.to_string())


if __name__ == "__main__":
    main()
