# OICOREX1 result: the Bitcoin open interest core on the other 15 minute markets (2026-10-31)

Registered first and pushed before any scoring (`workers/OICOREX1_REGISTRATION.md`, `workers/OICOREX1_INVENTORY.md`, `workers/OICOREX1_thresholds.json`), scored once with `src/scalper/oicorex1.py` (`python -m scalper.oicorex1 score`; it refuses a second run). Rows, fills, fees and the score come from `gen6.window_rows`, `gen6.trades`, `gen6.nets` and `gen6.score`; nothing is re-implemented. Parity: the Bitcoin row reproduces GEN6 exactly (discovery 222 / PF 2.28, validation 333 / PF 1.85, z 4.53). Fees 7% x C x p x (1-p) rounded up per order, C = 10 headline. Splits: discovery 2026-08-06 to 2026-09-21, validation 2026-09-21 to 2026-10-28 (UTC close time).

**For the owner, plainly.** Even a hit would have been a capped probe like OICORE, not a finding. There is no hit: all eight markets are **FALSIFIED**. The core worked on Bitcoin and on no other market.

## Verdicts

| market | threshold (doi >) | discovery n / PF / z | validation n / PF / z | PF at fees x1.2 (disc / val) | PF at C = 1 (disc / val) | verdict |
|---|---|---|---|---|---|---|
| KXBTC15M | 86299.56 | 222 / 2.28 / 4.41 | 333 / 1.85 / 4.53 | 2.26 / 1.82 | 2.16 / 1.75 | reference (GEN6) |
| KXDOGE15M | 2993.33 | 182 / 1.36 / 1.22 | 396 / 0.97 / -0.19 | 1.35 / 0.96 | 1.30 / 0.92 | FALSIFIED |
| KXXRP15M | 4666.15 | 185 / 1.09 / 0.49 | 401 / 1.19 / 1.41 | 1.07 / 1.17 | 1.04 / 1.12 | FALSIFIED |
| KXNEAR15M | 1139.04 | 215 / 0.92 / -0.32 | 632 / 0.79 / -1.59 | 0.91 / 0.78 | 0.88 / 0.75 | FALSIFIED |
| KXZEC15M | 1531.01 | 209 / 0.68 / -1.62 | 600 / 1.08 / 0.67 | 0.67 / 1.07 | 0.65 / 1.03 | FALSIFIED |
| KXBNB15M | 2980.79 | 179 / 1.23 / 0.91 | 169 / 0.94 / -0.28 | 1.22 / 0.93 | 1.20 / 0.90 | FALSIFIED |
| KXHYPE15M | 3712.44 | 175 / 1.20 / 0.93 | 135 / 0.74 / -1.42 | 1.19 / 0.72 | 1.15 / 0.70 | FALSIFIED |
| KXSILVER15M | 5344.83 | 142 / 0.55 / -1.95 | 110 / 0.80 / -1.00 | 0.55 / 0.79 | 0.53 / 0.77 | FALSIFIED |
| KXWTI15M | 7281.53 | 153 / 1.02 / 0.12 | 250 / 1.11 / 0.53 | 1.00 / 1.10 | 0.98 / 1.07 | FALSIFIED |

Bar: PF at least 1.5 in both stages (C = 10), PF over 1.0 at fees x1.2, n at least 100 / 50; z bar 5.27 (N 728,685). No market passed the PF test in both stages, so none reached the z bar, and the holdout (closes on or after 2026-10-28) was NOT read for any market.

Dogecoin (named by the owner): discovery PF 1.36 (n 182, z 1.22) fades to 0.97 in validation (n 396, z -0.19). XRP (named): 1.09 then 1.19 (z 0.49, 1.41), both under 1.5. Bitcoin wins 29% / 28% at an average fill of 17.8c / 19.2c; the others win 13% to 36% at fills of 18c to 31c. Closest to a pattern: Dogecoin, BNB and HYPE are above 1.2 in discovery and below 1.0 in validation (the same decay the window series shows everywhere in this project); ZEC is the reverse (0.68 then 1.08). Zero-volume split (`pf_nozv`) changes nothing: same PF to two decimals.

## Inventory in one paragraph

Usable open interest (present at the -360 and -180 candles in at least 97% of windows and moving) and a full discovery period: Dogecoin, XRP, Solana, BNB, HYPE, ZEC, NEAR, silver, WTI, copper, natural gas. The four rate markets have no usable open interest (80% or more of windows null, flat); Brent, AUD, CAD, EUR, GBP, JPY, palladium and platinum have no discovery data (history starts Sep 18 or later), so each is NOT_ENOUGH_DATA. The try cap of 8 left Solana (history ends Oct 22), natural gas and copper unscored, by the registered outcome-free rank. Full table: `workers/OICOREX1_INVENTORY.md`. Gold and Ethereum were not reopened (GEN6/GEN7, SLOTEX-ETH).

## Co-loss with Bitcoin (report, no verdict)

Windows (matched on close time) where Bitcoin's core and the other market's core both fire. "Lost" = that order's net below 0 at C = 10. Expected both-lost = n x Bitcoin loss rate x market loss rate within those windows. Net in dollars at C = 10 per order.

### Discovery

| market | windows both fire | both won | both lost | only Bitcoin lost | only market lost | both lost expected if independent | observed / expected | net Bitcoin | net market |
|---|---|---|---|---|---|---|---|---|---|
| KXDOGE15M | 10 | 2 | 5 | 0 | 3 | 4.0 | 1.25 | 31.48 | 0.67 |
| KXXRP15M | 21 | 1 | 14 | 5 | 1 | 13.6 | 1.03 | -7.68 | -1.19 |
| KXNEAR15M | 10 | 0 | 6 | 3 | 1 | 6.3 | 0.95 | 4.83 | -2.32 |
| KXZEC15M | 12 | 0 | 7 | 3 | 2 | 7.5 | 0.93 | 12.28 | 1.65 |
| KXBNB15M | 8 | 1 | 3 | 2 | 2 | 3.1 | 0.96 | 19.20 | 11.05 |
| KXHYPE15M | 7 | 0 | 7 | 0 | 0 | 7.0 | 1.00 | -4.03 | -12.83 |
| KXSILVER15M | 10 | 0 | 7 | 0 | 3 | 7.0 | 1.00 | 11.58 | -27.23 |
| KXWTI15M | 10 | 0 | 6 | 1 | 3 | 6.3 | 0.95 | 22.66 | 1.31 |

Windows where at least 2 of the 9 cores fire (Bitcoin plus the eight): 264, 555 orders, net $116.65 at C = 10.

### Validation

| market | windows both fire | both won | both lost | only Bitcoin lost | only market lost | both lost expected if independent | observed / expected | net Bitcoin | net market |
|---|---|---|---|---|---|---|---|---|---|
| KXDOGE15M | 55 | 4 | 28 | 9 | 14 | 28.3 | 0.99 | 59.70 | -7.91 |
| KXXRP15M | 68 | 7 | 45 | 9 | 7 | 41.3 | 1.09 | 42.50 | 21.85 |
| KXNEAR15M | 73 | 5 | 50 | 8 | 10 | 47.7 | 1.05 | 20.72 | -33.63 |
| KXZEC15M | 77 | 4 | 38 | 18 | 17 | 40.0 | 0.95 | 66.78 | 39.66 |
| KXBNB15M | 29 | 3 | 13 | 7 | 6 | 13.1 | 0.99 | 16.27 | 19.02 |
| KXHYPE15M | 8 | 0 | 5 | 2 | 1 | 5.2 | 0.95 | -3.21 | -2.68 |
| KXSILVER15M | 11 | 1 | 8 | 2 | 0 | 7.3 | 1.10 | -1.96 | 11.91 |
| KXWTI15M | 22 | 1 | 15 | 2 | 4 | 14.7 | 1.02 | 11.10 | -13.69 |

Windows where at least 2 of the 9 cores fire (Bitcoin plus the eight): 759, 1789 orders, net $230.34 at C = 10.

Reading: observed both-lost is 0.93 to 1.25 times the independence figure in discovery and 0.95 to 1.10 in validation, i.e. close to independence (loss rates of 60% to 90% already make most joint windows joint losses). The joint counts are small (7 to 77 windows). This misses the prediction of 1.2 times or more for the crypto markets (only Dogecoin discovery, 10 windows, reaches 1.25). It does not matter for a decision, since no market is worth holding.

## Tries

8 (one per scored market). Running N: about 728,677 + 8 = **728,685** (z bar 5.27). The Bitcoin parity run, C = 1, fees x1.2, the nozv split and the co-loss tables are reports, not tries. The holdout was never read.

## Proposed README section (not applied; README.md was not edited)

```
## Result: OICOREX1 (the Bitcoin open interest core on the other 15 minute markets), 2026-10-31

Registered first (`workers/OICOREX1_REGISTRATION.md`), result `workers/OICOREX1_RESULT.md`, inventory `workers/OICOREX1_INVENTORY.md`, code `src/scalper/oicorex1.py` (gen6 rows, fills and fees unchanged; Bitcoin reproduced 222 / 2.28 and 333 / 1.85). Owner decision "lets go on the other oicore markets". Each market's threshold is its own discovery 90th percentile of doi over all discovery rows, GEN6's derivation (it reproduces Bitcoin's 86,299.56 exactly). Eight markets: Dogecoin 182 / 1.36 then 396 / 0.97, XRP 185 / 1.09 then 401 / 1.19, NEAR 0.92 / 0.79, ZEC 0.68 / 1.08, BNB 1.23 / 0.94, HYPE 1.20 / 0.74, silver 0.55 / 0.80, WTI 1.02 / 1.11 (discovery / validation PF at C = 10): **FALSIFIED, 8 of 8**; no market reached PF 1.5 in either stage and none came near the z bar 5.27, so the holdout was not read. Four rate markets have no usable open interest, and Brent, AUD, CAD, EUR, GBP, JPY, palladium and platinum have no discovery data (**NOT_ENOUGH_DATA**); Solana, natural gas and copper were left unscored by the 8 try cap. Counterparty: none named for any market (MECH1 did not support the Bitcoin story). Co-loss with Bitcoin where both fire: 0.9 to 1.25 times independence on small joint counts. The core is a Bitcoin-only pattern; with gold (GEN6, GEN7) and Ethereum (SLOTEX-ETH) it now fails on every market it was moved to. N +8; running count about 728,685 (z bar 5.27).
```
