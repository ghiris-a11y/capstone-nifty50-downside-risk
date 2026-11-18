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
