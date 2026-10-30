# FALS5 registration: is the Bitcoin open interest core's edge the OI JUMP or the OI LEVEL regime? (research only)

Written 2026-10-30, about 9:30 AM CT, by worker FALS5 and pushed BEFORE any FALS5 scoring. Before this commit I read
`workers/RULES.md`, the README sections GEN6, FALS4 and MECH1, `workers/OIDRIFT_REGISTRATION.md` and `workers/OIDRIFT_RESULT.md`,
`workers/OIFWD_AUDIT.md` (today's audit), `workers/FALS4_REGISTRATION.md`, `workers/FALS4_RESULT.md`, `src/scalper/fals4.py`,
`src/scalper/oidrift.py`, `workers/candidates/README.md` and `workers/candidates/REF_GEN6_OIDRIFT.json`. No row of any table
was built or scored before this file was pushed. Nothing live is touched; `functions/`, `index.html` and the candidate files of
other rounds are not edited.

## The question

The core (`REF_GEN6_OICORE`): `KXBTC15M`; at the candle ending 180 s before the close, buy the side whose ask is in 5c to 50c (YES
first) when `doi = oi(-180) - oi(-360)` is greater than 86,299.56; fill at the next candle's (-120 s) closing ask of that side; hold
to settlement. Discovery (Aug 6 to Sep 20) n 222 PF 2.28; validation (Sep 21 to Oct 27) n 333 PF 1.85 (GEN6, reproduced by FALS4).

Today's audit found the fixed threshold has drifted under the market: 86,300 was the discovery 90th percentile of doi and in the
week before the freeze it sits BELOW the median (47.7% of windows pass it). Open interest in these markets has grown, so a fixed
count of new contracts selects very different windows now than it did in August. That raises a falsifier question the earlier
rounds did not ask: **is the edge a property of the open interest JUMP (new contracts being created in those 3 minutes), or of the
open interest LEVEL regime (busy days, when any cheap side at 180 s does better)?** If it is the level, the rule will keep firing
more and more often as open interest grows and the fixed threshold stops selecting anything.

## Data and windows (unchanged from GEN6 and FALS4)

Settled `KXBTC15M` windows from `data/l1b.sqlite`, `book.sqlite`, `fresh.sqlite` (first file holding a ticker wins), loaded through
`scalper.fals4.load()`, which filters `close_ts < 2026-10-28 00:00 UTC` in SQL. DISCOVERY = closes 2026-08-06 to 2026-09-20 UTC,
VALIDATION = 2026-09-21 to 2026-10-27 UTC. **No outcome of any window closing on or after 2026-10-28 is read.** Check 4 alone
counts SIGNALS (candles only, no `result` column loaded) for the days after Oct 27, so the owner can see the current signal rate;
that is a count of candidate windows and threshold crossings, never a result.

Fees 7% x C x p x (1-p) rounded UP to the cent per order; C = 10 headline, C = 1 and fees x1.2 (multiplied before rounding)
reported for anything that could become a candidate. Fill = the -120 s candle's closing ask of the bought side (YES: `ask_c`; NO:
`1 - bid_c`), a quote at or after the signal candle, as FALS4. Zero-volume signal or fill candles reported (FALS4 found 0).

Definitions used below:
- **candidate window**: a settled window with the -360, -180 and -120 candles present, `oi` known at -360 and -180, and a side
  with ask in 5c to 50c at -180 (YES first). This is the population the core picks from.
- **level**: `oi(-360)`, the open interest at the END of the candle ending 360 s before the close (so it is known before the jump).
- **jump**: `doi = oi(-180) - oi(-360)`.
- **relative jump**: `rdoi = doi / oi(-360)`; a window with `oi(-360) <= 0` has no relative jump and is no trade.

## Checks (all fixed now; history only)

**Check 1. Level versus jump.** Candidate windows are cut into terciles of `level` within each UTC calendar month (Aug, Sep, Oct;
cut points from the candidate windows of that month only, no outcome used), to take the trend out. For each tercile, discovery and
validation: the core's n and PF; the BASE (every candidate window bought at the -120 ask, no doi condition) n and PF; the share of
candidate windows the core fires on; and the core's share of trades in that tercile. Also, within the TOP tercile only, the
candidate windows the core does NOT fire on (cheap side, same level regime, no jump): n and PF. That last line is the direct test:
if the level is the edge, those windows are good too; if the jump is the edge, they are not.
- Prediction: `doi` and `level` are positively correlated (busier windows add more contracts), so the core's trades lean to the
  top tercile (I expect 50% to 65% of trades there). If the edge is the jump, PF is similar across terciles (every tercile with
  n at least 30 above PF 1.3 in validation) and the top tercile's non-firing windows are near the base (PF 0.9 to 1.2). If it is
  the level, the top tercile carries it all (top tercile PF at or above the core's, the other two pooled below 1.2) and the top
  tercile's non-firing windows are also above 1.4. **My prediction: the jump.** Core PF in the middle tercile 1.4 to 2.5 in both
  windows; top tercile non-firing windows PF 0.9 to 1.3; the bottom tercile too thin to read (n under 30 in discovery).
- Reading rule (fixed now): **LEVEL** if, in both windows, the top tercile has PF at least 1.5 AND the other two terciles pooled
  (n at least 30 each window) have PF below 1.2 AND the top tercile's non-firing windows have PF at least 1.4. **JUMP** if, in
  both windows, the non-top terciles pooled have PF at least 1.5 AND the top tercile's non-firing windows have PF below 1.3.
  Anything else: **MIXED** (say what), and the word for the round stays NOT_YET_FALSIFIED unless check 2's kill fires.

**Check 2. Relative jump (1 try, counted in N).** Replace the absolute threshold with `rdoi` at the matched quantile: q = the share
of discovery windows (every settled window with a valid doi, any side, as GEN6's percentile was taken over windows) with
`doi > 86,299.56`; the relative threshold is the (1 - q) quantile of `rdoi` over the same discovery windows, applied UNCHANGED to
validation. Same side, fill, fee and hold as the core. Report n, PF at C = 10, C = 1, fees x1.2, day-clustered z, overlap with the
core's trades per window, and the share of candidate windows it fires on per ISO week (does the relative version hold its rate
while the absolute one climbs).
- Prediction: discovery PF 1.6 to 2.4 (it shares about 60% to 75% of the core's discovery trades), validation PF 1.3 to 1.8 with
  overlap 40% to 60% (its validation trades are the early-October lower-level windows the absolute rule under-weights). About a
  50% chance it clears 1.5 in both windows.
- **Kill (fixed now): FALSIFIED if PF at C = 10 is below 1.5 in EITHER window, or not positive at fees x1.2 in either window, or
  fewer than 60 trades in either window.** Otherwise NOT_YET_FALSIFIED, below the deflated bar (two history windows, z under about
  5.26 for N about 700,160), which earns only a forward candidate `REF_GEN6_OIREL` (freeze at the next full hour UTC after its
  commit; evaluator in a new small module `scalper.oirel`; stated as NOT independent of `REF_GEN6_OICORE`).

**Check 3. Threshold drift over time (information).** Per ISO week (Monday start, UTC) from the week of Aug 6 to the week of
Oct 27: candidate windows, the share of them with `doi > 86,300`, the core's n and PF that week (PF printed when n at least 10),
and the week's median `level`. Spearman rank correlation between the weekly share and the weekly PF over weeks with n at least 10.
- Prediction: the share climbs from under 15% in August to over 40% in late October; PF does not fall in step (rank correlation
  between -0.6 and +0.2; FALS4's 8 day blocks were all above 1.0, the last three 1.27 to 1.63 against 2.1 to 3.85 in August, so a
  MILD decline is what I expect, not a collapse). Reading rule: "the fixed threshold has stopped selecting" is claimed only if the
  rank correlation is below -0.6 AND the last 3 weeks with n at least 10 all have PF below 1.3.

**Check 4. Signal rate (information, no outcome read).** Per ISO week from Aug 4: all BTC windows with a valid doi, the share
above 86,300, candidate windows, and signals (cheap side AND above 86,300), including the days after Oct 27 from candles only
(no `result` column is loaded for them). What "about 60 a week" has become.
- Prediction: signals per week rose from about 10 to 20 in August to 60 to 75 in the last full weeks of October, and the share of
  all windows above 86,300 from about 10% to 45%.

**Check 5. Same-fill honesty (confirm, do not change).** (a) Reproduce the core's n and PF per window from `fals4.trades(win)`:
must be 222 / 2.28 and 333 / 1.85. (b) Assert on every trade that the fill equals the -120 s candle's ask of the bought side
(YES `ask_c`, NO `1 - bid_c`) and that the fee equals `ceil(0.07 x C x p x (1 - p) x 100) / 100` per order. (c) State where the
same two definitions sit in `src/scalper/gen6.py` (`fee` line 48, `_sq(nq, yes)[1]` line 113), read for confirmation only.
Nothing here is changed; a mismatch is reported, not fixed.

## Counterparty

As GEN6, FALS4 and MECH1: still unnamed. MECH1 found favourite holders lose as a group in the firing windows but no taker type
carries it. This round does not name one either; it asks whether the selection is about the jump or the regime, which narrows
where to look (a jump story points at the writers of the new contracts; a level story points at a busy-day crowd).

## Verdict words

Per `workers/RULES.md`: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE. Check 2 gets its own word by its kill line.
The round's word for the core is NOT_YET_FALSIFIED unless check 1 reads LEVEL, in which case the core's forward row is flagged as
"selection drifting, read against OIDRIFT" (the core is not re-scored here; the ledger owns the forward read).

## Tries (N)

Each scored table counts 1: check 1 core by tercile (1), base by tercile (1), top tercile non-firing (1); check 2 relative jump
(1); check 3 weekly PF (1); check 4 signal rate (information, no outcome: counted anyway, 1); check 5 reproduction (1). Planned N
added **7**; the result reports the exact count. Running count before FALS5 about 700,154.
