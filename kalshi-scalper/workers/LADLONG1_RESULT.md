# LADLONG1 result (V2 worker, 2026-10-31, research only)

Registration `workers/LADLONG1_REGISTRATION.md` (commit dbf1bf1, pushed before any outcome was read). Code `src/scalper/ladlong1.py`
(`python -m scalper.ladlong1 dv`, run once; nothing changed after the score). Printout `studies/ladlong1_result_2026-10-31.txt`
(aggregates only). Data: `conf2_lad.sqlite` then `lad2.sqlite`, 1,544 hourly KXBTCD closes Aug 24 to Oct 29 (656 discovery, 631
validation, 257 holdout), strikes chosen from the quotes 52 to 55 minutes before the close. **The frozen holdout was NOT read
(no band reached the step that allows it).** Times US Central in words; nothing live touched.

## Genuinely new or a reword (as registered)

A reword of tested cells at another clock, with one new cell. Mirror of TAIL / NEWH4 H3 (buyer's PF 0.64 / 0.72 on the 2c to 6c
longshots, README "Result: NEWH4"); UPnear and DNnear (88c to 94c paid) are a reword of the LADL1 cell (L1's 88c to 97c rule on
KXBTCD, README "Result: LADL1") at the 45 minute clock instead of 10 and 6; the 94c to 98c cells (UPfar, DNfar) and the 45 minute
clock are the new part. NEWH14 I2 is information only; THETA1 and FLB1 are other horizons.

## Verdicts

Mean net is cents per contract at C = 10 after the per-order rounded fee and the spread crossed (UP pays 1 - YES bid, DN pays the YES
ask), fill at the candle after the 45 minute look. z is clustered on hourly events. Bootstrap = 5th percentile of the 30 day net
(720 hourly events resampled, 5,000 draws) at C = 10 in dollars.

| Band (buy) | Window | Trades / events | Win vs paid | Mean net C10 / C1 / x1.2 | PF C10 | z (event) | Worst event | Worst day | Boot p5 (30d) |
|---|---|---|---|---|---|---|---|---|---|
| UPfar 2c-6c YES mid (NO, paid ~0.967) | disc | 1,085 / 603 | 95.85% vs 96.66% | -1.08 / -1.82 / -1.10 | 0.72 | -1.09 | -$49.19 | -$53.97 (Sep 3) | -$321.86 |
| | val | 1,130 / 593 | 96.99% vs 96.88% | -0.14 / -0.90 / -0.17 | 0.95 | -0.20 | -$29.46 | -$36.72 (Oct 15) | -$165.26 |
| UPnear 6c-12c (NO, ~0.918) | disc | 731 / 550 | 92.61% vs 91.93% | +0.15 / -0.39 / +0.06 | 1.02 | 0.13 | -$29.45 | -$37.44 (Sep 14) | -$134.29 |
| | val | 687 / 526 | 93.60% vs 91.67% | +1.37 / +0.85 / +1.27 | 1.25 | 1.35 | -$19.27 | -$23.94 (Oct 13) | -$22.27 |
| DNnear 88c-94c (YES, ~0.926) | disc | 687 / 538 | 93.16% vs 92.52% | +0.13 / -0.41 / +0.05 | 1.02 | 0.11 | -$28.05 | -$24.32 (Sep 15) | -$129.89 |
| | val | 649 / 511 | 92.14% vs 92.64% | -0.99 / -1.55 / -1.07 | 0.86 | -0.82 | -$28.33 | -$39.94 (Oct 12) | -$220.53 |
| DNfar 94c-98c (YES, ~0.970) | disc | 1,028 / 611 | 96.98% vs 97.01% | -0.28 / -1.04 / -0.30 | 0.90 | -0.41 | -$19.73 | -$41.34 (Aug 31) | -$154.54 |
| | val | 1,101 / 595 | 96.64% vs 97.02% | -0.62 / -1.39 / -0.64 | 0.80 | -0.94 | -$29.55 | -$29.80 (Oct 8) | -$210.07 |

Event counts per window all clear the bar (300 discovery, 150 validation), so none is NOT_RUNNABLE. **All four bands: FALSIFIED**
(mean under +0.5c in at least one window; UPfar, DNnear and DNfar are negative in at least one window, UPnear is +0.15c in discovery).
Pooled discovery plus validation: UPfar -0.60c (PF 0.82, z -1.00), UPnear +0.74c (PF 1.12, z 0.96), DNnear -0.42c (PF 0.94, z -0.50),
DNfar -0.45c (PF 0.85, z -0.96); none near the deflated bar (z 5.27 at N 728,677). Information (not tries): both UP wings pooled
-0.58c then +0.43c, both DN wings -0.12c then -0.76c.

## What it says

- **The wings are not rich enough to sell at the ask.** The registered prediction (mean between -0.8c and +0.8c, FALSIFIED) held for
  three bands; UPnear's validation +1.37c exceeds it by 0.6c but its discovery is +0.15c, so it fails the both-windows bar. The
  far-above wing (UPfar) won 95.85% of the time in discovery against the 96.66% paid: the NO side was priced slightly cheaper than
  its frequency, the opposite of TAIL's buyer result (win 2.9% against 4.2%), then 96.99% against 96.88% in validation. So the sign of
  the TAIL premium did not carry to the seller's side at the 45 minute clock and the 52 to 55 minute strike rule; one window of 28
  days is about 45 losing strikes, so it is not a measured reversal either.
- **The tail is the cost.** One bad hour loses $19 to $49 on the strikes of one event; the worst single day is -$24 to -$54 at 10
  contracts per strike, under the registered -$125 limit, so the day-loss limit was never the binding bar. The bootstrap 5th
  percentile of the 30 day net is negative in every window of every band (-$22 to -$322), because a positive-mean version would
  still need the 3% to 7% of losing strikes to arrive on schedule.
- **Zero-volume candles:** far-wing UPfar and DNfar fills are 30% to 40% on candles with no trade (355 and 380 of about 1,100 UPfar
  trades; 338 and 400 of DNfar), but without them the means stay near zero (UPfar -0.49c / -0.02c, DNfar +0.25c / -0.32c).
- **Cost shape:** at C = 1 every band is worse (-0.4c to -1.8c) because the 1 cent fee rounding is a bigger share of a 2c to 12c
  gain; at C = 10 the rounded fee is 0.3c a contract at 97c and 0.6c at 92c.

## Overlap

The hourly strikes are a different ticker from the live Bitcoin 15 minute markets but the same underlying and, once an hour, the
same close. A position here CAN coexist with live L1 or OICORE Bitcoin exposure in the same hour. Paper only; nothing to build.

## Count

N tried: **4** (UPfar, UPnear, DNnear, DNfar). Running count about 728,673 + 4 = **about 728,677**; deflated one-sided z bar **5.27**.
Gold and Ethereum ladders: NOT_RUNNABLE (KXGOLDH candles start 900 s before the close; KXETHD candles start 420 s before the close
and cover Sep 29 to Oct 13), 0 tries.

## Proposed README section (for the lead to merge; this worker did not edit README.md)

## Result: LADLONG1 (sell the far wings of the hourly Bitcoin ladder by buying the other side, held), 2026-10-31

Reopened by the owner (via the main session, Oct 30 evening) as the mirror of TAIL; a go-ahead to test, not a promotion. Registered
first (`workers/LADLONG1_REGISTRATION.md`, commit dbf1bf1), result `workers/LADLONG1_RESULT.md`, code `src/scalper/ladlong1.py`,
printout `studies/ladlong1_result_2026-10-31.txt`. **A reword of tested cells at another clock plus one new cell:** the mirror of
TAIL / NEWH4 H3 (buying the 2c to 6c longshot: PF 0.64 / 0.72), UPnear and DNnear are LADL1's 88c to 97c cell at the 45 minute clock
instead of 10 and 6, the 94c to 98c cells are new. KXBTCD 1,544 hourly closes (Aug 24 to Oct 29, 656 discovery / 631 validation /
257 holdout), strikes chosen from the YES mid 52 to 55 minutes before the close (spread at most 4c; after the G3H1 look-ahead
lesson, `lad1.sqlite` not used), look at 45 minutes, fill at the next candle's ask (UP bands buy NO at 1 - bid, DN bands buy YES),
one contract-leg per strike, held, fee 7% x p x (1-p) rounded up per order. **Four bands, four tries, all FALSIFIED:** C = 10
mean net per contract discovery / validation: UPfar (YES mid 2c to 6c, buy NO) -1.08c / -0.14c, PF 0.72 / 0.95; UPnear (6c to 12c)
+0.15c / +1.37c, PF 1.02 / 1.25; DNnear (88c to 94c, buy YES) +0.13c / -0.99c, PF 1.02 / 0.86; DNfar (94c to 98c) -0.28c / -0.62c,
PF 0.90 / 0.80. 603 / 593, 550 / 526, 538 / 511, 611 / 595 events; event z -1.09 to +1.35; worst single event -$19 to -$49 and worst
day -$24 to -$54 at 10 contracts; bootstrap 5th percentile of 30 day net negative everywhere (-$22 to -$322). The far wings are
not rich enough to sell at the ask: UPfar won 95.85% then 96.99% against 96.66% and 96.88% paid, so TAIL's buyer-side shortfall did
not carry to the seller after the spread and fee. The holdout was not read. Gold and Ethereum ladders NOT_RUNNABLE (candles start
900 s and 420 s before the close). N +4; running count about 728,677 (z bar 5.27). A position could coexist with live L1 or OICORE
Bitcoin exposure at the same close; paper only, nothing to build.
