# EVT1 result: scheduled-event windows on gold and Bitcoin 15 minute markets (run once, 2026-10-30; research only)

Registration: `workers/EVT1_REGISTRATION.md` (pushed before the score, commit 7727ea1). Code: `src/scalper/evt1.py`. Full table:
`studies/evt1_result_2026-10-30.txt` (copy of `data/evt1_result.txt`; history candles only, no live order rows).

## Verdict

- **Powered cells (discovery >= 30 trades and validation >= 20): FALSIFIED.** 32 of 384 side cells were powered (gold: TSY and
  CME_GOLD_SETTLE, cheap side; Bitcoin: TSY, CME_BTC_CLOSE, FUNDING and SETTLE_BTC). **None passes the screen; none has the
  matched-control diff at z >= 2 in both splits.**
- **Every macro release type is NOT_ENOUGH_DATA:** CPI, PPI, JOBS, RETAIL (2 discovery and 1 validation event windows each),
  GDP_PCE (1 and 1), FOMC (1 and 0), CLAIMS (7 and 5), EIA (6 and 5), MACRO0830 "US macro releases at 07:30 CT" (14 and 8),
  MONTHLY0830 (9 and 4), DERIBIT (7 and 5), MAINT (2 and 9 to 11). No side cell of these reaches 30 discovery trades.
- **Screen passes: 0. No candidate written to `workers/candidates/`, so no evaluator was frozen and no parity run was needed**
  (`scalper.evt1:forward_eval` and `parity` exist in the code if a later, separately registered read needs them).
- **N = 480** (384 side cells + 96 L1-read cells). Running count about 591,486 -> about **591,966**.

## The powered cells (PF at C = 10, next-candle ask fill, held; diff = event minus same-slot control, cents a contract)

| market, unit, position, side | D n | D PF | D diff (z) | V n | V PF | V diff (z) |
|---|---|---|---|---|---|---|
| gold TSY before CHEAP360 | 35 | 0.94 | +13.1 (+1.10) | 27 | 1.36 | +12.9 (+1.52) |
| gold TSY before CHEAP180 | 32 | 0.35 | -9.7 (-0.97) | 21 | 1.42 | +26.1 (+2.88) |
| gold TSY after CHEAP360 | 33 | 0.74 | -9.1 (-0.79) | 31 | 0.80 | -20.3 (-1.34) |
| gold CME_GOLD_SETTLE before CHEAP360 | 30 | 1.12 | +10.8 (+1.16) | 26 | 1.65 | -6.4 (-0.66) |
| gold CME_GOLD_SETTLE after CHEAP360 | 31 | 0.54 | -9.7 (-1.20) | 22 | 1.23 | +10.2 (+1.01) |
| BTC TSY before / after CHEAP360 | 33 / 31 | 0.32 / 0.89 | -18.5 (-1.53) / +16.3 (+1.94) | 21 / 28 | 0.76 / 0.88 | +5.9 (+0.61) / -17.7 (-0.97) |
| BTC CME_BTC_CLOSE after CHEAP360 | 30 | 1.35 | +9.5 (+1.06) | 27 | 1.31 | +1.8 (+0.17) |
| BTC FUNDING after CHEAP180 | 67 | 1.74 | +1.1 (+0.19) | 67 | 2.11 | +3.0 (+0.47) |
| BTC FUNDING contain CHEAP180 | 67 | 1.60 | -0.2 (-0.03) | 55 | 1.24 | -1.1 (-0.15) |
| BTC SETTLE_BTC before CHEAP180 | 93 | 1.40 | +15.9 (+2.87) | 72 | 0.94 | -3.7 (-0.59) |
| BTC SETTLE_BTC before FAV360 | 47 | 0.87 | -5.8 (-0.95) | 36 | 99 (0 losses) | +13.7 (+2.06) |
| BTC SETTLE_BTC after FAV360 | 53 | 1.07 | -7.9 (-2.35) | 40 | 0.57 | -6.8 (-1.01) |
| BTC SETTLE_BTC after CHEAP180 | 83 | 1.68 | +4.8 (+0.91) | 79 | 2.21 | +6.7 (+1.08) |
| BTC SETTLE_BTC after FAVMID180 | 50 | 0.33 | -15.9 (-1.69) | 45 | 0.35 | -15.4 (-1.59) |

(The other 17 powered cells: |diff z| < 1.7 in both splits; see the full table.) **Reading.** The only cells with PF above the bar in
both splits (Bitcoin cheap side at 180 s around funding times and SETTLE_BTC, PF 1.6 to 2.2) are not event effects: the same rule's
matched control has PF 1.15 (discovery) and 0.97 (validation), and the event-minus-control diff is +1c to +7c at z 0.2 to 1.1. That is
the general Bitcoin cheap-side-at-180 s pattern already on the forward ledger as `REF_BTC_UNDERDOG_180`, not something the funding
clock adds. Every cell that reaches z >= 2 in one split flips sign or vanishes in the other.

Chance check: 56 of 768 split-cells have |z| >= 2 (7.3%; many are 1 to 4 trade cells whose z means nothing), and 0 cells have z >= 2
in both splits, as predicted. Zero-volume: no powered-cell trade had a zero-volume signal or fill candle (PF with and without is the same).

## L1 read (does L1's own rule lose more often in event windows?)

L1's rule (0.88 to 0.97 at 360 s, signal-ask fill, held), loss rate against the same matched control. **No unit x position reaches
z >= 2 in either split** (largest +1.54: Bitcoin SETTLE_BTC after, discovery 5.7% against the slot control, validation +8.5 points
z +1.17). The macro releases cannot answer it: L1 entered 0 to 12 times per position per split in gold and 0 to 5 in Bitcoin around
8:30 ET releases (e.g. Bitcoin MACRO0830 contain: 1 loss in 4 entries in each split, z +1.15; gold MACRO0830: 0 losses in 4 to 12),
and FOMC windows held 0 or 1 entries. **There is no evidence here for an event skip rule, and not enough data to rule one out for
the macro releases.** At CAL's rate, a forward record reaches a powered macro read (300 entries on 30 release days) only around
mid December 2026 pooled over all series, about a year on gold and Bitcoin alone.

## Disclosures

- Daily-recurring "settlement" types (CME gold settle, CME Bitcoin close, funding) are compared with other slots of the same days,
  so they are close to time-of-day tests (MKTTIME1, HOURCLOSE); stated in the registration.
- CME and Deribit schedules were added by their official recurring rule (generated in code, not new CSV rows); Labor Day skipped.
- Slot-matched controls are thin per slot (about 30 to 45 days), and the control SE is included in z. A few cells show a diff of 0
  where the event and its slot control both had no loss.
- Only discovery and validation were read; nothing closing on or after 2026-10-28 was touched.
