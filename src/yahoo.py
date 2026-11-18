"""Polite Yahoo Finance downloader shared by the data scripts.

* 1-second delay between requests, retry with exponential backoff (CLAUDE.md rule 6)
* every failure is appended to data/logs/download_failures.csv; nothing is dropped silently
* returns adjusted daily OHLCV (auto_adjust=True) with a plain DatetimeIndex named "Date"
"""
import os
import time
from datetime import datetime, timezone

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(ROOT, "data", "logs")
DELAY_S = 1.0
_last_call = [0.0]


def log_failure(symbol, stage, message):
    os.makedirs(LOG_DIR, exist_ok=True)
    path = os.path.join(LOG_DIR, "download_failures.csv")
    row = pd.DataFrame([dict(utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                             symbol=symbol, stage=stage, message=str(message)[:300])])
    row.to_csv(path, mode="a", header=not os.path.exists(path), index=False)


def fetch(symbol, start, end=None, retries=4, stage="download", adjusted=True):
    """Adjusted OHLCV for one symbol. `end` is exclusive (yfinance convention).
    adjusted=False returns raw OHLC plus an "Adj Close" column (used by the live feed).
    Returns an empty DataFrame (and logs) if every attempt fails."""
    import yfinance as yf
    cols = ["Open", "High", "Low", "Close", "Volume"] + ([] if adjusted else ["Adj Close"])
    err = None
    for attempt in range(retries):
        wait = DELAY_S - (time.time() - _last_call[0])
        if wait > 0:
            time.sleep(wait)
        try:
            _last_call[0] = time.time()
            df = yf.download(symbol, start=start, end=end, auto_adjust=adjusted, progress=False,
                             threads=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if df is not None and len(df):
                df = df[cols].copy()
                df.index = pd.to_datetime(df.index).tz_localize(None)
                df.index.name = "Date"
                return df
            err = "empty response"
        except Exception as ex:  # network, throttling, parsing
            err = ex
        time.sleep(2 ** attempt)  # backoff 1, 2, 4, 8 s
    log_failure(symbol, stage, err)
    return pd.DataFrame(columns=cols)


def file_name(symbol):
    """Filesystem-safe name used for frozen and snapshot parquet files."""
    return symbol.replace("^", "_").replace("=", "_").replace("&", "_and_") + ".parquet"
