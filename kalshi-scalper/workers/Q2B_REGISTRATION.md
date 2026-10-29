# QUOTE2B registration: resting two-sided quotes on the Bitcoin hourly ladder with a real queue model (V2 worker Q2B, 2026-10-29, research only)

Written and pushed BEFORE any recorded book or trade row was read. Before writing it I only listed the files on `origin/quote-data` under `book/` (one run directory so far, `book/2026-10-29/1026/`, holding `book.csv.gz`, `trades.csv.gz`, `coverage.csv.gz`) and read the column names in `scripts/record_book.py`. No book level, size, price or trade has been opened. The series metadata (`GET /series/KXBTCD`: `fee_type: "quadratic"`, `fee_multiplier: 1`) was read; it is not market data.

**Ledger check.** Not a reworded tested idea. QUOTE1 (last 150 s of the 15 minute contracts, top of book, no re-quote) and MAKER4 (15 minute contracts, 12 to 4 minutes left, NO depth on file, so decided by fill bounds Q1 and Q0) are the nearest. QUOTE2B differs in market (the hourly "above K" ladder, `KXBTCD`), in span (50 to 10 minutes before an hourly close, away from the convergence that sank QUOTE1), and in that the queue position is MEASURED from recorded depth rather than bounded. It is the card the recorder was built for (`studies/RECORDER_SPECS_2026-10-29.md` R1). MAKER5 (the 15 minute version) needs recorder R2, which is not built; it is not registered here. G3H1 (a directional cheap-side entry on the same recorder) is a separate card and does not share tries with this one.

## Counterparty (who pays, and why they keep doing it)

Impatient takers on the near-the-money hourly strikes who cross the spread to trade now: people hedging a 15 minute or perpetual Bitcoin position into the top of the hour, people closing, retail on a phone. They pay the spread. **The obstacle, stated before the run:** the other takers are informed (they watch the BRTI and spot venues and hit the quote a ladder bot has not yet moved), so the side that fills is on average the side the price then leaves. QUOTE1 and MAKER4 both died of this plus the fee. The replay below does not assume adverse selection away or in; it measures it from the later mid.

## Data (fixed)

`origin/quote-data`, `book/<date>/<HHMM>/` from the run starting 2026-10-29 10:26 UTC onward: `book.csv.gz` (best 5 YES bids and 5 NO bids with sizes, every ~3 s per strike, 7 strikes nearest the money picked 55 minutes before each close and not re-picked within the hour), `trades.csv.gz` (public tape every 30 s, de-duplicated by trade id), `coverage.csv.gz` (one row per hourly close). YES ask = 1 minus the best NO bid; the size at the YES ask is the size of that NO bid. Prices are dollars as recorded.

**Usable hour (chosen on coverage only, before any fill is computed):** a coverage row exists; at least 3 strikes recorded; ok polls at least 80% of polls; first ok poll at or before close minus 50 minutes; last ok poll at or after close minus 9.5 minutes. The tape poll asks for at most 1000 trades with no cursor, so a 30 s read can truncate (this project's recurring trap). **Truncation rule:** if any tape poll of a strike in the hour returned 990 or more rows, that strike-hour's tape is re-fetched in full from the public API (paged, `min_ts` close minus 51 minutes to `max_ts` close minus 9 minutes) and used instead; if the re-fetch fails the hour is excluded and counted. Hours with no trade on any quoted strike are reported both ways (included as recorded, and excluded).

**Clock.** Each run's offset = median of (server `Date` header + 0.5 s minus `poll_ts_local_ms`) over its book rows. The header has 1 s resolution, so the order is taken to be live **1.0 s after the posting poll** (offset-corrected), not the 0.25 s of MM1. Trades are compared on exchange time (`created_time`). If a run has no Date headers the run is NOT_RUNNABLE for that run's hours and they are excluded and counted.

## Rules (exact)

Per hourly close T, on the recorded strikes, from T minus 50 min to T minus 10 min.

1. **Decision times.** Minute boundaries from T-50 min to T-15 min (36 boundaries). At each, the decision uses the first recorded poll of each strike at or after the boundary (the posting poll).
2. **Eligible strike for a new pair:** best YES bid and YES ask both present at the posting poll, bid < ask, mid between 0.20 and 0.80, the strike flat (no inventory) and not stopped this hour.
3. **Post.** One buy of C YES contracts at the best YES bid and one sell of C YES contracts at the best YES ask (a NO bid at 1 minus ask). Never inside the spread. **At most 3 strikes may hold a live pair or inventory at once**; when more are eligible, the ones whose mid is nearest 0.50 are chosen (ties by lower strike).
4. **Queue model (the point of the test).** A new order joins BEHIND all displayed size at its price at the posting poll (`yes_bid_sz_1` for the buy, `no_bid_sz_1` for the sell). Only trades move us forward: cancellations and the size ahead shrinking never advance our place. Our order fills only when, after it is live, (a) cumulative taker volume AT our price exceeds the size ahead of us (a taker SELLING YES, `taker_outcome_side == "no"`, at our bid for our buy; a taker BUYING YES, `"yes"`, at our ask for our sell), by the excess up to C (partial fills kept), or (b) the price trades or quotes THROUGH ours (a print strictly through our price, or a recorded best opposite quote at or through our price), which fills the whole remainder at OUR price. **A quote moving away from our price is not a fill.**
5. **Re-quote.** At each boundary, a strike that is flat (no fills, or a completed cycle) has its unfilled remainders cancelled and, if still eligible, a fresh pair posted at the back of the new queue. A strike with net inventory cancels the remainder of the side that filled more and keeps the other side resting at its original price, with its size capped at the net inventory, until the strike is flat again (cycle complete), stopped, or flattened. No chasing: the closing order is never re-priced.
6. **Inventory limit.** Net at most C contracts each way per strike, at most 3 strikes active (so at most 3C contracts each way in the hour).
7. **Stop.** At any poll where the mid has moved 5c or more against an open inventory (long: mid at or below our buy price minus 0.05; short: mid at or above our sell price plus 0.05), the strike is flattened by crossing at the NEXT recorded poll's opposing quotes (taker), walking the 5 recorded levels; any size beyond 5 levels is priced at the 5th level and counted. A stopped strike does not quote again this hour.
8. **Flatten, fixed: crossing at T minus 10 minutes, never held to settlement.** At T-10 min every resting order is cancelled and every open inventory is flattened by crossing at the first recorded poll at or after T-10 min, walking the book as in 7. **Why flatten and not settle:** holding to settlement turns every one-sided fill into a $0 or $1 bet on Bitcoin's direction, which is exactly the view this lane avoids; QUOTE1 showed inventory near the close is where the losses are (the price converges to 0 or 1); and T-10 min keeps the card flat before L1's Bitcoin decision at about 6 minutes left on `KXBTC15M` (correlated exposure, though a different contract), and before the final-minute informed flow.
9. **Size per quote: C = 1 and C = 10** contracts, both scored; the verdict needs BOTH.
10. **Fees.** Kalshi's formula rate x C x p x (1-p), rounded UP to the cent per order (an order = one posted quote, on its total filled quantity; a crossing flatten = one order, summed over the levels walked, then rounded). The series reports `fee_type: "quadratic"` and does not state a maker fee for `KXBTCD` by itself, so the maker fee is not confirmed. **Verdict: maker fills pay the taker rate 7%** (conservative). Crossing fills pay 7%. Information only: maker 1.75% (the published maker schedule where it applies) and zero maker fee. Stress: the verdict fee x1.2.

## Measured, not assumed: adverse selection

For every maker fill: the mid of that strike at the first poll at or after fill time + 30 s and + 5 minutes, signed so that positive means the price moved our way (for our buy, later mid minus fill price; for our sell, fill price minus later mid). Reported as the mean in cents per contract, both horizons, with the date-clustered z, beside the half-spread earned per fill. A 5 minute markout past T-10 min uses the poll at that time (the recorder runs to T), so every fill has both markouts.

## Unit, windows, metrics

- **Independent unit: the hourly close.** One hour's P/L is the sum over its strikes; strikes of one hour are not independent. z is clustered by US Central date.
- **Windows by date:** the usable hours in close-time order split into thirds; **the last third is the holdout and is read once**, in the single run (the scorer refuses a second run). Halves are also reported.
- **Metrics, profit factor first:** PF of hourly P/L per window and pooled, loss rate of hours, net per hour, pairs posted, fill rate per side, completed cycles, one-sided inventories, stops, flattens, spread earned, stop and flatten losses, fees, markouts at 30 s and 5 min, the account curve at $500 with C = 10 (max drawdown, worst day).

## Numeric prediction (honest; QUOTE1 PF 0.00, MAKER4 Q1 0.00 and Q0 0.09 at maker fee, 0.64 at zero fee)

FALSIFIED. Near-the-money hourly strikes in this span probably quote a 1c to 3c spread; the verdict fee at a 50c price is 2c per order at C = 1 and 18c per 10 at C = 10, so a completed cycle nets about zero or less before any adverse move. **Verdict PF 0.00 to 0.25 at C = 1 and 0.05 to 0.35 at C = 10. Information: maker 1.75% PF 0.2 to 0.6; zero maker fee PF 0.4 to 1.0.** Markouts negative: mean 30 s markout -0.3c to -1.5c per contract, 5 minute markout -1c to -4c. At least a third of filled pairs end one-sided (stopped or flattened). Fill rate per posted side 15% to 45% (the real queue ahead is usually tens to hundreds of contracts). Prior of a pass under 2%.

## Kill criteria and bar

- **NOT_RUNNABLE:** the recorder schema changes, or more than 20% of hours lack a usable clock or a complete tape after re-fetch.
- **NOT_ENOUGH_DATA:** fewer than **300 usable hourly closes**, or fewer than 300 hours in which at least one pair was posted. `run` also refuses before **2026-11-12 00:00 UTC**.
- **NOT_YET_FALSIFIED** only if, at the verdict fee and at BOTH C = 1 and C = 10: PF at least 1.5 in each of the three date windows and pooled; both halves above 1; net per hour above 0; at fees x1.2 net above 0 and PF above 1.2; stop and flatten losses under half the spread earned; and the date-clustered z at least **5.17** (N about 439,000). Otherwise **FALSIFIED**. Rules are not widened after the result.
- A pass earns only a forward test registration and the owner's decision. `KXBTCD` is outside the current second-slot registry; no live design is implied.

**Tries (N).** 2 sizes x 3 fee assumptions = 6 (the 2 verdict-fee rows decide; stress is a gate, not a try). Running count about 439,012.

**Code.** `kalshi-scalper/src/scalper/quote2b.py`: `count` (counts files and usable hours from coverage only, prints the ready date), `run` (refuses before 2026-11-12 00:00 UTC, below 300 usable hours, or a second time; writes `data/quote2b_result.txt`). Tested only on a synthetic fixture (`tests/test_quote2b.py`).

## Amendment (2026-10-29, written with the scorer, still before any recorded book or trade row was read)

1. **Re-fetch threshold 500 rows, not 990.** The recorder de-duplicates trade ids before writing, so a truncated 1000-row read can land in the file with fewer than 990 rows. A strike-hour's tape is re-fetched from the public API if any one recorded read holds 500 or more rows. Re-fetching only replaces recorded rows with the complete tape, so it cannot favour the result.
2. **Scorer readings where the rules were silent:** minute boundaries T-50 to T-11 manage resting orders (cancel when flat, convert to a closing order when not); new pairs only at T-50 to T-15. A posting poll must fall within 30 s after its boundary, else that strike is not posted at that boundary. A stop executes at the strike's next recorded poll after the one that triggered it. If no poll exists at or after T-10 min, the flatten is priced at the worst case (0 for a sale, 1 for a purchase). Markouts use the first poll at or after the horizon and are skipped (counted) if that poll is more than 60 s late.
