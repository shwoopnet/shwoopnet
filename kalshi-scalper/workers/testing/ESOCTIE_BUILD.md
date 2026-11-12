# ESOCTIE build note (Testing Desk, Nov 12, 2026)

Authority: `kalshi-scalper/workers/history_miner/esoctie/ESOCTIE_REGISTRATION.md` with NOTES 1 to 4 at 4678cec0 on `claude/history-miner`; constants in `esoctie_series_frozen.json` (byte copy of ESOCTIE_SERIES.json, sha256 c80cd418... checked in code). **Built and tested on synthetic data only: no request, no data opened, no candle sent, no bet booked.**

- `esoctie.py`: reader, walk-forward base rate, kill lines, rule scorer, candle-job builder. An independent build on scorekit and tie3's job format.
- `test_esoctie.py`: ticker clock S as US Eastern, fee rounding, held-out refused, open-time guard (close never decides), walk-forward base rate with the 300 s settle gap (a result inside the gap cannot move a decision, one outside can), cheap-tail and one-way-cost kill lines, void fired bet booked as a fee loss, candle job passes the runner's check, verdict wording.
- **Agreement with the History Miner's reference** (`ESOCTIE_REF=<its folder> python3 test_esoctie.py`): on the same 1,400-event fixture the two agree on filled events, eligible events, EVERY base rate, the 10c share, the one-way cost, the number of bets, net and profit factor; and the candle job is identical (108 requests, same 4,200 tickers, same windows).
- Everything printed carries "selected on development" (NOTE 4): it can falsify, it cannot support. One try. The held-out (closes from 2026-10-23T00:00Z) is refused in code.
- Candle window: S minus 11 minutes to S, packed by S, at most 100 tickers and 9,000 minute-tickers a request.
- Not read: the Tie's price anywhere, until the candles land.
