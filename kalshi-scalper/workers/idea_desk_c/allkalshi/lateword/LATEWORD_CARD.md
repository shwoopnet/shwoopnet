# LATEWORD: late-listed Trump mention words (Idea Desk C, Nov 16, 2026; a quick first read under the owner's order of Nov 15; written before any price for this card is pulled)

**What is new.** The signal is a listing fact: Kalshi lists most of an event's words at once, and adds some words hours later. A word added late was added for a reason, usually a topic in the news. Its own listing time is the signal, a field no card has used. It is not a price move, not a band, not a word's base rate (MENT1, MENTPERSIST1), not Trump's post counts (TRUMPTOPIC1) and not calibration by lead (CAL1, FLB1).
- **Nearest relatives:** NEWLIST1 and NEWLIST1B, which looked at newly listed markets, are the closest. They pooled new listings across series and asked about price behaviour after listing. LATEWORD conditions on a word being added late WITHIN an already-listed event and buys at a fixed time before the speech.
- **Hypothesis, stated before any price:** a late-added word reflects a live topic, so the speaker is more likely to say it than its price implies. Buy YES.
- **Not a ban shape.** The band 0.30 to 0.70 keeps out the cheap side and the favourite. It is held to settlement, so it is not a short round trip and not market making.

**The rule (constants in `lateword_lib.py`).**
- **Universe:** KXTRUMPMENTION and KXTRUMPMENTIONB, from the landed MENTDRIFT_LISTS_A run (2026-11-15T1458Z_43727241819, complete, not truncated).
  - Development: each market's OWN occurrence_datetime is 2026-04-17 to before 2026-08-06. A missing occurrence is dropped.
  - "Event does not qualify" is dropped.
- **First listing F:** the earliest open_time of the event's words.
- **Late word:** opened at least 6 h after F.
- **Decision D:** the word's own open_time + 30 min. The word must not have closed by D, which is a fact known at D.
- **Why not the speech time (the Head's caution, Nov 16).** occurrence_datetime is NOT a schedule known before the event.
  - In the development list it differs between the markets of one event in 61 of 96 events.
  - The last close is within about 15 minutes of the first occurrence in most events.
  - So it is set or revised near the end. It is used only to choose the development sample, never for timing.
  - (Measured from time fields only.)
- **Trade:** buy YES at D when the YES ask is 0.30 to 0.70.
  - Quote: the candle ending at D, else the latest ending in [D - 180 s, D].
  - It must be two-sided under rule 18.
- **Size and exit:** 1 contract, held to settlement.
- **Tries:** **1**, added to the deflation ledger.

**Costs and the bar.**
- **Haircuts:** h = 0, 1c and 2c, all printed. The primary is 1c, but 2c when the word closes within 120 s after D (C8).
- **Fee:** ceil(7% x p x (1-p) x 100) / 100.
- **Void:** a void refunds the price and keeps the fee.
- **Label:** "upper bound, not fill-checked".
- **Printed:** halves at floor(n/2) in entry order; z clustered by event.
- **Floor:** under 100 trades the bar line reads "no evidence at n = x" and never PASS (Auditor B, Nov 16). The result line says development only, no held-out read, and that the event is the unit.
- **Bar (paper):** PF 1.3+ at the primary line with both halves 1.0+, and PF 1.0+ at 2c, unrounded with no tolerance.
- **On a fail:** dropped with no write-up.
- **On a pass:** it goes to the full checks, then the held-out.
- **Sample size:** 272 late words in 33 events, before the band and the quote check. The read is thin, and the z by event says so.

**Reading order.**
1. The market's own occurrence, then open and close times, then the word title.
2. The candles at D.
3. The result, read last and only for traded words.
- If a list page still has a cursor, the scorer stops.

**Windows.**
- Development: occurrence Apr 17 to before Aug 6, which is TRUMPTOPIC1's fit third.
- **Never pulled:** occurrence Aug 6 to before Oct 3 (TRUMPTOPIC1's spent held-out). The landed list holds its Aug 6 to Sep 12 part with results, LOADED, NOT LOOKED AT, dropped by occurrence first.
- **Held-out:** occurrence 2026-10-03T00:00Z to before 2026-11-05T00:00Z. Read once, on the Head's go, as its own list and candle job. This block was MENTDRIFT's held-out; MENTDRIFT was dropped unread on Nov 15, so it is unread.
- **Never pulled:** from 2026-11-05 on, TRUMPTOPIC1's forward window.

**Stage B:** `LATEWORD_CANDLES.json`, built by `build_lateword_candles.py` from the list's time fields and word titles.
- One historical single-market read per late word (count in the job's notes).
- Window [D - 180 s, D], so no candle after the decision is fetched.
- Pacing 5 s, under 470 requests, one file.

**Disclosure:** to size this and to check the clock, I read the landed list's time fields (ticker, event_ticker, open_time, occurrence_datetime, close_time) and the word title, for development events only. No price, volume or result was read.

**Files:** `lateword_lib.py`, `build_lateword_candles.py`, `lateword_score.py`, `test_lateword.py` (2 tests: the hand case and the truncation stop).

**Joint held-out (the Head of R&D, Nov 16, 15:46Z).** The window of own occurrence 2026-10-03 to before 2026-11-05 is read ONCE for every Trump-word family that passes development (LATEWORD, MENTTWIN, MENTBREADTH and any later one), in one print, with m counting every family. No family reads it alone.
