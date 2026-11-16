# SIBHIT: game pace from sibling rung hits, NBA player points (Idea Desk C, Nov 15, 2026; a quick first read under the owner's order of Nov 15; written before any price for this card is pulled)

**What is new.** The signal is a field no card has used: how many of a game's KXNBAPTS rungs have already closed. A rung closes the moment its player reaches the number, so this count is a live, public pace reading of the whole game. It is not a price move, not a price band, not a calibration table and not a single market's own path.
- Nearest relatives, for the Verification Analyst if it passes: INGAMELAG1 (lag between related markets in-game, closed) and the momentum-follow family. SIBHIT does not use any market's price change.
- **Why it is not lead-lag between related markets.** Lead-lag trades one market's PRICE move ahead of another's. SIBHIT trades no price move at all: its input is a settled fact, how many rungs of the game have been REACHED. That is outcome information arriving as settlements, not a price that may later be followed.
- **Is it the stale-quote idea in another shape?** Partly, and that is the honest risk. If it works, it is because a rung's quote does not fully price the game's pace that the sibling settlements reveal, which is a slow update. But stale-quote tests (STALE1 and the like) asked whether a quote that has not moved will move. SIBHIT asks whether the game-wide pace, a quantity no single quote carries, is under-priced in every open rung at once. It is not conditioned on any quote's age or staleness.
- **Not a ban shape.** The side is picked by the pace count, never by price. The band 0.30 to 0.70 keeps out the cheap side and the favourite. It is held to settlement: not a short round trip and not market making.

**The rule (constants in `sibhit_lib.py`).**
- **Universe:** KXNBAPTS markets only, development closes from 2026-10-21 to before 2026-11-06 (from the landed KXNBAPTS_LISTS_A).
- **Game:** an event_ticker. O is its earliest occurrence_datetime.
  - A = O - 180 min.
  - T = O - 60 min. From close times alone, the rungs of a game close from about O - 150 to about O + 15, the final whistle sitting near O - 30 to O. So T is late in the game.
- **Base:** the rungs still open at A. A game needs at least 10.
- **Share:** s = the base rungs whose close time is strictly before T - 240 s, divided by the base. The cutoff is the start of the earliest candle the entry may use, so no hit after the quote can enter the count (the Head's caution, Nov 15).
- **Threshold:** S_MED = 0.07362240289069558, the median of s over the 120 development games, computed from close times only before any price was pulled. The design script and its output are in this folder.
- **HIGH (s >= S_MED):** buy YES on every base rung still open after T whose YES ask is 0.30 to 0.70.
- **LOW (s < S_MED):** buy NO on every such rung whose NO ask (1 - YES bid) is 0.30 to 0.70.
- **Quote:** the 1 minute candle ending at T, else the latest candle ending in [T - 180 s, T]. It must be two-sided under rule 18 (0 < bid < ask < 1, 1e-9).
- **Size and exit:** 1 contract a rung, held to settlement.
- **Tries:** 2 (HIGH-YES, LOW-NO), both added to the deflation ledger.

**Costs and the bar.**
- **Entry:** raw ask + h, with h = 0, 1c and 2c all printed. The primary is 1c, but 2c when the rung closes within 120 s after T (C8).
- **Fee:** ceil(7% x p x (1-p) x 100) / 100.
- **Void:** a void refunds the price and keeps the fee.
- **Label:** "upper bound, not fill-checked".
- **Printed:** halves at floor(n/2) in entry order; z clustered by game; drop counts.
- **Bar (paper):** PF 1.3+ at the primary line with both halves 1.0+, and PF 1.0+ at 2c, unrounded with no tolerance.
- **On a fail:** the try is dropped with no write-up (the owner's order).
- **On a pass:** it goes to the full checks: Verification Analyst, fill check, then the held-out.

**Printed for information (Auditor B, Nov 15), not tries.**
- S_MED is the median over all 120 development games, so the arm split is in-sample: it is built from close times only, with no price or result. The scorer also prints both arms with the split set at the median of the FIRST half of games in time order.
- The per-game share is printed as its spread (min, quartiles, max). A rung that closes early for a reason other than a hit (a player ruled out) counts in s.

**Clock check (the Head's choice B, Nov 16), before scoring.** The list carries no tip time, so the check tests the shape of a schedule. A game is dropped and counted (printed as `clock_check`) unless its occurrence_datetime is ONE value across all its rungs, exactly on :00 or :30 to the second. A recorded end would be irregular. On the landed list all 120 games pass (80 on :00, 40 on :30; measured from time fields only, Nov 16). Residual risk, stated for the held-out check: Kalshi rescheduling a game and rewriting the value to another round time.

**Reading order.**
1. Time fields from the list (ticker, event, close, occurrence) fix the games, the arm and the open rungs.
2. The candles at T for those rungs.
3. The `result` field, read last and only for the rungs traded.

**Windows.**
- Development: closes 2026-10-21 to before 2026-11-06.
- PROPUNDER's reserve: closes 2026-11-06 to before 2026-11-13, never pulled.
- **Held-out:** closes 2026-11-13T00:00Z to before 2026-12-04T00:00Z. Read once, on the Head's go, as its own lists and candle job after Dec 4. The earlier KXNBAPTS (O) and (L) cards held this block. They were dropped unread as versions on Nov 15, so it is unread.

**Stage B:** `SIBHIT_CANDLES.json`, built by `build_sibhit_candles.py` from the list's time fields.
- 120 games, 120 requests, 5,339 tickers.
- A 3 minute window per game, at most 60 tickers a request.

**Files:** `sibhit_lib.py`, `build_sibhit_candles.py`, `sibhit_score.py`, `test_sibhit.py` (hand case: 1 game, 3 trades, every drop reason).
