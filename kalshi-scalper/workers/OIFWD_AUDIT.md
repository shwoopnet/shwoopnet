# OIFWD-AUDIT: the forward pipeline of the Bitcoin open interest core (research only)

Written 2026-10-30, about 9:20 AM CT, by worker OIFWD-AUDIT. An audit, not a try: N is unchanged. Nothing live was touched. No
settlement result of any forward window was read, printed or computed here; the counts below are windows, candidate windows, signals
and fills only. The registered forward read (`workers/FORWARD_LEDGER.md`, written by the AUTO loop) owns the outcomes.

## Verdict

**The evaluator is correct. The ledger showed 0 windows because the data feed had stalled locally, not because the rule was quiet
and not because the evaluator was broken.** Nothing in the evaluator, the candidate JSON or the frozen rule was changed. One status
line was added to the AUTO pass so a stall is visible from now on.

- `data/fresh.sqlite` had no KXBTC15M window closing after 8:15 PM CT Oct 29 (01:15 UTC Oct 30) when this audit started at 9:10 AM CT
  Oct 30. The freeze is 10:00 PM CT Oct 29 (03:00 UTC Oct 30), so the ledger had ZERO windows to hand REF_GEN6_OICORE. "Windows
  evaluated 0 on 0 days" was the data gap, exactly as printed; the one OIDRIFT window was the 01:15 UTC close (its freeze is 01:00 UTC).
- Why the feed stalled: `fresh_update` last ran at 8:16 PM CT Oct 29 (the loop refreshes every 6 hours). The AUTO loop's last pass was
  1:19 AM CT Oct 30; the container restarted at 2:08 AM CT (PID 1 start time), which killed the `nohup` loop, and nothing restarts it.
  No scalper process was running when this audit began. Kalshi's public feed itself is fine: one `fresh_update` run at 9:10 AM CT
  fetched 918 new settled markets (rc 0), and the BTC candles now reach 9:00 AM CT (14:00 UTC).
- **Action for the lead (not done here, it is the lead's process):** restart the loop,
  `cd kalshi-scalper && nohup bash workers/autoscore_loop.sh >/dev/null 2>&1 &`. Until then the ledger stays at the 01:19 CT state.

## 1. Does the forward evaluator apply exactly the frozen rule?

Read: `src/scalper/gen6.py` (`window_rows`, `trades`, `nets`, `fee`, `forward_eval`), `src/scalper/oidrift.py`, `src/scalper/fwdledger.py`
(`load_candles`, `evaluate`, `order_fee`, `net_per_contract`), `src/scalper/autoscore.py`, `src/scalper/fresh_update.py` and
`src/scalper/backfill.py` (what builds `data/fresh.sqlite`).

| element of the frozen rule | history path (`gen6.build` + `trades`) | forward path (`fwdledger.load_candles` + `gen6.forward_eval`) | same? |
|---|---|---|---|
| rows per window | `window_rows` | `window_rows` (the same function) | yes |
| look | L in [180, 180]: the candle ending 180 s before the close | `s["L_lo"] <= r["L"] <= s["L_hi"]` on the same rows | yes |
| side | both, YES row before NO row, first qualifying row per window (`_order` then first index per `wid`) | rows come in `window_rows` order (240 s first, YES before NO); first qualifying row returned | yes |
| cheap side | ask 0.05 to 0.50 inclusive (1e-9 slack) in `window_rows` | same code | yes |
| doi | `q[3] - cs[t-180][3]`: oi at close-180 minus oi at close-360 | same code | yes |
| condition | `col > 86299.56000000001` on float64; NaN fails | `v > th` on the same float64 feature; NaN raises NoData if no row traded | yes (a NaN window is "no trade" in history and "not evaluated" forward; neither is an entry) |
| fill | the next candle's (close-120) ask for the side, `_sq(nq, yes)[1]` | same code | yes |
| exit | `EXITS[0]` = hold: exit None | same | yes |
| fee | `fee(p, c, m) = ceil(m x 0.07 x c x p x (1-p) x 100 - 1e-9) / 100 / c` | `order_fee(p, c, m) / c` = `ceil(m x 0.07 x c x p x (1-p) x 100 - 1e-9) / 100 / c`; held pays the entry leg only | identical rounding |
| candles loaded | `bid_c` and `ask_c` not null; `volume or 0`, `oi or 0` | the same filter and the same `or 0.0` | yes |
| windows | `result in ('yes','no')` | `evaluate` skips unsettled windows and windows at or before the freeze | yes |

Differences found: none that change an entry. Two notes, both shared by the two paths (so parity holds) and worth knowing:

- A null `oi` is read as 0 in both paths, so a candle with a missing open interest would make doi equal to plus or minus the other
  candle's oi, which could be a spurious signal. It has not happened: 0 null and 0 zero oi values in the 4,465 BTC candles of the
  3 days before the freeze and in the 718 since.
- Fills can be sub-cent: Kalshi quotes fractions of a cent on near-certain markets (1,631 BTC candles with an ask under 1c in the week
  before the freeze, 130 since). The one forward signal so far filled at 0.4c. FALS4 already checked the core without fills under 5c
  (PF 1.87), so this is known, not new.

Proof by machine: `python -m scalper.gen6 parity btc` (the forward evaluator against the history scorer on every validation window,
Sep 21 to Oct 28) reports **45,656 windows checked, 0 mismatches**.

OIDRIFT: `oidrift.forward_eval` reads the candle at close-180 and close-360 (NoData if either or its oi is missing), compares doi to
the trailing 30 day 90th percentile (`threshold`, 20+ days needed), picks the cheap side (YES first) and fills at the close-120 ask.
Its own `parity` was reported exact (n 67) in `workers/OIDRIFT_REGISTRATION.md`. Not re-run here. Today's threshold: 223,900.

## 2. The data feed

Before the refresh (9:10 AM CT): last KXBTC15M candle 8:15 PM CT Oct 29; every one of the 18 pooled series stopped at the same minute,
so it was the updater, not Bitcoin. Windows per hour closing after the freeze: 0 in every hour. `data/autoscore_state.json` had
`fresh_at` = 8:16 PM CT Oct 29.

After one `fresh_update` run (public API, no key; the same command the loop runs): last KXBTC15M candle **9:00 AM CT Oct 30**;
settled BTC windows closing after the freeze, per UTC hour: 03h 3, 04h to 13h 4 each, 14h 1 (44 in total, every quarter hour present,
all settled). Open interest in the new candles: 718 candles since the freeze, 0 null, 0 zero, 676 distinct values; max oi in a window
reaches the hundreds of thousands of contracts. **The feed is complete and open interest is present and moving.** What stopped was the
process that copies it.

## 3. Replay

### The 7 days before the freeze (10:00 PM CT Oct 22 to 10:00 PM CT Oct 29), forward code path

- 664 settled BTC windows (NoData 0, evaluator errors 0).
- 353 candidate windows (a side with ask 5c to 50c at the candle ending 180 s before the close).
- doi over the -360 to -180 candles, all 664 windows: median 81,123; 90th percentile 239,202; 95th 292,994; max 845,073;
  **47.7% of windows are above 86,300.** 317 windows above the threshold; cheap side AND above the threshold: 67.
- **Signals: 67 in the week**, 34 YES and 33 NO, by UTC day 13, 3, 16, 8, 12, 7, 7, 1 (the last day is the 3 hours to the freeze).
  Fills (next candle's ask): median 9c, 90th percentile 56c, max 88c.
- History code path (`gen6.build` + `trades`, the validation scorer, over l1b, book and fresh): the same 664 windows, **67 signals, the
  same 67 tickers, the same side and the same fill in every one** (only forward 0, only history 0, side or fill differs 0).
- History rate: validation n 333 over Sep 21 to Oct 28 (37 days) is 63 a week; GEN6_RESULT said about 60 a week. 67 matches.

So the forward code path fires at the history's rate on the week before the freeze. The evaluator is not the reason for 0.

Information, not a read: the 86,300 threshold was the discovery period's 90th percentile of doi (Aug 6 to Sep 20). In the week before the
freeze it sits BELOW the median (47.7% of windows pass it), and the trailing 30 day 90th percentile that OIDRIFT uses is 223,900. The
core therefore now fires on about 19% of candidate windows and about 10% of all windows, which is what OIDRIFT exists to show.

### Since the freeze (10:00 PM CT Oct 29 to 9:00 AM CT Oct 30, 11 hours), forward code path, after the refresh

- 44 settled windows, NoData 0, errors 0.
- 22 candidate windows (5c to 50c side at 180 s).
- doi: median 62,561; 90th percentile 227,859; 95th 243,452; max 385,667; 34.1% of windows above 86,300 (15 windows).
- cheap side AND doi above 86,300: **1 window**. Evaluator signals: **1** (KXBTC15M-26OCT300845-45, YES, signal ask 6.3c at
  7:42 AM CT, doi 93,825, filled at the next candle's ask, 0.4c). The joint count and the signal count agree, as they did before the
  freeze (67 and 67).
- Expected from the prior week's rate: 44 x 67/664 = 4.4 signals; 1 observed. P(1 or fewer | mean 4.4) is about 0.07: a quiet half day,
  not evidence of anything. The cheap-side windows and the high-doi windows simply did not coincide (22 and 15 of 44, overlap 1).
- OIDRIFT since its 01:00 UTC freeze: 52 windows, 0 signals, 0 NoData, threshold 223,900 (about 5 windows were above it; none had a
  cheap side).

**Is 0 entries expected?** For the ledger as written at 1:19 AM CT: yes, trivially, because the data ended before the freeze. On the
real windows since the freeze the rule gives 1 entry in 11 hours against about 4 expected, which is inside chance. The next ledger
run will show 44 windows evaluated and 1 trade for OICORE (its outcome belongs to the ledger, not to this note).

## 4. Fix

Not broken, so the evaluator, the candidate JSON and the frozen rule are untouched.

## 5. What was added (small, every error caught)

- `src/scalper/oifeed.py`: `status_line()` reads `data/fresh.sqlite` read-only and prints one line: the last KXBTC15M candle time (CT)
  and its age, the settled BTC windows closed since the OICORE freeze, how many had a 5c to 50c side at 180 s, the largest doi seen since
  the freeze against the rule threshold, and the word STALE when no new candle is under 7 hours old (the loop refreshes every 6). It reads
  candles and the settled flag only, never a result value (the test asserts that on the source); a missing or broken file gives
  "OICORE feed: status failed: ..." and never raises. `PYTHONPATH=src python -m scalper.oifeed` prints it.
- `src/scalper/autoscore.py`: the line is appended to every pass's status (so it is in `data/autoscore_loop.log` hourly and in the daily
  STATUS line of `workers/AUTO_LOG.md`), and a STALE line is written to `workers/AUTO_LOG.md` at most once per 6 hours. Wrapped in its own
  try so it can stop nothing.
- `tests/test_oifeed.py` (added to `run_tests.sh`): counts on a built sqlite (the freeze window excluded, an unsettled window excluded,
  YES and NO cheap sides, max doi), the STALE word at 8 hours, and the two failure cases.

Not changed: `fwdledger.py`, `gen6.py`, `oidrift.py`, the candidate files, the ledger, anything under `functions/` or `index.html`.
`data/` is git-ignored and was not committed; the refreshed `fresh.sqlite` stays local to this container.

## Reproduce

```
cd kalshi-scalper && PYTHONPATH=src python -m scalper.gen6 parity btc        # 45656 windows, 0 mismatches
cd kalshi-scalper && PYTHONPATH=src python -m scalper.oifeed                  # the feed line
cd kalshi-scalper && python tests/test_oifeed.py && python tests/test_fwdledger.py
```
The replay script lived in the session scratchpad (counts only: forward path versus history path over the 7 days before the freeze,
then the hours since); it is described fully above and is not committed because it is a one-off audit tool.
