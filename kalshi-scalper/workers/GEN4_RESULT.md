# GEN4 result (V2 worker, 2026-10-29, research only)

Registration `workers/GEN4_REGISTRATION.md` (commit 0c613bc, pushed before any outcome was read). Discovery survivors frozen in `studies/gen4_survivors_FROZEN_2026-10-29.json`, sha256 `1bddf5ff9637439af00145fb4c9cd1e74381d242e3f85a67afc84bf410549530`, committed and pushed as 6a38d80 BEFORE validation was built. Validation read once. Code `src/scalper/gen4.py`; printouts `studies/gen4_discovery_result_2026-10-29.txt`, `studies/gen4_validation_result_2026-10-29.txt`. Data `origin/quote-data` at b7dc9cbe8 for both stages (no newer commit existed at the validation read). Nothing in the grammar, split or screens changed after scoring.

## Funnel (Bitcoin, KXBTC15M)

| Stage | Count |
|---|---|
| Discovery windows / dates | 149 windows on 5 dates (Oct 22 to 26); 13,198 eligible poll-side rows |
| Generated | 18,208 (17,898 distinct canonical forms) |
| Distinct (20+ trades, entry-set Jaccard at most 0.9 within an exit) | 5,000 |
| Discovery PF1 over distinct | median 0.79, 95th percentile 1.72 |
| Passed discovery (PF1 1.5, 40+ trades, 4+ dates, x1.2 net above 0) | 113 |
| Validation windows / dates | 107 windows on 3 dates (Oct 27 to 29) |
| **Passed validation** (PF1 1.3, 20+ trades, 2+ dates, x1.2 net above 0, latency PF 1.0) | **51 of 113 (45.1%)** |
| Control: discovery failures with 40+ trades passing the same validation screen | 233 of 1,869 (12.5%) |
| Family control rule (survivors at least control + 5 points) | met |

**Gold: `NOT_RUNNABLE`** on this split (0 gold windows before Oct 27; gold is recorded from Oct 28 15:45 UTC). The registered gold split (discovery to Nov 3, validation Nov 4 to 6) runs with the same code (`market="gold"`, spot features dropped) after Nov 6.

## Best 10 by validation PF (all 1 contract fills at the recorded ask; PF at C = 1, in brackets C = 10)

| id | side | entry window | conditions | exit | discovery PF n | validation PF (10c, x1.2, latency) n | val mean, z | mean ask | trades/week* |
|---|---|---|---|---|---|---|---|---|---|
| B01 | FAV | 150-45 s | lsz_ask <= 7.78, zd >= -1.58 | 30 s | 2.13 (2.24) n 46 | 2.64 (2.77, 2.57, 2.64) n 35 | +12.2c z 2.42 | 0.70 | 82 |
| B02 | FAV | 150-60 s | imb >= -0.428, zd >= -2.07 | 30 s | 2.09 (2.21) n 51 | 2.40 (2.51, 2.33, 2.37) n 39 | +11.6c z 2.31 | 0.70 | 91 |
| B03 | NO | 150-20 s | dm5 <= 0, sp15 >= -0.195, zd >= -0.35 | 5 s | 1.62 (1.71) n 40 | 2.39 (2.52, 2.35, 2.35) n 33 | +14.0c z 2.13 | 0.57 | 77 |
| B04 | FAV | 150-45 s | ask >= 0.17, lsz_ask <= 8.07, lsz_bid <= 8.05 | hold | 2.04 (2.03) n 41 | 2.27 (2.27, 2.22, 2.24) n 32 | +13.2c z 2.04 | 0.69 | 75 |
| B05 | NO | 120-10 s | sp30 >= 0.53 | 5 s | 1.78 (1.89) n 41 | 2.18 (2.40, 2.13, 2.16) n 37 | +8.9c z 1.68 | 0.31 | 86 |
| B06 | NO | 150-45 s | sp30 >= 0.53, spread <= 0.01 | hold | 1.54 (1.59) n 52 | 2.08 (2.16, 2.05, 1.98) n 41 | +9.6c z 1.78 | 0.38 | 96 |
| B07 | NO | 150-20 s | sp15 >= 0.341, vol <= 0.311 | 5 s | 1.68 (1.77) n 43 | 2.08 (1.91, 2.06, 2.10) n 24 | +10.9c z 1.39 | 0.37 | 56 |
| B08 | FAV | 150-20 s | imb >= -0.428 | 5 s | 2.24 (2.28) n 52 | 1.99 (1.88, 1.94, 1.97) n 39 | +10.4c z 1.85 | 0.70 | 91 |
| B09 | NO | 120-20 s | sp30 >= -0.0683 | hold | 1.51 (1.55) n 49 | 1.94 (1.84, 1.90, 1.92) n 40 | +8.4c z 1.52 | 0.35 | 93 |
| B10 | FAV | 150-120 s | sp30 <= 2.26, sp5 <= 0.353 | 30 s | 1.79 (1.93) n 46 | 1.93 (2.01, 1.88, 1.90) n 33 | +9.3c z 1.59 | 0.71 | 77 |

*Trades a week at the recorder's current coverage (about 36 of 96 windows a day), from validation n / 3 days x 7. Features are side-relative (signed toward the side bought): `zd` spot distance to the strike in volatility units, `sp5/15/30` spot move in bp, `dm5` the side's mid change over 5 s, `imb` bid-minus-ask size imbalance, `lsz_*` log1p size.

## What the 51 passes are (read this before the table)

- **Two bets, not 51.** 41 are FAV rules whose entries are almost all at the FIRST recorded poll (mean 142 to 149 s left): buy the side priced 50c to 85c about 2.5 minutes before the close. Greedy clustering of validation entry sets (Jaccard above 0.5) gives 8 clusters; the largest holds 33 strategies. The unconditional core, FAV at the first poll 150 to 120 s, hold, scored as information (1 try): **discovery PF1 1.61 (n 50, win 80% at a mean ask of 0.70), validation PF1 1.57 (n 35, win 80% at 0.70)**. The conditions add little to that core, which is why the control rule is met: discovery mostly selected "the favourite at 150 s", and that core was positive in both windows. The same rule at 90 to 60 s was PF 0.76 and 0.59, so the effect, if real, is specific to about 2.5 minutes and fades by 1.5 minutes. **The lead should decide whether this sits under the owner's ban on L1 and its variants** (a favourite buy near the close, at 50c to 85c instead of 88c to 97c); the registration's 85c cap follows AUTO3's precedent, nothing more.
- The other 10 (8 NO, 2 DOG) are spot momentum: buy the side the Coinbase/Kraken/Bitstamp proxy has moved toward over 15 to 30 s. YES settled 47.7% (discovery) and 44.9% (validation), so the NO lean is mildly helped by drift; the 2 DOG rules carry no such lean.
- Same-poll and next-poll (latency) fills give the same PF to within 0.1 in every pass: the book does not move in 0.6 s, so latency is not what limits these.
- Deflated z: the best validation z is 2.42 on 35 trades against the RULES bar of 5.19 for N about 475,600. Against the RULES bar every pass is `NOT_ENOUGH_DATA`; only FORWARD windows can change that.

## Forward ledger

52 files written to `workers/candidates/` in FWDLEDGER's format (no README existed; format taken from `REF_L1_GOLD.json` and `scalper/fwdledger.py`): `GEN4_B01` to `GEN4_B51` (stage `validation`) and `GEN4_REF_FAV150` (stage `reference`, the unconditional core above, so the ledger shows whether the conditions add anything). Source `quotes`, freeze `2026-10-30T00:00:00Z`, evaluator `scalper.gen4:evaluate` (rebuilds the window's features, including strike and spot proxy, from the recorder folders of its date). Checked: the evaluator reproduces the validation figures exactly for B01 to B03 (35/2.64, 39/2.40, 33/2.39), and a test run of `fwdledger.run` on B01 and the reference with an earlier freeze, written to scratch only, gave 34 trades each (PF10 2.67 and 1.51). None of these is a candidate in the owner's sense; the falsifier comes later.

## N added

2 x 18,208 generated (two fill models each) + 1 (the reference core) = **36,417**. Running count about 439,160 + 36,417 = **about 475,577**; Bonferroni z bar 5.19.

## Verdict

GEN4 (Bitcoin): 51 rules `NOT_YET_FALSIFIED` at the GEN4 screens and sent to FORWARD; against the RULES bar all are `NOT_ENOUGH_DATA` (best z 2.42, bar 5.19). Prediction check: discovery 113 (predicted 150 to 300, lower), validation 45% (predicted 20% to 35%, higher), control rule met (predicted not met, about 75%): wrong in the strategy's direction, and the reason is one shared core (the favourite at 150 s), not 51 independent findings. GEN4 (gold): `NOT_RUNNABLE` until the registered gold split has data (after 2026-11-06).
