# Code review notes, 2026-10-08 (overnight, nothing here is merged)

## Done on `claude/condense-review`

- Removed 41 lines of CSS that no markup or script refers to: the old Kalshi trade-row classes (`kal-trow*`), `kal-form`, `kal-check`, `kal-wide`,
  `kal-sub`, `kal-sum`, `kal-flag`, `kal-stat-row`, `kal-brow-sub`, plus `settings-action-btn`, `trade-chart-col`, `trade-notes-toggle`,
  `trade-notes-chevron` and `ft-since`. Each was searched for in the markup, the script and the tests first. All tests pass and
  `check-frontend.js` prints `FRONTEND: clean.` (This is also why nothing in the Kalshi page needed to change.)
- Checked for functions with identical bodies in `index.html` (none), and for functions referenced only at their own definition (13, all
  named immediately-invoked `init...` functions, so not dead).

## Left alone on purpose, for the owner to decide

1. **The single-order test path is deployed but nothing calls it.** `kalshiLiveTrade` and `kalshiLiveArm` (and `runLiveTest`, `runArmedTick`,
   and the 40c/50c `BANDS`, `planEntries`, `sizeFor` they use in `kalshiSignalLib.js`) are not called from `index.html`. They are admin-gated
   and behind `KALSHI_LIVE_ENABLED`, but they are still order-capable code that the 24 hour L1 session superseded. Removing them (and
   their gates in `kalshiLiveGates.test.js`) would shrink the part of the code that can move money, and drop the "armed" and
   "session" mutual-exclusion checks. It is a behaviour change, so it needs a decision and a deploy; I did not do it.
2. **Unused exports.** `LIVE_BASE`, `totalCash` (kalshiLiveLib); `SNAPSHOT_MINUTES`, `applyBaseline`, `shapeBalance`, `shapePositions`,
   `shapeFills` (kalshiAccountLib); `snapshotSeries`, `KEEP_DAYS`, `CYCLES` (kalshiBookLib) are exported but used nowhere else. They are
   also used internally, so removing the export changes nothing at runtime. Cosmetic, skipped.
3. **Three near-identical money formatters** in `index.html`: `kalshiMoney` (`-$1.00`), `ftMoney` (same plus an em dash for missing) and a local
   `money` inside the account fold (`$-1.00` for a negative). Merging them is safe for non-negative values; the local one would show a
   different sign position for a negative balance, which cannot occur today. Skipped as not worth the review.
