# Idea Desk A: work on data already held (Nov 12, 2026)

Asked for by the Chief of Staff (owner directive, Nov 12 02:06Z): while Kalshi reads are scarce, work only on what needs none. Everything here uses public market data already recorded on the `quote-data` branch (`book15r6/`, the 15 minute books and trade tape). **Zero Kalshi requests. No live account figure of any kind.** Scripts: `workers/desk_a_held/`.

Date constants (not data-dependent cuts): tape = run folders dated 2026-10-29 to 2026-11-08; books = 2026-11-04 to 2026-11-06 (development) and 2026-10-30 to 2026-11-03 (confirmation, section 3). Nothing closing on or after 2026-11-09 00:00Z is opened (that block is frozen for DEPTH1). No settlement result is tabulated anywhere in this file: the coverage `result` column is used only as "present or not" and dropped.

## 1. Verification of two of yesterday's closures (both CONFIRMED)

Independent script (`verify_p3p4.py`, written without reading V2's script), on a subset of V2's data (windows to Nov 8; V2 used windows to Nov 11). Windows kept by the filter: Bitcoin 738 of 738, Ethereum 739 of 740, XRP 740 of 742, Dogecoin 755 of 756, gold 423 of 424.

**CRONCLUSTER1 (verdict was NO CLUSTER): CONFIRMED.** `peak` = contracts taken in seconds 0 to 9 of the minute against a flat minute; a finding needed 1.3 or more.

| Series | peak, all (95% interval) | V2 | peak, 6 to 7 min left | V2 | peak, 2 to 3 min left | V2 | touch depth after / before the boundary (3 days of books) | V2 (14 days) |
|---|---|---|---|---|---|---|---|---|
| Bitcoin | 1.00 (0.99 to 1.02) | 1.01 | 1.05 (1.01 to 1.08) | 1.04 | 0.85 (0.82 to 0.89) | 0.87 | 1.12 (1.06 to 1.18) | 1.13 |
| Ethereum | 1.03 (1.01 to 1.05) | 1.03 | 1.10 (1.04 to 1.16) | 1.10 | 0.97 (0.92 to 1.03) | 0.98 | 1.05 (1.01 to 1.09) | 1.08 |
| XRP | 1.04 (1.02 to 1.06) | 1.03 | 1.21 (1.15 to 1.27) | 1.21 | 1.11 (1.04 to 1.18) | 1.10 | 1.04 (1.00 to 1.09) | 1.09 |
| Dogecoin | 1.05 (1.03 to 1.07) | 1.05 | 1.16 (1.08 to 1.24) | 1.17 | 1.13 (1.06 to 1.20) | 1.13 | 1.13 (1.07 to 1.20) | 1.10 |
| Gold | 0.98 (0.95 to 1.00) | 0.97 | 1.09 (1.03 to 1.15) | 1.11 | 0.80 (0.73 to 0.88) | 0.80 | 0.95 (0.90 to 1.00) | 0.96 |

No cell reaches 1.3 and depth is not lower after the boundary. Second 0 alone is 1.08 (Bitcoin) to 1.33 (XRP, Dogecoin) times flat, as V2 said. The closure is right; there is no send-time candidate.

**RETAILFRAC1 stage A (verdict was NO TWO CROWDS, stage B not run): CONFIRMED under the registered rule, with one correction to the description and one thing the rule did not measure.**

| Series | Fractional share of trades / contracts | V2 | p90 size whole / fractional | V2 | YES share whole / fractional | V2 | corr(net fractional, net whole) | V2 |
|---|---|---|---|---|---|---|---|---|
| Bitcoin | 76.2% / 65.7% | 76.1 / 65.5 | 250 / 129 | 263 / 134 | .501 / .510 | .501 / .509 | +0.66 | +0.63 |
| Ethereum | 53.5% / 51.2% | 53.4 / 50.9 | 117 / 95 | 125 / 96 | .505 / .524 | .505 / .520 | +0.20 | +0.27 |
| XRP | 49.8% / 53.1% | 50.5 / 53.5 | 99 / 92 | 99 / 92 | .508 / .515 | .508 / .515 | +0.46 | +0.55 |
| Dogecoin | 42.2% / 50.5% | 43.1 / 51.0 | 50 / 62 | 50 / 62 | .506 / .516 | .505 / .513 | +0.20 | +0.26 |
| Gold | 71.2% / 63.9% | 71.5 / 64.0 | 250 / 131 | 250 / 126 | .502 / .522 | .500 / .520 | +0.35 | +0.38 |

The registered two-crowds rule (p90 size ratio of 3 or more, or a YES-share gap of 5 points or more) fails on my numbers too: best size ratio 1.94, largest YES gap 2.0 points.

- **Correction to the description.** "Fractional takers pay 12 to 14 cents less per contract" is the CONTRACT-weighted mean (mine: 0.36 to 0.41 against 0.50 to 0.56, the same as V2). Per TRADE the gap is 4 to 7 cents (0.45 to 0.46 against 0.50 to 0.52). Both are composition (small dollar-typed orders lean to the cheap side); quote the one that is meant.
- **What the rule did not measure.** Section 2 finds that a resting order filled by a fractional (dollar-typed) taker keeps +0.23c to +0.40c after 60 seconds in all five series, and one filled by a whole-number taker keeps -0.27c to +0.01c, with intervals that do not overlap in any series. So the two classes DO differ, in how informed they are at one minute, not in size or direction. This does not reopen the card: the difference is a third of a cent, and stage B is a taker rule that must clear about 2c of spread and fee, so the closure stands and no try is spent. The honest label is "closed: the classes differ in one-minute informedness by about 0.3c to 0.5c, too small for a taker rule", not "no two crowds". It matters only to maker cards.

Not re-derivable by this desk on held data: TIECOND1 (V2's local tables are not on a repo branch), EXDIV1 (closed on a reading of terms, not on data), and Refinement's six Nov 11 FAILs, which Refinement's own audit (`refine_tools/AUDIT_NOV11_FAILS.md` on `claude/refine-live`) covers; section 4 of `DESK_A_POWER_NOV12.md` adds the chance that each was a wrong fail.

## 2. MMMAP1 on the five R6 series (protocol P8; development days Nov 4 to 6)

Per taker trade: `e` = effective half-spread against the mid of the last book snapshot received at least 0.25 s before the trade; `m_h` = how far the mid moved in the taker's direction h seconds later; `r_60 = e - m_60` = what a maker filled at the touch keeps after one minute, before any queue effect. Trades in the last 60 s of a window are dropped. Cents; 95% interval by resampling whole windows. 13.4 million taker trades, about 1,220 windows.

| Series | Trades | Quoted half-spread | e | m_30 | m_60 | m_180 | r_60 per trade | r_60 per contract | Median size at the touch | Taker contracts an hour |
|---|---|---|---|---|---|---|---|---|---|---|
| Bitcoin | 9.61M | 0.39 | +0.28 | +0.18 | +0.13 | +0.02 | +0.18 (+0.09, +0.27) | +0.17 (+0.04, +0.27) | 6,799 | 12.6M |
| Ethereum | 1.15M | 0.43 | +0.56 | +0.51 | +0.42 | +0.36 | +0.13 (+0.02, +0.26) | +0.09 (-0.15, +0.28) | 531 | 750k |
| XRP | 0.69M | 0.52 | +0.73 | +0.53 | +0.57 | +0.74 | +0.18 (+0.06, +0.32) | +0.23 (-0.01, +0.45) | 269 | 390k |
| Dogecoin | 0.53M | 0.54 | +0.83 | +0.91 | +0.89 | +0.72 | -0.05 (-0.18, +0.07) | +0.04 (-0.22, +0.31) | 128 | 209k |
| Gold | 1.40M | 0.41 | +0.33 | +0.10 | +0.06 | +0.07 | +0.28 (+0.18, +0.40) | +0.11 (-0.03, +0.24) | 1,811 | 1.79M |

**Reading, by the rule fixed in P8 (r_60 of +0.5c or more with the interval above zero, 500 trades, 3 dates, median touch under 2,000): NO R6 series qualifies.** The best is gold at +0.28c a trade (and only +0.11c a contract: large trades are the informed ones). These are the comparison lines for the non-crypto books (NC15), which get the same script about Nov 15.

By order class, r_60 per trade (the finding quoted in section 1):

| Series | Filled by a whole-number taker | Filled by a fractional taker |
|---|---|---|
| Bitcoin | +0.01 (-0.10, +0.11) | +0.23 (+0.12, +0.32) |
| Ethereum | -0.08 (-0.24, +0.09) | +0.32 (+0.20, +0.44) |
| XRP | -0.03 (-0.17, +0.13) | +0.40 (+0.26, +0.53) |
| Dogecoin | -0.27 (-0.41, -0.13) | +0.25 (+0.09, +0.41) |
| Gold | -0.04 (-0.23, +0.12) | +0.39 (+0.29, +0.51) |

By the price the taker paid (EXPLORATORY: these cuts were chosen after the table above was seen, on 3 days in which the four crypto series move together, so the intervals are too narrow):

| Taker paid | Bitcoin | Ethereum | XRP | Dogecoin | Gold |
|---|---|---|---|---|---|
| 0.10 to 0.30 (maker sold the cheap side) | -0.52 | -1.08 | -1.04 | -1.04 | +0.47 |
| 0.30 to 0.70 | +0.24 | +0.04 | +0.17 | -0.22 | +0.38 |
| 0.70 to 0.90 (maker sold the favourite) | +1.16 (+0.18, +2.31) | +1.70 (+0.58, +2.87) | +2.15 (+0.88, +3.16) | +1.14 (-0.18, +2.12) | -0.12 |

On the four crypto series the whole of the maker's kept spread sits on one side: selling the favourite at 70c to 90c keeps 1c to 2c at one minute (1.5c to 3c at three minutes), and selling the cheap side loses about 1c. Gold shows nothing of the kind. **This is not a market-making edge. It is a direction: on these three days the cheap side's price rose on average after trades, which is the cheap-side family again** (GEN12 and GEN13 closed as taker rules; OICORE is the live member; V2's MAKERTAIL1 is the maker-entry member). It is reported so nobody reads the 70c to 90c cell as a new idea.

## 3. Confirmation on five earlier days (registered here BEFORE the Oct 30 to Nov 3 books are loaded)

The same script on books dated 2026-10-30 to 2026-11-03, which this desk has not opened. Three statements, each CONFIRMED or NOT, no re-cutting:

- **C1 (class).** r_60 per trade against fractional takers minus r_60 against whole-number takers is +0.2c or more in at least 4 of the 5 series.
- **C2 (favourite cell).** r_60 per trade for takers paying 0.70 to 0.90 is +0.5c or more in at least 3 of the 4 crypto series.
- **C3 (cheap cell).** r_60 per trade for takers paying 0.10 to 0.30 is -0.3c or less in at least 3 of the 4 crypto series.

C1 confirmed makes "dollar-typed flow is the uninformed flow" a fact about these books that maker cards may use. C2 and C3 confirmed says the cheap-side drift was present in both periods (8 days, still one regime); either failing says the 3 day cell was the sample. Nothing here is a strategy test and no try is counted; no settlement result is read.

### Result of the confirmation (run once, after the commit above; 15.4 million taker trades, about 1,480 windows, Oct 30 to Nov 3)

| Series | r_60 per trade, all | Whole-number taker | Fractional taker | Difference | Taker paid 0.70 to 0.90 | Taker paid 0.10 to 0.30 |
|---|---|---|---|---|---|---|
| Bitcoin | +0.21 (+0.15, +0.28) | +0.01 (-0.08, +0.10) | +0.28 (+0.21, +0.35) | +0.27 | +0.34 (-0.66, +1.17) | +0.39 (-0.37, +1.04) |
| Ethereum | +0.06 (-0.03, +0.18) | -0.18 (-0.31, -0.05) | +0.27 (+0.17, +0.36) | +0.45 | -0.10 (-0.93, +0.68) | +0.32 (-0.51, +1.00) |
| XRP | +0.05 (-0.08, +0.15) | -0.15 (-0.28, -0.00) | +0.25 (+0.13, +0.37) | +0.40 | -0.36 (-1.13, +0.45) | +0.30 (-0.61, +1.06) |
| Dogecoin | -0.13 (-0.26, -0.01) | -0.38 (-0.54, -0.21) | +0.26 (+0.13, +0.40) | +0.64 | +0.25 (-0.83, +1.39) | -0.43 (-1.41, +0.47) |
| Gold | +0.25 (+0.14, +0.35) | -0.19 (-0.39, -0.02) | +0.43 (+0.32, +0.55) | +0.62 | +0.40 (-0.64, +1.31) | +0.44 (-0.41, +1.25) |

- **C1: CONFIRMED (5 of 5 series).** Against a fractional taker a maker keeps +0.25c to +0.43c at one minute; against a whole-number taker, zero or less. Eight days, two separate periods, every series. Dollar-typed flow is the uninformed flow on these books.
- **C2: NOT CONFIRMED (0 of 4).** The favourite cell is +0.34, -0.10, -0.36, +0.25: nothing.
- **C3: NOT CONFIRMED (1 of 4).**

So the price cells of section 2 were the three day sample, as suspected, and are dropped. The overall line holds in both periods: **no R6 series qualifies** (best: gold +0.25c to +0.28c a trade; Bitcoin +0.18c to +0.21c behind a touch of about 6,800 contracts).

**What C1 is good for, and what it is not.** A maker cannot choose who hits its quote, and the fractional share of contracts moves only between about 45% and 75% across the window, so conditioning a quote on "when dollar-typed flow is high" is worth a few hundredths of a cent: no card. Its use is as a diagnostic for the market-making family: any maker simulation (MMSIM1 and its versions) should report the fractional share of the contracts that filled it. A simulated edge that comes from whole-number fills is suspect; one that comes from fractional fills is the believable kind. This costs nothing and reads no held-out data if it is added to the development run only.
