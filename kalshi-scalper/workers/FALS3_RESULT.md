# FALS3 result: falsifier for GEN4's core (Bitcoin favourite 50c to 85c at about 148 s), research only

Registration `workers/FALS3_REGISTRATION.md` (commit ada965a, pushed before any scoring). Recorder data `origin/quote-data` at `b7dc9cbe8`; candles `data/l1b.sqlite`, `book.sqlite`, `fresh.sqlite` (Dogecoin also `e3b`, `alts2`), 8,041 Bitcoin windows closing 2026-08-06 to 2026-10-29 (85 days, thirds from Aug 6, Sep 3, Oct 1). Scripts in the scratchpad (not committed). `src/scalper/gen4.py` was read only after my Check 1 numbers existed.

## Verdict: BROKEN by Check 2 (long history). The bare rule (GEN4_REF_FAV150) is FALSIFIED.

## Check 1: independent re-implementation on the recorder (reproduces)

| version | discovery (Oct 22 to 26) | validation (Oct 27 to 29) |
|---|---|---|
| GEN4's definition (first poll in 150 to 120 s where the favourite's ask is 0.50 to 0.85) | n 50, win 80.0%, ask 0.696, **PF1 1.61**, PF10 1.60, x1.2 1.58, next poll 1.61 | n 35, win 80.0%, ask 0.702, **PF1 1.57**, PF10 1.57, x1.2 1.54, next poll 1.53 |
| Strict first poll only (no later poll tried) | n 41, PF1 1.72 | n 32, PF1 1.46 |
| B01 (my spot proxy) | n 47, PF1 2.64 (GEN4: 46, 2.13) | n 35, PF1 2.70 (GEN4: 35, 2.64) |

GEN4's figures reproduce exactly. 9 + 3 of GEN4's entries come from a later poll, after the favourite's ask dropped back to 85c or less. My B01 discovery is higher because my spot proxy accepts one exchange and uses the current second; GEN4's needs two exchanges and the last full second. No arithmetic error found.

## Check 2: long history on 1 minute candles (decisive, BROKEN)

Favourite = the side with closing mid above 0.5, its ask 0.50 to 0.85, at the candle ending T s before the close. Fill A is that ask, fill B is the next candle's ask. Held to settlement, fee rounded up per order. Every decision candle had volume above 0, so the counts with and without zero-volume candles are identical.

| series | T | fill | n | win | ask | PF1 | mean | x1.2 | PF thirds | day z |
|---|---|---|---|---|---|---|---|---|---|---|
| **Bitcoin** | **180** | same | 2,576 | 66.0% | 0.694 | **0.77** | -5.30c | -5.68c | 0.80 / 0.72 / 0.80 | -4.97 |
| Bitcoin | 180 | next | 2,576 | 66.0% | 0.696 | 0.72 | -5.19c | -5.50c | 0.77 / 0.65 / 0.75 | -6.19 |
| **Bitcoin** | **120** | same | 1,876 | 67.7% | 0.696 | **0.83** | -3.73c | -4.11c | 0.84 / 0.80 / 0.85 | -3.24 |
| Bitcoin | 120 | next | 1,863 | 67.5% | 0.676 | 0.87 | -1.43c | -1.70c | 0.91 / 0.92 / 0.79 | -2.03 |
| Gold | 180 / 120 | same | 2,078 / 1,620 | | | 0.85 / 0.85 | -3.2c | | all thirds 0.80 to 0.90 | |
| Ethereum | 180 / 120 | same | 2,364 / 1,721 | | | 0.93 / 0.90 | -1.4c / -2.1c | | 0.86 to 0.98 | |
| Dogecoin | 180 / 120 | same | 2,332 / 1,619 | | | 0.93 / 0.86 | -1.4c / -3.0c | | 0.73 to 0.99 | |

The registered BROKEN line is PF below 1.2 at both 180 and 120 s. Every Bitcoin third at both times is between 0.65 and 0.92. Across all 78 rolling 8-day blocks of the history (all windows), Bitcoin's PF at 180 s **never reached 1.05** (median 0.80, maximum 1.05). The 150 s that GEN4 used sits between the two grid points, and both are clearly negative. A check of alignment on the 253 overlapping windows found that a candle's closing quote matches the recorder about 5 s after `end_ts` (mean ask difference 1.3c at 115 s against 1.8c at 120 s). So the two grid points stand for about 175 s and 115 s, which bracket 148 s.

**HUNT2 and UNDER1 on these cells.** HUNT2 left no per-cell output file (only `README.md`'s summary: the whole grid, including 2 and 3 minutes at 0.50-0.70 and 0.70-0.88, was what the shuffled null produces). UNDER1 (`data/under1_result.txt`) found the mirror image. Bitcoin's CHEAP side at 2 to 3 minutes was positive in discovery: 3 min 0.30-0.45 NO +4.67c / +0.95c, YES +3.02c / 0.00c; 3 min 0.20-0.30 NO +5.58c / +2.94c. After the spread, a positive cheap side means the favourite at its ask is overpriced there, which is what Check 2 measures directly.

## Check 3: recorder artefacts (registered line met at 180 s, no mechanism found)

- **Coverage.** The recorder holds 256 of the 665 Bitcoin windows between its first and last close (Oct 22 20:00 to Oct 29 20:00). 257 windows were polled, and 1 polled window has no result. YES rate: recorded 46.5%, not recorded 48.7%. Volatility proxy (absolute change of the mid between 240 and 60 s): 0.189 against 0.196. The first poll is at 149.8 s in the median; 4 windows started later than 145 s.
- **The same candle rule on the same days, recorded against not recorded.** At 180 s: recorded PF **1.43** (n 84, win 76%) against not recorded **0.75** (n 145, win 64%). At 120 s: 0.93 (n 56) against 0.91 (n 108). A difference of at least 0.5 at 180 s meets the registered line. A permutation test (5,000 random subsets of 84) gives p = 0.018. Inclusion follows the job's clock, and re-weighting the history to the recorded hour mix gives -5.83c a contract against -5.68c unweighted, so hour of day does not explain it. The recorder sampled a lucky third of the windows: the windows outside it on the very same days lost. No outcome-aware selection mechanism was found.

## Check 4: fill realism (no break)

The ask size at entry was a median of about 3,000 contracts, with 2 to 3% under 10. The next-poll fill gives PF 1.61 / 1.53, and fees x1.2 give 1.58 / 1.54 on the recorder. For B01's exit at 30 s, **16 of 47 and 18 of 35 exits fell back to settlement** (no valid poll, or no bid, in the 30 to 25 s slot). Exits with fewer than 10 contracts at the bid: 2 and 1. Requiring 10 contracts at the bid at C = 10 gives PF 2.72 / 2.79. On the recorder, latency and size do not limit it; the long history does.

## Check 5: calibration against LATECAL

Win rate minus ask, Bitcoin favourite:

| source | 0.50-0.70 | 0.70-0.85 |
|---|---|---|
| Candles, 180 s (85 days) | -2.67 points (n 1,320) | -4.33 (n 1,333) |
| Candles, 120 s | -0.52 (n 933) | -3.23 (n 990) |
| Recorder, 150 to 120 s (8 days) | **+13.27** (n 45) | **+7.17** (n 41) |
| LATECAL, recorder 120 to 90 s, ask 0.50-0.80 | -3.38 (T1 + T2, n 40) | |

There is no reason for 148 s to be 10 points off when 175 s and 115 s are both 1 to 4 points on the overpriced side across 85 days. The +7 to +13 points is the luck of the recorded windows (Check 3), not a feature of the time.

## What this means for the forward ledger

`GEN4_REF_FAV150` (the bare core) is FALSIFIED on Check 2. The 41 FAV relatives, B01 included, are this buy plus filters chosen out of 18,208 tries on 5 days. Their base loses over 85 days (PF 0.77 / 0.83), and their filters (book size, spot distance) cannot be rebuilt from candles, so they cannot be tested on the long history here. They should be read as overwhelmingly likely to shrink to the base. Whether to drop them from the ledger now is the lead's call. The forward ledger alone cannot rescue them: 8 more days of PF 1.5 would be as likely as the lucky subset already seen. The 10 NO and DOG spot-momentum survivors were not tested here.

## Prediction check

The prediction was that Check 1 reproduces, Check 2 breaks it at PF 0.85 to 1.0, and Check 3 finds nothing. Check 1 reproduced. Check 2 broke it more strongly than predicted: PF 0.77 and 0.83, every third below 0.93. Check 3 found a lucky subset (p 0.018), not an artefact.

## Tries

5 (Checks 1 to 5). Running count about 475,577 + 5 = **about 475,582**.
