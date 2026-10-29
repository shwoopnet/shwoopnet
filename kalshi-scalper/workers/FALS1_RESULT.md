# FALS1 result: falsifier for MKTTIME1's gold 20:00 to 24:00 Central block (run once, 2026-10-29, V2, research only)

Registration: `workers/FALS1_REGISTRATION.md` (committed before scoring). 10 tries (running count about 438,915). Script and raw output in the session scratchpad only (`fals1.py`, `fals1_out_mine.txt`, `fals1_out_pub.txt`); no live rows used.

## Verdict: BROKEN, by the registered reproduction check (the 0.10 gate is a knife edge on where window B ends)

The ledger word for MKTTIME1 stays FALSIFIED as it registered. The direction of the effect is robust; the owner's gate (lift of at least 0.10 in every third) is not.

## 1. Independent reimplementation

My code was written from the raw databases before I read `mkttime1.py` or `tstop1.py`. It found 1,682 gold entries, 316 in the block with 25 losses. All entries are CDT (UTC-5). No market had both sides in the band.

| Thirds | A lift | B lift | C lift | Pooled PF all to kept |
|---|---|---|---|---|
| Registered here: equal counts of distinct UTC close dates (cuts Sep 2, Sep 28) | +0.238 | **+0.085** | +0.181 | 1.184 to 1.345 |
| Published: equal counts of close times over ALL 15M series' entries (cuts Sep 2 16:45, Sep 30 05:15 UTC), on the published 1,676 entries | +0.187 | +0.137 | +0.112 | 1.195 to 1.342 |

The second row is an exact match to the published figures: PF 1.439 to 1.626, 1.026 to 1.163 and 1.170 to 1.282, 315 skipped entries, 24 losses. I found three differences:

1. **Universe.** I have 6 extra entries (Aug 7, and four on Oct 12 where `book` and `fresh` overlap). `feat1.build` drops entries that have no candle at t-60 or t-180, and `tstop1.load` drops markets with any null candle.
2. **Thirds.** The published cut uses close times pooled across every 15M series, not gold's own dates. Moving the B/C boundary from Sep 30 05:15 to Sep 28 00:00 (about 2 days) drops B's lift from +0.137 to +0.085, under the gate.
3. **The published z of +0.98 measures something else.** It is the day-clustered z of the per-entry gain of the kept set over the baseline. That tests whether the block's own sum is below zero, not whether the block is worse than the rest. I reproduce it: +0.97 on the published set, +1.16 on mine. My registered statistic is rest minus block, clustered by Central date: **z 1.87 on the published set and 2.03 on mine**, with the block 3.0 to 3.3c per entry worse. Both are far from the deflated bar of about 5.17.

## 2. Robustness (lifts per third: A / B / C)

| Check | Registered thirds | Published thirds | Kill fired? |
|---|---|---|---|
| (a) DST | all entries CDT (UTC-5), history Aug 6 to Oct 27, before the Nov 1 change | same | cannot break it (not a try) |
| (b1) 19-23 CT | +0.153 / +0.167 / +0.199 | +0.106 / +0.159 / +0.198 | no |
| (b2) 21-01 CT | +0.109 / -0.048 / -0.056 | +0.052 / -0.032 / -0.071 | no (the kill needed BOTH shifts to collapse), but the block does not survive moving later: hours 20 to 21 carry it and 00 CT is not bad |
| (c) next candle's ask | +0.213 / +0.087 / +0.179 | +0.155 / +0.144 / +0.115 (B baseline net goes negative, kept net higher) | registered thirds: B under 0.10 |
| (d) 10 contracts | +0.257 / +0.091 / +0.193 | +0.202 / +0.146 / +0.118 | registered thirds: B under 0.10 |
| (e) fees x1.2 | identical to the baseline | identical | no. It changes nothing: at C = 1 the fee rounds to 1c at every price from 88c to 97c, even at x1.2 |
| (f) zero-volume candles dropped | 0 such entry candles | 0 | no (no-op) |
| (g) day-block bootstrap, 2,000 | pooled lift p2.5 / p50 / p97.5: +0.004 / +0.159 / +0.379; share at or below 0: 2.1% | -0.006 / +0.143 / +0.365; 2.9% | no (under 20%). But resampling days within each third, only 23% (registered) and 25% (published) of resamples pass 0.10 in all three |
| (h) permutation within weekday, max over 6 blocks, 1,000 | p 0.060; any block at least the observed lift in each third: 0.003 | p 0.025; 0.010 | no (under 0.10). This does not count the 14 rules times 5 markets MKTTIME1 tried; times 5 markets it is about 0.12 to 0.30 |
| (i) price and spread | block price paid 0.928 vs 0.926 for the rest; spread 0.71c vs 0.79c (the block is NOT pricier or wider). Loss rate 7.9% vs 4.8%. Block minus rest per entry by price bucket: -5.0c, -5.5c, -0.9c (3 of 3 negative) | same signs | no |

Not registered, so information only: the block's whole gap sits in its wider-spread entries. Above the median spread of 0.6c the block is -3.9c per entry against +2.0c for the rest; at or below the median it is +0.2c against +1.1c.

## Reading

- **What broke.** The owner's 0.10-in-every-third gate. Under a split by gold's own dates, B's lift is +0.085. It is also +0.087 at the next candle's fill and +0.091 at 10 contracts. A boundary moved by about 2 days changes pass to fail.
- **What held.** The direction. The lift is positive in every third under both splits, the 3 price buckets agree, the block is not just the high-price or wide-spread entries, the bootstrap rarely reaches zero, and the within-family permutation gives p 0.025 to 0.06. The effect is concentrated in 19 to 23 CT, not 21 to 01.
- **Statistics.** Block versus rest is z about 1.9 to 2.0 in sample on 315 entries and 24 losses. That is far from the deflated bar (about 5.17) and not much better than chance once the 5 markets tried are counted.
- **Note for MKTTIME1-F.** Its pass needs a block-vs-rest z of at least 2.0 on about 200 forward block entries. This history reaches only about 2.0 on 315, so even a real effect of this size would usually fail that read (low power). That is a fact about the registered forward test, not a reason to change it after the fact.
