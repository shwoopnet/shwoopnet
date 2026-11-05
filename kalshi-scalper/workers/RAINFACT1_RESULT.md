# RAINFACT1 result (run 2026-11-05, development only; frozen third never listed): FALSIFIED (quotes follow the fact)

Registered first: `workers/RAINFACT1_REGISTRATION.md` (commits a622496 and 2a5eae7, before any candle or observation), code `src/scalper/rainfact1.py`, tests `tests/test_rainfact1.py`, Amendment 1 `workers/RAINFACT1_AMENDMENT1.md` (a market-day window defect, disclosed there). Raw outputs in git-ignored `data/rainfact1/` (`score_run1.json`, `score.json`, `info.txt`).

## Numbers first
- Universe: 839 settled `KXRAIN` markets closing before 2026-10-03T16:00Z (2026-08-29 to 2026-10-02, 35 dates), 34 mapped cities (WPB dropped: no `p01i` rows for PBI at IEM, decided before any outcome). **221 market-days triggered** (airport hourly precipitation summed to at least 0.01 inch in the market day). Candles fetched for all 221, none failed.
- **All 221 triggered days resolved YES** (221 of 221, after Amendment 1; the first run showed 220 of 221 because of one window defect). So the premise holds: an airport gauge reading of 0.01 inch does decide the market. It is "riskless by fact" in this sample.
- **But the quote was already there.** At the registered entry (first candle ending after t_fact + 11 minutes), 214 of 221 books read **bid 0.99 / ask 1.00**: no offer under $1. 7 had a valid quote: 5 at ask above 0.95 (group C), **2 trades (group B, ask 0.93 and 0.94, one day, both won, +6.0c a contract after the fee, +5.0c with fees x1.2 and 1c slippage)**, group A (ask at most 0.30): **0 trades**. D1 2 trades, D2 0. First-run counts were the same apart from the DTW day (222 triggers, 212 no quote, 8 group C, same 2 trades).
- Median entry-candle ask over the 10 quotes seen: 0.99 (5th percentile 0.92). Last candle before the fact was already at ask 1.00 for more than half of the days (25th percentile 0.96).
- Information only (quote as of the last candle ending by t_fact + N minutes, no delay assumption): at t_fact itself 35 days had any offer under $1 and 14 of them were at ask 0.95 or lower (14 of 14 won); at +5 minutes 12 and 3; at +10 minutes 6 and 3; at +30 and +60 minutes 4 and 2 or 1. In plain words: the market knew about the rain before the METAR timestamp (rain at the station precedes the :51 report; radar and the earlier reports are public), and after the fact there is almost never an offer below $1 to lift.
- Exact tail probability for the 2 trades (null: price is fair): 0.87. No LEAD possible.

## Verdict against the registered kill lines
Triggered days 221 (at least 100) and trades 2 (fewer than 30): **FALSIFIED (quotes follow the fact)**, the first of the two registered kill lines. The prediction was 8 to 40 trades and about 85% of entries at ask 0.97 or above or no quote; actual was 98% (219 of 221 with no trade-able offer). The prediction on win rate and on trigger days (200 to 340) held. No audit trigger fired (the mean net of the 2 trades is +6c, under the +10c audit line; group A has no trades).

## What this does and does not say
- It says a thin-looking, 35-city daily rain market is NOT stale after a public airport reading: the YES side is bid 0.99 and offered at $1 (nobody sells). The loser in this idea (a resting stale offer) is not there.
- It does NOT say anything about selling YES or about buying NO of a decided market: a decided NO needs the day to end (the reading can only prove YES). It does not say the airport and the settlement source never disagree: 221 of 221 triggers won, so the sample has no disagreement; the lower bound of a one-sided 95% interval on the agreement rate is about 98.7%.
- Fills are not modelled: candles carry no depth, and the 2 trades are minute-closing quotes, not fills.
- N +2 as registered (running count about 730,442). Not tuned; the frozen third (close_time at or after 2026-10-03T16:00Z) was never listed or read. The listing returned results with each market, so results were in memory at listing time; the code kept them in a separate field that only `score` reads (the trigger stage never touches them; a test would catch the reverse, none was needed).

## Where an edge would have to be
Not here. A decided-by-fact rain contract is priced to $1 before the public station timestamp. The next place a published fact could lead a quote is one where the fact is NOT visible to a market maker's own sensors, i.e. a fact that exists only in a document published on a schedule (a government release, a settlement file), which the ledger already assigns to EVENT830, NOWCAST1 and the weekly statistic markets.
