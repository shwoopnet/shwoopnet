# OIDRIFT result: drift threshold forward candidate for the Bitcoin open interest core (research only)

Registration `workers/OIDRIFT_REGISTRATION.md` (commit b4d8e3f, pushed before the candidate file existed). Verdict: none yet; the
forward ledger decides (RULES words only). 1 try, no tuning.

## Built

- `src/scalper/oidrift.py`, evaluator `scalper.oidrift:forward_eval`: threshold = p90 of doi (oi at -180 s minus oi at -360 s) over
  settled KXBTC15M windows closing in the 30 UTC days before the scored window's day, read from `data/l1b`, `book`, `fresh` (first
  file wins); fewer than 20 days, a missing signal / back / fill candle, or an oi of 0 (the ledger's stand-in for a missing oi) is
  NoData. Threshold for windows closing on 2026-10-30: about 223,800.
- `workers/candidates/REF_GEN6_OIDRIFT.json`, stage reference, KXBTC15M, freeze **2026-10-30T01:00:00Z** (commit at about 00:30 UTC,
  rounded up). A dry ledger run shows it with 0 windows evaluated and no errors.
- `src/scalper/oifill.py`, plugged into `drift.run_all()` after goldslip in its own try/except; aggregates to `workers/OIFILL.md`.
- `tests/test_oidrift.py` (threshold span, earlier days only, 20 day minimum, strict `>`, NoData cases, side choice; OIFILL depth
  maths, nearest-after lag cap, a 0 signal run and a 1 signal run).

## Parity (history, validation Sep 21 to Oct 27, windows built the way `fwdledger.load_candles` builds them)

| | n | PF at 10 contracts |
|---|---|---|
| `scalper.oidrift` evaluator | **67** | **2.65** |
| FALS4 check 5 (`fals4.trades(thr_fn=...)`) | 67 | 2.65 |

Trade-level comparison: 0 trades only in the evaluator, 0 only in FALS4, 0 with a different side or fill; 0 NoData windows.
**No mismatch.** (Discovery is not compared: this rule needs 20 earlier days, FALS4's check needed 10.) Run:
`PYTHONPATH=src python -m scalper.oidrift parity`. No window closing on or after 2026-10-28 was scored.

## OIFILL

For each forward signal of REF_GEN6_OICORE and REF_GEN6_OIDRIFT (re-run with the ledger's own loader and `evaluate`), the R6 book
row nearest after close - 180 s (R6 corrected exchange time, at most 10 s later) gives the size at the bought side's best ask and the
contracts within 2c above it (5 recorded levels, a lower bound), plus the median book ask minus the candle fill. Today: 0 forward
signals (both freezes are in the future), so `workers/OIFILL.md` says so. Checked against real R6 rows with three stand-in signals
(not committed): rows found within about 1.3 s, sizes in the thousands of contracts, so the R6 read works.

## Tries

N added 1 (the forward definition). Running count about 563,359 + 1 = about 563,360.
