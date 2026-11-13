# CANDLEGAP: what a missing one-minute candle means on CS2 match markets (History Miner, Nov 13, 2026, zero-try measurement, Head of R&D approved)

Written and committed BEFORE the candles are pulled. A measurement only: no rule, no bet, no result read, no price analysis, no try. [research]

**Question.** On Kalshi's sports and esports match markets, does a missing one-minute candle mean "the quote did not change in that minute" or "there was no quote"? REMATCH (2,276 "no candle" pairs), MAPBREAK (its state candle) and VOIDSNAP all lean on a guess.

**Data.** The 36 KXCS2GAME markets polled in `wheelbook/2026-11-12/2031/` on branch `wheelbook-2026w46` (book rows written when the top 5 changed, a poll row every read, fast polls about every 3 s). CS2 only: ESOCTIE and INPLAYJUMP hold out e-soccer, e-basketball and Liga Pro closes, and rule (h) forbids a candle pull over their held-out closes. No card holds out KXCS2GAME closes on Nov 12 to 13 (MAPBREAK is closed; VOIDSNAP's sample ends Oct 22 and its held-out set is before Sep 12).

**The pull.** Job `CANDLEGAP_CS2` (`kalshi-scalper/workers/kalshi_pull_jobs/CANDLEGAP_CS2.json`): ONE batched request, the 36 tickers, 1 minute candles from 2026-11-12T20:31:00Z to 2026-11-13T00:04:00Z (the recorded run, 213 minutes; 36 x 213 = 7,668 minute-tickers, under the 9,000 per request limit).

**Unit.** A market-minute: ticker x the UTC minute [m, m + 60), the candle being the one whose `end_period_ts` is m + 60. A minute counts only if it lies wholly inside the market's fast-poll window (from the later of S, the ticker's US Eastern start, and the market's first sighting, to the run's last poll) and after the market's first stored book row (before it the book state is unknown).

**Book state (the recorder's files only).** The book at a moment is the last stored row at or before it. "Book changed in the minute": a row for the ticker was written in [m, m + 60). "Two-sided": at the minute's end the stored book has a YES bid and a NO bid (YES ask = 1 minus the best NO bid) with bid below ask. "Empty or one-sided": otherwise.

**The five counts (a partition of the counted market-minutes):**
1. candle present, book changed;
2. candle present, book unchanged;
3. candle missing, book unchanged, a two-sided quote standing;
4. candle missing, book unchanged, empty or one-sided;
5. candle missing although the book changed.

**Match.** When a candle is present and carries a bid and ask close, does each equal the recorder's last book of that minute (YES bid, and 1 minus the best NO bid) within 1c? Counted for bid, ask, and both.

**Splits, fixed now.** Every count is given (a) for minutes before the market's own close and (b) after it. The close is the `close_time` of the market in the recorder's own settled or closed list reads (a time, not a result; a market with no such row is "still open at run end" and all its minutes are (a)). The (a) counts carry the headline sentence. A secondary column uses "top of book changed" (best YES bid or best NO bid moved) instead of "any of the top 5 changed".

**Caveats stated before data.** The recorder's poll log does not name the tickers each read asked, so "the ticker was polled every cycle" is inferred from its tier (the recorder fault reported Nov 13); book rows are written only on change, so an unchanged minute is inferred from no row. Many of these markets settled before the run began and were still polled (the same fault): split (b) holds them.

**Frozen script.** `candlegap.py` (sha256 in `FREEZE.sha256`), committed before the job is dispatched. Usage: `python3 -I candlegap.py <wheelbook run folder> <CANDLEGAP_CS2 pull folder>`.
