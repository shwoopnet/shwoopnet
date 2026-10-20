# Research data archive (2026-10-20)

Public Kalshi market data (settled markets with 1 minute candles) and a few public price files, copied from the research container so they survive it. **No keys, balances or account data are in here.** Kalshi's history only goes back about 69 days, so the early August days in these files cannot be downloaded again after mid-September.

Each file is a consistent copy of a SQLite database (made with SQLite's backup, integrity-checked after decompression for `l1b`, `book` and `e3b`), compressed with `xz -9`. Restore with `bash restore.sh` from this branch's folder; it writes the databases into `kalshi-scalper/data/` of a checkout of `claude/epic-ptolemy-0amjd9`.

| File | Size | What it is | Coverage | sha256 |
|---|---|---|---|---|
| `alts2.sqlite.xz` | 7.6 MB | other coins and series, September to October (E3 search) | market: 19139 rows, close 2026-09-03 to 2026-10-13 | `3d174c8f0cd68ade...` |
| `alts3.sqlite.xz` | 12.7 MB | commodities, Zcash, NEAR, XRP and Dogecoin history (E5) | market: 32314 rows, close 2026-08-06 to 2026-10-13 | `a4dba51898c081bd...` |
| `alts4.sqlite.xz` | 2.3 MB | older-days copies of the E3 series | market: 5442 rows, close 2026-08-06 to 2026-09-03 | `bd3ae3a6834c368b...` |
| `arb1.sqlite.xz` | 1.0 MB | locked-arithmetic scans (ARB1) | (see the README section for this test) | `2fe1799a9618646d...` |
| `book.sqlite.xz` | 4.3 MB | the 40 days L1 was found on (Bitcoin, Ethereum, gold), 1 minute candles | market: 10293 rows, close 2026-09-02 to 2026-10-12 | `772cebab5adc2ab9...` |
| `e3b.sqlite.xz` | 5.4 MB | XRP and Dogecoin, 69 days (E3 and its holdout E3B) | market: 13062 rows, close 2026-08-06 to 2026-10-13 | `92956eeb5f37a706...` |
| `flb1.sqlite.xz` | 1.6 MB | long-dated favourites (FLB1) | market: 28005 rows, close 2026-08-14 to 2026-10-13 | `4ecae01331d90fe7...` |
| `l1b.sqlite.xz` | 3.0 MB | the 28 older days L1 was never tuned on (Bitcoin, Ethereum, gold): the L1 holdout | market: 7213 rows, close 2026-08-06 to 2026-09-02 | `e932f5e7ebbdb635...` |
| `ladders.sqlite.xz` | 2.1 MB | hourly Bitcoin, Ethereum and S&P ladders (E4) | market: 166479 rows, close 2026-09-04 to 2026-10-13 | `41cd76a59e3f538b...` |
| `pm1.sqlite.xz` | 1.1 MB | Polymarket second price (PM1) | (see the README section for this test) | `6098cb3d0acdb92a...` |
| `pm2.sqlite.xz` | 0.8 MB | Polymarket filter (PM2) | (see the README section for this test) | `0ea9781b9b5ae343...` |
| `sports.sqlite.xz` | 0.7 MB | sports favourites | market: 9118 rows, close 2026-09-03 to 2026-10-13 | `cc1fbbe84484c0e1...` |
| `weather.sqlite.xz` | 1.6 MB | weather markets (WX1) | market: 2898 rows, close 2026-08-06 to 2026-10-13 | `57f9cc8a728ef8d6...` |
| `xm1.sqlite.xz` | 0.2 MB | hourly ladder as a second price (XM1) | window: 1896 rows, close 2026-09-02 to 2026-10-12 | `8e4ac2253f90247c...` |
| `json_prices_ohlc.tar.xz` | 0.3 MB | daily and intraday price files | daily and intraday price files for SPY, QQQ, VIX, SCHD, JEPQ | `2571a661f8b26092...` |

The registrations and results that use each file are in `kalshi-scalper/README.md` on branch `claude/epic-ptolemy-0amjd9`.
