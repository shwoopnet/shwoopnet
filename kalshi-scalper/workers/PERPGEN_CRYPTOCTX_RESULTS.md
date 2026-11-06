# PERPGEN CRYPTOCTX results (worker; CRYPTO group, rules with at least one CONTEXT atom; protocol `workers/PERPGEN_PROTOCOL.md`, amendment `workers/PERPGEN_CRYPTOCTX_AMENDMENT.md`)

Engine `src/scalper/perpgen_cryptoctx.py`; ledgers `workers/perpgen_ledger/RUN51..RUN90_CRYPTOCTX.ids.gz` (written before each 500 rule batch was scored); cuts `workers/PERPGEN_CRYPTOCTX_CUTS.json` (sha256 in the `.sha256` file). Stage 1 = discovery at 12 bps a side. Stage counts are rules reaching each bar in order: n>=200, dates>=20, PF>=1.3, mean>0 at 24 bps, both halves PF>1, no date over 25% of net.

## Stage 1 (discovery) per run

| run | N new distinct | fail n<200 | fail dates<20 | fail PF<1.3 | fail mean24 | fail halves | fail date share | survived | clusters (J>=0.9) | best discovery PF with n>=200 (rule) |
|---|---|---|---|---|---|---|---|---|---|---|
| 51 | 5000 | 1443 | 338 | 3217 | 2 | 0 | 0 | 0 | 0 | 1.389 `doi240<=q0.90&vlr15>=q0.90&xeth240>=q0.90\|short\|480` |
| 52 | 5000 | 1452 | 348 | 3196 | 1 | 1 | 1 | 1 | 1 | 1.769 `mtf==2&xeth240>=q0.90\|short\|480` |
| 53 | 5000 | 1485 | 342 | 3171 | 1 | 0 | 1 | 0 | 0 | 1.824 `mtf==2&xbtc240>=q0.90&xbtc60>=q0.10\|short\|480` |
| 54 | 5000 | 1492 | 342 | 3166 | 0 | 0 | 0 | 0 | 0 | 1.268 `fr_avg3<=q0.90&vol240>=q0.25&vol60>=q0.90\|long\|1440` |
| 55 | 5000 | 1500 | 338 | 3162 | 0 | 0 | 0 | 0 | 0 | 1.213 `r15>=q0.90&tvm<=q0.90&xbtc240>=q0.90\|short\|480` |
| 56 | 5000 | 1461 | 364 | 3173 | 2 | 0 | 0 | 0 | 0 | 1.379 `r240<=q0.50&r5>=q0.90&xbtc240<=q0.10\|long\|480` |
| 57 | 5000 | 1534 | 334 | 3130 | 2 | 0 | 0 | 0 | 0 | 1.592 `hod4==4&rng60<=q0.75&xbtc240>=q0.75\|short\|240` |
| 58 | 5000 | 1560 | 390 | 3050 | 0 | 0 | 0 | 0 | 0 | 1.213 `dlo1440>=q0.75&xbtc240>=q0.90&xeth240>=q0.10\|short\|480` |
| 59 | 5000 | 1495 | 331 | 3174 | 0 | 0 | 0 | 0 | 0 | 1.337 `dow==6&r60>=q0.25\|long\|480` |
| 60 | 5000 | 1517 | 355 | 3126 | 1 | 1 | 0 | 0 | 0 | 1.498 `spr<=q0.25&xbtc240>=q0.90\|short\|480` |
| 61 | 5000 | 1518 | 351 | 3131 | 0 | 0 | 0 | 0 | 0 | 1.268 `r15>=q0.50&xbtc240>=q0.90&xbtc60<=q0.75\|short\|480` |
| 62 | 5000 | 1554 | 344 | 3102 | 0 | 0 | 0 | 0 | 0 | 1.268 `rng60>=q0.90&xeth240<=q0.25\|long\|240` |
| 63 | 5000 | 1547 | 337 | 3114 | 1 | 1 | 0 | 0 | 0 | 1.369 `r15>=q0.90&wkend==0&xbtc240>=q0.90\|short\|480` |
| 64 | 5000 | 1507 | 361 | 3131 | 1 | 0 | 0 | 0 | 0 | 1.356 `tvm<=q0.25&volratio<=q0.90&xbtc240>=q0.90\|short\|480` |
| 65 | 5000 | 1483 | 361 | 3152 | 1 | 0 | 3 | 0 | 0 | 1.515 `spr>=q0.25&xeth240<=q0.25&xeth60>=q0.75\|long\|1440` |
| 66 | 5000 | 1468 | 364 | 3166 | 1 | 0 | 0 | 1 | 1 | 1.509 `rel_btc60>=q0.75&xeth240>=q0.90\|short\|480` |
| 67 | 5000 | 1593 | 315 | 3089 | 3 | 0 | 0 | 0 | 0 | 1.420 `dlo240<=q0.25&hod4==2&tvm<=q0.25\|long\|480` |
| 68 | 5000 | 1502 | 317 | 3178 | 2 | 0 | 1 | 0 | 0 | 1.651 `r240<=q0.90&xbtc15>=q0.90&xbtc60<=q0.25\|long\|480` |
| 69 | 5000 | 1543 | 345 | 3109 | 1 | 0 | 1 | 1 | 1 | 1.609 `r5>=q0.75&xeth240>=q0.90\|short\|480` |
| 70 | 5000 | 1589 | 345 | 3066 | 0 | 0 | 0 | 0 | 0 | 1.203 `doi240>=q0.50&hod4==2\|long\|480` |
| 71 | 5000 | 1507 | 350 | 3139 | 3 | 0 | 1 | 0 | 0 | 1.518 `r5<=q0.75&xbtc240<=q0.90&xeth240>=q0.90\|short\|480` |
| 72 | 5000 | 1566 | 349 | 3084 | 1 | 0 | 0 | 0 | 0 | 1.301 `fr_chg<=q0.90&mtf==2&xeth240>=q0.90\|short\|240` |
| 73 | 5000 | 1530 | 338 | 3132 | 0 | 0 | 0 | 0 | 0 | 1.210 `rng60>=q0.90&xbtc240<=q0.10&xbtc60<=q0.90\|long\|240` |
| 74 | 5000 | 1562 | 339 | 3098 | 1 | 0 | 0 | 0 | 0 | 1.378 `dlo240<=q0.50&rng60>=q0.90&xeth240<=q0.25\|long\|240` |
| 75 | 5000 | 1559 | 337 | 3102 | 1 | 0 | 1 | 0 | 0 | 1.656 `dlo1440>=q0.50&dlo240>=q0.25&hod4==2\|long\|480` |
| 76 | 5000 | 1541 | 376 | 3080 | 1 | 0 | 2 | 0 | 0 | 1.760 `r5>=q0.90&xeth240>=q0.90\|short\|480` |
| 77 | 5000 | 1598 | 339 | 3062 | 1 | 0 | 0 | 0 | 0 | 1.369 `xeth240<=q0.10&xeth60>=q0.75\|long\|240` |
| 78 | 5000 | 1518 | 347 | 3131 | 3 | 1 | 0 | 0 | 0 | 1.539 `rng60>=q0.90&xeth240<=q0.10\|long\|240` |
| 79 | 5000 | 1513 | 374 | 3113 | 0 | 0 | 0 | 0 | 0 | 1.225 `dow==2&wkend==0\|short\|480` |
| 80 | 5000 | 1510 | 315 | 3172 | 2 | 0 | 1 | 0 | 0 | 1.565 `dhi240<=q0.90&xbtc60>=q0.90&xeth240<=q0.25\|long\|120` |
| 81 | 5000 | 1533 | 354 | 3113 | 0 | 0 | 0 | 0 | 0 | 1.283 `rel_btc60<=q0.25&xbtc15>=q0.10&xbtc240>=q0.90\|short\|480` |
| 82 | 5000 | 1507 | 345 | 3145 | 2 | 0 | 1 | 0 | 0 | 1.445 `fr_avg3>=q0.90&hod4==2&r240<=q0.50\|long\|480` |
| 83 | 5000 | 1557 | 294 | 3149 | 0 | 0 | 0 | 0 | 0 | 1.283 `xeth240<=q0.25&xeth60>=q0.75\|long\|1440` |
| 84 | 5000 | 1514 | 336 | 3146 | 2 | 0 | 2 | 0 | 0 | 1.643 `xbtc240<=q0.90&xeth240>=q0.90\|short\|480` |
| 85 | 5000 | 1505 | 356 | 3136 | 1 | 1 | 1 | 0 | 0 | 1.434 `hod4==0&r5>=q0.50&volratio>=q0.75\|long\|1440` |
| 86 | 5000 | 1515 | 307 | 3178 | 0 | 0 | 0 | 0 | 0 | 1.219 `dhi1440<=q0.25&tvm>=q0.10&wkend==0\|short\|1440` |
| 87 | 5000 | 1495 | 337 | 3168 | 0 | 0 | 0 | 0 | 0 | 1.210 `dhi1440<=q0.75&xbtc240>=q0.90\|short\|480` |
| 88 | 5000 | 1549 | 354 | 3095 | 2 | 0 | 0 | 0 | 0 | 1.344 `r5<=q0.50&rng60<=q0.50&xeth240>=q0.90\|short\|480` |
| 89 | 5000 | 1506 | 325 | 3167 | 2 | 0 | 0 | 0 | 0 | 1.381 `dhi1440<=q0.10&rel_btc240<=q0.50&vol60>=q0.75\|long\|240` |
| 90 | 5000 | 1552 | 320 | 3127 | 1 | 0 | 0 | 0 | 0 | 1.367 `fr_avg3>=q0.75&hod4==2&vol240<=q0.90\|long\|480` |

## Stage 2 (validation, the 3 frozen survivors, read once at 12 bps a side)

Frozen lists committed first (commit 38aeadf): `workers/PERPGEN_FROZEN_CRYPTOCTX_RUN52.json`, `_RUN66`, `_RUN69` (the other 37 runs froze empty lists). Raw output `workers/perpgen_ledger/cryptoctx_validation.json`.

| run | rule | disc n / PF | val n | val dates | val PF 12 / 5 / 24 bps | PF assumed / flipped funding | halves PF | control PF (reversed) | core mean vs rule mean | fails | label |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 52 | `mtf==2&xeth240>=q0.90\|short\|480` | 265 / 1.77 | 179 | 20 | 0.36 / 0.42 / 0.26 | 0.36 / 0.35 | 0.05, 1.51 | 1.36 | -0.51% vs -0.88% | PF12<1.3, halves, PF24<1, control, core | FALSIFIED |
| 66 | `rel_btc60>=q0.75&xeth240>=q0.90\|short\|480` | 303 / 1.51 | 192 | 27 | 0.44 / 0.51 / 0.35 | 0.44 / 0.44 | 0.24, 0.97 | 1.24 | -0.51% vs -0.86% | PF12<1.3, halves, PF24<1, control, core | FALSIFIED |
| 69 | `r5>=q0.75&xeth240>=q0.90\|short\|480` | 387 / 1.61 | 252 | 27 | 0.47 / 0.55 / 0.35 | 0.47 / 0.46 | 0.28, 0.90 | 1.13 | -0.51% vs -0.72% | PF12<1.3, halves, PF24<1, control, core | FALSIFIED |

Validation survivors 0, clusters K = 0, audit (A1 to A10) and the holdout were not run and not read: no rule reached them, the holdout guard file was never written. All three discovery survivors are the same bet (ETH 240 minute return at its top decile, short, 8 hour hold) and all three LOSE in validation (PF 0.36 to 0.47, first half worst), the reversed direction wins (control PF 1.13 to 1.36, but a control is not a rule and was not tested as one; it is a hint of regime or reversal in a window, nothing more).

## Totals

N for this slice = 200,000 (40 runs x 5,000 distinct rules, RUN51 to RUN90, every ledger line written before its batch was scored). Discovery survivors 3 of 200,000 (3 clusters, all the xeth240 short 8 hour bet); validation survivors 0; audit survivors 0; holdout unread; CANDIDATES 0, LEADS 0, as predicted. About 15 percent of rules contain xgold60 or xus500_60 and cannot trade in discovery (no leader data in the crypto discovery region), counted in N.
