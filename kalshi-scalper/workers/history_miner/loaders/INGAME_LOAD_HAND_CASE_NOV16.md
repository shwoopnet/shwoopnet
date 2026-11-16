# ingame_load.py: hand case and wall (History Miner, Nov 16, 2026, written before the code; Desk A's LOADER CONTRACT of Nov 16 15:33Z)

Purpose: the engine loader for the sports-data ingame recorder (record_ingame.py), first in Desk A's order. Engine schema out.

Window and walls (constants; Auditor B's lines of Nov 15 21:23Z, 21:26Z and Nov 16 15:19Z; the Head's SPORTS-PRE ruling of Nov 15 21:27Z):
1. Directory wall: only ingame/<date>/ for dates 2026-11-08 to 2026-11-12 are listed; a later directory is never opened.
2. Time first: in every obs row the t_recv_ms column is read FIRST; a row at or after 2026-11-13T00:00:00Z (1794528000 s), or before 2026-11-08T00:00:00Z (1794096000 s), or unparseable (a repeated header) is dropped and counted before any other column.
3. Ticker wall: KXNBATOTAL, KXNFLTOTAL, KXNHLGAME, KXNHLTOTAL only (spread kinds and the NBA and NFL moneylines are dropped and counted: SPORTS-PRE holds KXNBAGAME and KXNFLGAME outcomes to 2027-01-01).
4. Results: from the listing pages of IG_RESULTS (run 2026-11-16T1306Z_43872534396) and IG_RESULTS_NHL (run 2026-11-16T1339Z_43875945403) only, each gz file refused unless its sha256 is one of the five named; in each market close_time is read FIRST and a close outside [1794096000, 1794528000) is dropped and counted; then the ticker wall; then result for kept markets only.
5. Allow line: refuses unless HELDOUT_PULL_RUNS.md has a line with the mark "readable ONLY by the History Miner's ingame loader", "ingame_load.py", this file's own sha256 and the five listing sha256s. No flag, no env var.
Output: market(ticker, series, close_ts, result) for kept markets; candle(ticker, end_ts, yes_bid, yes_ask, last, volume, oi) with end_ts = the poll's second, oi = None, plus extra columns bid_size, ask_size, kind, event; a candle whose end_ts is after its market's close is dropped and counted; a candle of a ticker without a kept market is dropped and counted.

Hand case (invented):
- A row with t_recv 1794528000000 is dropped by the time wall; touching any other column of it raises (guard).
- A row with t_recv 1794200000000, ticker KXNBAGAME-X-A: dropped by the ticker wall (counted "ticker outside the wall").
- A row KXNHLTOTAL-26NOV10AB-5 at 1794300000000, market closing 1794304000 (2026-11-10T09:46:40Z) with result "no": kept as candle end_ts 1794300000, the market row (KXNHLTOTAL-26NOV10AB-5, KXNHLTOTAL, 1794304000, "no").
- The same ticker at 1794320000000 (after its close): dropped, "candle after close".
- A listing market closing 1794528000 (Nov 13): dropped, its result never touched (guard).
- A listing file whose sha256 is not one of the five: refused. No allow line: refused.

Correction before the freeze (disclosed): the close in the third case was first written as 1794310000; the test and this file use 1794304000 (09:46:40Z), so the later row (1794320000000) is still after the close.
