# PERPGEN NONCRYPTO results (gold, silver, copper, US 500, Tech 100, WTI; worker 2026-11-06)

Protocol `PERPGEN_PROTOCOL.md`, disclosures `PERPGEN_NONCRYPTO_AMENDMENT.md`, engine `src/scalper/perpgen_noncrypto.py`, cuts `PERPGEN_NONCRYPTO_QCUTS.json` (sha256 4621bba4bd6b7b183c0499ca3d16ef83e71d308dea48c54ea1bce2264d198d4c). Ledger `perpgen_ledger/RUN<nn>_NONCRYPTO.ids.gz` written before each batch of 500 was scored. Discovery: 5,586 decision rows, 12 bps a side.

| run | seed | N new distinct | stage-1 fails (trades / dates / PF / halves,cost,conc) | reached 200 trades | best discovery PF among rules with at least 200 trades | best PF among rules with 50 to 199 trades (not eligible) | discovery survivors | validation | audit | holdout |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1001 | 5000 | 3958 / 123 / 919 / 0 | 1042 | 0.453 (vol60>=q50|short|240) | 1.050 (dhi240>=q75&pir1440>=q75|short|480) | 0 | not read (no survivors) | none | not read |
| 2 | 1002 | 5000 | 4065 / 114 / 821 / 0 | 935 | 0.429 (r15>=q10&r5>=q75|short|240) | 1.140 (dlo240>=q10&vlr60>=q50&volratio>=q75|short|480) | 0 | not read (no survivors) | none | not read |
| 3 | 1003 | 5000 | 4078 / 103 / 819 / 0 | 922 | 0.418 (fr_chg>=q25&rng60>=q25|short|240) | 1.207 (mtf==3&pir1440>=q75|short|480) | 0 | not read (no survivors) | none | not read |
| 4 | 1004 | 5000 | 4058 / 130 / 812 / 0 | 942 | 0.439 (doi240<=q75&r5>=q10&spr>=q10|short|240) | 1.072 (pir1440>=q75&r1440>=q10|short|480) | 0 | not read (no survivors) | none | not read |
| 5 | 1005 | 5000 | 4125 / 116 / 759 / 0 | 875 | 0.451 (doi60<=q90&vol60>=q50|short|240) | 0.956 (doi60>=q10|short|1440) | 0 | not read (no survivors) | none | not read |
| 6 | 1006 | 5000 | 4165 / 98 / 737 / 0 | 835 | 0.406 (r5<=q50&vlr15>=q25|short|240) | 0.989 (sp<=q90|short|1440) | 0 | not read (no survivors) | none | not read |
| 7 | 1007 | 5000 | 4197 / 107 / 696 / 0 | 803 | 0.425 (r5>=q75|short|240) | 1.024 (r1440>=q75|short|480) | 0 | not read (no survivors) | none | not read |
| 8 | 1008 | 5000 | 4196 / 116 / 688 / 0 | 804 | 0.446 (pir1440>=q10&r240>=q25|short|240) | 0.971 (r15>=q25&r60<=q90&vol240>=q75|short|480) | 0 | not read (no survivors) | none | not read |
| 9 | 1009 | 5000 | 4212 / 90 / 698 / 0 | 788 | 0.403 (doi60>=q50&rng240<=q75|short|240) | 1.148 (dlo240>=q50&fr_last<=q90&pir1440>=q75|short|480) | 0 | not read (no survivors) | none | not read |
| 10 | 1010 | 5000 | 4193 / 101 / 706 / 0 | 807 | 0.416 (fr_avg3<=q75&tvm<=q75|short|240) | 1.184 (pir1440>=q50&spr>=q50&volratio>=q50|short|480) | 0 | not read (no survivors) | none | not read |
| 11 | 1011 | 5000 | 4211 / 98 / 691 / 0 | 789 | 0.407 (r15<=q75&sp<=q25|short|240) | 1.067 (doi240<=q25&volratio>=q50|short|480) | 0 | not read (no survivors) | none | not read |
| 12 | 1012 | 5000 | 4230 / 89 / 681 / 0 | 770 | 0.440 (dhi240<=q75&dlo240>=q25|short|240) | 1.321 (r15<=q50&r240>=q25&vol60>=q75|short|480) | 0 | not read (no survivors) | none | not read |
| 13 | 1013 | 5000 | 4245 / 96 / 659 / 0 | 755 | 0.413 (dlo240>=q10&r5>=q75|short|240) | 1.061 (dhi240>=q75&dlo1440>=q50&rng60>=q50|short|480) | 0 | not read (no survivors) | none | not read |
| 14 | 1014 | 5000 | 4307 / 81 / 612 / 0 | 693 | 0.413 (fr_avg3>=q10&r15<=q90|short|240) | 1.021 (r15>=q25&tvm>=q10|short|1440) | 0 | not read (no survivors) | none | not read |
| 15 | 1015 | 5000 | 4261 / 118 / 621 / 0 | 739 | 0.432 (dlo240>=q10&doi60<=q90&vlr15>=q25|short|240) | 1.116 (vol60>=q50&volratio>=q75|short|480) | 0 | not read (no survivors) | none | not read |
| 16 | 1016 | 5000 | 4296 / 92 / 612 / 0 | 704 | 0.407 (dlo1440<=q90&dlo240>=q25|short|240) | 1.308 (vol240<=q90&volratio>=q75|short|480) | 0 | not read (no survivors) | none | not read |
| 17 | 1017 | 5000 | 4303 / 80 / 617 / 0 | 697 | 0.417 (doi60<=q90&r15>=q75|short|240) | 1.092 (fr_chg>=q10&volratio>=q75|short|480) | 0 | not read (no survivors) | none | not read |
| 18 | 1018 | 5000 | 4302 / 87 / 611 / 0 | 698 | 0.455 (dhi240<=q90&dlo1440>=q10|short|240) | 1.302 (r240>=q25&volratio>=q75|short|480) | 0 | not read (no survivors) | none | not read |
| 19 | 1019 | 5000 | 4268 / 93 / 639 / 0 | 732 | 0.392 (r60>=q10&rng60>=q10|short|240) | 1.057 (fr_last>=q10&pir1440>=q75|short|480) | 0 | not read (no survivors) | none | not read |
| 20 | 1020 | 5000 | 4270 / 90 / 640 / 0 | 730 | 0.415 (fr_avg3>=q10&fr_chg>=q25|short|240) | 1.101 (rng60<=q75&vol240>=q25&vol60>=q75|short|480) | 0 | not read (no survivors) | none | not read |

**Total: 100,000 distinct (rule, NONCRYPTO) pairs scored, ledger lines 100,000 (N exact: `zcat workers/perpgen_ledger/RUN*_NONCRYPTO.ids.gz | wc -l`, all distinct). Discovery survivors: 0.** No frozen list holds a rule (`PERPGEN_FROZEN_NC01..NC20.json`, empty), so validation was not read, no audit ran and no holdout was unlocked.

## What the numbers say
- **Date and trade starvation is the dominant failure:** about 83 percent of rules fail the 200 trade bar (about 47 percent have fewer than 200 signal rows at all); only 14 to 21 percent of rules ever reach 200 trades, and almost all of those are the hold horizons of 4 hours or less. The 8 hour and 24 hour horizons cannot reach 200 trades over about 34 pooled discovery dates (see the amendment); they are in N and are not survivors.
- **Cost is the second:** every rule that reached 200 trades has PF at most 0.46 at 12 bps a side (round trip 0.24 percent plus the recorded spread, against 15 minute to 4 hour moves of gold, silver, copper, indices and WTI that are mostly under 30 bps). Rules between 50 and 199 trades reach PF up to about 1.32, but they are below the sample bar and are not evidence. `dates` fails (200 trades but under 20 dates) are about 2 percent.
- **Held back on purpose:** no bar was lowered; the NOT_ENOUGH_DATA reading applies to the non-crypto group as a whole at this history length (23 to 57 days per ticker). Re-running after the history grows (new cuts, new frozen id) is the way to give it a fair chance.
- **Prediction check:** protocol predicted discovery survivors under 1 percent and zero CANDIDATES. Result: 0 of 100,000; zero CANDIDATES.
- Equity and PF figures are at the placeholder 12 bps a side fee; the 24 bps stress and the flipped funding sign are only evaluated for rules that pass the earlier bars (none).
