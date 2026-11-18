# Frozen snapshot validation report

Snapshot: 2026-11-18 10:07 UTC | symbols: 44 | dates 2015-01-01 to 2026-11-17

## Blocking checks

- Manifest SHA-256 matches: 44/44
- Symbols with nulls: 0
- Symbols with non-positive prices: 0
- Symbols with duplicate dates: 0
- Result: PASS

## Zero-volume placeholder rows (dropped and logged by the pipeline loader)

41 stocks have such rows. Dates and number of stocks affected:

- 2015-08-12: 4 stocks (^NSEI traded)
- 2015-09-15: 1 stocks (^NSEI traded)
- 2015-10-16: 1 stocks (^NSEI traded)
- 2015-11-30: 1 stocks (^NSEI traded)
- 2018-11-07: 1 stocks (^NSEI traded)
- 2021-11-04: 1 stocks (^NSEI traded)
- 2022-09-12: 1 stocks (^NSEI traded)
- 2022-10-24: 1 stocks (^NSEI traded)
- 2024-01-15: 2 stocks (^NSEI traded)
- 2025-03-18: 40 stocks (^NSEI traded)
- 2025-09-08: 1 stocks (^NSEI traded)
- 2026-01-15: 41 stocks (not a ^NSEI trading day)

## Stock dates absent from the ^NSEI calendar

- 2015-01-01: 41 stocks
- 2015-04-15: 41 stocks
- 2016-01-01: 41 stocks
- 2016-08-12: 41 stocks
- 2018-01-01: 41 stocks
- 2019-01-01: 41 stocks
- 2019-10-27: 41 stocks
- 2020-11-14: 41 stocks
- 2026-01-15: 41 stocks

## One-day log moves above 20% (flag only; kept as genuine unless excluded in config/universe_excluded.csv)

- ADANIPORTS.NS: 2020-03-23 -21.0%; 2023-02-01 -21.3%; 2024-06-04 -23.8%
- AXISBANK.NS: 2020-03-23 -32.7%
- BAJFINANCE.NS: 2020-03-23 -26.4%
- BAJAJFINSV.NS: 2020-03-23 -29.9%
- BEL.NS: 2024-06-04 -22.1%
- GRASIM.NS: 2020-03-23 -20.0%
- SBIN.NS: 2017-10-25 +24.4%
- SHRIRAMFIN.NS: 2020-03-23 -25.1%
- ^INDIAVIX: 2015-01-06 +20.8%; 2015-03-02 -21.1%; 2015-08-24 +49.7%; 2016-09-29 +28.7%; 2018-02-06 +22.1%; 2019-05-23 -35.3%; 2020-02-24 +21.6%; 2020-02-28 +26.8%; 2020-03-12 +26.6%; 2020-03-13 +22.4%; 2020-05-04 +25.1%; 2020-08-31 +21.9%; 2020-12-21 +21.9%; 2021-02-26 +20.6%; 2021-11-26 +22.2%; 2022-02-14 +20.7%; 2022-02-24 +26.5%; 2024-04-23 -21.9%; 2024-06-04 +24.5%; 2024-06-05 -34.8%; 2024-08-05 +35.2%; 2025-04-07 +50.5%; 2025-04-15 -22.1%; 2026-03-02 +22.3%; 2026-03-04 +21.0%; 2026-03-10 -21.1%; 2026-04-08 -22.6%; 2026-07-08 +23.1%; 2026-09-24 +20.4%

## Adjusted close vs an independent second download (5 sample tickers)

- RELIANCE.NS: 2932 common dates, max relative difference 3.47e-07, dates differing by more than 0.1%: 0
- HDFCBANK.NS: 2932 common dates, max relative difference 3.82e-07, dates differing by more than 0.1%: 0
- INFY.NS: 2932 common dates, max relative difference 5.27e-07, dates differing by more than 0.1%: 0
- TCS.NS: 2932 common dates, max relative difference 8.28e-07, dates differing by more than 0.1%: 0
- SBIN.NS: 2932 common dates, max relative difference 3.11e-07, dates differing by more than 0.1%: 0

Yahoo's adjusted closes differ by tiny floating-point amounts between downloads; this is why every report number is computed from this frozen copy only.
