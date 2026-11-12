# MMSIM1 shadow baseline (registered Nov 12, 2026, BEFORE any shadow event exists): the registered quoting rule with honest fills, forward record, no money

Ordered by the Head of R&D (Nov 12, 2026) as the owner's shadow-list entry for MMSIM1. It **supersedes section 1 of `workers/SHADOW_RULES_NOV12.md`** on branch `claude/epic-ptolemy-0amjd9` (commit 79724f0), which scored the rule "as registered", i.e. with the fill rule that `workers/DESK_A_MMSIM1_FILL_MODEL_NOV12.md` shows leaves out the adverse fills. Status: **UNPROVEN, and expected to be killed.** It is a baseline: the forward record of what never-repriced quotes on the hourly Bitcoin ladder earn when fills respect price priority. A shadow places no order, holds no key, makes no Kalshi request and promotes nothing.

## 1. Start (a date constant) and why

`SHADOW_START = "2026-11-24T00:00:00Z"`. Only events CLOSING at or after it are shadow evidence. Events closing from 2026-11-07T15:00Z up to it are MMSIM1's held-out block (read once on or after Nov 24, `MMSIM1_AMENDMENT_3.md`); the shadow never opens them. Development events (before 2026-11-07T15:00Z) are never re-scored as shadow evidence.

## 2. The rule (fixed; no parameter is tuned)

- **Universe.** Every KXBTCD hourly event; the 7 strikes the book recorder (`scripts/record_book.py`, `quote-data:book/`) records for it.
- **Quote.** For each strike and each side (YES, NO): at the first book poll at or after T-50 minutes that shows a best bid on that side, post ONE contract at that best bid, behind the visible size at that price (queue ahead = that size). A strike is quoted only if BOTH sides show a best bid at its first poll in the window. Never repriced. Cancelled at T-15 minutes.
- **Fill (price priority).** Filled at our price at the EARLIEST of: (1) cumulative taker contracts at our price reach the queue ahead plus 1; (2) a taker trade prints strictly through our price after the post; (3) a book poll after the post shows that side's best bid below our price or absent. The row records which.
- **After a fill.** Both sides filled = a pair, pays exactly 1. One side filled = sold at that side's best bid at the last poll at or before T-15, **only if that bid shows size of 1 or more**; if there is no such bid the contract is booked as sold at 0 (a total loss of its price).
- **Fees.** Maker legs at 0 and at 0.0175 x p x (1 - p). The taker sale at 0.07 x p x (1 - p), rounded UP to the cent (one contract).
- **Judged figure.** One contract a side, maker fee 0, taker fee rounded. Maker 0 is the generous bound: a kill at maker 0 is a kill at any fee.

## 3. Exclusions (fixed now)

- An event with a gap of more than 15 seconds between consecutive book polls anywhere from T-50 to T-15 is excluded whole and counted in the report.
- A strike with no poll in the window, or without both best bids at its first poll, is not quoted and is counted.
- Nothing else is excluded. No event is dropped for its result.

## 4. Kill and return

- **KILL 1:** after at least 50 scored events, net per quote (total result divided by the number of quotes posted) at or under -1c.
- **KILL 2:** cumulative result at or under -$10 at one contract a side, at any point.
- Checked once per finished UTC day, in close-time order, never inside a day. A kill is final: scoring stops and the record is kept.
- **RETURN:** never for this rule. Only a NEW version (one that cancels or reprices), registered separately, that first passes its own development test under the same fill rule.
- If neither kill has fired after 300 scored events over at least 14 days, the baseline is reported against the lifecycle's shadow gate (cash PF 1.3 or better, second half 1.2 or better, no day above 30% of net) as a fact only. This file gives the baseline no route to a probe.
- For scale (development, 168 events, same rule): about -18c an event and about -1.4c a quote. KILL 1 is expected at the 50 event mark, about 3 days after the start.

## 5. What is recorded (the log that makes the record real)

- **Per quote** (event, strike, side), one row: `event_close, ticker, side, post_poll_ms, post_price, queue_ahead, fill_type (none | queue | through_tape | below_book), fill_ms, filler_fractional (0/1, queue fills only), flatten_poll_ms, flatten_bid, flatten_bid_size, outcome (none | pair | single), result_maker0, result_bound`.
- **Per event**, one row: `event_close, strikes_recorded, strikes_quoted, quotes, fills, pairs, singles, max_poll_gap_ms, excluded (0/1), tape_contracts, result_maker0, result_bound`.
- **Source.** The existing book recorder's files only. Public data, no key, no order.
- **Writer.** One pinned script (its commit hash on every row file), run once per finished UTC day. Where the rows are committed (a results branch) and who schedules it are engineering decisions for Main; until then the script and the day's rows can be produced by hand from `quote-data`.
- **Two recorder gaps to close (asked of Main, not done here):** a coverage row per event on the hourly book recorder (sum of tape contracts against Kalshi's reported volume, largest poll gap), as the 15 minute recorder already writes, so a dropped trade cannot hide a fill; and one free fact, read by a person: Kalshi's fee schedule for maker fills on this series.
- **What no public record can show:** our own queue position and whether a post-only order would be accepted. Rule 3 of the fill does not depend on either.

## 6. Counting

N tried: 0 added. It is the one registered MMSIM1 rule under the corrected fill model, recorded forward. No variant, no parameter.
