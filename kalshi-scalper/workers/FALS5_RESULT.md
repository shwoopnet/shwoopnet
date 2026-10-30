# FALS5 result: is the Bitcoin open interest core's edge the OI JUMP or the OI LEVEL regime? (research only)

Registration `workers/FALS5_REGISTRATION.md` (commit aeeafd4, pushed before any scoring). Code `src/scalper/fals5.py`, which calls
FALS4's loader and trade function unchanged (`fals4.load`, `fals4.trades`: 7,869 settled `KXBTC15M` windows, discovery Aug 6 to
Sep 20, validation Sep 21 to Oct 27; nothing closing on or after 2026-10-28 00:00 UTC is loaded with an outcome). Fills at the
-120 s candle's closing ask of the bought side, fee 7% x C x p x (1-p) rounded up per order, C = 10 unless stated, held.
Run: `cd kalshi-scalper && PYTHONPATH=src python -m scalper.fals5` (under a second). Written 2026-10-30, about 10:00 AM CT.

## Verdicts

- **Check 1 (level versus jump): MIXED by the registered rule. The jump is necessary; the level multiplies it.** Busy windows
  WITHOUT the jump lose (top tercile, core does not fire: PF 1.09 discovery, **0.62** validation, below the unconditioned base),
  so the level regime alone is no edge. But the same jump pays about twice as much in the top level tercile (PF 2.98 / 2.61) as in
  the lower two pooled (1.73 / 1.38), and the bottom tercile in validation is 0.95 on 51 trades.
- **Check 2 (relative jump, 1 try): NOT_YET_FALSIFIED** at the registered bar (PF 1.73 / 1.71 at C = 10, n 298 / 286, positive at
  fees x1.2 in both), below the deflated bar (day z 3.24 / 3.30 against about 5.26). It is **not better than the core** (the trades
  it adds in discovery lose, PF 0.81 on 122), only more stable in its firing rate. Forward candidate `REF_GEN6_OIREL` registered
  (freeze 2026-10-30T15:00:00Z), **not independent of `REF_GEN6_OICORE`**.
- **Check 3 (threshold drift): the fixed threshold has NOT stopped selecting** (registered reading: NO). Weekly PF and the weekly
  share above 86,300 have Spearman -0.43 over 13 weeks; the last three weeks with 10+ trades are 1.94, 1.31, 3.04 (the last a part
  week). A mild decline with the drift, as predicted, not a collapse.
- **Check 4 (signal rate): "about 60 a week" is still about 55 to 67 a week.** The share of ALL Bitcoin windows above 86,300
  doubled from 17% to 27% a week (August to mid September) to 39% to 51% (since Sep 21) and has been flat since; signals per week
  went from 16 to 50 (about 32 on average) to 54 to 68, and the part week of Oct 26 (4.6 days, candles only) has 36.
- **Check 5 (same-fill honesty): confirmed, nothing changed.** 222 / 2.28 and 333 / 1.85 reproduced; on all 555 trades the fill
  equals the -120 s candle's ask of the bought side and the fee equals ceil(0.07 x 10 x p x (1-p)) per order; 0 zero-volume candles.
- The core's word stays **NOT_YET_FALSIFIED** (the forward ledger owns its read). Nothing here changes a rule, a candidate or
  anything live.

## Check 1: level (oi at -360 s) terciles within each UTC month

Candidate windows (valid doi, a 5c to 50c side at -180 s, fill candle present): 4,294 (discovery 2,431, validation 1,863).
Tercile cuts by month: Aug 265,765 / 342,699 (1,304 windows); Sep 278,053 / 362,501 (1,607); Oct 311,798 / 410,487 (1,383).
corr(level, doi) over candidate windows: 0.05 discovery, 0.09 validation (the jump and the level are nearly uncorrelated, but the
tail is not: the share of candidate windows above 86,300 rises with the level, below).

| tercile | stage | core (jump) | base (every candidate window bought) | core fires on | share of core trades | top tercile, core does NOT fire |
|---|---|---|---|---|---|---|
| bottom | disc | n 34 PF 1.97 win 24% z 1.47 | n 855 PF 1.18 win 26% | 4% | 15% | |
| bottom | val | n 51 PF **0.95** win 22% z -0.15 | n 575 PF 1.18 win 26% | 9% | 15% | |
| middle | disc | n 86 PF 1.66 win 22% z 1.47 | n 807 PF 1.10 win 23% | 11% | 39% | |
| middle | val | n 115 PF 1.56 win 27% z 1.86 | n 625 PF 0.97 win 23% | 18% | 35% | |
| top | disc | n 102 PF **2.98** win 37% z 3.66 | n 769 PF 1.28 win 24% | 13% | 46% | n 667 PF 1.09 win 22% z 0.77 |
| top | val | n 167 PF **2.61** win 30% z 4.17 | n 663 PF 0.91 win 21% | 25% | 50% | n 496 PF **0.62** win 18% z -4.04 |
| bottom + middle | disc | n 120 PF 1.73 win 22% z 2.33 | n 1,662 PF 1.14 | | | |
| bottom + middle | val | n 166 PF 1.38 win 25% z 1.59 | n 1,200 PF 1.06 | | | |

Registered reading rule: LEVEL needed the non-top terciles pooled below 1.2 (they are 1.73 / 1.38) and the top tercile's
non-firing windows at or above 1.4 (they are 1.09 / 0.62): not LEVEL. JUMP needed the non-top terciles pooled at or above 1.5 in
both windows (1.38 in validation): not JUMP. **MIXED.**

**Plain reading.** The edge is in the jump: a busy window with no jump is a losing cheap-side buy (0.62 in validation, worse than
buying every cheap side, 0.91). So "busy days" do not explain the core, and the audit's worry that the drifted threshold has turned
the rule into a busy-day bet is not what the history shows. What the history does show is an interaction: the jump pays most where
open interest is already large, and least where it is small (bottom tercile, 0.95 in validation on 51 trades). The fixed threshold
has drifted into firing MORE in every tercile (bottom 4% to 9%, middle 11% to 18%, top 13% to 25%); the extra bottom-tercile fires
are the ones that earned nothing. That is consistent with FALS4's finding that a HIGHER, moving threshold concentrates the edge
(OIDRIFT, validation PF 2.65 on 67). A "jump AND high level" rule is suggested by this table and was NOT run: it would be a new
filter on in-sample terciles and needs its own registration.

## Check 2: relative jump (doi / oi at -360 s) at the matched discovery quantile (1 try)

Discovery windows with a valid doi: 4,357; above 86,299.56: 941 (21.6%). Relative threshold = the matching quantile of doi / level
over the same windows: **0.26764675317954373** (a rise of 26.8% of the open interest standing at 360 s), 941 discovery windows
strictly above it. Applied unchanged to validation. No window had a level of 0.

| relative jump, cheap side, next-candle fill, held | discovery | validation |
|---|---|---|
| C = 10 | n **298** PF **1.73** win 24% z 3.24, net $193 | n **286** PF **1.71** win 28% z 3.30, net $191 |
| C = 1 | n 298 PF 1.64 z 2.97 | n 286 PF 1.62 z 3.04 |
| C = 10, fees x1.2 | n 298 PF 1.71, net $189 | n 286 PF 1.69, net $187 |
| core, for reference (FALS4) | n 222 PF 2.28 | n 333 PF 1.85 |

Overlap: discovery 176 of 298 relative trades are core trades (59%; 79% of the core's 222); validation 229 of 286 (80%; 69% of the
core's 333). The trades only the relative rule takes: discovery n 122 PF **0.81**, validation n 57 PF 1.52. The trades only the
core takes: discovery n 46 PF 1.55, validation n 104 PF 2.12.

Firing share of candidate windows per ISO week: absolute 4% to 20% in discovery, 16% to 20% in validation; relative 7% to 29% in
discovery (29% in the short first week), 14% to 17% in validation. The relative rule holds its rate; the absolute rule's rate
roughly doubled between the two windows.

**Kill line (registered): FALSIFIED if PF below 1.5 in either window, not positive at x1.2, or under 60 trades.** None met:
**NOT_YET_FALSIFIED**, below the deflated bar (z about 3.3 against about 5.26). As registered, this earns a forward candidate and
nothing more: `workers/candidates/REF_GEN6_OIREL.json`, freeze **2026-10-30T15:00:00Z** (the next full hour after the commit),
evaluator `scalper.oirel:forward_eval` (`src/scalper/oirel.py`, `tests/test_oirel.py`, added to `run_tests.sh`). Parity of the
evaluator against this check on Aug 6 to Oct 27, windows built the way the ledger builds them: **584 trades, PF 1.72 both ways,
0 only-evaluator, 0 only-scorer, 0 side or fill differences, 0 NoData** (`PYTHONPATH=src python -m scalper.oirel parity`).
**It is NOT independent of `REF_GEN6_OICORE`:** 59% to 80% shared trades, the same bet with a different yardstick. Read the two
rows together, never as two confirmations.

Why it is not an improvement: dividing by the level down-weights exactly the high-level windows where check 1 says the jump pays
most, and admits low-level windows with modest absolute jumps, which is where the discovery-only trades (PF 0.81) come from. Its
value is definitional: its firing rate does not drift with the market's growth, so a forward read of it is comparable across months
in a way the fixed count is not.

## Check 3: per ISO week (Monday start, UTC), share of candidate windows above 86,300 and the core's PF

| ISO week | stage | candidate windows | share above 86,300 | median level | core n | core PF | core net C = 10 |
|---|---|---|---|---|---|---|---|
| W32 (Aug 03, from Aug 6) | disc | 177 | 20% | 291,860 | 35 | 1.19 | $5 |
| W33 (Aug 10) | disc | 364 | 9% | 289,092 | 34 | 3.36 | $62 |
| W34 (Aug 17) | disc | 365 | 4% | 310,129 | 16 | 4.66 | $26 |
| W35 (Aug 24) | disc | 350 | 14% | 319,977 | 50 | 2.74 | $75 |
| W36 (Aug 31) | disc | 381 | 6% | 305,781 | 23 | 1.37 | $6 |
| W37 (Sep 07) | disc | 409 | 8% | 285,868 | 31 | 2.57 | $49 |
| W38 (Sep 14) | disc | 385 | 9% | 331,165 | 33 | 1.41 | $15 |
| W39 (Sep 21) | val | 333 | 16% | 341,807 | 54 | 2.30 | $52 |
| W40 (Sep 28) | val | 355 | 19% | 358,190 | 68 | 2.26 | $64 |
| W41 (Oct 05) | val | 375 | 17% | 369,265 | 65 | 1.52 | $34 |
| W42 (Oct 12) | val | 362 | 17% | 352,313 | 60 | 1.94 | $56 |
| W43 (Oct 19) | val | 339 | 20% | 358,344 | 67 | 1.31 | $23 |
| W44 (Oct 26, to Oct 27) | val | 99 | 19% | 382,241 | 19 | 3.04 | $25 |

Spearman(weekly share above, weekly PF) over the 13 weeks with 10+ trades: **-0.43**. The three best weeks (3.36, 4.66, 2.74) are
August weeks with a 4% to 14% share; the validation weeks at 16% to 20% run 1.31 to 2.30. Registered reading "the fixed threshold
has stopped selecting" (rank correlation below -0.6 AND the last three weeks all below 1.3): **NO**. The direction is as predicted
(a mild decline as the threshold admits more windows), and every week is above 1.0 at C = 10.

## Check 4: signal rate per ISO week since Aug 4 (candles only; no result column loaded, so the days after Oct 27 are counts only)

| ISO week | windows with a doi | share above 86,300 | median doi | candidate windows | signals (cheap side AND above) |
|---|---|---|---|---|---|
| W32 (Aug 03, from Aug 6) | 375 | 27% | 59,192 | 177 | 35 |
| W33 (Aug 10) | 663 | 17% | 44,369 | 364 | 34 |
| W34 (Aug 17) | 663 | 21% | 47,556 | 365 | 16 |
| W35 (Aug 24) | 664 | 26% | 52,640 | 350 | 50 |
| W36 (Aug 31) | 664 | 17% | 45,640 | 381 | 23 |
| W37 (Sep 07) | 664 | 18% | 43,329 | 409 | 31 |
| W38 (Sep 14) | 664 | 27% | 54,061 | 385 | 33 |
| W39 (Sep 21) | 664 | 39% | 70,513 | 333 | 54 |
| W40 (Sep 28) | 664 | 42% | 71,238 | 355 | 68 |
| W41 (Oct 05) | 664 | 40% | 70,095 | 375 | 65 |
| W42 (Oct 12) | 664 | 45% | 75,569 | 362 | 60 |
| W43 (Oct 19) | 664 | 51% | 90,097 | 339 | 67 |
| W44 (Oct 26, part week to the last candle on file, Oct 30 14:15 UTC) | 434 | 45% | 74,831 | 227 | 36 |

Read: the jump distribution stepped up in the week of Sep 21 (median doi from about 45,000 to 50,000 to about 70,000 to 90,000;
the share above 86,300 from about a fifth to about half) and has been flat since. Signals went from about 32 a week to about 60
a week at that step and stayed there; the part week of Oct 26 is running at about 55 a week. So "about 60 a week" is still true;
what changed is that it is now about half of all windows that clear the threshold, and the cheap-side requirement does most of the
selecting (227 candidate windows, 36 signals). OIDRIFT's trailing threshold (about 223,900 today) is where the 90th percentile
actually sits now.

## Check 5: same-fill honesty

Reproduction from `fals4.trades(win)`: discovery n 222 PF 2.28, validation n 333 PF 1.85 (ok). Assertions over all 555 trades:
fill equals the -120 s candle's ask of the bought side (YES `ask_c`, NO `1 - bid_c`) on 555 of 555; fee equals
ceil(0.07 x 10 x p x (1-p) x 100) / 100 per order on 555 of 555; zero-volume signal or fill candles 0. In `src/scalper/gen6.py`
(read for confirmation only): `fee = ceil(m x 0.07 x c x p x (1-p) x 100 - 1e-9) / 100 / c` (line 48) and `fill = _sq(nq, yes)[1]`,
the NEXT candle's ask (line 113). The same definitions; nothing was changed.

## Predictions against results

- Check 1: predicted JUMP; the result is jump-necessary with a level interaction (MIXED). Predicted 50% to 65% of core trades in
  the top tercile: 46% / 50%. Middle tercile PF 1.4 to 2.5: 1.66 / 1.56, inside. Top tercile non-firing 0.9 to 1.3: 1.09 inside,
  0.62 below (the level alone is worse than I expected). Predicted a positive level-doi correlation: it is 0.05 to 0.09, near zero,
  though the tail still rises with the level.
- Check 2: predicted discovery 1.6 to 2.4 (1.73), validation 1.3 to 1.8 (1.71), both inside; overlap 40% to 60% (59% / 80%, the
  validation overlap higher than predicted). The 50% call on clearing 1.5 in both: it did.
- Check 3: predicted rank correlation -0.6 to +0.2: -0.43. I predicted the share among candidate windows over 40% in late October;
  it is 17% to 20% there and 45% to 51% among ALL windows, so I had mixed the two populations.
- Check 4: predicted 10 to 20 signals a week in August rising to 60 to 75: it was 16 to 50 rising to 54 to 68, a doubling, not a
  quadrupling.

## For the lead

- The audit's question has an answer on history: the rule is not a busy-day bet. The level alone loses; the jump is the signal.
  The threshold's drift costs edge at the margin (the bottom-tercile fires added in validation earned nothing), it has not removed it.
- Three forward rows now watch the same bet: `REF_GEN6_OICORE` (fixed 86,300), `REF_GEN6_OIDRIFT` (trailing p90) and
  `REF_GEN6_OIREL` (relative 26.8%). They are one bet, three yardsticks. The core and OIREL fire on about 60 a week; OIDRIFT on
  about 13. If they diverge forward, the history says the high-threshold one should be the best and the relative one the weakest.
- Not run, a question for a registration if anyone wants it: the jump restricted to the top level tercile (history 2.98 / 2.61 on
  102 / 167). It is an in-sample split and would be the core with one more filter, so it would start as NOT_ENOUGH_DATA.
- The counterparty is still unnamed (MECH1), so the core still cannot meet the bar's counterparty line.

## Unintended information look (disclosed)

A dry `python -m scalper.fwdledger run` was made to confirm `REF_GEN6_OIREL` loads without error (it shows 0 windows, as its
freeze is in the future). The run's one-line status also printed every other candidate's forward trade count and PF at 10
contracts, including `REF_GEN6_OICORE 1 trades PF10 0.00`. I did not seek it and used nothing from it, but it is a forward figure
seen by this worker, so it is counted below as one information look. The ledger file it rewrote (`workers/FORWARD_LEDGER.md`) is
the AUTO loop's and is not committed by me.

## Tries (N)

Scored tables and looks: check 1 core by tercile, base by tercile, top tercile non-firing, non-top pooled (4); check 2 relative
at C = 10, C = 1, fees x1.2, the only-relative / only-core split (4); check 3 weekly PF (1); check 4 signal rate, no outcome (1);
check 5 reproduction (1); the ledger status line (1). N added **12**; running count about 700,154 + 12 = **about 700,166**
(z bar about 5.26). The forward candidate is check 2's try, not another.

## Proposed README section (for the lead to merge; README.md not edited)

```
## Result: FALS5 (the Bitcoin open interest core: jump or level regime), 2026-10-30

Registered first (`workers/FALS5_REGISTRATION.md`), result `workers/FALS5_RESULT.md`, code `src/scalper/fals5.py` (FALS4's loader and
fills unchanged; 222 / 2.28 and 333 / 1.85 reproduced, every fill the -120 s ask and every fee rounded up per order). Today's audit
found the fixed 86,300 threshold now sits below the median 3 minute open interest change, so this round asked whether the edge is the
JUMP or the LEVEL regime. Level terciles within each month: busy windows WITHOUT the jump lose (top tercile, core not firing: PF 1.09 /
**0.62**), so the level alone is no edge; the jump pays most where open interest is already large (top tercile 2.98 / 2.61, lower two
pooled 1.73 / 1.38, bottom tercile 0.95 in validation on 51): **MIXED** by the registered rule, read as jump-necessary with a level
interaction. The drift has the rule firing more in every tercile; the extra low-level fires earned nothing, but weekly PF against the
weekly share above the threshold is only Spearman -0.43 and every week is above 1.0, so the threshold has not stopped selecting. Signal
rate: the share of all Bitcoin windows above 86,300 doubled in the week of Sep 21 (about 20% to about 45%) and has been flat since;
signals went from about 32 to about 60 a week and are still about 55 to 67. Relative jump (doi over the level at 360 s, matched
discovery quantile 26.8%, 1 try): PF **1.73 / 1.71** on 298 / 286 (C = 1 1.64 / 1.62; x1.2 1.71 / 1.69; z 3.2 / 3.3), **NOT_YET_FALSIFIED**
at the bar, below the deflated bar, not better than the core (its discovery-only trades PF 0.81) and 59% to 80% the same trades: forward
row `REF_GEN6_OIREL` (freeze 2026-10-30T15:00Z, `scalper.oirel`, parity 584 trades exact), to be read WITH `REF_GEN6_OICORE` and
`REF_GEN6_OIDRIFT`, never as a third confirmation. The core stays NOT_YET_FALSIFIED; its counterparty is still unnamed. One unintended
information look (the ledger's status line) is counted. N +12; running count about 700,166 (z bar 5.26).
```
