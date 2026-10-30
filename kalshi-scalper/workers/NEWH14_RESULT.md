# NEWH14 result (Strategy Research V2 worker NEWH14, 2026-10-30, research only)

Registration `workers/NEWH14_REGISTRATION.md` (commit b78a0be, pushed before any scoring). Code `src/scalper/newh14.py`
(`PYTHONPATH=src python -m scalper.newh14 dv`, run once). Printout `studies/newh14_result_2026-10-30.txt` (aggregates only).
Data: KXBTCD hourly ladder candles from the local caches `conf2_lad` then `lad2` (1,544 hourly closes Aug 24 to Oct 29, 2026: 656
discovery, 631 validation, 257 holdout), Coinbase BTC-USD 1 minute closes from `newh7.sqlite` (public). Nothing fetched for the
scoring; the only network reads were two pages of Kalshi's public settled market list for the GOLD2 count. Discovery to Sep 21,
validation to Oct 18; the frozen holdout (Oct 18 to 30) was NOT read because nothing passed. Nothing was changed after the score and
nothing was re-run. Times are US Central in words. Nothing live was touched.

## (b) GOLD2: NOT_RUNNABLE on the count (0 tries)

`python -m scalper.newh14 goldd` (close times only; no quote, no result, no GVZ read):

| Source | KXGOLDD daily closes |
|---|---|
| `ladl1.sqlite` (two quote looks per strike at 10 and 6 minutes before the close; no candles; nothing at 14:00 ET) | 38 (Aug 24 to Oct 28) |
| `flb1.sqlite`, `theta1.sqlite` (hourly candles for a few strikes) | 8 each |
| Kalshi's public settled list, two pages, 1,570 markets | **39 distinct close times on 39 days, first 2026-08-24, last 2026-10-29** |

By the standard windows: discovery 15 days, validation 16, holdout 8; **discovery plus validation 31 against the 100 needed.**
The record's two numbers resolve this way: "108 daily events from 2026-04 to 2026-09" (the GOLD2 card, Oct 28) is not KXGOLDD as
Kalshi lists it today (the series' public history begins 2026-08-24; no local file holds any earlier KXGOLDD event); "about 60"
(NEWH4, NEWH10) was an overestimate. The number is 39. **Verdict: NOT_RUNNABLE.** No GVZ was read, no quote joined to a model, no try
spent. At about 22 closes a month the recorder's `ladder.csv` (already polling KXGOLDD near 21:00 UTC) would reach 100 closes around
March 2027, and only if its 14:00 ET quotes are recorded too, which they are not (it polls the last 150 seconds).

## (a) NOVIEW: the structures and the model (as registered)

Two strikes of one KXBTCD hourly event, chosen from the market's own prices at the signal candle (K_hi: YES mid nearest 25c inside
15c to 40c; K_lo: YES mid nearest 75c inside 60c to 85c; both two-sided within 6c), so the structure carries no directional view.
**STRANGLE** = YES at K_hi plus NO at K_lo (pays 1 outside the range, 0 inside). **CONDOR** = YES at K_lo plus NO at K_hi (pays 2
inside, 1 outside). Model arms scan the candles 45 to 30 minutes before the close (first signal wins) and need a 5c edge per set of a
realised-volatility fair value (Coinbase spot, trailing 24 hours of 1 minute returns, zero drift, 60 s settlement average) over the
set's price; the unconditional arm looks once at 45 minutes. Both legs filled at the NEXT candle's asks, held to settlement, fee 7% x C
x p x (1-p) rounded up per order per leg, C = 10 a leg headline. **The one-minute ladder candles carry no sizes, so a 10 contract fill
on each leg is modelled, not observed.**

## Verdicts

| Rule | Discovery: n / PF10 / PF1 / PF x1.2 / day z | Validation: n / PF10 / PF1 / PF x1.2 / day z | Verdict |
|---|---|---|---|
| H1 STRANGLE-RV (buy the wings when the model says the ladder is too narrow) | 434 (28 d) / 0.79 / 0.75 / 0.77 / -2.60 | 431 (27 d) / 0.69 / 0.66 / 0.68 / -3.82 | **FALSIFIED** |
| H2 CONDOR-RV (buy the middle when the model says the ladder is too wide) | 154 (26 d) / 0.83 / 0.79 / 0.81 / -1.07 | 149 (26 d) / 0.80 / 0.76 / 0.78 / -1.28 | **FALSIFIED** |
| H3 CONDOR-ALWAYS (buy the middle every hour: the variance risk premium) | 606 (28 d) / 0.98 / 0.94 / 0.96 / -0.24 | 551 (27 d) / 1.07 / 1.03 / 1.05 / +0.73 | **FALSIFIED** |

Net at C = 10 a leg: STRANGLE-RV -$255 then -$385 (x1.2: -$277, -$406); CONDOR-RV -$72 then -$80; CONDOR-ALWAYS -$29 then +$92 (x1.2:
-$59, +$65). **Zero volume both ways:** 0 and 1 zero-volume trades per arm (the Bitcoin ladder's 25c and 75c strikes trade every
minute at 45 minutes left); PF unchanged without them. **Funnel** (all 1,544 events, holdout included): 43 closes had no two quoted
wings; 43 had no spot within 2 minutes (the model arms); STRANGLE-RV signalled on 1,032 events, CONDOR-RV on 338, CONDOR-ALWAYS filled
1,396. Median signal lead 2,700 s in every arm (the first candle). Set cost at the fill within 0.3c of the set cost at the signal.
Predictions held: STRANGLE-RV 0.80 to 1.10 predicted, 0.79 / 0.69 seen; CONDOR-RV 0.90 to 1.20, seen 0.83 / 0.80; CONDOR-ALWAYS 0.95
to 1.15, seen 0.98 / 1.07.

## Information looks (counted, never rules)

- **I1 STRANGLE-ALWAYS** (the mirror of H3): PF 0.75 then 0.69 (z -3.43, -4.08) on the same 606 and 551 sets. Buying the wings every
  hour loses about 4c a set; buying the middle every hour wins about 2c a set before costs and about 0c after them.
- **I2 calibration at 45 minutes (1,157 discovery and validation events):** the market's P(inside) = mid(K_lo) minus mid(K_hi)
  against the settled inside share: bucket 0.30 to 0.40 priced 0.361, settled 0.474 (n 95); 0.40 to 0.50 priced 0.456, settled
  0.485 (437); 0.50 to 0.60 priced 0.539, settled 0.569 (534); 0.60 to 0.70 priced 0.626, settled 0.718 (85). **The settlement lands
  inside the 25c to 75c range 3 to 9 points more often than the ladder prices**, so the ladder's wings are rich on average (the
  variance risk premium has the expected sign, and it is the same sign TAIL found at the 2c to 6c wings). The realised-volatility model
  sits on the WRONG side of it: its P(inside) is 6.8 points below the market's on average (sd 13.8), it called the ladder too narrow
  on 60% of events and too wide on 18%, so it bought the wings into a premium that runs the other way.

## What each one says

- **The premium is real and too small to harvest with two taker legs.** CONDOR-ALWAYS collects about +2.8 to +4.8 points of
  probability per set gross (inside share 52.8% and 54.8% against about 50% priced) and pays two fees of 1.3c to 1.4c a contract plus
  two half spreads of about 0.5c to 1c each: about 4c to 5c a set. PF 0.98 / 1.07 is that arithmetic. At fees x1.2 it is 0.96 / 1.05.
  Nothing here is near 1.5, and the day z (-0.24, +0.73) says the premium is not even reliably positive week to week.
- **A trailing realised-volatility model is a worse width than the ladder's.** The 24 hour window carries the busy hours into the
  quiet ones; over the next 45 minutes Bitcoin moved less than that model said in 60% of events, so STRANGLE-RV bought the wings on
  two thirds of all hours and lost 2 to 3 points of probability a set plus costs (PF 0.79 / 0.69). This is LAD1's lesson again, now
  on a structure instead of a strike: the model's disagreements with the ladder are the model's errors.
- **CONDOR-RV** (the model's "too wide" calls) fired only 338 times and did not beat the unconditional condor (0.83 / 0.80 against
  0.98 / 1.07): the model's "too wide" hours were, if anything, the hours that did move. The condition selected against the premium.
- **What would change the arithmetic:** a maker fill on both legs (no spread crossed, the maker fee), which turns the 4c to 5c cost
  into about 2c to 3c against a 3 to 5 point gross premium. That is QUOTE2B's lane on the book recorder (B3s, no earlier than Nov 12)
  and is not registered here; this round says only that the taker version is closed.
- **Gold ladders:** NOT_RUNNABLE for this shape (KXGOLDH candles start 900 s before the close, mostly zero volume; no public gold
  spot series at minute resolution for the sample), 0 tries, as registered.

## Count

N tried: **3** (STRANGLE-RV, CONDOR-RV, CONDOR-ALWAYS) + 2 information looks (I1, I2) = **5**. GOLD2: 0.
Running count about 728,623 (after GEN11) + 5 = **about 728,628**. Deflated z bar 5.27.

## Files

`src/scalper/newh14.py`, `workers/NEWH14_REGISTRATION.md`, this file, `studies/newh14_result_2026-10-30.txt`.

## Proposed README section (for the lead to merge; this worker did not edit README.md)

## Result: NEWH14 (volatility structures across the strikes of the hourly Bitcoin ladder; the GOLD2 count), 2026-10-30

Registered first (`workers/NEWH14_REGISTRATION.md`, commit b78a0be), result `workers/NEWH14_RESULT.md`, code `src/scalper/newh14.py`,
local KXBTCD candles (1,544 hourly closes, Aug 24 to Oct 29) and public Coinbase 1 minute spot; discovery to Sep 21, validation to
Oct 18, holdout to Oct 30 NOT read because nothing passed. **GOLD2 (KXGOLDD against a GVZ-implied distribution): NOT_RUNNABLE, 0
tries.** Counted first, as the brief asked: Kalshi's public settled list has **39 KXGOLDD daily closes in all history (first
2026-08-24)**, 31 in discovery plus validation against the 100 needed; locally 38 closes with two late quote looks and nothing at 14:00
ET. The card's "108 daily events from April" is not this series and "about 60" was an overestimate. **NOVIEW:** two strikes of one
hourly event chosen from the market's own prices (YES mid nearest 25c and nearest 75c), no directional view, both legs at the next
candle's asks, held; the one-minute candles carry no sizes, so a 10 contract fill a leg is modelled, not observed. **STRANGLE-RV**
(buy both wings when a trailing 24 hour realised-vol model prices the ladder too narrow by 5c a set, 45 to 30 minutes left): PF 0.79
on 434 then 0.69 on 431 (day z -2.60, -3.82), **FALSIFIED**. **CONDOR-RV** (buy the middle when the model says too wide): 0.83 on 154
then 0.80 on 149, **FALSIFIED**. **CONDOR-ALWAYS** (buy the middle every hour at 45 minutes, the variance risk premium): 0.98 on 606
then 1.07 on 551 (x1.2: 0.96, 1.05; day z -0.24, +0.73), **FALSIFIED**. Information: the settlement lands inside the 25c to 75c range
3 to 9 points more often than the ladder prices (I2, 1,157 events), so the wings are rich on average, the same sign TAIL found at the
far wings; the gross premium of about 3 to 5 points a set is eaten by two taker fees and two spreads (about 4c to 5c a set), and the
realised-vol model sits on the wrong side of it (6.8 points too wide on average, "too narrow" on 60% of hours), which is LAD1's
lesson on a structure instead of a strike. Buying the wings every hour loses about 4c a set (I1, PF 0.75 / 0.69). The gold ladders
are NOT_RUNNABLE for this shape (KXGOLDH candles start 900 s before the close, mostly zero volume; no public gold spot minutes for the
sample). What could change the arithmetic is a maker fill on both legs, which is QUOTE2B's lane on the book recorder, not registered
here. The taker version of a two-leg volatility structure on Kalshi's Bitcoin ladder is closed on 1 minute candles. N +5; running
count about 728,628 (z bar 5.27).
