# ETHFUNNEL registration (Strategy Research V2, 2026-10-30, owner-approved measurement, Ethereum brief A "why it fires so rarely")

Written and pushed before anything is counted. Information only: not a strategy, not a hypothesis, 0 tries (N stays about 728,648, z bar 5.27). It places no order, reads only public data and the 1 minute candles already on file, and touches no trading code (`functions/kalshiLiveLib.js` is read, never edited).

## Purpose

Ethereum's smooth climb rule (`SMOOTH_SERIES`, `smoothGate`, `pathShape`) produced 1 Ethereum order in about 6.9 live days (from 2026-10-23 18:30 UTC, 1:30 PM CT) against about 9 expected from history (about 1.3 a day). This counts, window by window, where Ethereum windows drop out of the live rule, so the owner can see which stage removes the most. The decision it could inform (series order, a display label, the gate) is the owner's; this note states facts only.

## Fixed universe and replication

- Market `KXETH15M`, every window with 1 minute candles on file (`data/fresh.sqlite`, plus `l1b`, `book` for the earlier months; first source wins on overlap, as `risk1.py` loads them). The file runs from 2026-08-06 to 2026-10-30.
- Decision candle: the candle ending exactly 360 s before the close (the live look is 330 to 400 s). A window without that candle, or with an invalid quote (`valid_quote`, same rule as `validQuote` in code), cannot reach stage 2 and is counted as its own line.
- Side: `l1Pick` order: YES if its ask is in 0.88 to 0.97, else NO if 1 minus the YES bid is in the band (rounded to 4 places, 1e-9 slack). Path: the bought side's mid (YES mid, or 1 minus it for NO) at every candle with both prices, oldest first, up to the decision candle. Plain float arithmetic, exactly as `pathShape`: earlier candles = path length minus 1, `minStep` = worst one minute step, `climb` = last minus first; smooth = earlier >= 4 and minStep >= -0.005 and climb >= 0.10.
- Module: `src/scalper/ethfunnel.py`. Public data and files on disk only; no network call, no credential.

## Stages (counted window by window; each stage is a count, the next stage is shown as a share of the previous)

1. All windows.
2. A side priced 0.88 to 0.97 at the 6 minute look.
3. Stage 2 with at least 4 earlier candles.
4. Stage 2 with worst one minute step -0.005 or better (alone, not stacked on stage 3).
5. Stage 2 with climb 0.10 or more (alone).
6. All of stages 2 to 5 together = the live rule.
7. Stage 6 AND no other crypto order would be taken first in that window under today's order and paused list. Tick order is gold, XRP, Bitcoin, Dogecoin, Ethereum; one crypto order per window among `CAPPED_SERIES`; `PAUSED_SERIES` (XRP and the three probes) are skipped; gold is not part of the crypto rule. The other series' decisions are replicated by their own live gates on their own candles: Bitcoin (6 minute look, band, smooth gate, same function), Dogecoin (6 minute look, band, no smooth gate, fixed size). Assumption stated up front: a candidate order is assumed to fill (an order that did not fill does not hold a window live, and fills are not known without outcomes or fill data); cost cap, balance, window cap and the halt are not modelled. The contention count is therefore an upper bound.

Because stages 3, 4, 5 are shown alone (each on top of stage 2 only), their windows overlap; stage 6 is their intersection. For stage 4 the "not met" case also includes windows with fewer than 2 candles in the path (no step exists), and these are counted as failing stage 4 and listed.

Two runs: (A) the last 78 days on file (decision times from 78 x 86,400 s before the last window's close on file); (B) only the live days, decision times from 2026-10-23 18:30 UTC to the last window on file.

## Distribution

For in-band windows (stage 2) only: the observed distribution of the worst one minute step (quantiles and a histogram of the step values themselves), in both runs. Only the three live thresholds (4 candles, -0.005, 0.10) are reported against. No threshold sweep, no "what if 0.01" column, no loosening output.

## Prediction (written before counting)

- History: the live rule (stage 6) passes about 1.4% of all windows (about 1.3 a day).
- The worst-minute-step stage removes the most in-band windows (stage 4's drop from stage 2 is the largest of stages 3, 4, 5).
- On the live days the replay of the full gate gives at least 3 qualifying windows at stage 6 (I put about 70% on this), in which case contention with Dogecoin (stage 7) explains most of the gap to the actual 1 order.

## Limits (hard)

- NO outcomes joined: no wins, losses, P&L, settlement results; the `result` column of the market table is never selected, and the order export's `result` and `settledPnl` fields are never read.
- NO loosening output (see above).
- Parity: the live order records are private. The only source allowed is a local private export already on this machine (the gitignored `data/` folder or the session scratchpad): the nightly report `live_report.json` in the scratchpad (1,233 compact order rows, generated 2026-10-29 15:32 UTC), of which only `ts`, `ticker`, `side`, `count`, `entryLead` and `status` are read (status is an order state, not an outcome). No token is used or printed, no endpoint is called, and no order row is committed (only counts). Parity is judged over the report's days that fall inside the live period (2026-10-23 18:30 UTC to the report time): per window and per series (Ethereum, Bitcoin, Dogecoin) the replay's "would order" against "an order document exists". Disagreement over 2% of windows means STOP and report a parity bug; nothing is tuned. Known honest sources of disagreement are listed in the result, not fixed by adjusting the replay (the replay uses the decision candle's close; live uses the quote at the tick; XRP held crypto windows until its pause on 2026-10-28; gold quiet hours do not matter here).
- If no export had existed, the result would say parity was NOT checked.

## Re-read

The live-day columns are re-read once on 2026-11-12 with FLIPS0-F (nothing is scheduled by this note).
