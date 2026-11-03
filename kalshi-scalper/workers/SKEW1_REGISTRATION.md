# SKEW1 registration: is the crash tail of the hourly Bitcoin ladder priced differently from the rally tail? (V2 worker, 2026-11-03, research only)

Written and committed BEFORE any settled result of this rule was read. What was looked at to write it: the README ledger, `workers/LADLONG1_RESULT.md`,
`workers/MAKERTAIL1_RESULT.md`, `workers/NEWH4_RESULT.md`, the schema of `data/conf2_lad.sqlite`, `data/lad2.sqlite`, `data/ladders.sqlite`, and
the funnel counts of `python -m scalper.skew1 counts` (candle prices only, `score=False`, no result read). Code `src/scalper/skew1.py`, tests
`tests/test_skew1.py`. Nothing live is touched.

## 1. Duplicate check (said first)

- **LADLONG1** (workers/LADLONG1_RESULT.md): buys the 88c to 98c side (the other side of the 2c to 12c wings), 45 minute look. It DOES split by side, but the
  expensive end; no cheap tail is bought. Not the same trade.
- **NEWH4 H3 TAIL-BTC**: buys the 2c to 6c longshot, YES or NO pooled, 30 minute look, PF 0.64 / 0.72. **It did not split by side** and it stops at 6c.
  Partial overlap of the 3c to 6c cell on the same instrument; the side split, the 6c to 30c range and the distance conditioning are new.
- **MAKERTAIL1**: resting maker bids on 3.5 days of recorded books; saw YES tails PF 0.23 (81 orders), NO tails PF 1.25 (94 orders) post hoc, flagged as
  a hypothesis. It is the source of this card; it is a different execution (resting), a different sample (3.5 days) and not a rule.
- **HRSEAS1, OIHR1, PERPOI1, VOLGAP1, NEWH14 I2, `OICORE_SHAPE_INVENTORY.md`**: cheap-tail trades are only controls or pooled baselines there; none scores
  the crash tail against the rally tail. Result: **NOT a duplicate** (a side split of cheap taker tails at 3c to 30c has not been scored).

## 2. Mechanism and counterparty

Bitcoin returns have downside jumps (liquidation cascades) and slower upside; a ladder quoted near-symmetrically in log distance would underprice the
crash tail (buying NO below spot) relative to the rally tail (buying YES above spot), or the reverse if retail overpays for rally lottery tickets.
Counterparty: whoever sells the far-below-spot NO side cheaply (a symmetric quoter), or the retail buyer of far-above-spot YES. Prior: negative for both
sides after spread and fee (TAIL, LADLONG1), the claim is only that the DIFFERENCE is positive.

## 3. Rule (frozen)

Hourly KXBTCD events, 1-minute-resolution candles from the local data.
- **Look** = the candle ending 25 minutes before the close (T-1500 s). **Fill** = the NEXT candle (T-1440 s) at its ask. Held to settlement.
- **Spot proxy S** (from the ladder itself, no outside price): the strike where the YES mid crosses 0.5 at the look candle, linearly interpolated between
  adjacent strikes with spread <= 10c. No bracket = no trade (NoSpot).
- **(a) DOWN tail:** among strikes K < S that are two-sided (spread <= 6c) at the look with NO ask (1 - YES bid) in [0.03, 0.30], the ONE nearest to S;
  buy NO. **(b) UP tail:** among strikes K > S two-sided with YES ask in [0.03, 0.30], the ONE nearest to S; buy YES. One trade per side per event.
- Fill: the same strike must be two-sided (spread <= 6c) at the fill candle and its ask there <= 0.30 (the hard limit), else no trade. C = 10 contracts,
  fee 7% x C x p x (1 - p) rounded up per order, spread crossed (the ask is paid). x1.2 fee is reported as a cost haircut.
- **Distance conditioning:** sigma_h = population std of the previous 72 hourly log changes of the implied spot S (at least 36, only changes that end at or
  before the previous hour's look), sigma25 = sigma_h x sqrt(25/60); d = |ln(K/S)| / sigma25. Three FIXED bins: d < 0.8, 0.8 to 1.4, 1.4 and up. The
  bin-adjusted difference is the equal-weight mean over bins having >= 20 trades on both sides of the difference of the two sides' means.
  Events with fewer than 36 prior changes are NoSigma and not traded.
- **Data:** `conf2_lad.sqlite` then `lad2.sqlite` (the first file holding a close wins it), settled closes 2026-08-24 to 2026-10-26. **Frozen W3 = closes at
  or after 2026-10-27 00:00Z (184 hourly closes): the loader does not read their results, so they are not opened.** DEV halves: split at the median close of
  DEV events with a usable spot and sigma (printed by the run); H1 before it, H2 at or after. Funnel from prices only: 1,476 closes loaded, 1,249 DOWN and 1,278 UP
  trades pass the quote filters before any result (each side far above 150).
- Ethereum KXETHD (`ladders.sqlite`, 328 closes, about 14 days) is run the same way and is **information only**, not a try.

## 4. The claim and the prediction (before any outcome)

Claim: DOWN minus UP mean net (cents per contract, C = 10, after fee and spread) is positive in both DEV halves, both raw and bin-adjusted, and at least one
side reaches PF >= 1.5 in both halves.
**Numeric prediction:** both sides lose: DOWN win rate 0.5c to 1.5c below its paid price (about 11% vs 12% on a mean paid near 0.12), UP the same or 1c to 2c
worse; PF DOWN 0.70 to 1.00, UP 0.55 to 0.95; difference between -1.0c and +2.0c with the sign not stable across halves; verdict **FALSIFIED**. MAKERTAIL1's side
split came from 175 correlated orders and I expect it to shrink toward zero on 1,200 per side.

## 5. Kill rules and verdicts (frozen)

- **NOT_ENOUGH_DATA:** fewer than 150 DEV trades on either side.
- **FALSIFIED:** neither side has PF (C = 10, after fees) >= 1.5 in BOTH DEV halves, OR the side difference (raw or bin-adjusted) is not positive in both halves.
- **PASS_DEV:** both conditions fine. Only then ask the coordinator before the frozen W3 is opened (one read, same code with `frozen=True`).
- Information, not tries: ETH, per distance bin, per paid band, zero-volume fills, x1.2 fee, paired event z.
- Capped probe spec is written only on a PASS_DEV followed by a W3 pass: 1 contract, hard limit 0.30, one side only, kill after 40 trades if net is negative.

## 6. Ledger

Tries: 2 (DOWN tail, UP tail) at +2 per rule: **N +4**. Expected read: today, 2026-11-03, once (`python -m scalper.skew1 dv`); nothing is changed after the score.
