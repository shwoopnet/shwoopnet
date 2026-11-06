# OVN1 to OVN4 shared rules (overnight and weekend gap, Kalshi equity and index perps; written 2026-11-06, before any return, premium or outcome was computed)

Discovery only. No live code, no functions/, no index.html, no promote verb. Strategy Research V2 worker, mechanism: the overnight and weekend gap while the cash market is shut but the perp trades. Counterparty: perp traders pricing news with no cash-market price discovery; the cash open resolves the gap. Honest alternative: the perp is a fair forecast of the open, the gap is already in the price, and the 0.24% round-trip fee is the whole result.

## Data actually available (checked 2026-11-06, listings and schedule only, no return computed)
- `origin/perp-data`: 73 recorder samples, 2026-10-21T16:56Z to 2026-11-06T14:56Z, 3 to 7 a day at IRREGULAR times (not hourly), read per commit with `git show <c>:perps/<file>`. Each commit rewrites the day file, so rows are de-duplicated on (ts_utc, ticker).
- Single-stock perps (AAPL, NVDA, TSLA and 50 more): quoted bid and ask are 0 until 2026-11-05 13:39 ET (NVDA price column 0.0000, reference redenominated from about 21 to 4 on 2026-11-02); no usable stock quote exists before the held-out cut.
- `reference_price` in the recorder is the venue's own cash index: it is FROZEN at the last cash value while the cash market is shut (US500 13.3472 from Fri 16:40 ET to Mon 13:11 ET) and moves in cash hours. It is the cash reference used here.
- Yahoo chart (keyless) answered HTTP 429 from this machine on 2026-11-06 (two plain requests); not retried with changed headers. So an outside Yahoo cash reference is NOT available and every test below uses the recorder's own `reference_price`. A Yahoo version is NOT_RUNNABLE here.
- `perps30/` (the 30 second open and close recorder): absent from origin/main and from every perps branch on 2026-11-06 (only `src/scalper/recorder.py` on `claude/perps-fast-recorder`). Nothing read from it.
- Hourly candles (`GET /margin/markets/{t}/candlesticks?period_interval=60`) carry bid and ask close per hour: US500 from 2026-10-06, USTECH100 from 2026-10-14, but stock/ETF perps only from 2026-11-05. No reference in the candles. Used by OVN4 only.

## Universe (chosen on COST only)
Asset classes Equities and Indices (the cash market is shut overnight). Keep a perp if its median relative recorded spread (ask-bid)/mid over its dev-period rows with bid>0 and ask>0 is at most 5 bps. No return is used. In practice this leaves KXUS500PERP and KXUSTECH100PERP; stock perps have no dev quote and drop out (reported).

## Cut and halves
Frozen last third of recorded dates: UTC dates 2026-11-01 to 2026-11-06 (6 of 17). Cut = 2026-11-01T00:00:00Z. Rows, candles and events resolving at or after it are never read (candle fetch end_ts = cut; recorder rows filtered before any join). Dev = 2026-10-21 to 2026-10-31. Halves by event date (ET date of the cash open): D1 before 2026-10-27, D2 from 2026-10-27. Cluster for z = the ET date of the open (a weekend gap is one cluster).

## Costs
Round trip = taker at the recorded bid/ask on both legs (buy at ask, sell at bid) plus fee 0.12% of notional per side (0.24% round trip, from the repo's perps guide; NOT confirmed against Kalshi's fee page, so the x1.2 stress is 0.288%). Funding ignored (holds under 12 hours, deadband and cap noted; flagged as an omission).

## Count
Four tests, +2 each: N +8, running about 730,455 -> 730,463, deflated z bar about 5.27. Holdout is only read if a test has at least 60 dev events on at least 30 clusters and passes everything; none is expected to.
