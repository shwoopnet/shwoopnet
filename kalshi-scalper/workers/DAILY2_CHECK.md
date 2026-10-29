# DAILY2 check: Kalshi daily and weekly markets on the 10 year yield, WTI, EUR/USD, USD/JPY and gold

Worker DAILY2, Strategy Research V2, 2026-10-29. Research only. Series list read from Kalshi's public `/series` (15,475 series), filtered on Treasury, yield, 10Y, oil, WTI, crude, EUR, yen, JPY; settled markets counted with `api.settled_markets` for closes from 2026-08-01 to 2026-10-30 (Kalshi's public reach for these series starts about 2026-08-21). One settled market per series was read for its rules text. Counts, close times, strike types, volumes and rules only; no model value was compared with any quote.

## Daily series with settled markets (testable)

| Series | What it settles on (rules text) | Close (UTC, daylight time) | Settled events | Markets | Strike types | Median contracts per event |
|---|---|---|---|---|---|---|
| `KXWTI` "WTI oil on day" | ICE/NYMEX **daily settlement price** of the named WTI futures month (rolls to the next month 2 business days before the current month's last trading day), "above K", 2 decimals | 18:30 (2:30 PM ET, the NYMEX settlement) | 47 (Aug 21 to Oct 28) | 1,480 | greater only (about 31 per day) | about 373,000 |
| `KXEURUSD` "EUR/USD daily range" | ICE (TradingView FX_IDC) **open price of EUR/USD at 10 AM EDT** | 14:00 | 47 (Aug 24 to Oct 29) | 705 | 611 between (range buckets), 47 greater, 47 less (tails) | about 8,000 |
| `KXUSDJPY` "USD/JPY daily range" | ICE (TradingView FX_IDC) **open price of USD/JPY at 10 AM EDT** | 14:00 | 47 (Aug 24 to Oct 29) | 705 | 611 between, 47 greater, 47 less | about 6,500 |

Listed with settlements but dead or out of scope: `KXUSDJPYAD` (Pyth, 21:00, 35 events, median **0** contracts per event); `KXBRENTD` (Pyth Brent, 37 events; not a candidate here, and CMD1 found Yahoo's `BZ=F` is not its settlement contract).

## The 10 year Treasury yield: no testable daily series

- `KXTNOTED`, `TNOTED` (Treasury 10Y daily yield): **no settled market** in the reach.
- `KXUST10A` ("UST 10 Year Weekly", par yield from Treasury, 19:30 UTC): 8 events. `KX10YRDIRHW` / `KX10YRDIRLW`: 3 events each. `TNOTEW`, `KXTNOTEW`, `KXNOTE10W`, `TNOTE`: none settled.
- `KX10YRRATEH` (Pyth 10Y UST yield, hourly, close of the 1 minute candle before the hour): 178 events since **2026-10-09** only (about 15 trading days), median 364 contracts per event, and its source is Pyth, not `^TNX`.
- **Not run, not counted:** no daily Treasury series reaches 30 closes in total, let alone per window. `NOT_ENOUGH_DATA` without spending a try.

## Weekly series: too few closes

`KXWTIW` 10 events, `KXEURUSDAW` 9, `KXUSDJPYAW` 9, `KXBRENTW` 9, `KXUST10A` 8. Under 30 in total; **not run, not counted**.

## Gold (KXGOLDD, KXGOLDW): skipped as covered

- **GOLD2 strategy card** (README, about line 7121): KXGOLDD against a GVZ-implied Normal probability from GC=F, 6c edge, 14:00 ET look. Registered; it is the gold daily ladder fair value.
- **CMD1** (README, 2026-10-21) already RAN the same mechanism on KXGOLDD (distance to spot scaled by realised volatility and time left, Yahoo `GC=F`, 3 hours out): gold **-7.1c** a contract with the volatility rule calibrated (standardised error 1.02), so the market was simply sharper.
- **LADL1** covers L1's rule on KXGOLDD and KXGOLDW; **GOLDFV1** found Kalshi gold's 15 minute market tracks COMEX within a minute.
- So gold is skipped, per the brief.

## WTI overlaps CMD1 (disclosed)

CMD1 ran `KXWTI` on the same mechanism with a decision 3 hours and an entry 2 hours before the close (pooled FALSIFIED, -7.28c; WTI's standardised error 1.43, i.e. its volatility was understated, partly because Yahoo `CL=F` is not always the contract Kalshi settles on). DAILY2's WTI variants differ only in the look (60, 30 and 10 minutes before the 2:30 PM ET settlement) and in using the **named contract** as the reference (see the registration). That is close to a reword of CMD1; it is run because the brief names WTI and the near-the-close looks were never tried, and it is counted as 3 new tries. EUR/USD and USD/JPY daily ranges appear nowhere in the ledger (the FX entries in README are the 15 minute up/down series and L1's rule).

## Outside reference data (Yahoo, keyless; bar counts and date ranges only were read)

- 1 minute bars: only the last 30 days (Yahoo refuses older chunks), about 21 trading days.
- **2 minute bars: the last 60 days** in chunks (`period1`/`period2`), from about 2026-08-31.
- 5 minute bars: from 2026-08-20 (CL=F) and 2026-08-06 (EURUSD=X).
- `CL=F` (front month), `CLZ26.NYM` (December 2026, the contract Kalshi names from mid October) available; `CLV26.NYM`, `CLX26.NYM` are delisted on Yahoo. `EURUSD=X`, `JPY=X` available.
- Choice (in the registration): 2 minute bars, so the reference is at most about 1 minute older than the rule's 60 second lag, at the cost of the Kalshi days before 2026-08-31.
