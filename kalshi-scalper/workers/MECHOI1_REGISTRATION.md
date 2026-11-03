# MECHOI1 registration: why does the Bitcoin open interest core (OICORE) work? A mechanism decomposition of its own windows (2026-11-03, written and pushed BEFORE any outcome, spot move or win rate of these windows was computed)

Worker MECHOI1, Strategy Research V2. Owner question: "why does OICORE work?" Analysis of an already registered signal (REF_GEN6_OICORE, GEN6). **No new trade rule is proposed; nothing here means trade; nothing here is an L1 filter** (L1 filters belong to another chat; if a number would matter to them, the result says so plainly). No promote verb. Counted as one try (+1) in N: 728,726 -> **728,727**, bar 5.27.

## Ledger check (stop-if-duplicate) and how this differs from MECH1
`grep -n -i "mechanism decomp\|MECHOI" README.md workers/*.md`: no hit. Nearest neighbours:
- **MECH1** (who is on the other side, the PUBLIC TRADE TAPE of the 555 firing windows): tested ONE story, "late favourite takers opening new contracts", and it did not hold (favourite taker share 52% vs controls about 50% to 53%; no whales; counterparty unnamed). It never looked at the SPOT price, never split the firing windows by what the quote or the open interest did, and had only 58 controls. **MECHOI1 differs:** it uses the OKX spot path and the candles' own quote and open interest history, it compares against ALL non-trigger windows on the same days, and it tests four competing stories with a separating statistic each, not the tape. It does not need the tape (optional, not used).
- FALS4 (proxies at matched counts: 3 minute volume, big move, time of day all PF 0.82 to 1.01 in validation: "the signal is new contracts created") and FALS5 (busy windows without the jump lose; jump pays most where oi is already large) already say that VOLUME and a BIG MOVE alone do not reproduce the edge. MECHOI1 asks the next question: what does spot do after the jump, and does the cheaper side win because of it.
- NEWH8 R1 to R4 (conditions inside the core's windows: the cheap side is cheaper, rarely led), OIDRIFT/OIREL (cleaner trigger definitions), SLOTEX (exit variants), OICOREX1 and XOI1 (transfers to other markets) are trade tests; none decomposes the mechanism. Not a duplicate.

## Disclosure: what was read and run before this commit
Read: `workers/OICORE_SHAPE_INVENTORY.md`, `src/scalper/candlefield.py`, `src/scalper/gen6.py` (the doi feature is `oi(-180) - oi(-360)`, the 180 s row, the fill at the next candle's ask, `vfee`), `src/scalper/lag15.py` (the OKX 1 minute kline fetcher), `src/scalper/streaks.py`, `workers/XOI1_REGISTRATION.md`, `workers/MECH1_RESULT.md`, `workers/candidates/REF_GEN6_OICORE.json`. Run: `python -m scalper.mechoi1 counts`, which prints only the number of dates and windows (90 dates, 8,483 settled Bitcoin windows with a usable open interest pair); no outcome, spot price or win rate was read. The OKX endpoint was tested once for reachability (2 candles, no analysis). `src/scalper/mechoi1.py` is committed with this file, written but not yet run on any outcome; if it changes after this commit the result will say how.

## Data
- Kalshi 1 minute candles of KXBTC15M (bid close, ask close, volume, open interest, strike) from `data/{l1b,book,fresh,five}.sqlite` via `oicorex1.window_list` (settled windows with a usable oi at the -360 and -180 candles) and `gen6.window_rows` (the 180 s row, YES first, fill at the -120 candle's ask, `fee = 7% x C x p x (1-p)` rounded up, C = 10, held to settlement). One record per window with a cheaper side (ask 0.05 to 0.50), exactly OICORE's trade set.
- OKX BTC-USDT 1 minute klines, `lag15.okx_klines`. Spot at time t = close of the kline that ends at t. Caveat: Kalshi settles on a reference rate average, not OKX; `proxy_agree` (share of windows where "OKX close at the close time is above the strike" matches the Kalshi result) is reported as a check of the proxy.
- Dates (UTC close date) with at least one settled window with a usable oi pair, 90 dates, split in three equal thirds: **W1 2026-08-06 to 2026-09-04, W2 2026-09-05 to 2026-10-04, W3 2026-10-05 to 2026-11-03 (FROZEN HOLDOUT)**. The code never builds a record, loads a kline or reads a result for a W3 date. Only W1 and W2 are used; **no second look.** Caveat stated: OICORE's threshold was fitted on 2026-08-06 to 2026-09-20 (discovery), which lies inside W1 and W2, so the effect sizes below are optimistic by selection; W1 and W2 are reported separately as points.

## Definitions (everything is known at the look, except the "post" outcomes that are the thing measured)
- Look = the candle ending 180 s before the close (t). Signal window = (t - 180, t] seen as spot from ct-360 to ct-180. Post window = ct-180 to ct.
- `doi = oi(ct-180) - oi(ct-360)`. **TRIGGER, version FIXED (as OICORE):** doi > 86,299.56. **Version REL:** doi > the 90th percentile of doi over all records closing in [ct - 24 h, ct - 900 s] (their doi is known by then); at least 40 such records or the window is not eligible in REL. **PRIMARY version for all decision rules: FIXED.** REL is reported beside it with the same statistics (agreement is noted; REL alone decides nothing).
- **Baseline** = records of the same version with neither a rise trigger nor a drop trigger (|doi| below the threshold; for REL also not in the drop fallback), same series, same days.
- Cheaper side: the side OICORE buys (YES first if its ask is 0.05 to 0.50, else NO). `d = +1` if YES, `-1` if NO. `win` = that side won. **excess = win - fill** (gross, per contract, "wins more often than its price"); `net = win - fill - fee` per contract; PF at C = 10.
- Spot quantities (bp = 10,000 x ln ratio; "sd units" divide by `sigw = sigma_min x sqrt(3)`, sigma_min = std of the 60 one minute log returns ending at the look; needs 50 of 60):
  `post = ln S(ct)/S(ct-180)`, `apost = |post|`; `sigmv = ln S(ct-180)/S(ct-360)`, `asig = |sigmv|`; `Dpost = d x post`, `Dsig = d x sigmv` (positive = spot moved toward the cheaper side's winning direction); `gap = d x ln S(ct-180)/K` (negative = cheaper side currently behind), `zg = gap / sigw`.
- Cheaper-side ask change: `unch` = |cheaper-side ask at -180 minus its ask at -360| <= 1c. Spread = ask minus bid of YES at the look.
- Lumpiness: with the three minute changes of oi, share = max|d_i| / sum|d_i|; **lumpy if share >= 0.60** (an even spread is 0.33; one minute carrying 60% or more is lumpy). Records missing any of the four oi candles are left out of M4 only.
- Terciles of `zg` are cut on the baseline records of the same version: FAR = lowest third (cheaper side furthest behind in spot terms), NEAR = highest third.

## The four mechanisms, the statistic that separates them, the thresholds
All statistics for trigger set T vs baseline B, **95% intervals by a day-clustered bootstrap (dates resampled with replacement, 2,000 reps, seed 7)**.
- **M1 VOL EVENT** (the jump marks volatility already underway; no direction).
  Lines: (a) day-matched post ratio **R_post = sum over T of apost / sum over T of (mean apost of baseline records of the same date) >= 1.20, CI lower bound above 1.0**; (b) no lean: |Dpost lean| <= 0.10 sd, where lean = mean Dpost_sd in T minus in B; (c) the cheaper side beats its price in BOTH directions: excess_yes_T >= +3c and excess_no_T >= +3c; (d) FAR minus NEAR excess in T >= +3c.
  SUPPORTED = (a, with CI) and (b) and (c) and (d); LEANING = (a) point and (c); else NOT SUPPORTED.
  Secondary (reported, not a line): R_post_sd (post move in sd units, trigger over baseline) separates "volatility persists" from "more than the trailing hour predicted"; R_sig for the signal window.
- **M2 INFORMED DIRECTION** (new informed positions: spot already leans toward the cheaper side and keeps leaning).
  Lines: (a) lean_sig = mean Dsig_sd in T minus in B >= +0.15, CI lower bound above 0; (b) lean_post = mean Dpost_sd in T minus in B >= +0.10, CI lower bound above 0; (c) excess in T windows with Dsig > 0 minus excess with Dsig <= 0 >= +5c and excess(Dsig > 0) >= +3c.
  SUPPORTED = (a, b with CIs) and (c); LEANING = (b) point and ((a) or (c)) points; else NOT SUPPORTED.
- **M3 STALE MAKER** (makers did not reprice).
  Lines: (a) excess(T, ask unchanged) minus excess(T, ask moved) >= +4c, CI lower bound above 0; (b) excess(T, unchanged) >= +3c; (c) the spread at the look is not wider: median spread T minus B <= +0.5c.
  SUPPORTED = (a with CI), (b), (c); LEANING = (a) point; else NOT SUPPORTED. Reported: share unchanged in T vs B.
- **M4 FORCED HEDGING / LARGE PRINTS** (the jump is a few large prints, so it is lumpy in time).
  Lines: (a) excess(T, lumpy) minus excess(T, even) >= +4c, CI lower bound above 0; (b) excess(T, lumpy) >= +3c.
  SUPPORTED = (a with CI) and (b); LEANING = (a) point; else NOT SUPPORTED. Reported: share lumpy in T vs B. The public tape is NOT used.
- **The separating prediction between mechanisms:** M1 predicts a LARGER post move with NO lean (R_post high, lean_post about 0, both directions pay); M2 predicts a LEAN (lean_post and lean_sig positive); M3 and M4 predict that the edge sits inside a subset (unchanged ask, lumpy) and say nothing about the spot. Several can be supported at once; "none" is a possible answer. LEANING is not support: it means the point passes and the interval is too wide to say, and with about 350 triggers in two thirds of the dates the intervals on subset differences will be wide (a half-width of 8c to 12c is expected). That is stated now, so a LEANING result is read as "underpowered", not as a finding.

## The MIRROR (does an open interest DROP predict the opposite?)
Same trade set, baseline and statistics, trigger = **drop: doi < -86,299.56 (FIXED) and doi < -(trailing 24 h p90) (REL)**, the same magnitude on the other side. Reported: n, win rate, mean fill, excess (win minus its own price, with CI: a CI wholly below zero means it predicts the OPPOSITE), excess minus baseline, net per contract, PF, R_post, lean. **If a version has fewer than 60 drop windows in W1 and W2, it is NOT_ENOUGH_DATA and, for REL only, a registered fallback is also reported: doi below the trailing 24 h 10th percentile (when that is negative), labelled as the fallback.** The mirror has no decision line; it is information.

## NUMERIC PREDICTIONS (written before scoring)
- FIXED rise, n about 340 to 380 in W1 and W2 (the 555 firing windows over 83 days scaled to 60 dates plus windows without a cheaper side removed); win rate 24% to 30%; excess +4c to +9c; PF 1.6 to 2.3 (optimistic, the threshold was fitted on part of it).
- Baseline excess -3c to -1c (a calibrated market minus spread).
- R_post 1.15 to 1.60 (central 1.35); R_post_sd 0.95 to 1.20 (central 1.05); R_sig 1.5 to 2.5; lean_post -0.10 to +0.10 sd; lean_sig -0.15 to +0.25 sd.
- Both directions positive: 70%. FAR minus NEAR: -3c to +8c.
- Ask unchanged share in T: 25% to 45%; unch_split -6c to +8c; spread diff -0.3c to +0.5c.
- Lumpy share in T 15% to 40%; lumpy_split -6c to +8c.
- Mirror: drop windows far rarer than rises; excess -5c to +1c, PF 0.6 to 1.1; chance it is CLEARLY the opposite (CI wholly below zero and below baseline excess): 25%.
- Probabilities of the labels (primary, FIXED): M1 SUPPORTED 25%, LEANING 35%; M2 SUPPORTED 7%, LEANING 15%; M3 SUPPORTED 7%, LEANING 20%; M4 SUPPORTED 5%, LEANING 20%. At least one SUPPORTED: 35%. The likeliest reading: part volatility clustering (M1 on the raw ratio), little left once trailing volatility is taken out.

## Method guards
- No look-ahead: every trigger input is known at the look; the REL threshold uses records closed 900 s or more before; terciles use only baseline records; the post and signal spot moves are the OUTCOMES measured, never selectors of the trade set.
- Parity: `python -m scalper.mechoi1 parity` must reproduce OICORE's published discovery figures (n 222, PF 2.28) on 2026-08-06 to 2026-09-20 (wholly inside W1 and W2) before `score` is run; if it does not, the loader is wrong and is fixed and disclosed before scoring.
- `score` is run once and refuses a second run. Any code change after this commit is disclosed in the result.
- Derived trigger ideas are written ONLY if a mechanism is SUPPORTED, as ideas (not registered tries, no N).

## Tries (N)
One (this decomposition, both thresholds as versions): running count 728,726 -> **728,727**, z bar 5.27. No profit factor here counts as a pass of anything; it explains a signal that is NOT_YET_FALSIFIED and needs no counterparty clearing by this file.

## Overlap with L1 and OICORE
None placed. No code in `functions/`, L1 or OICORE is touched. If a statistic points to a filter on L1's favourite side (for example, a spot or stale-quote condition), it is NOT proposed here; the result will say that it would matter to the L1 chat and what number.
