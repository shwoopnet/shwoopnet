# LATECAL ledger check (V2 worker, 2026-10-29, research only)

Question: is Kalshi's own quote in the last 150 seconds of the gold (`KXGOLD15M`) and Bitcoin (`KXBTC15M`) 15 minute markets calibrated at second resolution? A side quoted at ask p with s seconds left: does it win about p of the time?

## What is already tested, and how fine it is

| Test | What it covered | Time resolution | Covers the sub-minute surface? |
|---|---|---|---|
| HUNT2 (README, 2026-10-27, FALSIFIED) | Every series x time left x favourite band x side, held to settlement, 1 minute candle closes | **Finest step 1 minute**: time left in {1, 2, 3, 4, 5, 7, 8, 10, 13} minutes; bands 0.50-0.70, 0.70-0.88, 0.88-0.95, 0.95-0.985, 0.985-0.995 | Only the two points 60 s and 120 s, from candle closes. Nothing at 90 s, 30 s or 10 to 30 s, and nothing from second-resolution polls. |
| UNDER1 (FALSIFIED) | Cheap side (ask 0.03 to 0.45) by time left {2, 3, 4, 5, 6, 8, 10, 13} minutes | 1 minute, finest 2 minutes | No (cheap side only; nothing under 120 s). |
| REV1 (forward claim, reads 2026-11-05) | Bitcoin cheap NO at the candles ending 120 s and 180 s | 1 minute | No; it is a cheap-side cell at 120 s and 180 s. LATECAL's 0.50 to 0.98 bands are the other (favourite) side and do not overlap REV1's entries in price (a NO ask under 0.45 is a YES ask above 0.55 only on the opposite side, which LATECAL buys; see note). |
| T1 to T5 (FALSIFIED) | Tick-level taker scalps in the FIRST 10 minutes (seconds 0 to 599) | 1 second, but early in the window | No (early window, scalps, not calibration). |
| TAPE20 (FALSIFIED) | Trade tape in the two minutes before the 6 minute decision | Tape | No (before 6 minutes left). |
| RT1, RT2 | Re-entry and reversal after a 99c favourite drops to 92c | 1 minute | No (path rule, not a calibration grid). |
| TP1 | Take profit at 99c on L1 entries | 1 minute | No. |
| QUOTE1 (NOT_ENOUGH_DATA, PF about 0) | Two-sided passive quoting in the last 150 s, recorder polls, flat 20 s before close | Recorder polls | No: it is maker quoting with a flatten, not a test of whether the touch is calibrated to the outcome. |
| BTCAVG (`workers/BTCAVG_RESULT.md`, NOT_ENOUGH_DATA) | A spot-averaging model against the book at 45, 30 and 15 s left, Bitcoin | Recorder polls | Partly: it traded only where an outside model disagreed by 5c, 7 to 16 trades. It reported a calibration of its MODEL, not of the BOOK. It found at 30 s 72% of Bitcoin polls one-sided. |
| LAG2, RECORD1 | Spot-model lag at 120, 90, 60 s (LAG2, trades) and quote level (RECORD1, pending 300 trades) | Seconds | No: both ask whether an outside spot model beats the quote, not whether the quote is calibrated on its own. |
| ENTRY2 map (information) | Favourite bands by time, 120 s cell "everything negative" | 1 minute | 120 s only, information, not a try. |
| GEN1S / "calibration by time to close" note (README 7465) | 15 minute calibration said covered by GEN1S bands and windows | Minute ranges 840 to 180 s left | No: GEN1S never went below 180 s left. |

## Verdict of the check

**The sub-minute surface is NOT covered.** HUNT2's finest step is one minute and its two late points (60 s and 120 s) are candle closes; nothing tested has measured the BOOK's own calibration from 90 s to 10 s left at poll resolution, and nothing has used the recorder's quotes for it. The 120 to 60 s cells are near HUNT2's 1 and 2 minute cells (disclosed: they are partly a re-read of HUNT2 at finer resolution on new days, counted as tries anyway); the 60 to 30 s and 30 to 10 s cells are new. So LATECAL is registered (`workers/LATECAL_REGISTRATION.md`).

Two flags for the lead, not reasons to stop:
- **Hold to settlement.** README (2026-10-29, item 1 of the four families) says "holding to settlement is outside the owner's rule" for new strategy cards. A calibration cell is held to settlement by definition (the last 150 s leave no room to exit). The lead's brief asks for exactly this, so it is run, but any rule it produced would need the owner's word on holding to settlement before even a forward test.
- **Power.** Recorder rows: Bitcoin about 257 windows (Oct 22 to 29), gold about 58 windows (Oct 28 to 29). Gold thirds hold about 19 windows each, so every gold cell is expected `NOT_ENOUGH_DATA` under the 30 window kill; Bitcoin's thirds hold about 85 windows, and BTCAVG found 72% of polls one-sided at 30 s, so the late Bitcoin cells may also be thin.

Note on REV1: LATECAL never buys a side priced under 0.50, so it never takes REV1's entry. It can take the opposite side of a REV1 entry (the YES favourite when NO is cheap) at 120 s; that is not REV1's claim and does not read it.
