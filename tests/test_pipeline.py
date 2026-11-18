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


def test_frozen_loader_respects_end_and_drops_placeholders(tmp_path, monkeypatch):
    idx = pd.bdate_range("2024-01-01", periods=10)
    df = pd.DataFrame({"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": np.linspace(100, 109, 10),
                       "Volume": [1000] * 4 + [0] + [1000] * 5}, index=idx)
    df.index.name = "Date"
    df.to_parquet(tmp_path / "TEST.NS.parquet")
    monkeypatch.chdir(tmp_path)  # dropped-row log goes to tmp_path/data/logs
    monkeypatch.setattr(p, "FROZEN_DIR", str(tmp_path))
    out = p.load_prices("TEST.NS", "2024-01-01", str(idx[8].date()))
    assert out.index.max() == idx[7]              # end date is exclusive
    assert idx[4] not in out.index and len(out) == 7  # zero-volume row dropped
    assert (tmp_path / "data" / "logs" / "dropped_rows.csv").exists()


def test_universe_is_balanced_panel_size():
    uni = pd.read_csv(Path(__file__).resolve().parents[1] / "config" / "universe.csv")
    assert 40 <= len(uni) <= 45 and uni["ticker"].is_unique
