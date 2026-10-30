# GEN7 result (2026-10-30): open interest flow generator, 840 to 240 s. Gold FALSIFIED; Bitcoin 2 rules to FORWARD, both mostly GEN6's open interest core one minute earlier

Registration `workers/GEN7_REGISTRATION.md` (commit 43df007, pushed before any row was built). Survivors frozen in `workers/GEN7_FROZEN.md` (commit 9c75af9; sha256 btc b8f09a9a..., gold 3c85fd8d...; control lists hashed there) before any validation row was built. Validation read once. Code `src/scalper/gen7.py`. Fills at the next candle's closing ask, C = 10, fee rounded up per order. Nothing closing on or after 2026-10-28 00:00 UTC was scored.

## Funnel

| | Bitcoin | Gold |
|---|---|---|
| Discovery windows / days (Aug 6 to Sep 20) | 4,357 / 46 | 3,192 / 45 |
| Validation windows / days (Sep 21 to Oct 27) | 3,512 / 37 | 2,453 / 32 |
| Generated (all in N) | 14,408 | 13,211 |
| rejected: exit not allowed / under 30 trades / reference overlap (OICORE, OIDRIFT, REV1, UNDERDOG_180) / L1 variant / duplicate | 809 / 3,431 / 131 / 3 / 5,034 | 786 / 2,742 / 2 / 3 / 4,678 |
| Distinct | 5,000 | 5,000 |
| Discovery PF over all distinct: median / 95th pct | 0.73 / 1.10 | 0.67 / 1.00 |
| Distinct at screen size (100+ trades, 15+ days) | 4,192 | 4,133 |
| Passed discovery (PF 1.5, size, zero volume 20% or less) | 15 | **0** (best at size 1.47) |
| Passed validation (PF 1.3, 50+ trades, stress PF above 1.0) | **2 (13.3%)** | 0 |
| Family control: discovery failures at size passing the same validation screen | 26 of 4,177 (0.6%) | 25 of 4,133 (0.6%) |
| Control rule (survivors at least control + 5 points) | **met** (+12.7 points, on 2 of 15) | not met |
| Validation PF median of the controls | 0.73 | 0.69 |

No entry or exit of any survivor fell on a zero-volume candle (PF with and without flagged trades is identical for all 15). N added: 14,408 + 13,211 draws + 2 information looks (in / outside the OICORE windows, below) = **27,621**; running count about **590,982**, Bonferroni z bar about **5.23**.

## Best 10 (Bitcoin, by validation PF; all 15 discovery survivors are listed in the frozen file)

PF at C = 10. `npv1` = open interest change over the last minute divided by that minute's volume (new contracts per contract traded); `doiN` = open interest change over N minutes; `sdoiN` its share of open interest; `doiw` / `npvw` since the window's first candle. Trades per week from validation (37 days).

| rule | Disc PF (n, z) | Val PF (n, days) | Val C=1 / stress / signal fill | Val z | Trades/wk | OICORE overlap (Jaccard, entries in OICORE windows) | verdict |
|---|---|---|---|---|---|---|---|
| **B01** cheap both 240, npv1 > 0.281, vol > 132k; sell at 60 s | 3.28 (101, 3.42) | **1.80** (126, 34) | 1.60 / 1.76 / 1.92 | 2.28 | 24 | 0.20, 75 of 126 | NOT_YET_FALSIFIED (screens) |
| **B02** cheap both 300 to 240, npv1 > 0.393, doi5 > 97.8k; TP +20c, stop -20c, else sell at 60 s | 1.75 (135, 2.54) | **1.71** (101, 31) | 1.52 / 1.67 / 1.70 | 1.97 | 19 | 0.13, 50 of 101 | NOT_YET_FALSIFIED (screens) |
| cheap both 300 to 240, doi5 > 130k, ETH d2 <= -0.124, doi3 > 39.8k; hold | 1.55 (167) | 1.24 (219) | 1.19 / 1.22 / 1.23 | 0.93 | 41 | 0.15, 73 | FALSIFIED (validation) |
| cheap both 240, doi3 > 69.8k, npvw > 0.324; TP +8c, stop -20c, else hold | 1.85 (136) | 1.15 (132) | 1.04 / 1.12 / 1.15 | 0.49 | 25 | 0.10, 41 | FALSIFIED |
| fav yes 360 to 300, npvw > 0.355, doi3 <= 69.8k, sdoi3 <= 0.261; TP +20c else sell 60 s | 1.55 (207) | 1.13 (65) | 1.01 / 1.10 / 1.12 | 0.32 | 12 | 0.01, 4 | FALSIFIED |
| fav yes 480 to 360, doi3 > 82.2k, npvw > 0.39; sell at 120 s | 1.68 (285) | 1.02 (264) | 0.87 / 0.99 / 0.93 | 0.12 | 50 | 0.03, 17 | FALSIFIED |
| cheap yes 840 to 240, sdoi5 > 0.172, doi1 > 50.6k; hold | 1.51 (257) | 0.94 (405) | 0.90 / 0.93 / 0.91 | -0.50 | 77 | 0.16, 104 | FALSIFIED |
| fav yes 840 to 300, npv5 > 0.307, ETH mid > 0.875; TP +12c else sell 60 s | 1.58 (340) | 0.88 (236) | 0.71 / 0.86 / 0.88 | -0.59 | 45 | 0.02, 10 | FALSIFIED |
| cheap both 240, npv5 > 0.307, bid <= 0.64; TP +3c else hold | 1.56 (117) | 0.80 (94) | 0.73 / 0.77 / 0.84 | -0.65 | 18 | 0.10, 38 | FALSIFIED |
| cheap both 360 to 300, doi3 > 125k, npv3 > 0.052, gold d2 > -0.03; TP +12c, stop -20c, else sell 60 s | 1.50 (104) | 0.76 (158) | 0.67 / 0.74 / 0.81 | -1.16 | 30 | 0.07, 33 | FALSIFIED |

The other five (all favourite rules at 840 to 300 s) had validation PF 0.37 to 0.75. **Every favourite survivor failed validation**, including the three whose mean fill sat in or near L1's band (0.85 to 0.93), so the L1-adjacent question does not arise.

## Distinct bets, or one rule with filters?

**One rule, and it is GEN6's.** Both survivors are the cheap side at 240 to 300 s with a high `npv1` (open interest rising by more than 28% to 39% of the last minute's volume). B01 and B02 share 38 validation windows (Jaccard 0.20 with each other). Their Jaccard with REF_GEN6_OICORE is low (0.20, 0.13) only because OICORE has 333 validation entries; **half to 60% of their own entries are OICORE windows**, entered one to two minutes before OICORE's 180 s look. Information look (2 tries, counted):

| validation | entries in OICORE windows | entries outside |
|---|---|---|
| B01 | n 75, PF **2.04** | n 51, PF **1.11** |
| B02 | n 50, PF **2.08** | n 51, PF **1.24** |

So the part of each survivor that is new (not an OICORE window) is near the control's level of noise; the edge they show is the OICORE windows seen a minute early. Read them as "the open interest jump is already visible at 240 to 300 s in many of the same windows", not as a second bet. Other details: B01 entered only at 240 s, B02 70 at 300 s and 31 at 240 s; YES share 0.52 / 0.58; 38 and 24 fills under 5c (PF without them 1.81 and 1.55); validation net at 10 contracts +$76 and +$53.

**Answer to the brief's question.** Earlier in the window (480 to 840 s) open interest flow carried nothing that survived: no rule with its first look at 480 s or earlier passed validation, and the generator's median discovery PF (0.73) is the spread and fee on a calibrated quote. On gold, open interest flow at any look from 840 to 240 s carried nothing (0 discovery survivors from 4,133 at size, best 1.47; control 0.6%). On Bitcoin the only signal is the late one GEN6 found, reaching back to about 300 s.

## Verdicts

- **Gold: FALSIFIED** (0 discovery survivors; family control not met).
- **Bitcoin family: control rule met** (2 of 15 against 0.6%), but on 2 rules that are mostly OICORE windows. **The two survivors are NOT_YET_FALSIFIED at the GEN7 screens and NOT_ENOUGH_DATA against the RULES bar** (two windows only; day z 2.28 and 1.97 against 5.23). Sent to FORWARD as `workers/candidates/GEN7_B01.json` and `GEN7_B02.json` (stage validation, freeze 2026-10-30T01:00:00Z, evaluator `scalper.gen7:forward_eval`). Parity: `forward_eval` against the history scorer on all 3,512 validation windows for both rules, **0 mismatches** in 7,024 checks (`python -m scalper.gen7 parity btc`). The ledger loads them (0 forward trades so far, as expected).
- **Not independent of REF_GEN6_OICORE**: a forward read of B01 / B02 will share about half its windows with OICORE's; do not count them as separate confirmation.
- **Prediction check.** Bitcoin: 15 discovery survivors (predicted 20 to 120, fewer); validation 13% (predicted 3% to 15%, right); control met (predicted not met, wrong in the strategy's direction, for the same reason as GEN6: a shared condition). Survivors at 240 to 300 s on the cheap side with open interest conditions: as predicted. Gold: 0 survivors (predicted 5 to 60, fewer), control not met (right). Median discovery PF 0.73 / 0.67 (predicted about 0.85 / 0.75, lower).

## For the lead

- Nothing new to promote. The useful finding is negative and positive at once: open interest flow before 5 minutes left is not informative on either market, and on Bitcoin the GEN6 jump is partly visible at 4 to 5 minutes. If a single forward row for "the open interest core at 240 s" is wanted instead of two filtered relatives, it needs its own id and freeze; it was not added.
- FALS4's latency caveat applies the other way here: B01 fills at the 180 s candle's ask, B02 at the 240 or 180 s ask.

## Files

`src/scalper/gen7.py`, `workers/GEN7_REGISTRATION.md`, `workers/GEN7_FROZEN.md`, `workers/GEN7_frozen_btc.json`, `workers/GEN7_frozen_gold.json`, `workers/candidates/GEN7_B01.json`, `GEN7_B02.json`, this file. Row, control and validation files in `data/gen7_*` (not committed).
