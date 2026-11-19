"""Offline tests for src/update_data.py validation and live-risk logic (no network)."""
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import update_data as u  # noqa: E402


def frame(dates, prices, sym="TEST.NS", volume=1_000_000):
    d = pd.to_datetime(dates)
    p = np.asarray(prices, dtype=float)
    return pd.DataFrame({"date": d, "ticker": sym, "open": p, "high": p, "low": p, "close": p,
                         "adj_close": p, "volume": volume})


STORED = frame(["2026-11-09", "2026-11-10", "2026-11-11", "2026-11-12", "2026-11-13"], [100, 101, 102, 101, 100])
AFTER_CLOSE = (19, 0)


def run(fetched, sym="TEST.NS", stored=STORED, today=date(2026, 11, 17), hm=AFTER_CLOSE):
    return u.validate_new_rows(stored, fetched, sym, today, hm)


def test_appends_only_new_valid_rows():
    f = pd.concat([STORED, frame(["2026-11-16", "2026-11-17"], [101, 102])])
    new, quar, logs, failed = run(f)
    assert not failed and len(quar) == 0
    assert list(new["date"].dt.strftime("%Y-%m-%d")) == ["2026-11-16", "2026-11-17"]
    assert any("overlap check passed" in m for _, m in logs)


def test_null_price_is_never_appended_and_later_rows_wait():
    """A null followed by a valid row: nothing from the null onwards is appended (no gap, no null)."""
    f = pd.concat([STORED, frame(["2026-11-16"], [np.nan]), frame(["2026-11-17"], [101])])
    new, _, logs, failed = run(f)
    assert not failed and len(new) == 0
    assert any(level == "warning" and "held back" in m for level, m in logs)


def test_non_positive_price_blocks_ticker():
    f = pd.concat([STORED, frame(["2026-11-16"], [0.0])])
    assert run(f)[3]


def test_duplicate_dates_block_ticker():
    f = pd.concat([STORED, frame(["2026-11-16", "2026-11-16"], [101, 101])])
    assert run(f)[3]


def test_big_move_is_quarantined_not_appended():
    f = pd.concat([STORED, frame(["2026-11-16", "2026-11-17"], [50, 51])])  # -69% log move: split-like
    new, quar, _, failed = run(f)
    assert not failed and len(new) == 0 and len(quar) == 2


def test_vix_big_moves_are_allowed():
    s = frame(["2026-11-13"], [12.0], sym="^INDIAVIX", volume=0)
    f = pd.concat([s, frame(["2026-11-16"], [16.0], sym="^INDIAVIX", volume=0)])
    new, quar, _, failed = run(f, sym="^INDIAVIX", stored=s)
    assert not failed and len(new) == 1 and len(quar) == 0


def test_overlap_change_above_half_percent_is_flagged():
    f = STORED.copy()
    f.loc[f.index[-1], "adj_close"] = 100 * 1.01
    _, _, logs, failed = run(f)
    assert not failed and any(level == "flag" and "overlap" in m for level, m in logs)


def test_zero_volume_placeholder_skipped_for_stocks():
    f = pd.concat([STORED, frame(["2026-11-16"], [100], volume=0)])
    new, _, logs, failed = run(f)
    assert not failed and len(new) == 0 and any("placeholder" in m for _, m in logs)


def test_todays_row_skipped_before_cutoff():
    f = pd.concat([STORED, frame(["2026-11-16", "2026-11-17"], [101, 102])])
    new, _, _, _ = run(f, hm=(15, 45))
    assert list(new["date"].dt.strftime("%Y-%m-%d")) == ["2026-11-16"]


def test_live_paths_never_touch_frozen():
    for p in (u.LIVE, u.LOGS, u.OUT_LIVE, u.PRICES, u.QUAR, u.ULOG):
        assert "frozen" not in Path(p).parts


def test_garch_risk_is_positive_and_ordered():
    rng = np.random.default_rng(42)
    r = rng.standard_t(5, 1800) * 0.01 * np.sqrt(3 / 5)
    px = pd.Series(100 * np.exp(np.cumsum(r)), index=pd.bdate_range("2019-01-01", periods=1800))
    k = u.garch_risk(px)
    assert k["n_obs"] == u.GARCH_WINDOW
    assert 0 < k["var_95"] < k["var_99"] < 0.2
    assert k["es_95"] > k["var_95"] and k["es_99"] > k["var_99"]


def test_bootstrap_keeps_historical_big_moves_but_flags_them():
    empty = STORED.iloc[0:0]
    f = frame(["2020-03-20", "2020-03-23", "2020-03-24"], [100, 72, 75])  # -33% crash day
    new, quar, logs, failed = run(f, stored=empty)
    assert not failed and len(new) == 3 and len(quar) == 0
    assert any(level == "flag" and "bootstrap" in m for level, m in logs)


def test_empty_newest_row_is_held_back_not_failed():
    """Yahoo publishes the latest day late: rows before it are appended, the empty row is retried."""
    f = pd.concat([STORED, frame(["2026-11-16"], [101]), frame(["2026-11-17"], [np.nan])])
    new, quar, logs, failed = run(f)
    assert not failed and len(quar) == 0
    assert list(new["date"].dt.strftime("%Y-%m-%d")) == ["2026-11-16"]
    assert any(level == "warning" and "not final" in m for level, m in logs)
