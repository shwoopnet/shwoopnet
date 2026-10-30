# NEWH13 result (V2 worker NEWH13, 2026-10-30, research only)

Registration `workers/NEWH13_REGISTRATION.md` (commit 4377c22, pushed by the lead for a clean tree, unchanged from the worker's
text, before any fill quote after a signal or any outcome was read); scorer `src/scalper/newh13.py` (commit 2088ad2, pushed
before the one `dv` run). Printout `studies/newh13_result_2026-10-30.txt` (aggregates only). Nothing was changed after the
score. Fees rounded up per order per leg (C = 10 and C = 1, x1.2 at C = 10). Every fill is the next candle's ask, ending 420 s or
more before the close; held; nothing sold.

**No rule passed discovery, so no validation gate was applied and the frozen holdout (Oct 18 to Oct 30, 153 closes) was NOT
read.** Validation is printed for the record, as registered.

## Step 1: the family against the ledger (the untested list)

- 15 minute book against the hourly ladder at the shared close, directional: Bitcoin both legs (**XM1, BLADX**), Ethereum the
  15 minute leg (**XM1**), gold the 15 minute leg (**GLADH**, the ladder read as the wrong price). UNTESTED: the gold LADDER leg,
  run here as **H2**.
- Locks between the 15 minute contract and the hourly ladder: Bitcoin history (**LOCK2H**, 4 of 704 closes, NOT_ENOUGH_DATA);
  LOCK2's forward poll never read. UNTESTED: gold, run here as **H1**; Bitcoin's days before Sep 26, counted here as **I2**.
- Locks across one ladder's strikes (**LADLOCK**, **KINK**, **TAIL**), across events (**ARB1 to ARB5**, **RULES1**), another venue
  (**PM1 to PM3**), consistency as an L1 filter (**CONF1, CONF2, CORR1, LADL1, E4**): TESTED. No try. The 5 level book recorder is new
  data for the first of these: **I1**, information only.
- A Dutch book inside ONE 15 minute market (YES ask plus NO ask under $1): **NOT_RUNNABLE, 0 tries.** Kalshi keeps one book per
  market (YES bids and NO bids); the YES ask is 1 minus the best NO bid, so the two asks sum to 1 plus the spread at every instant
  (the ledger's L14 / O9 / O10 note says the same). A crossed state is matched by the exchange as it arises.
- Kalshi against an options-implied distribution: volatility models (**IV1, LAD1**) TESTED; the model-free cross against Deribit's
  own option prices at the same expiry instant (**DIGI1**, a card never registered) cannot be run in history: Deribit's public API
  keeps nothing of an expired option (probed today: the expired-instrument list holds only the latest expiry; the time-ranged trade
  endpoint returned no option trades for any past hour tried; chart and book-summary calls answer "not found" or "not open").
  Registered as a forward-only candidate **H3**, NOT_ENOUGH_DATA now, 0 outcome reads.

## Verdicts (PF at C = 10; fill at the next candle's ask, held)

| Rule | Counterparty named | Discovery n / PF10 / PF1 / PF x1.2 / win vs cost / day z | Validation n / PF10 / PF x1.2 / win vs cost / day z | Verdict |
|---|---|---|---|---|
| H1 GLOCKH (gold 15 minute YES or NO plus the bracketing KXGOLDH strike's other side, lock of 1c+ after fees at the signal, minutes 1 to 7, both legs filled at the next candle) | the slower of the two quoting bots when Pyth gold moves | 3 (3 d) / 0.22 / 0.20 / 0.21 / 33.3% vs 1.103 per set / -1.03 | 2 (2 d) / 0.28 / 0.23 / 50.0% vs 1.018 / nan | **NOT_ENOUGH_DATA** (7 signal locks in 873 closes; 2 had no fill; of 5 fills only 2 still locked, +10.8c and +2.2c; 3 fills cost $1.08 to $1.31 a set) |
| H2 GLADX-L (the gold LADDER leg bought toward the 15 minute book on a 3c monotonicity violation at the mids, minutes 4 to 7, 5c to 85c) | the ladder's quoters at the strikes next to the 15 minute strike | 10 (7 d) / 1.17 / 1.14 / 1.15 / 40.0% vs 35.6c / +0.21 | 11 (10 d) / 0.64 / 0.63 / 27.3% vs 33.5c / -0.56 | **NOT_ENOUGH_DATA** (24 triggers in 873 closes; 636 closes had no readable bracket within a 6c spread) |
| H3 BTCDIGI-F (KXBTCD closing 08:00 UTC against Deribit's daily call-spread probability, 60 to 30 minutes before) | ladder quoters not reading Deribit's book | no history exists (public API) | | **NOT_ENOUGH_DATA** (forward-only candidate; needs a recorder; about 60 events in two months) |
| H4 Dutch book within one 15 minute market | | | | **NOT_RUNNABLE** (by the exchange's structure, 0 tries) |

Net at C = 10, fees x1.2: H1 -$3.92 and -$0.64; H2 +$2.82 and -$8.62. Signal lock values seen in H1 (cents, before the fill):
1.1, 16.7, 51.6, 1.6, 1.2; at the fill: -30.7, -18.0, +10.8, +2.2, -8.0. The two big signal locks (16.7c, 51.6c) were a stale wide
ladder quote one candle later gone. H2's fill was on average 6c worse than the signal ask (29.8c to 35.6c, 27.6c to 33.5c): the
ladder's quote moves toward the 15 minute book by the next minute, which is the GLADH reading again (the ladder was wrong) but the
taker arrives after it has corrected.

**Zero volume both ways.** H1: 1 of 3 discovery trades and both validation trades had a zero-volume candle (PF without them 0.00
and undefined). H2: 4 of 10 and 2 of 11 (PF without 0.94 and 0.52). The ladder's candles are mostly empty, as NEWH10 found.

## Information looks (counted in N)

- **I1 KXBTCD 5 level book at depth** (book recorder, 16 hourly events, Oct 29 to Oct 30, 108,318 rows, 92,849 adjacent-strike
  evaluations with both strikes polled within 1.5 s): top-of-book crosses before fees **0**; locks after fees **0**; mark
  inversions (the YES bid at the higher strike above the YES bid at the lower one) **52 (0.056%)**, all between 44 and 15 minutes
  before the close, none in the last 15 minutes. At 3 second resolution and 5 levels the hourly Bitcoin ladder is consistent
  across strikes. Two days; a count, no claim.
- **I2 Bitcoin lock count on LOCK2H's unread days** (772 closes Aug 24 to Sep 25, minutes 14 to 1): 17 closes with a signal lock of
  1c+ (2.2%), 25 lock minutes, largest 14.7c, longest run 3 minutes, median best pair -2.2c; minutes 1 to 7 only: 12 closes, largest
  4.5c. LOCK2H saw 4 of 704 (0.6%) on the later days, so the minute-candle lock rate was higher in late August and September and
  fell; neither is confirmable from candle closes.
- **I3 gold lock count over the whole window** (minutes 14 to 1): discovery 7 of 442 pairable closes (1.6%), 17 lock minutes,
  largest 51.6c, longest run 5 minutes, median best -2.7c; validation 8 of 429 (1.9%), 9 lock minutes, largest 14.7c, longest run
  2, median best -3.1c. So gold shows a minute-candle lock about as often as Bitcoin's early days, and H1 says what they are worth
  at the next candle: 3 of 5 cost more than $1.
- **I4 H2's base rate** (the same legs at the first readable candle with no violation by 3c either side): ladder NO at k_hi won
  55% at 54c and 62% at 59c (PF 0.96 / 1.07); ladder YES at k_lo won 53% at 57c and 51% at 57c (PF 0.79 / 0.71, day z -1.57 / -2.14).
  So the gold ladder's near strikes carry no drift that H2 could have ridden; if anything the lower strike's YES is overpriced
  (the 15 minute market's "up" side bought at 57c won 51% to 53%), the same shape as the overpriced longshot elsewhere.

## What it says

- A minute-candle lock between gold's 15 minute contract and its hourly ladder exists about once in 60 top-of-hour closes and is
  usually a stale wide quote in the thin ladder: filled a minute later, 3 of 5 cost more than they pay. With LOCK2H (Bitcoin) and I2,
  the coincident-close lock on minute candles is NOT_ENOUGH_DATA on both assets for the same reason (candles are not simultaneous
  and carry no size); only the recorder's simultaneous quotes (LOCK2's own forward read, in the main session's lane: the quote
  recorder's `ladder.csv` and `quotes.csv` since Oct 28 already hold the last 150 s of the KXBTCD ladder and the 15 minute book at
  every top-of-hour close) can confirm or close it.
- The gold ladder leg traded toward the 15 minute book has no sample: 636 of 873 closes have no bracketing strike quoted within a
  6c spread at minutes 4 to 7, and the 24 triggers were filled 6c worse than their signal. With GLADH (the 15 minute leg), BLADX and
  XM1 (Bitcoin and Ethereum), the 15 minute against hourly ladder family is now covered on both legs for both assets, every cell
  FALSIFIED or NOT_ENOUGH_DATA, and nothing in it survives the next candle.
- At 3 second resolution and five levels the Bitcoin hourly ladder keeps monotonicity (zero crosses in 92,849 pair reads); the
  within-market Dutch book is impossible by construction; the cross-event locks were closed by ARB1 to ARB5. **Arithmetic
  arbitrage on Kalshi's crypto and gold books is closed at every resolution the public data reaches.** What remains in this family
  is forward only: LOCK2 (simultaneous quotes with sizes) and H3 (Deribit's options, which need a recorder and two months).

## Count

**N added: 7** (3 tries: GLOCKH, GLADX-L, BTCDIGI-F registered forward; 4 information looks: I1 to I4; H4 adds 0). Running count
about 700,154 (after GEN10) + 7 = **about 700,161**. Deflated one-sided z bar 5.26.

## Files

`src/scalper/newh13.py`, `workers/NEWH13_REGISTRATION.md`, this file, `studies/newh13_result_2026-10-30.txt`. The book and quote
recorder files were read from origin/quote-data into the scratchpad only; nothing under `data/` was added or committed.

## Proposed README section (for the lead to merge)

## Result: NEWH13 (cross-market consistency and arbitrage: the same event priced twice, gold and Bitcoin), 2026-10-30

Registered first (`workers/NEWH13_REGISTRATION.md`, commit 4377c22), scorer `src/scalper/newh13.py` (commit 2088ad2, before the
score), result `workers/NEWH13_RESULT.md`; local candles plus the public book recorder; discovery to Sep 21, validation to Oct 18,
holdout to Oct 30 NOT read because nothing passed. Family check first: the 15 minute against hourly ladder cross is XM1 and BLADX
(Bitcoin both legs, Ethereum one) and GLADH (gold, the 15 minute leg); coincident-close locks are LOCK2H (Bitcoin history) and the
unread LOCK2 forward; one-ladder locks are LADLOCK; cross-event locks ARB1 to ARB5; the Dutch book inside one market is
**NOT_RUNNABLE** by construction (one book, the YES ask is 1 minus the best NO bid, so the two asks sum to 1 plus the spread) and
got no try; Deribit's public API keeps nothing of an expired option, so a model-free options cross for the 08:00 UTC KXBTCD market
(**BTCDIGI-F**) is registered forward only, **NOT_ENOUGH_DATA** now. The two untested cells: **GLOCKH** (a lock between gold's 15
minute contract and the bracketing KXGOLDH strike at the shared close, 1c+ after fees at the signal, both legs filled at the next
candle, minutes 1 to 7): 7 signal locks in 873 closes, 5 fills, 3 of them costing more than $1 a set, PF 0.22 on 3 then 0.28 on 2,
**NOT_ENOUGH_DATA**; **GLADX-L** (the gold LADDER leg bought toward the 15 minute book on a 3c monotonicity violation at the mids,
minutes 4 to 7, 5c to 85c): 10 then 11 trades, PF 1.17 then 0.64, filled 6c worse than the signal, 636 of 873 closes with no
bracketing strike quoted within 6c, **NOT_ENOUGH_DATA**. Information: the recorded 5 level KXBTCD book (16 events, 92,849
adjacent-strike reads at 3 s) shows zero crosses and 0.056% mark inversions, none in the last 15 minutes (I1); Bitcoin's
minute-candle lock rate on LOCK2H's unread days (Aug 24 to Sep 25) was 17 of 772 closes against 4 of 704 later (I2); gold's is 7
of 442 and 8 of 429 (I3); the gold ladder's near strikes carry no drift (I4, the lower strike's YES won 51% to 53% at 57c).
Arithmetic arbitrage on Kalshi's crypto and gold books is closed at every resolution the public data reaches; the family's
remaining questions are forward only (LOCK2 on simultaneous quotes; BTCDIGI-F with a recorder). N +7; running count about
700,161 (z bar 5.26).
