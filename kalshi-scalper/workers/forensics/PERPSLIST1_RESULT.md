# PERPSLIST1 result: no evidence at n = 4 (the held overlap cannot say whether the perps list is a delayed copy) (2026-11-12)

Registration: `PERPSLIST1_REGISTRATION.md` (commit 6b75d1f, before any perp candle file was opened). Script `perpslist1.py`, raw output `results/PERPSLIST1.json`. A measurement: no rule scored, nothing settles, zero tries, zero Kalshi requests, no helper. Nothing about the live account.

## Verdict by the registered rule

**"No evidence at n = 4."** The rule needs at least 30 distinct list timestamps on each side of a minute boundary (within 12 s after it, and within 12 s before it). The held data has **4 on the after side** and 76 on the before side. The primary statistic comes out at A = 3.4 with an interval of 0.8 to 14.0, which says nothing and must not be read.

## Why the overlap is so thin

| Source | What is held | What it gives |
|---|---|---|
| Perp candles (`kalshi1m/`) | 5 dates: Nov 6, 8, 9, 10, 11. 60 Equities and Indices perps, 291,519 two-sided minute rows | Plenty |
| 30 second list files (`perps30/`) | **One file**: Nov 6, 20:46Z to 22:00Z, 148 timestamps | Every sample sits at the same two second-offsets: **5 s before a minute end, and 25 s after one**. None falls in the 12 s after a boundary, so the file cannot fill the after side at all |
| Hourly list files (`perps/`) | 18 timestamps on the candle dates with usable stock or index rows, 14 of them matched to candles | Scattered offsets; 4 timestamps within 12 s after a boundary, 2 within 12 s before |

(The single 30 second file is a known scheduling failure, already fixed on main today: GitHub ran 9 of about 165 scheduled starts in the first week.)

## What the one file does show (descriptive only, not a verdict)

Median r = the gap between the list mid and the candle's mid close, in units of that ticker's usual 1 minute move:

| List read at | 35 s before a minute end | **5 s before** | 25 s after | 55 s after |
|---|---|---|---|---|
| Median r (about 3,300 rows, 74 timestamps each) | 0.62 | **0.05** | 0.49 | 0.91 |

- Read 5 s before a minute end, the list mid is almost exactly that minute's candle close: the candle's mid lies inside the list's own bid to ask (widened by 2 basis points) on **95.5%** of 3,390 rows, and the mean gap is 1.0 basis point.
- The gap grows as the list read moves away from the boundary in either direction, so the candle's time stamp is the END of its minute, as assumed.
- This does NOT show the list is current. A list a few seconds old would also match if these quotes seldom move within ten seconds, and one afternoon on the second day of stock perps cannot tell those apart. It also cannot show the candles are current: both could be late together.

## What it means for the reads that depend on it

- **CASHSPREAD1 part B** (spreads read from the 30 second list files): a spread is a slow quantity, and the list agrees with the candles to about 1 basis point when read 5 s apart. A list a few seconds old would not change a spread LEVEL. Its real problem is the one file, not freshness. Label: "list freshness not measured; does not matter for spread levels".
- **PERPEQ1 and PERPBIN1** (perp candles): this test compares the list WITH the candles, so it could never clear the candles themselves. Their label stays **"perp candle freshness assumed, not measured"**. Nothing held can measure it: no perp order book or tape is recorded.
- Any perps test that needs the list at seconds scale (a lead, a lag, a lock against another market): **not supported** until this is re-read.

## What would be enough

List samples on both sides of a minute boundary, 30 timestamps or more each side, on dates that also have candles. Either:

1. **About ten more 30 second window files** (each file sits at its own two offsets, set by the second it starts; a file gives 75 to 150 timestamps per offset). With the schedule fixed today, the open and close windows of about a week should do. Earliest sensible re-read: about **Nov 19**.
2. **One file from the Sunday 10 second recorder** (`perps10/`): six offsets a minute always cover both sides, about 40 timestamps per offset in its 40 minute window. None is on the branch yet; the next is due Sunday Nov 15, readable once that date's candles are archived.

The re-read uses this script and this registration unchanged, and is still a measurement with zero tries. A third clock (a perp order book or trade tape) would be needed to say "current" rather than "in step with the candles"; none is recorded and none is asked for here.

## Caveats

`ts_utc` is whole seconds, stamped after the list answered. Stock and index perps only; crypto, metal and energy perps have no archived candles. Not checked by the Verification Analyst.
