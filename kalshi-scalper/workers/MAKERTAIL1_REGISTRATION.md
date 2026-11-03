# MAKERTAIL1 registration: a resting buy at the best bid in the far tail of the hourly Bitcoin ladder (KXBTCD), held to settlement, with a queue model on the REAL recorded book and tape (V2 worker, 2026-11-03, research only)

Written and committed BEFORE any outcome, win rate, fill or PnL was computed. What was looked at to write it: the README ledger, `workers/COST1_RESULT.md` (via the README line), `scripts/record_book.py` (schema), the CSV headers and the coverage rows of the recorder files (counts of polls only), and the table layout of `data/conf2_lad.sqlite` (columns and the series/time range; no `result` value read). No bid, ask, trade price or result was opened.

## Duplicate check (what is covered, what is new)

- **MAKER1** (tennis, deep markets, resting, replayed on the tape): all six FALSIFIED. Different market, not held to settlement from a tail.
- **MAKER2 / MAKER3** (L1's 88c to 97c favourite entries rested at the bid, candle fill proxy): filled 67% on dips, net -1.19c per fill, adverse selection. Favourite side, candle proxy, no queue. Not the tail, no real depth.
- **MAKER5 and L1Q1** (R6 15 minute markets, resting bids mid 20c to 80c, flattened by crossing; L1's signal as a resting bid): not read before 2026-11-06. Different series (15 minute), different price band (mid), flattened not held.
- **QUOTE2B / MM1** (two-sided quotes on this same KXBTCD book recorder, mid band, flat at T-10 min): not read before 2026-11-12. Same data, a different trade: it never holds a far tail to settlement.
- **G3H1** (cheap side ask under 10c, bid-up trigger, sell +3c): a taker round trip, not a resting buy held.
- **BOOKCH1** (R6 imbalance trigger, cheaper side of the 15 minute markets, taker): book sizes as a TRIGGER on 15 minute markets, forward only.
- **COST1**: the cost lever itself (maker fee 0 on plain `quadratic` series, including KXBTCD; I re-checked the API today: `GET /series/KXBTCD` returns `fee_type: "quadratic"`, `fee_multiplier: 1`, so the maker fee is 0 and the stop condition "not zero" does not apply). COST1 priced the arithmetic and said resting does not help L1-style entries; it did not test far tails.
- **LADLONG1 (PF 0.64 to 0.72), HRSEAS1 baseline (PF 0.78), VOLGAP1, OIHR1, PERPOI1 controls, LADLOCK, LOCK2H:** the cheap-tail trades that died as TAKER. This card is their resting counterpart on the same instrument with real depth.
- `workers/OICORE_SHAPE_INVENTORY.md` has no resting-order tail trade. BOOKCH1 is the only card using the order book sizes and it is a 15 minute taker test.

**New:** a far-tail resting buy held to settlement on the HOURLY Bitcoin ladder, scored with the recorded queue (size ahead at the look) and the recorded tape. Nothing in the ledger scores this.

## Data

`origin/quote-data`, `book/<date>/<run>/` (`book.csv.gz`, `trades.csv.gz`, `coverage.csv.gz`), written by `scripts/record_book.py` every 3 s (book, 7 strikes nearest the money, 5 YES and 5 NO levels with sizes) and every 30 s (the public tape with trade ids and `created_time`). The tip of that branch carries only the newest runs; every earlier run is in its history, so the scorer reads them with `git log origin/quote-data --diff-filter=A -- book/` and `git show <commit>:<path>`. 28 runs between 2026-10-29 10:26Z and 2026-11-03 16:01Z, 97 hourly closes in the coverage rows when this was written; the recorder was still committing at 2026-11-03 20:03Z, so it has been running. Outcomes: `market.result` in `data/conf2_lad.sqlite` for the ticker (KXBTCD rows reach close time 2026-11-03 19:00Z). Exchange time = the server `Date` header of the book row (1 second resolution).

## The trade (one definition, frozen)

For each hourly close T present in the coverage rows and each of its recorded strikes (up to 7), take the **look poll** = the last book poll of that ticker whose Date-header time is at or before T-1500 s (25 minutes before the close) and not more than 20 s earlier than that; no look poll = NoData, not a loss.

- **YES order:** best YES bid b in [0.01, 0.15] with a displayed size. **NO order:** best NO bid b in [0.01, 0.15]. One order per ticker per side, 1 contract, price b (the best bid at the look, never re-priced), equal weight, all such strikes. A strike with a bid in the band on both sides gets both orders (rare).
- The order is live from look + 1.0 s and rests until T-60 s, then is cancelled (unfilled = no trade, counted as 0 in the per-order mean).
- **Queue ahead** Q0 = the displayed size at b at the look. We join the back.
- **Fills from the tape** (taker prints with `created_time` after look + 1.0 s and at or before T-60 s): a resting YES bid at b is hit by prints with `taker_outcome_side == "no"` at `yes_price <= b`; a resting NO bid at nb is hit by prints with `taker_outcome_side == "yes"` at `yes_price >= 1 - nb`.
  - **PESSIMISTIC bound (the verdict bound):** nothing ahead of us ever cancels. Filled when the cumulative contracts printed exactly AT our price exceed Q0, or when any print goes THROUGH our price (a worse-for-the-taker price, which means our level was cleared). Filled at b.
  - **OPTIMISTIC bound (information only, but counted as a try):** the whole queue ahead cancels. Filled by the first print at or through our price.
  - Information only: a middle bound with half of Q0 cancelled.
- Maker fee 0 (`fee_type` quadratic, checked above). Outcome: the strike's settled result; net = (1 if our side won else 0) - b, per contract, in cents.
- **Taker comparison (same orders):** buy the same side and strike at the ask at look + 1.0 s (the first poll at or after it within 20 s; ask = 1 - best opposite bid; displayed size at the ask at least 10), held to settlement, fee = 7% x C x p x (1 - p) rounded UP to the cent, C = 10, reported per contract, plus fees x1.2.
- Haircuts stated up front: the tape is polled every 30 s but each trade carries its own `created_time`, so the 30 s granularity affects only whether a trade was missed (the recorder reads with overlap and de-duplicates by id); the look and fill clocks have 1 s resolution (the Date header), so prints within 1 s of the look are ignored; cancelled queue ahead is the two bounds above. If the tape has a gap longer than 90 s between two consecutive poll timestamps inside the order's life, the order is marked tape-gap and counted as NOT filled under the pessimistic bound and excluded from the optimistic bound; the number of such orders is reported.

## Frozen split

By close time, from the coverage rows only: DEV = closes 2026-10-29 through 2026-11-01 23:00Z, split into two halves at the median close (HALF1, HALF2). **HOLDOUT = closes from 2026-11-02 00:00Z through 2026-11-03 15:00Z (about the last third of the available days), not opened.** The holdout is scored ONLY if DEV passes the full bar below; otherwise it stays unread and the rule goes to the forward test. The forward set is every close from 2026-11-03 16:00Z on.

## Numeric prediction (before any count)

Tail orders: 1 to 3 a close (nearest-7 strikes at 25 minutes: the far strikes with a 1c to 15c bid), about 130 to 350 orders in the 5 days. Fill rate: PESSIMISTIC 10% to 25% (central 15%), OPTIMISTIC 45% to 75% (central 60%). Win rate of a filled order below its price: about 0.6 to 0.9 x the bid (a fill is a move against us). Net per resting order under the pessimistic bound: about -0.3c (range -1.0c to +0.2c); net per fill about -2c; PF on fills about 0.6 (0.3 to 0.95). Taker comparison PF about 0.7 (it already died at about 0.64 to 0.78 elsewhere). Prior of FALSIFIED: 90%.

## Kill rules and verdicts

- **FALSIFIED:** mean net per resting order not above 0 under the PESSIMISTIC bound in DEV, or PF on pessimistic fills under 1.5, or either half of DEV not positive.
- **NOT_ENOUGH_DATA:** under 150 pessimistic fills in DEV. The report then gives fills per day and the days to 150 at that rate (and the same for the forward set).
- **NOT_YET_FALSIFIED** is the best possible word: a pass needs day-clustered z above the deflated bar (about 5.27), a named counterparty (the tail seller who pays 15c for a 1c to 5c option?), the holdout positive, and the forward test. Nothing promotes; there is no promote verb.
- **Forward:** the same rule on closes from 2026-11-03 16:00Z, read once on 2026-11-12 (or when 150 pessimistic forward fills exist, whichever is later); the recorder is running (last quote-data commit 2026-11-03 20:03Z); it stops only if the workflow stops.

## Capped probe spec (written now, to be built only if a pass would justify it; the owner decides)

1 contract, a resting buy at the best bid, hard limit price <= 0.15, only KXBTCD strikes in the recorder's 7, posted 25 minutes before the close, cancelled at T-60 s, not on a 15 minute series (no L1 overlap), kill rule: stop after 40 fills if the net is negative or on 3 straight fill-losses past 8 fills, worst day at most 24 closes x 3 orders x 15c = $10.80 (a realistic worst about $4), fills per day to be filled from the result. The result file reports the fills per day.

## Tries and N

Two (PESSIMISTIC and OPTIMISTIC bounds; the middle bound, the taker comparison and the price buckets are information). N +4 (+2 per rule), running count about 730,074 on the coordinator's total, z bar about 5.27.

Code `src/scalper/makertail1.py`, tests `tests/test_makertail1.py` (synthetic book and tape), result `workers/MAKERTAIL1_RESULT.md`.

## Amendment 1 (2026-11-03, after the DEV result, before any forward row was scored; 20 forward orders exist, none scored)

Added at the coordinator's request. The 2026-11-12 forward read (closes from 2026-11-03 16:00Z) must ALSO report YES-side tails and NO-side tails SEPARATELY, under the pessimistic and the optimistic bounds, as pre-registered readouts. N +2 (one side claim, two bounds counted once each as the side rule).

- **Claim:** NO-side tails (crash strikes, strike below spot) beat YES-side tails.
- **Counting rule:** the side result counts only if the COMBINED forward pessimistic net per resting order and the NO-side forward pessimistic net per resting order are both above 0, with at least 150 forward pessimistic fills on EACH side. Otherwise the side split is information only and the claim is NOT_ENOUGH_DATA or FALSIFIED as the numbers fall.
- The DEV side split seen in the result (YES PF 0.23 on 81 orders, NO PF 1.25 on 94) is a hypothesis from one 3.5 day sample, NOT evidence, and is not to be re-cut or extended on DEV. No side analysis is run on DEV data here; SKEW1 (taker at the ask, the full KXBTCD history) is a separate card run by the coordinator.
- Nothing else in the rule, bounds, kill rules or holdout changes.
