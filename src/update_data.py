"""Daily live-data update (P3), run by .github/workflows/daily_update.yml at 7:00 PM IST.

For every ticker in config/universe.csv plus ^NSEI, ^INDIAVIX and INR=X:
  * load stored rows from data/live/prices_live.csv
    (long format: date,ticker,open,high,low,close,adj_close,volume)
  * fetch Yahoo data starting at the 5th-last stored date (5 overlapping trading days), or from
    --bootstrap-start if the ticker has no stored rows yet
  * validate before appending: block nulls, zero/negative prices and duplicate dates (ticker fails);
    skip zero-volume placeholder rows (logged); quarantine one-day moves above 20% to
    data/live/quarantine.csv (stocks, ^NSEI and INR=X; not ^INDIAVIX, which often moves that much);
    flag overlap days whose adj_close differs from the stored value by more than 0.5%
  * append only new, valid rows
Then fit GJR-GARCH(1,1) Student-t on the last 1,500 daily log returns of each stock and write the
one-day-ahead 95%/99% VaR and ES to outputs/live/latest_risk.csv.
Writes only data/live/, data/logs/ and outputs/live/; never reads or writes data/frozen/.
Exit code 1 if any ticker failed validation, had rows quarantined or could not be fetched.

  python src/update_data.py
"""
import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yahoo import ROOT, fetch  # noqa: E402

LIVE = os.path.join(ROOT, "data", "live")
LOGS = os.path.join(ROOT, "data", "logs")
OUT_LIVE = os.path.join(ROOT, "outputs", "live")
PRICES = os.path.join(LIVE, "prices_live.csv")
QUAR = os.path.join(LIVE, "quarantine.csv")
ULOG = os.path.join(LOGS, "update_log.csv")
EXTRA = ["^NSEI", "^INDIAVIX", "INR=X"]
COLS = ["date", "ticker", "open", "high", "low", "close", "adj_close", "volume"]
IST = timezone(timedelta(hours=5, minutes=30))
CLOSE_CUTOFF_IST = (16, 30)  # rows dated today are used only after 16:30 IST (market closes 15:30)
MOVE_LIMIT = 0.20
OVERLAP_TOL = 0.005
GARCH_WINDOW = 1500
MAX_LAG = 3               # a stock may trail the Nifty by at most 3 trading days before the run fails
MAX_NIFTY_AGE_BDAYS = 4   # the Nifty's last date may be at most 4 business days old (allows for holidays)

for _p in (LIVE, LOGS, OUT_LIVE, PRICES, QUAR, ULOG):  # rule 5: the Action never touches data/frozen
    assert "frozen" not in os.path.relpath(_p, ROOT).split(os.sep)


def is_stock(sym):
    return not (sym.startswith("^") or sym == "INR=X")


def to_long(df, sym):
    """yfinance frame (Open, High, Low, Close, Adj Close, Volume) -> long rows."""
    if not len(df):
        return pd.DataFrame(columns=COLS)
    out = pd.DataFrame({"date": pd.to_datetime(df.index).normalize(), "ticker": sym,
                        "open": df["Open"].values, "high": df["High"].values, "low": df["Low"].values,
                        "close": df["Close"].values, "adj_close": df["Adj Close"].values,
                        "volume": df["Volume"].values})
    return out.reset_index(drop=True)


def validate_new_rows(stored, fetched, sym, today_ist, now_ist_hm):
    """Pure validation step. stored/fetched: long frames for one symbol.
    Returns (rows_to_append, quarantined_rows, log_entries, failed: bool)."""
    logs, failed = [], False
    f = fetched.copy()
    if len(f) and today_ist is not None and now_ist_hm < CLOSE_CUTOFF_IST:
        intraday = f["date"] == pd.Timestamp(today_ist)
        if intraday.any():
            logs.append(("info", f"skipped today's row ({today_ist}): market data not final before 16:30 IST"))
            f = f[~intraday]
    if f["date"].duplicated().any():
        logs.append(("error", "duplicate dates in fetched data: "
                     + ", ".join(str(d.date()) for d in f.loc[f["date"].duplicated(), "date"])))
        return f.iloc[0:0], f.iloc[0:0], logs, True

    last = stored["date"].max() if len(stored) else None
    # overlap check: adjusted close on dates already stored
    if len(stored):
        ov = f.merge(stored[["date", "adj_close"]], on="date", suffixes=("", "_stored"))
        if len(ov):
            rel = (ov["adj_close"] / ov["adj_close_stored"] - 1).abs()
            bad = ov[rel > OVERLAP_TOL]
            if len(bad):
                logs.append(("flag", "adj_close changed by more than 0.5% on overlap days (possible corporate "
                             "action or re-adjustment): " + "; ".join(
                                 f"{r.date.date()} {r.adj_close_stored:.4f}->{r.adj_close:.4f}" for r in bad.itertuples())))
            else:
                logs.append(("info", f"overlap check passed on {len(ov)} days"))
    new = f[f["date"] > last] if last is not None else f
    new = new.sort_values("date")

    price_cols = ["open", "high", "low", "close", "adj_close"]
    # Yahoo sometimes returns recent days with empty prices until it finishes publishing them. Rows with
    # empty prices are never appended: keep only the rows before the first empty one, so no gap is created,
    # and retry from there on the next run. If Yahoo never fills the day, the staleness check in main()
    # fails the run once the ticker is more than MAX_LAG Nifty trading days behind.
    empty = new[price_cols].isna().any(axis=1).to_numpy()
    if empty.any():
        k = int(np.argmax(empty))
        logs.append(("warning", f"empty prices from {new['date'].iloc[k].date()} (Yahoo not final yet); "
                     f"{len(new) - k} row(s) held back and retried next run"))
        new = new.iloc[:k]
    if new[price_cols].isna().any().any():  # cannot happen after truncation; kept as a guard
        bad = new[new[price_cols].isna().any(axis=1)]
        logs.append(("error", "null prices on " + ", ".join(str(d.date()) for d in bad["date"])))
        failed = True
    if (new[price_cols] <= 0).any().any():
        bad = new[(new[price_cols] <= 0).any(axis=1)]
        logs.append(("error", "zero or negative prices on " + ", ".join(str(d.date()) for d in bad["date"])))
        failed = True
    if failed:
        return new.iloc[0:0], new.iloc[0:0], logs, True

    if is_stock(sym):
        ph = new["volume"] <= 0
        if ph.any():
            logs.append(("info", "skipped zero-volume placeholder rows: "
                         + ", ".join(str(d.date()) for d in new.loc[ph, "date"])))
            new = new[~ph]

    quarantined = new.iloc[0:0]
    if not len(stored) and sym != "^INDIAVIX" and len(new) > 1:
        # bootstrap: history is loaded once; past moves above 20% (e.g. March 2020) are flagged, not quarantined
        mv = np.log(new["adj_close"].astype(float)).diff()
        big = new.loc[mv.abs() > MOVE_LIMIT, "date"]
        if len(big):
            logs.append(("flag", "bootstrap history contains one-day moves above 20% (kept): " + "; ".join(
                f"{d.date()} {v:+.1%}" for d, v in zip(big, mv[mv.abs() > MOVE_LIMIT]))))
        return new, quarantined, logs, False
    if sym != "^INDIAVIX" and len(new):
        prev = stored.sort_values("date")["adj_close"].iloc[-1] if len(stored) else np.nan
        chain = np.concatenate([[prev], new["adj_close"].to_numpy(dtype=float)])
        moves = np.log(chain[1:] / chain[:-1])
        big = np.abs(np.nan_to_num(moves)) > MOVE_LIMIT
        if big.any():
            k = int(np.argmax(big))  # quarantine from the first big move on (later rows depend on it)
            quarantined = new.iloc[k:].assign(reason=f"one-day move {moves[k]:+.1%} > 20% (suspected unadjusted "
                                                     f"corporate action)")
            logs.append(("flag", f"quarantined {len(quarantined)} rows from {new['date'].iloc[k].date()}: "
                                 f"move {moves[k]:+.1%}"))
            new = new.iloc[:k]
    return new, quarantined, logs, False


def garch_risk(adj_close):
    """One-day-ahead VaR/ES (positive loss numbers) from GJR-GARCH(1,1) Student-t on the last 1,500
    log returns; same VaR/ES formulas as nifty50_var_pipeline.garch_forecasts."""
    from arch import arch_model
    from scipy import stats
    r = np.log(adj_close).diff().dropna().iloc[-GARCH_WINDOW:] * 100
    res = arch_model(r, mean="Constant", vol="GARCH", p=1, o=1, q=1, dist="t").fit(disp="off", show_warning=False)
    fc = res.forecast(horizon=1, reindex=False)
    sig = float(np.sqrt(fc.variance.values[-1, 0])) / 100
    mu, nu = float(res.params["mu"]) / 100, float(res.params["nu"])
    sc = np.sqrt((nu - 2) / nu)
    out = dict(n_obs=len(r), mu=mu, sigma_1d=sig, nu=nu)
    for a in (0.05, 0.01):
        tq = stats.t.ppf(a, nu)
        out[f"var_{int((1 - a) * 100)}"] = -(mu + sig * sc * tq)
        out[f"es_{int((1 - a) * 100)}"] = -mu + sig * sc * (stats.t.pdf(tq, nu) / a) * ((nu + tq ** 2) / (nu - 1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap-start", default="2019-01-01",
                    help="history fetched for a ticker with no stored rows (>= 1,500 trading days)")
    ap.add_argument("--skip-risk", action="store_true")
    a = ap.parse_args()
    for d in (LIVE, LOGS, OUT_LIVE):
        os.makedirs(d, exist_ok=True)

    now = datetime.now(IST)
    run_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    uni = pd.read_csv(os.path.join(ROOT, "config", "universe.csv"))
    symbols = uni["ticker"].tolist() + EXTRA
    stored_all = (pd.read_csv(PRICES, parse_dates=["date"], float_precision="round_trip") if os.path.exists(PRICES)
                  else pd.DataFrame(columns=COLS))
    appended, quarantined, log_rows, failures = [], [], [], []

    for sym in symbols:
        stored = stored_all[stored_all["ticker"] == sym].sort_values("date")
        if len(stored) >= 5:
            start = stored["date"].iloc[-5].date()
        elif len(stored):
            start = stored["date"].iloc[0].date()
        else:
            start = a.bootstrap_start
        raw = fetch(sym, str(start), None, stage="update_data", adjusted=False)
        if not len(raw):
            failures.append(sym)
            log_rows.append(dict(run_utc=run_utc, ticker=sym, level="error", new_rows=0,
                                 message=f"no data returned from {start}"))
            continue
        new, quar, logs, failed = validate_new_rows(stored, to_long(raw, sym), sym, now.date(),
                                                    (now.hour, now.minute))
        if failed:
            failures.append(sym)
        appended.append(new)
        if len(quar):
            quarantined.append(quar)
            failures.append(sym)  # needs a human decision; fail the run so GitHub sends an alert
        for level, msg in logs:
            log_rows.append(dict(run_utc=run_utc, ticker=sym, level=level, new_rows=len(new), message=msg))
        log_rows.append(dict(run_utc=run_utc, ticker=sym, level="error" if failed else "ok", new_rows=len(new),
                             message=f"stored {len(stored)} rows to {stored['date'].max().date() if len(stored) else '-'}; "
                                     f"appended {len(new)}"))

    # missing-day check: stock has no row on a date the Nifty traded (warning; Yahoo can lag)
    new_all = pd.concat([stored_all] + [x for x in appended if len(x)], ignore_index=True)
    nifty_days = set(new_all.loc[new_all["ticker"] == "^NSEI", "date"])
    recent = sorted(d for d in nifty_days if d > pd.Timestamp(now.date()) - pd.Timedelta(days=10))
    for sym in uni["ticker"]:
        have = set(new_all.loc[new_all["ticker"] == sym, "date"])
        miss = [d for d in recent if d not in have and sym not in failures]
        if miss:
            log_rows.append(dict(run_utc=run_utc, ticker=sym, level="warning", new_rows=0,
                                 message="no row on Nifty trading day(s): " + ", ".join(str(d.date()) for d in miss)))

    # staleness: fail if the Nifty stops updating or a stock falls more than MAX_LAG Nifty days behind
    last_by = new_all.groupby("ticker")["date"].max()
    nifty_cal = sorted(nifty_days)
    if "^NSEI" in last_by and np.busday_count(last_by["^NSEI"].date(), now.date()) > MAX_NIFTY_AGE_BDAYS:
        failures.append("^NSEI")
        log_rows.append(dict(run_utc=run_utc, ticker="^NSEI", level="error", new_rows=0,
                             message=f"Nifty data stale: last date {last_by['^NSEI'].date()}"))
    for sym in uni["ticker"]:
        if sym in last_by and "^NSEI" in last_by:
            lag = sum(1 for d in nifty_cal if last_by[sym] < d <= last_by["^NSEI"])
            if lag > MAX_LAG:
                failures.append(sym)
                log_rows.append(dict(run_utc=run_utc, ticker=sym, level="error", new_rows=0,
                                     message=f"stale: {lag} Nifty trading days behind (last {last_by[sym].date()})"))

    out = new_all.drop_duplicates(["date", "ticker"], keep="first").sort_values(["date", "ticker"])
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    tmp = PRICES + ".tmp"
    out[COLS].to_csv(tmp, index=False)
    os.replace(tmp, PRICES)  # atomic: an interrupted run never leaves a half-written file
    if quarantined:
        q = pd.concat(quarantined).assign(run_utc=run_utc)
        q["date"] = pd.to_datetime(q["date"]).dt.strftime("%Y-%m-%d")
        if os.path.exists(QUAR):  # keep one entry per (date, ticker): the first time it was quarantined
            q = pd.concat([pd.read_csv(QUAR), q]).drop_duplicates(["date", "ticker"], keep="first")
        q.to_csv(QUAR + ".tmp", index=False)
        os.replace(QUAR + ".tmp", QUAR)
    n_new = sum(len(x) for x in appended)
    print(f"{run_utc} UTC: appended {n_new} rows for {len(symbols)} symbols; "
          f"quarantined {sum(len(x) for x in quarantined)}; failures: {failures or 'none'}")

    if not a.skip_risk:
        px = pd.read_csv(PRICES, parse_dates=["date"], float_precision="round_trip")
        vix = px[px["ticker"] == "^INDIAVIX"].sort_values("date")
        rows = []
        for r in uni.itertuples(index=False):
            s = px[px["ticker"] == r.ticker].sort_values("date").set_index("date")["adj_close"]
            if len(s) < GARCH_WINDOW + 1:
                log_rows.append(dict(run_utc=run_utc, ticker=r.ticker, level="error", new_rows=0,
                                     message=f"only {len(s)} prices; need {GARCH_WINDOW + 1} for live risk"))
                failures.append(r.ticker)
                continue
            try:
                risk = garch_risk(s)
            except Exception as ex:
                failures.append(r.ticker)
                log_rows.append(dict(run_utc=run_utc, ticker=r.ticker, level="error", new_rows=0,
                                     message=f"GJR-GARCH fit failed: {ex}"))
                continue
            rows.append(dict(as_of=str(s.index[-1].date()), forecast_for="next trading day", ticker=r.ticker,
                             sector=r.sector, last_adj_close=float(s.iloc[-1]),
                             last_return=float(np.log(s.iloc[-1] / s.iloc[-2])), model="GJR-GARCH(1,1) Student-t",
                             window_days=GARCH_WINDOW, **risk,
                             india_vix=float(vix["adj_close"].iloc[-1]) if len(vix) else np.nan,
                             india_vix_date=str(vix["date"].iloc[-1].date()) if len(vix) else "",
                             generated_utc=run_utc))
        risk_path = os.path.join(OUT_LIVE, "latest_risk.csv")
        pd.DataFrame(rows).to_csv(risk_path + ".tmp", index=False)
        os.replace(risk_path + ".tmp", risk_path)
        print(f"latest_risk.csv: {len(rows)} stocks")

    pd.DataFrame(log_rows).to_csv(ULOG, mode="a", header=not os.path.exists(ULOG), index=False)
    if failures:
        print(f"FAILED validation or fetch: {sorted(set(failures))}")
        sys.exit(1)


if __name__ == "__main__":
    main()
