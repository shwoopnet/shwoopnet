# NHLOT price measurement, second build (History Miner, Nov 13, 2026)

From the text only: `IDEA_DESK_B_WAVE3.md` on `claude/idea-desk-b` 5d1ead7d (sha256 71fac71b...), the six sections named by `nhlot/INPUT_LAYOUT.md`, the later one right where they differ. Desk B's `measure_prices.py`, `fixture_outputs/` and `build_candles_job.py` were NOT opened. Zero tries; no outcome or result field is read. `outputs/case_NN.json` are this build's prints on Desk B's nine MADE-UP cases, committed BEFORE any comparison. Every print carries the hindsight label of the 00:10Z amendment. [research]

Usage: `python3 -I nhlot2.py <candle run folder> <games.json>`.

## Readings this build had to choose (each to the Head as a dated amendment before the builds are called equal)
1. **Usable game ("games with moneyline candles"):** both moneyline tickers have at least one candle anywhere in the answer.
2. **The 45 minute window:** candles whose end_period_ts is after close_ts - 2,700 and at or before close_ts; the first qualifying minute in time order.
3. **A minute with no candle, or a side absent:** no carry-forward from another minute. A strike with no candle that minute, or with neither side, is "no quote that minute" (does not count toward the 4); a strike with one side counts as quoted and is decided only by the side it shows (bid >= 0.93 high, else ask <= 0.07 low, else undecided).
4. **Moneyline mid:** needs both bid and ask that minute; a missing side means the condition fails at that minute.
5. **The cheaper side:** the moneyline ticker with the lower ask at the detection minute; equal asks: the ticker that sorts first as a plain string.
6. **Buyable (registered):** the cheaper side's own contract at the candle ending one minute after the detection minute: both sides present, ask <= 0.43 and ask - bid <= 0.03 (1e-9 tolerance). No candle or a missing side: not buyable. Best-of-two (optimistic): buyable at the detection minute or at the next.
7. **Quartiles:** linear interpolation at (n - 1)p on the sorted asks (Python `statistics.quantiles(..., n=4, method="inclusive")`); median by `statistics.median`.
8. **"First 5 minutes of the window":** detection minutes ending at or before close_ts - 2,400.
9. **Cross-check minute:** for a detected game, the overtime market at the detection minute; for a game not detected, the overtime market's LAST candle inside the window. Says overtime: YES bid >= 0.93; says no overtime: YES ask <= 0.07; a quote that is neither: undecided; no candle: no quote.
10. **Verdict order:** under 30 detections is NOT_ENOUGH_DATA first (whatever the fire rate); then the fire rate (12% and 35% inclusive); then the buyable share (exactly 30% is not closed). The shares are printed only with 30 or more detections and the fire rate in range.
11. **The run folder is walked by its MANIFEST rows** (Desk B's reader walks file names): the run must be "complete", every job request must have a 200 row, a stored file is checked against sha256 and bytes when the manifest carries them, and every file must lie inside the run folder. A HELDOUT path (any case) is refused.
