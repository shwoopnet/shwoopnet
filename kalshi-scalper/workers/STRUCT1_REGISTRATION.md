# STRUCT1 registration: two information pieces on L1's history (Strategy Research V2, 2026-10-29, research only, no verdicts asked)

Written and pushed before any scoring by this worker. Nothing here changes a live rule. The owner declined to change the 25c exit; Part A only states numbers. The owner's 2026-10-28 instruction against further L1 research is noted; this is run because the V2 lead assigned it (as MKTTIME1 was, on an owner request of 2026-10-29) and both parts are information reads, not candidate strategies.

## Common

- Entries: `scalper.tstop1.load()` (L1's 6 minute look, side 88c to 97c, 1 minute candles, paths in `r["path"]`, which holds the candles ending close-300 to close-60; the candle ending at the close is not in it). Markets: gold `KXGOLD15M`, Bitcoin `KXBTC15M`, Ethereum `KXETH15M`, Dogecoin `KXDOGE15M`, XRP `KXXRP15M`.
- Windows: close-date thirds as `tstop1.load()` cuts them (`r["win"]`, cut on close times pooled over all 15 minute series; A, B, C). Robustness (Part B): each market's own close-date thirds (distinct UTC close dates of that market's entries, three equal groups). These thirds have been read by many earlier tests; no window here is a fresh holdout.
- Fill at the decision candle's ask of the bought side (as `tstop1` builds it), 1 contract, fee 7% x C x p x (1-p) rounded up to the cent per order (`l1studies.fee`), also at C = 10; fees x1.2 reported. Zero-volume signal candles: counted and the read reported with them dropped as well, where the database carries volume.
- Counterparty (for Part B): none is claimed beyond thin quoting at hand-off and settlement hours; the honest alternative is chance.

## Part A: hold versus the 25c exit, per market (information; 0 tries, a per-market cut of EXIT2 and EXIT1, which are cited)

- History: per market and per third, PF and mean net per contract (a) held to settlement, (b) with the 25c exit: sell at the first candle in `r["path"]` whose bought-side bid (YES bid; for NO, 1 - YES ask) is at or below 0.25, at that bid, fee on the sale rounded up per order (no fee on a 0 bid). Counts of exits and of those that would have settled a win. Both at C = 1 and C = 10.
- Live: the newest saved nightly report in the scratchpad (`livewatch/report_20261029T1816Z.json`, 720 hours). Each order with `result == "exit"`: market result from `data/fresh.sqlite` (public API by ticker if missing); price paid estimated as the bought side's ask on the candle ending at the order's minute (floor of `ts` to the minute); hold outcome = C(1-p) - fee if the side won, -Cp - fee if it lost. Per market: exits, how many would have won, realised exit P/L (`settledPnl`) against the estimated hold P/L. Rows stay in the scratchpad; only aggregates go in git.

## Part B: gold and Dogecoin time structure, only blocks the ledger has not tested (14 tries)

Covered already (not tried again): see `STRUCT1_TIME.md` (HOURCLOSE :00 for gold and Dogecoin; 4 hour Central blocks and weekends per market in MKTTIME1; SESS1's closed futures session including gold's daily break; S14 reopen gap; CAL1 weekdays; HOURS2; GOLD1 Part I; IDEAS20D sessions for Bitcoin and Ethereum only).

Block of an entry by its entry time (close minus 360 s). Rule for every block: **skip the block** (do not take those entries).

| # | Market | Block |
|---|---|---|
| 1 to 3 | gold | window closes at :15, at :30, at :45 (one try each) |
| 4 to 6 | Dogecoin | window closes at :15, at :30, at :45 |
| 7, 10 | gold, Dogecoin | Tokyo open: entry within 60 minutes either side of 09:00 Asia/Tokyo, on a Tokyo weekday |
| 8, 11 | gold, Dogecoin | London open: within 60 minutes of 08:00 Europe/London, on a London weekday |
| 9, 12 | gold, Dogecoin | New York open: within 60 minutes of 09:30 America/New_York, on a New York weekday |
| 13 | gold | COMEX daily settlement (13:30 ET): entry 13:00 to 14:30 America/New_York, weekdays |
| 14 | gold | the last hour before the daily close: entry 16:00 to 17:00 America/New_York |

Gold weekends and holiday closures: a calendar lookup (markets present per weekday and per New York date, gaps over 15 minutes), not a try; weekend skipping is MKTTIME1's.

**Reported per block and per third:** baseline PF, kept PF (block skipped), removed PF (the block alone), counts and losses of the removed entries, kept net share, and the day-clustered z of (rest mean minus block mean) per entry, clustered by New York date (cluster-robust two-sample, as FALS1). Also pooled over thirds, at C = 10, at fees x1.2, and with zero-volume signal candles dropped.

**"Holds in all three thirds" (fixed now):** in each of A, B and C: kept PF at least baseline PF + 0.10, kept net at least 70% of baseline net (if baseline net is zero or negative, kept net not lower), and rest-minus-block z above 0; and the same on the market's own thirds. Anything that holds is information for the lead: a forward read at most, never a live change. Deflated bar for comparison: z about 5.17 (N about 438,922 + 14).

**Prediction (now):** nothing holds in all three thirds on both thirds schemes; at most one block in fourteen passes two of three; removed blocks hold 3 to 15 losses per third, so the per-third z values sit mostly within plus or minus 1.5.

**Tries:** Part A 0, Part B 14 (running count about 438,922 + 14 = about 438,936).
