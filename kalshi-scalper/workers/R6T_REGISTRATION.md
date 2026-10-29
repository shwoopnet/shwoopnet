# R6T registration: MAKER5 and L1Q1 on recorder R6 (V2 worker R6T, 2026-10-29, research only)

Written and pushed BEFORE any R6 row was read. Before writing it I read `scripts/record_15m_book.py` and `.github/workflows/record-15m-book.yml` from `origin/main` (PR #621) for the column names and how they are written, and listed `origin/quote-data`: **there is no `book15r6/` file yet** (0 windows recorded at 2026-10-29, the recorder merged today). No book level, size, price, trade or result of R6 has been opened. Two cards, scored by one scorer (`src/scalper/r6tests.py`), each run once.

**Ledger check.** MAKER5 is MAKER4's card (FALSIFIED by a fill BOUND, no depth on file) and QUOTE1's (last 150 s, PF about 0) with the queue MEASURED from recorded depth, on all five series, in the 12 to 7 minute span MAKER4's correction requires. L1Q1 is MAKER2/MAKER3 (FALSIFIED: the fills are the dips; candle proxy, no trades, no queue) with a real queue and the real tape. Neither is a reworded test: both are the recorder's stated purpose (`studies/RECORDER_SPEC_R6_15MIN_BOOK_2026-10-29.md` section 8), and the result of each is predicted from its ancestor below.

## Shared rules (both cards; each the conservative choice where there was one)

**Data (fixed).** `origin/quote-data`, `book15r6/<date>/<HHMM>/` from the first run (2026-10-29) to the recorder's end (no window opening at or after 2026-11-13 23:59 UTC): `book.csv.gz` (`t_send_ms, t_recv_ms, server_date_header, ticker, series, close_time`, best 5 `yes_bid_px/sz` and 5 `no_bid_px/sz`, best first, a missing level empty), `trades.csv.gz` (`ticker, created_time, yes_price_dollars, count_fp, taker_outcome_side`, every trade of the window, cursor followed to the end, de-duplicated), `coverage.csv.gz` (one row per window per series, including `polls, ok_polls, max_gap_ms, first_recv_ms, last_recv_ms, tape_pages, tape_sum_count, volume_fp, result, note`). Markets: `KXGOLD15M, KXBTC15M, KXETH15M, KXDOGE15M, KXXRP15M` (all five the recorder holds; chosen by what is recorded, not by any quote). YES ask = 1 minus the best NO bid, with the size of that NO bid; NO ask = 1 minus the best YES bid.

**Clock.** Each run's offset = median of (`Date` header + 0.5 s minus `t_recv_ms`) over its book rows; poll time = `t_recv_ms` + offset (exchange time). A run with no Date header is NOT_RUNNABLE for its windows (excluded, counted). The header has 1 s resolution, so **an order is live 1.0 s after its posting poll** (Q2B's choice, not MM1's 0.25 s). Trades are compared on `created_time`.

**Queue model (MM1S / Q2B, unchanged).** A new order joins BEHIND all displayed size at its price at the posting poll (and, for L1Q1, behind the larger of that and the size at the same price on the first poll after it is live). Only trades move it forward: cancellations and the size ahead shrinking never advance it. It fills only after it is live, by (a) taker volume AT its price beyond the size ahead (a taker selling YES, `taker_outcome_side == "no"`, hits resting YES bids; a taker buying YES, `"yes"`, hits resting NO bids, whose YES price is 1 minus the NO bid), partial fills kept, up to C; or (b) a print strictly THROUGH its price, or a recorded opposite best quote at or through its price (the level was cleared), which fills the whole remainder at OUR price, never the better one. A quote moving away is not a fill.

**Crossing.** Any taker leg walks the 5 recorded levels of the poll it uses, best first; size beyond 5 levels is priced at the 5th level and counted; an empty side is the worst case (0 for a sale, 1 for a purchase).

**Fees.** 7% x C x p x (1-p) rounded UP to the cent per order (an order = one posted bid on its total filled quantity, or one crossing on all its levels). **Verdict: maker fills pay the taker rate 7%** (the maker fee for these series is not confirmed from public data). Information only: maker 1.75% and zero maker fee. Stress: the verdict fee x1.2. Settlement pays no fee. **Sizes C = 1 and C = 10, the verdict needs BOTH.**

**Unit, windows, statistics.** The independent unit is one window of one market. z is clustered by US Central date (markets and windows of one day are not independent). Windows by close-time thirds of the scored units (ties by series); **the last third is the holdout and is read once**, in the single run (the scorer refuses a second run). Halves also reported. Windows with no trade at all reported both ways (included, excluded). Windows whose tape `tape_sum_count` differs from `volume_fp` by more than 1% are counted and reported (not excluded).

**Read date and sample.** `run` refuses before **2026-11-06 00:00 UTC**, below **300 usable windows** (by coverage, below), or a second time. The verdict is `NOT_ENOUGH_DATA` if fewer than **300 scored windows had an order posted**.

**Bar (RULES.md, not loosened).** `NOT_YET_FALSIFIED` only if, at the verdict fee and at BOTH C = 1 and C = 10: PF at least 1.5 in each of the three date windows and pooled; both halves above 1; net per window above 0; at fees x1.2 net above 0 and PF above 1.2; and the date-clustered z of per-window P/L at least **5.17** (N about 439,100). Card-specific gates below. Otherwise `FALSIFIED`. A pass earns only a forward test registration and the owner's decision.

## 1. MAKER5: two-sided resting quotes, 12 to 7 minutes before the close, never re-priced

**Rule (exact).** Per market window closing at T:
1. Posting poll: the first poll at or after T-12 min, within 30 s of it. It needs a best YES bid and a best NO bid, YES bid below YES ask, and a mid between 0.20 and 0.80 (MAKER4's band, fixed now; outside it one side is a tick from 0 and the spread is the tick). Otherwise no order this window (counted).
2. Post one bid of C YES at the best YES bid (b) and one bid of C NO at the best NO bid (n), i.e. a YES sell at a = 1 - n. **Never re-priced, never re-posted**: one pair per market window. When one side fills, the other keeps resting at its price to complete the cycle. Net inventory is at most C each way.
3. **Adverse stop 5c:** at any poll where the mid is 5c or more against open inventory (long YES: mid at or below b - 0.05; long NO: mid at or above a + 0.05), every resting order is cancelled and the inventory is flattened by crossing at the NEXT recorded poll (taker). A stopped market posts nothing more this window.
4. **Flatten at T-7 min:** every resting order is cancelled and any inventory (including a partial fill) is crossed at the first poll at or after T-7 min; if no poll exists before T-6.7 min, the worst case. Nothing is held to settlement.

**Not at the same time as L1.** L1 decides at the 6 minute look (`L1_WINDOW_MS`, 5.5 to 6.7 minutes left) and holds to settlement. MAKER5 has no order or inventory after T-7 min (the flatten is the poll at or just after T-7 min, never later than T-6.7 min, else priced at the worst case as if it had been done), so it is flat before L1 can enter the same market and holds nothing of a window L1 can be in. **One exception, stated:** XRP was an early-entry series (`EARLY_PROBE_SERIES`, about 10 minutes left), which falls inside 12 to 7. XRP is paused in code since 2026-10-28, so L1 sends no XRP order now; it stays in the test, and any live design would have to drop XRP or skip any window where L1 holds XRP.

**Counterparty.** Impatient takers mid-window (hedgers, people closing, retail on a phone) who cross a 1c to 3c spread. **The obstacle:** informed takers watching spot hit the side about to be wrong, so one-sided fills are adverse; measured below, not assumed.

**Measured, not assumed.** For every maker fill: the mid at the first poll at or after fill + 30 s and + 120 s (skipped, counted, if that poll is over 20 s late), signed so positive is our way, mean cents per contract with the date-clustered z, beside the half-spread earned. Also: pairs posted, fill rate per side, completed cycles, one-sided inventories, stops, flattens, spread earned, stop and flatten losses, fees, per market.

**Card gate (in addition to the bar):** stop and flatten losses under half the spread earned.

**Prediction (MAKER4 Q1 0.00 and Q0 0.09 at maker fee, 0.64 at zero fee; QUOTE1 PF 0.00).** FALSIFIED. Verdict PF 0.00 to 0.35 at C = 1 and 0.05 to 0.45 at C = 10; information maker 1.75% 0.2 to 0.7, zero maker fee 0.4 to 1.0. Mean 30 s markout -0.2c to -1.0c, 120 s markout -0.5c to -2.5c. Fill rate per posted side 10% to 40%; at least a third of filled pairs end one-sided. Prior of a pass under 2%.

**Tries:** 2 sizes x 3 fee assumptions = **6** (the 2 verdict rows decide; stress is a gate).

## 2. L1Q1: L1's entry as a resting bid at the 6 minute decision

**Signal (L1's own rule, from R6's book).** Signal poll S = the last poll at or before T-360 s (the close of the candle ending 360 s before the close), within 10 s of it. The side bought is the side whose ask at S is 0.88 to 0.97 (YES ask = 1 - best NO bid; NO ask = 1 - best YES bid). Neither, or both: no signal (counted). All five markets, every window on its own: the portfolio rules of the live bot (one crypto order per window, window cap, the Bitcoin and Ethereum smooth gate, the XRP pause) are NOT applied; the question is execution, and they are reported as not modelled.

**Plain L1 (the comparison, not a try).** Cross for C at the first poll at or after S + 1.0 s, walking the ask side of that poll's book, taker fee; held to settlement.

**Rest.** At S post a bid for C of the bought side at that side's best bid at S (YES bid for YES, NO bid for NO), live at S + 1.0 s, queue as above. Filled only by the queue model before **T-120 s**. At T-120 s the unfilled remainder is cancelled, then:
- **variant a (skip):** nothing more; a partial fill is kept.
- **variant b (cross):** if the side's ask at the first poll at or after T-120 s is still 0.88 to 0.97, the remainder is crossed there (walking the book, taker fee); otherwise nothing more.

Everything filled is held to settlement: $1 per contract if the coverage `result` is the side bought, else 0. A window without `result` "yes" or "no" is not usable.

**Counterparty.** Takers who sell the favourite late in the window into resting bids (people taking profit or cutting a position before the close). **The obstacle, from MAKER2 and MAKER3:** the bid fills when the favourite dips, i.e. when it is more likely to lose; the entries that never come back to the bid are the winners.

**Report.** Signals; full, partial and no fill rates for the bid; PF and net per contract of FILLED entries (at the bid), the same entries at plain L1's price, and of MISSED signals at plain L1's price (what the misses were worth); net per opportunity of a, b and plain L1 on the same windows, and the differences a minus plain and b minus plain with the date-clustered z; adverse selection (win rate of filled against missed); per market.

**Card gate (in addition to the bar):** the variant's net per opportunity above plain L1's on the same windows in every third, at both sizes.

**Prediction (honest).** FALSIFIED for both. Fill rate of the bid before T-120 s 35% to 65% (a 90c favourite's bid queue is deep). Filled entries lose more often than missed ones: PF of filled entries at the bid 0.5 to 1.0, missed signals at plain L1's price PF 1.3 or more. Net per opportunity: variant a 0.2c to 1.0c per contract BELOW plain L1, variant b 0.3c to 0.8c below. Verdict PF variant a 0.6 to 1.1, variant b 0.7 to 1.1, plain L1 about 1.0 to 1.2. Prior of a pass under 1%.

**Tries:** 2 variants x 2 sizes x 3 fee assumptions = **12** (plain L1 is the comparison, not a try).

## Kill criteria (both)

- `NOT_RUNNABLE`: the recorder schema changes, or more than 20% of usable windows lack a clock.
- `NOT_ENOUGH_DATA`: under 300 scored windows with an order posted.
- `FALSIFIED`: any gate failed with at least 300. Rules are not widened after the result.

**Usable window (coverage only, chosen before any row):** a coverage row with a ticker; `ok_polls / polls` at least 80%; `max_gap_ms` at most 20,000; `tape_pages` at least 1 and no `tape incomplete`, `tape page cap` or `tape out of time` note; MAKER5: `first_recv_ms` at or before T-12 min + 30 s and `last_recv_ms` at or after T-6.7 min; L1Q1: `first_recv_ms` at or before T-365 s, `last_recv_ms` at or after T-115 s, and `result` "yes" or "no".

## Count

R6T tries: 6 (MAKER5) + 12 (L1Q1) = **18**. Running count about 439,106 (BAND2) + 18 = **about 439,124**. Deflated bar z about 5.17.

**Ready dates.** Neither is read before 2026-11-06 00:00 UTC. At full coverage the five markets give about 440 windows a day, so 300 usable windows exist by 2026-10-30 or 31; posted orders (MAKER5 needs a 20c to 80c mid at 12 minutes left; L1Q1 needs an L1 signal) should pass 300 before the read date. The AUTO loop runs both on the first hourly pass on or after 2026-11-06 00:00 UTC.

**Code.** `kalshi-scalper/src/scalper/r6tests.py`: `count` (usable windows per market from coverage files only), `run maker5`, `run l1q1` (each refuses before 2026-11-06, below 300 usable windows, or a second time; writes `data/maker5_result.txt` / `data/l1q1_result.txt`). Tested only on a synthetic fixture (`tests/test_r6tests.py`). Wired into `src/scalper/autoscore.py` like QUOTE2B.
