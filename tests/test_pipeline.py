"""Regression tests for nifty50_var_pipeline.py."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import nifty50_var_pipeline as p  # noqa: E402


def _series(n=120, seed=42):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2023-01-02", periods=n)
    ret = pd.Series(rng.normal(0, 0.01, n), idx)
    vol = pd.Series(rng.integers(1_000_000, 2_000_000, n).astype(float), idx)
    return ret, vol


def test_zero_volume_gives_no_infinite_features():
    ret, vol = _series()
    vol.iloc[[30, 80]] = 0  # Yahoo placeholder rows
    X = p.build_features(ret, None, None, vol, "price")
    assert not np.isinf(X.to_numpy()).any()


def test_features_use_only_past_information():
    ret, vol = _series()
    X = p.build_features(ret, None, None, vol, "price")
    # ret_l1 at day t must equal the return of day t-1
    assert np.allclose(X["ret_l1"].iloc[1:].to_numpy(), ret.iloc[:-1].to_numpy())


def test_kupiec_accepts_exact_nominal_rate():
    h = pd.Series([1] * 5 + [0] * 495)
    _, pval = p.kupiec(h, 0.01)
    assert pval > 0.05


def test_xgboost_quantile_calibration_on_seeded_demo_data():
    """Regression test for the xgb_quantile column bug (VaR read from the 0.1*alpha quantile)."""
    ret, vix, macro = p.demo_data()  # seed 42
    X = p.build_features(ret, vix, macro, None, "price+vix+macro")
    data = pd.concat([X, ret.rename("y")], axis=1).dropna()
    X, y = data.drop(columns="y"), data["y"]
    fc = p.xgb_quantile(X, y)
    bounds = {0.05: (0.03, 0.07), 0.01: (0.003, 0.025)}
    for a, (var, es) in fc.items():
        rate = float((y.reindex(var.index) < -var).mean())
        lo, hi = bounds[a]
        assert lo <= rate <= hi, f"alpha={a}: exception rate {rate:.4f} outside [{lo}, {hi}]"
        assert (es.reindex(var.index) >= var).all(), f"alpha={a}: ES below VaR"
