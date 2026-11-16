# SIBHIT-R: fast NBA games, sell the overs (Idea Desk C, Nov 16, 2026, ~15:25Z; registered on the Head of R&D's GO of 15:19Z, BEFORE any further read)

**Why this exists, said plainly.** SIBHIT (registered Nov 15, run once Nov 16, print 3745490b) failed on development, but in the reverse direction from the one registered. In games with a high share of rungs already hit, buying YES lost heavily; in low-share games, buying NO lost. SIBHIT-R is the reverse rule. It was chosen AFTER seeing the development result, so the development data is spent for it and proves nothing. It is scored ONCE on a window SIBHIT never read (but see Amendment 3: the window's results were read by PROPS1, for a different purpose).

**Mechanism (stated before the new read).**
- **Fast games:** a fast-scoring game late in the fourth quarter is more often a blowout. Starters are rested, so open player-points rungs ("X or more") are reached less often than their prices imply.
- **Slow games:** close, low-scoring games keep starters on the floor to the end, so their open rungs are reached more often than priced.
- **Who loses:** buyers who extrapolate the game's pace into each player's line.
- **What this is not:** not a price move, band or calibration table; the input is the count of sibling rungs already settled (SIBHIT's field).

**The rule: SIBHIT's clock, base, pace share, threshold and band, with no retuning. Only the side is reversed.**
- **Universe and windows:**
  - Universe: KXNBAPTS.
  - O is a game's occurrence_datetime. It must pass the clock check: one value per game, exactly on :00 or :30. Otherwise the game is dropped and counted.
  - A = O - 180 min. T = O - 60 min.
  - Base: the rungs still open at A, at least 10.
- **Share:** s = the base rungs whose close time is strictly before T - 240 s, divided by the base.
- **Threshold:** S_MED = 0.07362240289069558, SIBHIT's development median, fixed. It is NOT recomputed on the new window.
- **Fast (s >= S_MED):** buy NO on every base rung still open after T whose NO ask (1 - YES bid) is 0.30 to 0.70.
- **Slow (s < S_MED):** buy YES on every such rung whose YES ask is 0.30 to 0.70.
- **Quote:** the candle ending at T, else the latest ending in [T - 180 s, T], two-sided under rule 18.
- **Size and exit:** 1 contract, held to settlement.
- **Tries: 2** (R-FAST-NO, R-SLOW-YES), each judged on its own. Both are added to the deflation ledger. SIBHIT's 2 failed tries stay counted.

**Costs and the bar (the Head's, Nov 16).**
- **Haircuts:** raw, 1c and 2c, all printed. The primary is 1c, but 2c for a rung closing within 120 s after T (C8).
- **Fee:** ceil(round(7% x p x (1-p) x 100, 9)) / 100.
- **Void:** a void refunds the price and keeps the fee.
- **Label:** "upper bound, not fill-checked".
- **Pass:** n 100 or more AND PF 1.3+ at the primary line with both halves (floor(n/2), entry order) 1.0+ AND PF 1.0+ at 2c, unrounded with no tolerance.
- **Under 100:** reads "no evidence at n = x".
- **z:** clustered by game.
- **On a pass:** a second independent build (16b) before any claim, then the Verification Analyst.

**Numeric prediction (before the read).** Development is spent and selected, so expect regression.
- R-FAST-NO: PF at 1c 0.95 to 1.5, mean -2c to +7c a trade.
- R-SLOW-YES: PF at 1c 0.85 to 1.25.
- P(R-FAST-NO passes) about 25%. P(R-SLOW-YES passes) about 10%.
- A pass on R-FAST-NO alone would fit the mechanism; a pass on R-SLOW-YES alone would not, and would be read with suspicion.

**Window.**
- **First choice:** the 2025-26 NBA KXNBAPTS games that no one has read for price or result.
- PROPS1 read Kalshi candles and results for its TEST third only (the last third of 2025-26 games by start time). Its FIT two thirds were read from ESPN box scores only, never Kalshi.
- The 2026-27 season before Oct 21 is not used. Our own development block (closes Oct 21 to before Nov 6) is spent.
- Auditor B maps every hold on the 2025-26 KXNBAPTS window. The window is written into this card, as two date constants, BEFORE any list or candle of it is pulled.
- **Fallback:** closes 2026-11-13 to before 2026-12-04 (SIBHIT's held-out, unread), pulled after Dec 4.

**Window constants:** TO BE FILLED from Auditor B's hold map, before any pull. A dated amendment below will carry them.

## Amendment 1 (Nov 16, 2026, ~15:30Z; the Head of R&D's ruling of 15:23Z; written before any list or candle of this window is pulled)

- **PROPS1 is CLOSED** (the Head of R&D: V2 is archived, nobody is assigned to read it, and its TEST third is already partly read). This is the same kind of closure as RV and EVM4.
- **Window constants:** KXNBAPTS 2025-26 markets with close_time from **2026-03-01T00:00:00Z** (1772323200) to before **2026-04-14T00:00:00Z** (1776124800). That is the regular season only; the play-in and playoffs are excluded. The scorer tests close_time first and drops everything else before reading any other field.
- **Exclusion by ticker (the ruling):** the 1,099 markets PROPS1 read candles for. **Open problem, stated before any pull:** that ticker list is not in any committed file. PROPS1's database is git-ignored and its session is archived. PROPS1's sample cannot be rebuilt without its ESPN model (the sample was the first 40 by sha1 among the markets its model scored). The Head is asked how to handle this before the candle job is built. The list job does not depend on it.
- **What PROPS1's read covered:** pre-game candles only, from 2 h before tip to tip, of at most 1,099 markets across NBA, WNBA and NFL stats. SIBHIT-R's quote is the late fourth-quarter minute T = O - 60.

## Amendment 2 (Nov 16, 2026, ~15:30Z; the Head of R&D's choice (A) of 15:24Z; written before any pull)

- **No ticker exclusion.** Because the 1,099-ticker list cannot be recovered, SIBHIT-R reads every market in the window. The disclosure: PROPS1 read pre-game candles only (tip - 2 h to tip), for a cheap-side test, on at most about 12% of the window's markets. SIBHIT-R reads the late fourth-quarter minute. It is a different question at a different minute, so the overlap cannot have selected SIBHIT-R's result.
- **On a pass:** the forward read on the 2026-11-13 to before 2026-12-04 block (after Dec 4) is still required before any shadow, beside the second build (16b) and the Verification Analyst.
- **Sample and held-out (the Head of R&D, Nov 16, 15:26Z; written before the list lands).**
  - **Pool:** the games that pass SIBHIT's base and clock checks inside the window, each game an event_ticker. Only time fields are used; no price or result.
  - **Order:** sorted by the lowercase hex of md5("SIBHITR-2026-11-16" + event_ticker), ascending, event_ticker as the tie break.
  - **Read sample:** the first 40 games. Candles are pulled and scored for these only (about 1,800 requests, 4 files under 470; the budget is approved).
  - **Held-out:** every other game of the window is a HELD-OUT for SIBHIT-R. Unread, and pulled only if the 40-game read passes, as its confirmation (one read, same bar). If the 40-game read fails, the held-out is never pulled.

## Amendment 3 (Nov 16, 2026, ~15:30Z; Auditor B's condition (1); written before any pull)

- **The window is not untouched.** PROPS1's code read the Kalshi RESULTS of all its TEST markets, 55,098 with a model probability, for model calibration. That covers every KXNBAPTS 2025-26 market in this window. It also read pre-game candles of up to 1,099 sampled markets.
- **The true statement:** SIBHIT's development data is spent for this rule, and the window's results were read by PROPS1 for a different purpose (a cheap-side calibration). No SIBHIT or SIBHIT-R rule was ever applied to it.
- **PROPS1 is closed** (the Head of R&D, Nov 16, 15:23Z). The Head chose to accept the 1,099 sampled markets as read, disclosed, with no exclusion (choice (A), 15:24Z).

## Amendment 4 (Nov 16, 2026, ~15:35Z; Auditor B's note; written before the list is opened)

- **Order, all on time fields:**
  1. The close_time window (2026-03-01 to before 2026-04-14) is tested first.
  2. SIBHIT's `games()` builds each game (event_ticker) and applies the base of at least 10 rungs and the clock check (one occurrence per game, exactly on :00 or :30). A game failing either is dropped and counted.
  3. ONLY THEN is the sample drawn, from the passing games. The clock check is applied BEFORE the sample.
- **Sample rule, fixed in `sibhitr_lib.py` (`SEED`, `N_READ`, `order`, `games`):**
  - The hashed value is the ASCII string "SIBHITR-2026-11-16" followed immediately by the game's event_ticker.
  - Games are sorted by the lowercase hex digest of its md5 (string order, which is byte order for hex), ascending, with the event_ticker string as the tie break.
  - The read sample is the first 40.
- **How the held-out stays out:** `games(rows, "read")` returns only the 40. The candle builder and the scorer call it that way, so no held-out game reaches a candle request, a quote, a side or a result. The scorer calls `games(rows, "heldout")` once, only to print `heldout_games_unread`, a count built from time fields. The held-out is read only after a pass, by a later reviewed change.

## Amendment 5 (Nov 16, 2026, ~15:40Z; after the list landed, before any candle; time fields only)

- **What happened:** SIBHITR_LISTS_A came back with all 18 pages full and a cursor on the last one. The scorer's truncation rule stopped the build, as written.
- **What the pages show:** the historical list is ordered newest first by close time. From close times only, the pages run from June 14, 2026 down to January 15, 2026; the window (Mar 1 to Apr 14) sits on pages 4 to 13. The list goes on past January, so KXNBAPTS existed before March. PROPS1's census said March to June, as a lower bound.
- **The change:** a list counts as truncated only when its last stored page has a cursor AND that page's earliest close is not before the window start. A last page reaching before Mar 1 covers the whole window, because later pages are older.
- **Disclosure:** this rule changed after the list landed. It depends only on close times, never on a price, volume or result, and it widens nothing: the window, sample, sides and bar are unchanged. It is sent to Auditor B before any candle job.

## Amendment 6 (Nov 16, 2026, ~15:45Z; after the list landed, before any candle; time fields only): the registered clock does not exist in 2025-26

- **The finding:** every 2025-26 KXNBAPTS market in the historical list has `occurrence_datetime` empty (1,000 of 1,000 on a window page). SIBHIT's clock (T = occurrence - 60 min) and its clock check therefore cannot be applied, and the builder finds 0 games. Nothing was built and no candle was requested.
- **The obvious substitute does not work.** `expected_expiration_time` is present in 2025-26, one value per game, on :00 or :30. But in the 2026-27 development list it sits either 0 h or 3 h after occurrence, and the two offsets are mixed inside every one of the 120 games. It is not a stable stand-in for SIBHIT's clock. Using it would be a new rule chosen after seeing the list.
- **Effect:** SIBHIT-R as registered cannot be read on 2025-26. Amendment 5 (the truncation rule) is moot for now.
- **Next:** the Head chooses between (1) the registered fallback, closes 2026-11-13 to before 2026-12-04, pulled after Dec 4, where occurrence exists, and (2) a new registration with a different clock. No candle is pulled meanwhile.

## Amendment 7 (Nov 16, 2026, ~15:40Z; the Head of R&D's ruling (1))

- SIBHIT-R moves to its registered fallback: closes from 2026-11-13T00:00Z to before 2026-12-04T00:00Z, listed and pulled after Dec 4. The occurrence field exists there.
- The same md5 split applies: 40 games read, all other games of the window held out and pulled only if the read passes.
- The 2025-26 window is not used. Its list (SIBHITR_LISTS_A) stays LOADED; only the time fields named in Amendment 6 were seen.
- Reminder set for Dec 5 to build the list job (live endpoint, close bounds).
