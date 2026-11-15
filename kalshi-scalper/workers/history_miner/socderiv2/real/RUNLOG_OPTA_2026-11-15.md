# SOCDERIV second build: the one real run under option (a) (2026-11-15), on the Head's standing go after Auditor B's CLEAN (15:18Z)

- Time: 2026-11-15T15:18:38Z to 15:44:09Z, exit 0, not stopped. Run once.
- Build: socderiv2.py f073620c94d216998ba157ccea5c1b867ae1f4aed54204d43b1ecce0d29d6bc6; socderiv2_model.py 9c3145a683fd64109536eb02567ed0b302f26ee5b320a38f547bdb1d0ab508f8 (commit 7cf648db).
- Guard: hm_guard.py c0b7826e; list HELDOUT_PULL_RUNS.md sha256 c561184a7c3eb80bbb53752133247bfa8d85377009ae073f2fda39f227216ec4, copied from origin/main right before the run (no SOCDERIV run listed).
- Inputs, the same landed runs as the 2026-11-14 run: SOCDERIV_LISTS/2026-11-13T0806Z_43390567279, SOCDERIV_CANDLES_A/2026-11-14T0032Z_43534889585, SOCDERIV_CANDLES_B/2026-11-14T0040Z_43535707061.
- Job files: the lists job as committed at run time (f0140ab4, sha256 f342414a, equal to the run's embedded job, Auditor B's ruling of Nov 14); candles A 3132c7d5 and B f9225735 from main. Series file 01b7febc.
- Outputs, committed before reading them and before seeing the Testing Desk's:
  - SOCDERIV2_PRINT_OPTA_2026-11-15.json, sha256 0bd7e553be75bf401af7aa04c39797f8384ed9529bab5e36401a055ee283f2ae
  - socderiv_pergame_OPTA_2026-11-15.csv, sha256 69cefc5ff6f893e1504cef65c8968d53e5a55f0bdd64d3bfaeb736b1650369b9
- Development windows only. The 2026-11-14 print (b1bd1983, the older build) stays as the record of that run.

## Note (2026-11-15 ~15:55Z, the Head's request; no re-run): 4 blank strikes in the per-game CSV
- **Rows:** KXBRASILEIROTEAMTOTAL-26OCT23CRUCR-CRU1 to CRU4, game KXBRASILEIROGAME-26OCT23CRUCR.
- **Why the leg is unreadable:** the game's two team codes are CR and CRU, and CR is a prefix of CRU, so a suffix such as CRU1 starts with both codes. The reader's team rule (exactly one code must start the suffix) makes the leg UNREADABLE. These are the 4 targets_unreadable in the print. The registration's shape-edge reading, "a game whose team codes are one the start of the other", treats it so, and the Testing Desk's build agrees (16b equal).
- **The defect is format only:** for an unreadable leg the reader stores no strike, so the strike column is blank although the market carries a floor_strike. The fit fields are blank and fires is False, as specified for unreadable rows. No figure, count or verdict depends on it.
- A future build should still write floor_strike on such rows. Not changed here; the frozen build stays as run.
