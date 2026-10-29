# FALS2 result: falsifier for RISK1 (the account risk estimate)

Worker FALS2, 2026-10-29, run as registered in `workers/FALS2_REGISTRATION.md` (pushed before any scoring, commit 732e35e). Own code in the scratchpad (`fals2_data.py`, `fals2_step1.py`, `fals2_boot.py`, `fals2_intra.py`), written before `src/scalper/risk1.py` was opened. A check of RISK1's arithmetic and of how fragile it is, not a strategy test. Nothing here changes a live rule.

## Verdict: CHANGED (by the registered stress rule; the base arithmetic is CONFIRMED)

- **Checks 1 and 2 reproduce RISK1.** The per-market table matches in every cell, and my independent bootstrap lands within the registered limits everywhere (medians within 5%, p5 within $8, share below start within 0.4 points).
- **The registered verdict rule trips on (b1) and (b2), gold slippage.** With 1.0c more slippage on gold than the 0.60c measured, the share of $528 paths below the start after 30 days is **31%** (the limit was 25%). With 1.5c more it is **47%**, and the 90 day median is +$12. RISK1 already showed this in its own unregistered sensitivity table. My run reproduces that row too (+$37 / 28% at 1.5c total, against RISK1's +$38 / 27.6%). So this is not an arithmetic error. It shows that **the whole estimate depends on gold's roughly 1c a contract after costs, and about 1c of extra cost removes most of it.**
- **A modelling gap found here (unregistered, an upper bound, labelled as such).** RISK1 checks the 25c exit only at each 1 minute candle's closing bid. The live exit watch polls about every 10 s. The candles' own lows show the bought side's bid touching 25c or less inside a minute, without any candle closing there: 16 gold and 43 Dogecoin entries that were held to the end, of which 11 gold and 33 Dogecoin then won. Live would have sold most of those at about 25c. If every such touch is treated as a sale at 25c, gold falls from +0.98 to +0.45c a contract (PF 1.22 to 1.09; T2 PF 0.88), and the $528 30 day median falls from +$97 to **+$16**, with **40% of paths below the start** and the stop firing in 26% of 90 day paths. This is an upper bound, because a touch shorter than 10 s, or a one-sided book flicker, would not be sold. The live record points the same way at a smaller size: in `workers/DRIFT.md` (30 days, matched orders), live loss rates are at or above the history's in every market (gold 4.4 vs 4.4, Dogecoin 3.4 vs 2.6, Ethereum 8.7 vs 5.8). The final minute (the candle ending at the close) is also left out of the exit in both RISK1 and my code, although the live watch runs then. Gold had 12 held winners whose bid touched 25c in that minute.

## Check 1: per-market table (1 contract, fee at C = 1, live filters, slippage)

| Market | Entries | Lost at settle | 25c exits (would have won) | Mean net c/contract ALL / T1 / T2 / T3 | PF ALL / T1 / T2 / T3 | RISK1 |
|---|---|---|---|---|---|---|
| Gold | 1,386 | 38 | 33 (4) | +0.98 / +1.48 / +0.20 / +1.22 | 1.22 / 1.39 / 1.04 / 1.28 | identical |
| Dogecoin | 2,514 | 32 | 126 (30) | -0.47 / -0.43 / -0.51 / -0.47 | 0.91 / 0.92 / 0.91 / 0.91 | identical |
| Ethereum (smooth, window free) | 62 | 0 | 1 (0) | +1.98 / +3.46 / +4.29 / -4.17 | 2.33 / inf / inf / 0.32 | identical |

84 full Central days (2026-08-06 to 2026-10-28), all CDT (UTC-5), with no zero-volume decision candles. **Dogecoin is not in `l1b`, `book` or `fresh` before Oct 11**; both RISK1 and I read it from `e3b` and `alts2`. Which copy of a ticker found in two files gets used (the first file, or the file with more candles) changes nothing. Gold at C = 1 with more slippage: +1.0c gives -0.02 (PF 1.00; T2 0.85), +1.5c gives -0.52 (PF 0.89).

## Check 2 and Check 3: bootstrap comparison (10,000 paths, whole days, restart the next day after a stop)

Net = final cash (savings included) minus the start. "Stop" = share of paths where the 12% stop fires at least once.

| Row | Start | 30 d median | 30 d p5 | 30 d below start | 30 d stop | 90 d median | 90 d p5 | 90 d below start | 90 d stop |
|---|---|---|---|---|---|---|---|---|---|
| **RISK1 (published)** | $528 | +99 | -16 | 7.9% | 1.8% | +330 | +103 | 0.5% | 5.5% |
| **FALS2 main (Check 2)** | $528 | +97 | -16 | 8.3% | 2.4% | +348 | +99 | 0.8% | 6.2% |
| (a) fill at the next candle's ask | $528 | +61 | -40 | 16.8% | 2.1% | +207 | +2 | 4.8% | 5.5% |
| **(b1) gold slippage 1.60c** | $528 | +31 | -68 | **31.1%** | 3.8% | +102 | -82 | 19.4% | 10.7% |
| **(b2) gold slippage 2.10c** | $528 | +4 | -92 | **47.2%** | 4.9% | +12 | -151 | 45.5% | 16.1% |
| (c) 3-day blocks | $528 | +93 | -4 | 5.8% | 0.8% | +329 | +115 | 0.3% | 2.3% |
| (d) best 5 days dropped | $528 | +57 | -46 | 18.3% | 2.4% | +197 | -10 | 6.1% | 7.5% |
| RISK1's 1.50c row, re-run (check) | $528 | +37 | -63 | 28.1% | 3.6% | +124 | -67 | 15.2% | 10.5% |
| *unregistered: intra-minute 25c touches sold (upper bound)* | $528 | *+16* | *-87* | *40.4%* | *9.4%* | *+58* | *-142* | *33.2%* | *26.2%* |
| **RISK1 (published)** | $1,028 | +200 | -9 | 5.9% | 1.0% | +670 | +246 | 0.3% | 2.6% |
| **FALS2 main (Check 2)** | $1,028 | +197 | -9 | 5.9% | 0.9% | +699 | +238 | 0.4% | 3.2% |
| (a) next candle | $1,028 | +131 | -55 | 13.1% | 0.4% | +447 | +59 | 2.6% | 1.7% |
| (b1) gold 1.60c | $1,028 | +66 | -114 | 28.3% | 1.8% | +214 | -126 | 16.0% | 5.5% |
| (b2) gold 2.10c | $1,028 | +8 | -162 | 47.4% | 2.3% | +21 | -265 | 45.7% | 6.8% |
| (c) 3-day blocks | $1,028 | +189 | +2 | 4.8% | 0.4% | +668 | +251 | 0.2% | 1.1% |
| (d) best 5 dropped | $1,028 | +129 | -62 | 13.6% | 0.9% | +444 | +56 | 2.9% | 3.5% |
| *unregistered: intra-minute touches (upper bound)* | $1,028 | *+76* | *-116* | *27.0%* | *4.2%* | *+265* | *-120* | *13.7%* | *12.3%* |

If the bot stays off for the rest of the path after a stop (STOP_END), $528 at 90 days gives median +$341, p5 +$51 and 2.4% below the start (RISK1: 1.8%). Worst drawdown for the main run at $528: median $52 and p95 $96 at 30 days, $83 and $137 at 90 days (RISK1: $52 / $93 and $80 / $133).

## Differences from RISK1 and why

1. **Bookkeeping cost (small, RISK1 slightly kind on the stop and slightly harsh on growth).** Live books every order at `maxCost` (the rounded-up limit x C plus the fee), so a win is booked a little low. That figure is what the loss stop and `foldSkim` read. RISK1 books the price actually paid, and for sizing and the window cap it uses a limit rounded from the candle price before slippage, which can be below what was paid. I booked `maxCost` at the rounded-up price paid. Under live bookkeeping less profit is skimmed to savings, so the ladder climbs a little faster (gold cap at 90 days 16.5 against RISK1's 14.9 at $528), the median is about 5% higher and the stop fires about 0.6 points more often. This is within the limits.
2. **Fold order.** All of a window's orders carry the same `ts`, so `foldSkim` orders them by id (Dogecoin, Ethereum, gold), which is what RISK1 does. I folded gold first. The effect is negligible.
3. **Day selection.** RISK1 keeps days with at least 85 Dogecoin markets, and I used the date range. Both give the same 84 days.
4. **Exit sampling (both codes; the material one).** Both check the exit only at candle closes and leave out the final minute (see the verdict above).

## (e) Look-ahead audit

- **Mine.** The entry, side, band and price are read only from the candle with `end_ts == close - 360`. The smooth path uses candles with `end_ts <= close - 360`. The exit scans only candles with `end_ts > close - 360` (or `> close - 300` for (a)). The result is used only to score. (d) picks its days by outcome on purpose, since that is the stress.
- **RISK1 (`risk1.py`, read after my numbers).** The decision candle is `c[0] == close - 360`. The smooth gate uses `c[0] <= t`. The exit uses `t < c[0] <= close - 60` with `valid_quote`. Nothing at or after the decision feeds the entry. There is one tiny mismatch with live: `favorite` tests the YES ask against the band without the 4-place rounding and 1e-9 tolerance that `l1Pick` uses. It changed no count here. **No look-ahead found in either.**

## Reading it, plainly

- RISK1's arithmetic is right: I get the same table, and the same bootstrap to within a few dollars.
- The estimate is not robust. About 1c a contract of extra cost on gold (b1) puts about 3 in 10 $528 paths below the start after a month. The 10 s exit watch selling intra-minute dips that the candles hide pushes in the same direction, by up to about the same amount. The next-candle fill (a) and dropping the 5 best days (d) each cut the 30 day median by about 40%.
- Runs of bad days (c) do not hurt. Resampling 3-day blocks narrows the spread slightly, so day-to-day clustering is not the risk here. The risk is the size of gold's edge.
- Dogecoin at 5 contracts adds nothing in the history (PF 0.91 at C = 1, 0.78 with the intra-minute exits).

**Prediction check:** the reproduction held (predicted). (a) cut the $528 30 day median by 37% (predicted at least a third). (b2) cut it by 96% (predicted). (c) did NOT widen p5 (predicted it would). (d) cut the median by 42% (predicted about a third). The verdict line was crossed by b1 and b2 (predicted b2).

**Tries:** 8 registered (Check 1, Check 2, a, b1, b2, c, d, e), plus the RISK1 1.50c row re-run as a check, plus the unregistered intra-minute exit upper bound = 10. Running count about 439,013 + 10 = about 439,023.
