# RACELOCK result (2026-10-30, research only)

Registration: `workers/RACELOCK_REGISTRATION.md` (pushed before scoring; amendment A1 pushed after T1 and before any result was read).
Code `src/scalper/racelock.py`, fetcher `src/scalper/racelock_fetch.py`. Series `KXCRYPTOLEAD15M`, 6,343 events (31,715 markets).
Look = candle ending 540 s before the close, fill = the next candle (480 s). 10 contracts a leg is MODELLED (one minute candles carry no
sizes). N: about 728,662 before, **about 728,666 after** (bar z 5.27).

## Information look (counted, not a rule; quotes are candle closes)

| window | events | all five legs quoted (fill candle) | median sum of YES asks (p10 / p90) | median sum of YES bids (p10 / p90) | median spread a leg |
|---|---|---|---|---|---|
| discovery | 3,235 | 2,278 (70%) | 1.23 (1.15 / 1.29) | 0.85 (0.75 / 0.94) | 8c |
| validation | 1,896 | 1,668 (88%) | 1.25 (1.17 / 1.31) | 0.85 (0.75 / 0.94) | 8c |
| holdout (counts only) | 1,212 | 1,124 (93%) | 1.20 (1.13 / 1.27) | 0.87 (0.80 / 0.94) | 6c |

The books are over-round by about 20 to 25 points on the ask side and under-round by about 15 points on the bid side, as the thin-maker
mechanism predicts. Legs with no valid quote at the fill candle in discovery: BTC 366, ETH 435, SOL 258, XRP 240, HYPE 154 (of 3,235);
a lock needs all five quoted, and 30% of discovery windows lack at least one (validation 12%, holdout 7%, so coverage improved over time).
32 events have no YES result at all (zero YES, perhaps voided); 6,311 have exactly one.

## T1 RACE-DUTCH (fill candle, after fees)

| window | windows with five quoted | YES locks C=10 (volume above 0 on all legs) | size, cents a set | NO locks C=10 (volume above 0) | size, cents a set | at fees x1.2 (YES / NO) |
|---|---|---|---|---|---|---|
| discovery | 2,278 | 5 (3) | mean 1.92 (max 3.7) | 4 (2) | mean 0.67 | 5 / 2 |
| validation | 1,668 | 1 (1) | 1.30 | 0 | none | 1 / 0 |
| holdout (counts) | 1,124 | 0 | none | 0 | none | 0 / 0 |

At C = 1 there is 1 YES lock in discovery (1.0c) and none elsewhere. Largest lock in dollars: $0.37 on 10 sets. All 10 lock events
had exactly one YES result. A lock is therefore a rare, tiny event: about 1 window in 400 at the fill candle (6 YES locks of 3,946
windows), a few cents on 10 sets, summing to under $1.50 over 10 weeks, on a modelled 10 contract fill a leg at the touch on a
book with a median of 294 contracts a market, five legs sent one after another with leg risk. The registered prediction said zero
fillable locks; that was wrong in count (3 and 2 fillable in discovery, 1 in validation) and right in substance (nothing worth a trade).
Registered words: the kill rule's FALSIFIED needs zero fillable locks, and there are not zero; the NOT_YET_FALSIFIED clause (exists in
validation at fees x1.2 and fillable) is technically met by one validation event (10-15 05:15 CT region, 1.3c a set). I report that as it
stands.

**T1 verdict: NOT_YET_FALSIFIED on the registered words (6 tiny fillable-looking locks, 1 in validation), with no economic content.**
Zero is not the finding; the finding is that locks are about 1 in 400 windows and worth cents. Not recommended even for a forward quote
check beyond the one fact that a live recorder with sizes could tell whether those legs are really hittable.

## T2 RACE-OVERROUND-SIDE (NO on the padded name at the next candle, held)

Run on a judgement, not the letter of the gate (amendment A1). Holdout not printed (both earlier windows fail).

| window | events with exactly one YES | trades | no fill (price outside 15c to 85c) | look incomplete | win rate | mean fill | gap | PF C=10 | net C=10 | PF C=1 | PF x1.2 | PF without zero-volume fill candle (n) | day z |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| discovery | 3,216 | 1,662 | 809 | 733 | 0.5018 | 0.5414 | -0.040 | **0.770** | -$907.39 | 0.755 | 0.759 | 0.742 (864) | -4.30 |
| validation | 1,888 | 1,379 | 361 | 147 | 0.4960 | 0.5342 | -0.038 | **0.775** | -$735.37 | 0.760 | 0.764 | 0.823 (542) | -5.02 |

The prediction was NO wins at least 3 points more often than its price; the result is 4 points LESS often, both windows. The padded
leg is the widest-spread leg, and a NO bought at 1 minus the bid pays that spread: the over-round is a spread cost, not a mispricing a
NO buyer can collect. My written expectation (PF 0.85 to 1.05, FALSIFIED) was too kind; the loss is larger and statistically solid.

**T2 verdict: FALSIFIED** (discovery PF 0.77 at n = 1,662, validation PF 0.775 at n = 1,379).

## Verdicts

- T1 RACE-DUTCH-YES and -NO: NOT_YET_FALSIFIED on the registered words, with a size too small to trade (cents a set, 1 in about 400 windows).
- T2 RACE-OVERROUND-SIDE: FALSIFIED.
- The pooled Dutch-book idea on this series: no usable lock. The books are 20c over-round on the ask side; the cost of the structure
  is the spread, which the five thin books pad on every leg.

## Proposed README section (for the lead to merge; I did not edit README.md)

> **RACELOCK (2026-10-30, Coin Race `KXCRYPTOLEAD15M`, 6,343 events, Dutch-book and over-round structure, no direction view).** Five
> mutually exclusive YES markets; at 9 minutes left the five asks sum to a median 1.23 to 1.25 and the five bids to 0.85 (spreads 8c a
> leg), so the structure is over-round, not exploitable. T1 (buy all five YES, or all five NO, at the next candle, after fees, 10 contracts a leg
> modelled): 6 YES and 4 NO locks in 3,946 windows with all five legs quoted (1 in about 400), 0.1c to 3.7c a set, under $1.50 in total,
> one of them in validation; NOT_YET_FALSIFIED on the registered words, with no economic content. T2 (NO on the leg with the largest ask
> above its normalised mid share, held): PF 0.77 discovery (n 1,662) and 0.775 validation (n 1,379), win rate 4 points below fill,
> FALSIFIED. N about 728,666.
