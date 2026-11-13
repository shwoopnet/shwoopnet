# COMBODONE: a combo whose early leg has already settled in its favour (Idea Desk C, Nov 13, 2026)

**Written before any combo-recorder row was read for this purpose.** Stage 1 is a zero-try COUNT (go or no-go), built by Desk B from this card. Nothing here is scored against an outcome. PAPER ONLY. [research]

`COMBODONE | family: a stale resting order in a multi-leg market after one leg is decided, bought against the product of the undecided legs, held to settlement | risk class: mid price, asks at 88c or more excluded, 1 contract | stage Idea, count registered, zero tries | prior about 2%`

## The two Kalshi texts it relies on (quoted from public pages; read by a worker on Nov 13)

1. **Combo payout and early settlement.** Kalshi help center, https://help.kalshi.com/markets/combos: a combo pays the product of its legs, can settle at $0 "immediately" when one leg settles at $0, and typically settles "within 1 to 12 hours after the last underlying position resolves". Combo prices come from "a Request For Quote (RFQ) system", and each combo is "a unique market with its own dedicated order book".
2. **Combo template** (FOOTBALLSTATS, served at https://kalshi-public-docs.s3.amazonaws.com/contract_terms/NFLPREPACK.pdf):
   - "Outcomes may resolve at different times (e.g., Week 1 game + Super Bowl winner). Early resolution to 'No': If any outcome becomes impossible or does not occur, market immediately resolves to 'No.'"
   - "Last Trading Date ... will be the same as the Expiration Date."
   - Kalshi's request-for-quote docs (https://docs.kalshi.com/getting_started/rfqs.md) refuse a request when "a leg is not open for trading".
   - **Inferred, not stated by Kalshi:** a combo whose early leg settled in its favour keeps trading, and new maker quotes for it may be refused, leaving only its resting book.

## Mechanism and the other side

After one leg settles in the combo's favour, the combo is worth the product of the legs still open. An order resting in the combo's own book, priced while that leg was undecided, may not have moved, and makers cannot re-quote it through the request system.

- **Other side:** whoever left the resting order (a holder's exit order, or a maker's leftover order).
- **Why they lose:** they did not reprice after a decided leg.

## The four uniqueness checks (lifecycle 7d) and the declined list (7e)

1. **Signal.** A decided leg (a settled fact) against a combo's stale resting order. Not a model value, not a price pattern, not a base rate. **Different** from the registered combo house side and from the leg-count markup cut, both of which act before any leg is decided.
2. **Entry and exit.** Entry only after a leg has settled in the combo's favour, at a resting ask; hold to settlement. No live or shadow rule trades combos. **Different.**
3. **Correlation with live strategies.** No shared market with gold L1, OICORE or EVENT830; expected near 0. Not measured.
4. **Declined list.** Compared with:
   - **lock and parity scans:** one held position against a fair value after a settled fact, not a riskless set across live markets;
   - **in-game lag:** the fact is settled and can be hours old; the stale price is in a market that cannot be re-quoted, not a related market a minute behind;
   - **market making:** a taker entry;
   - **favourite-and-hold:** asks at 88c or more are excluded;
   - **taker flow:** no flow field.
   No row applies.

## Stage 1: the exact count (Desk B builds the counter)

### What the recorder holds (scripts/record_combo.py and the files on `combo-data`)

- **When:** a run every 30 minutes (cron `11,41`).
- **`quotes.csv`:** up to 400 open combos a run, tightest yes spread first, with `yes_ask`, `yes_ask_size`, `close_time` and the leg count.
  - The quotes are the LIST copy (delayed, per HOW_TO_PRICE_A_PAPER_TRADE).
  - `leg_tickers` is filled ONLY for the first 100 rows, capped at 600 characters, and a capped string ends in `|...`.
- **`books.csv`:** the live top 5 YES and NO bids of the first 40 combos only.
- **`trades.csv`:** trades of the 15 most traded combos.
- **Not held:** any leg's settlement time or result. Legs are other Kalshi markets, and the recorder never reads them.

### The smallest pull that supplies leg settlement

A kalshi-pull lists job, built after the week is recorded, asking `/markets` with the `tickers` parameter for every distinct leg ticker seen in that week's `leg_tickers`, in batches of up to 100 tickers a request. It returns each leg's `status`, `result` and `settlement_ts`.

- **Size:** about 20 to 40 requests for a week. A distinct leg count of 2,000 to 4,000 is my estimate; the builder counts it exactly from the files first.
- **Runner change:** the runner must allow the `tickers` parameter and list the tickers in `ticker_allowlist`, as the candle jobs do.

### Definitions, fixed now

- **Eligible snapshot.** A `quotes.csv` row of combo C at receive time t such that ALL of these hold:
  - (a) its `leg_tickers` is present and not truncated (does not end in `|...`);
  - (b) at least one leg L of C has `settlement_ts` at least 60 seconds before t, and L settled on C's side (a `:yes` leg with result yes, or a `:no` leg with result no);
  - (c) no leg of C has settled against C's side at or before t;
  - (d) at least one leg of C is still unsettled at t;
  - (e) C's `close_time` is after t.
- **Resting ask.**
  - On the eligible row: `yes_ask` greater than 0 and at most 0.87 (rounded UP to the whole cent), with `yes_ask_size` of 1 contract or more.
  - If C is also in that run's `books.csv`, the counter reports the book's own ask too, as 1 minus `no_bid_px_1`, with `no_bid_sz_1` of 1 or more. That figure is printed beside the list figure; the kill line uses the list figure, which is the more lenient.
- **Independent combo.** One per distinct set of STILL-UNSETTLED legs (sorted ticker:side strings) per UTC day. Repeat snapshots of the same set on the same day count once.
- **The week.** 7 consecutive UTC days in which the recorder completed at least 80% of its scheduled runs (from `coverage.csv`). If no such week exists yet, the count waits; it is not read on a partial week.

### The kill line, fixed

**Fewer than 30 independent combos with a resting ask in eligible snapshots, in one full week, CLOSES the card** as "nothing to buy". The counter also prints:
- the number of eligible snapshots and independent combos with no ask;
- the median ask;
- the share of eligible rows whose leg list was available. Only the first 100 rows carry legs, so a combo with a wide spread is invisible; this is stated as a limit, and it makes the count conservative.

**Only if it survives:** stage 2 prices the gap. Fair value is the product of the still-open legs' mids at the same minute. The combo recorder does NOT hold leg prices, so stage 2 needs leg candles from kalshi-pull, with its own job and count. It also needs a separate registration with 1 try.

## Rules it sits under

- **Paper only.** Under the owner's combo rules (docs/POLITICS_RULES.md section 7): any live probe is $2 a combo with a $40 total stop, needs a paper edge of 10c per dollar first, and needs the owner's own popup with the exact spec.
- **Weakness, stated:** a 30 minute poll misses an order that lives seconds. A burst poll after a leg settles would be a recorder change for the owner.

## Amendment 1 (Nov 13, 2026, 02:20Z, before the counter is built and before any combo-data file is opened for this card)

Desk B raised nine readings that could go two ways. All nine are adopted as Desk B proposed, and they are now part of the card:

1. **The week.** 80% is counted over the seven days: at least 269 of 336 scheduled runs (48 a day), AND no single UTC day with fewer than 24 runs.
   - A run counts as completed when its folder has a coverage row with `stopped_early` = 0 and a quotes file.
   - `list_complete` is printed as a share, not required.
   - If more than one week qualifies, the earliest is used.
2. **A leg with a result other than yes or no** (scalar or void) settled at or before t: the snapshot is NOT eligible. Counted and printed apart.
3. **A leg that is unknown:** the leg pull does not return it, it has a result but no settlement time, or its string has no side. The snapshot is NOT eligible, and it is counted and printed apart as "leg unknown".
4. **A leg settled on C's side less than 60 seconds before t** does not satisfy (b). It counts as settled for (d) and for the still-unsettled set.
5. **Rounding.** The ask is rounded UP to the whole cent first, then compared with 0.87, using a 1e-9 tolerance (0.8701 becomes 0.88 and is out).
6. **Independent combo with a resting ask.** A (still-unsettled set, UTC day of t) pair counts if ANY of its eligible snapshots that day has a resting ask. The same set on two days counts twice. The number of distinct sets over the whole week is printed as well.
7. **Median ask.** Taken over independent combos, using each one's FIRST eligible snapshot with a resting ask, not its lowest.
8. **Leg-list share.** The share of ALL quote rows of the week whose leg string is present and not cut, printed with the counts of empty and cut strings.
9. **Book figure.** For eligible rows whose ticker is in the same run's books file: the count with 1 minus `no_bid_px_1` at most 0.87 (same rounding) and `no_bid_sz_1` of 1 or more, and the count of independent combos by that test, printed beside the list figures. The kill line reads the list figure only.

**Added limits:**
- The leg pull needs the runner to allow `/markets` with a `tickers` parameter (the Chief of Staff's change).
- Desk B counts the distinct legs exactly from the files only after Auditor B's CLEAN.
- **This count reads leg RESULTS to classify snapshots.** It scores nothing, but it is not blind to leg outcomes. Any stage 2 registration must say so and must fix its own held-out block by a date constant before the gap is priced.
