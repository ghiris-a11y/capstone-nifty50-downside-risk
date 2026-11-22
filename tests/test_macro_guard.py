"""load_macro must skip a macro file with blank or unverified rows, and use a complete VERIFIED one."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import nifty50_var_pipeline as p  # noqa: E402

IDX = pd.bdate_range("2020-01-01", periods=60)


def _write(tmp_path, rows):
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    pd.DataFrame(rows, columns=["date", "value", "source_url", "status", "note"]).to_csv(raw / "repo_rate.csv", index=False)


def _no_fx(*a, **k):
    raise RuntimeError("no network in tests")


def test_file_with_blank_row_is_skipped(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(p, "load_series", _no_fx)
    _write(tmp_path, [["2019-12-01", 5.15, "u", "VERIFIED", ""], ["2020-02-01", None, "", "VERIFIED", "not found"]])
    m = p.load_macro(IDX, "2020-01-01", "2020-04-01", lag_days={"repo_rate": 0})
    assert "repo_rate" not in m.columns
    assert "skipped" in (tmp_path / "data" / "logs" / "macro_skipped.log").read_text()


def test_unverified_status_is_skipped(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(p, "load_series", _no_fx)
    _write(tmp_path, [["2019-12-01", 5.15, "u", "VERIFIED", ""], ["2020-02-01", 4.40, "u", "UNVERIFIED", ""]])
    m = p.load_macro(IDX, "2020-01-01", "2020-04-01", lag_days={"repo_rate": 0})
    assert "repo_rate" not in m.columns


def test_fully_verified_file_is_used(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(p, "load_series", _no_fx)
    _write(tmp_path, [["2019-12-01", 5.15, "u", "VERIFIED", ""], ["2020-02-03", 4.40, "u", " verified ", ""]])
    m = p.load_macro(IDX, "2020-01-01", "2020-04-01", lag_days={"repo_rate": 0})
    assert m.loc["2020-01-02", "repo_rate"] == 5.15
    assert m.loc["2020-02-04", "repo_rate"] == 4.40
