# CPIMENT-RERUN result (2026-10-31): CPI1 FALSIFIED, MENT1 FALSIFIED (first valid scoring; run 1 is VOID)

Amendment pushed before any scorer ran: commit d23a6e4 ("CPI1/MENT1 rerun amendment and candle field helper (before scoring)"), `workers/CPIMENT_RERUN_AMENDMENT.md` plus the README section "Amendment to CPI1 and MENT1 (2026-10-31)". Code change: `src/scalper/candlefield.py` (`close_dollars` if present else `close`, on both paths), used by `cpi1.py` and `ment1.py`; result files renamed so the run-once guard stays on the new files. No rule, threshold, universe, window or split was touched. No try added to N (about 728,688, z bar 5.27). Each scorer was run once.

## Parity check (reads no outcome; `workers/CPIMENT_parity.py`)
Raw API candles with a bid AND an ask: old extraction vs fixed.
| Market | Candles | Old | Fixed |
|---|---|---|---|
| CPI-24JUN-T0.1 (historical) | 22 | 0 | 22 |
| CPI-22MAR-T0.5 (historical) | 17 | 0 | 17 |
| KXCPI-26SEP-T0.9 (live) | 34 | 34 | 34 |

So the old parser saw nothing on historical markets and the same thing as the fixed one on live markets (no regression).
Markets with a bid+ask quote at the registered look (last candle ending at least 24 hours before the close for CPI1, at or before 8 hours before the earliest close of the event for MENT1):
- CPI1 headline: 254 of 401 "above" markets, on 46 of 46 events. CPI1 core: 217 of 410, on 46 of 46 events. (Run 1 had 29 and 19.)
- MENT1: 6,211 of 6,346 markets, on 454 of 457 events. (Run 1 counted 71 events with a trade.)
Candle fetch: all 401 + 410 + 6,346 markets fetched; 80 (CPI) and 34 (MENT) have an empty candle list. The fetch code swallows errors, so an empty list could be a real no-trade market or a failed request; not distinguishable and not chased (it removes markets, it cannot create trades).

## CPI1 (registered: pooled headline + core; at least 25 independent releases, PF at least 1.5 after fee, PF above 1 in both halves, then mean at least +2.0c, release-clustered z at least 2.5, PF above 1.2 at fees x1.2)
| | Trades | Releases | PF | PF at fees x1.2 | Loss rate | Mean | Clustered z | Halves PF (first / second) |
|---|---|---|---|---|---|---|---|---|
| Headline | 138 | 45 | 0.93 | 0.92 | 70% | -0.82c | -0.28 | 0.89 / 0.98 |
| Core | 102 | 42 | 1.34 | 1.32 | 65% | +4.13c | +1.07 | 1.41 / 1.27 |
| **Pooled (the claim)** | **240** | **47** | **1.11** | **1.09** | 68% | **+1.28c** | **+0.46** | **1.08 / 1.14** |

Verdict: **FALSIFIED** (pooled PF 1.11 is under the 1.5 bar; 47 releases clears the 25 minimum; the 240 trades are inside my 150 to 300 prediction, and the PF is inside my 1.0 to 1.2 prediction). Both halves are above 1 but by little, and z 0.46 is far from 2.5 (and from the ledger's 5.27). Look-ahead control: nowcast RMSE by vintage age, headline 0.149 / 0.149 / 0.151 / 0.175 and core 0.155 / 0.155 / 0.155 / 0.156 at 1 / 5 / 10 / 20 labels before the end, the same to three decimals as in run 1 (so the history is the same file content for those months). The error grows with age only at 20 labels for headline and not for core, as in run 1: this does not prove an as-published archive, and the result does not rely on it because it failed anyway.

## MENT1 (registered: n is events, at least 100 events and 100 trades, PF at least 1.5 and above 1 in both halves, then mean at least +2.0c, z at least 2.5, PF at least 1.2 at fees x1.2)
**890 trades on 325 independent events (company-quarters): PF 0.86 (fees x1.2 0.85), loss rate 77%, mean -2.34c, event-clustered z -1.78, halves PF 0.84 / 0.87.** Verdict: **FALSIFIED** (PF under 1.5 and under 1 in both halves). Run 1's tentative reading (negative point estimate, NOT_ENOUGH_DATA) now has enough events and is negative on all of them. The prediction (PF 0.9 to 1.2, 400 to 1,500 trades, 200 to 400 events) held except the PF was a little lower.

## Information line only (not a second verdict): quote spread at most 10c
The registration does not bound the spread; a historical quote on an empty book can be very wide. Skipping a trade when the quote used had a spread above 10c (`workers/CPIMENT_info.py`; with no cap it reproduces the numbers above exactly):
- CPI1 pooled: 231 trades on 46 releases, PF 1.04, mean +0.53c, z +0.18, halves 0.91 / 1.21 (headline 132 trades PF 0.84; core 99 trades PF 1.31).
- MENT1: 836 trades on 313 events, PF 0.86, mean -2.27c, z -1.72, halves 0.84 / 0.88.
The cap changes nothing about the verdicts; a wide quote is not what hid an edge. The registered fill rule (buy at the ask, or NO at 1 minus the bid, one contract assumed filled) is optimistic about size, which can only make these results better than a live fill, not worse.

## Did the fix reveal anything else?
No second parser or join bug was found. Checks: the market universe is unchanged (401 headline and 410 core "above" markets, 6,346 mention markets, same as run 1); the nowcast RMSE tables match run 1; trade counts are inside the pre-registered predictions; the cap-free info run reproduces the registered run. Two process notes, no effect on the result: (1) `cpi1 fetch` re-downloads the nowcast and market lists as well as candles, so the nowcast.json snapshot was replaced (new sha256 3ebd14360c0b9183, run 1 logged d96aee00d96d333e; the file grows daily, and the identical RMSE tables suggest the old months are unchanged, but I cannot prove it because the old copy was overwritten). (2) The old, bad candle caches were kept in `data/old_bad_candles/` (not committed).

## Plain reading
With the quotes read correctly, neither rule has an edge. CPI1 is a thin positive on core CPI (PF 1.34, +4c a trade) that is not distinguishable from noise on 42 releases (z 1.07), cancelled by a slightly negative headline; pooled PF 1.11 is not tradable and fails the registered bar. MENT1 loses about 2.3c a contract. Both are closed as FALSIFIED. Nothing here supports payrolls/GDP follow-ups on the same idea.

## Proposed README section
### Result: CPI1 and MENT1 rerun (2026-10-31, first valid scoring after the candle parser fix; owner-approved rerun; discovery lane): both FALSIFIED
Run 1 of each is VOID. CPI1 (Cleveland nowcast vs Kalshi CPI strikes, as registered): pooled 240 trades on 47 independent releases, profit factor 1.11 (fees x1.2 1.09), mean +1.28c, release-clustered z +0.46, halves 1.08 / 1.14; headline 138 trades PF 0.93, core 102 trades PF 1.34; bar PF 1.5 and z 2.5: `FALSIFIED`. MENT1 (earnings-call words vs the word's own history): 890 trades on 325 independent events, PF 0.86 (x1.2 0.85), mean -2.34c, z -1.78, halves 0.84 / 0.87: `FALSIFIED`. With a 10c spread cap (information only): CPI1 PF 1.04, MENT1 PF 0.86. No second parser or join bug found. No try added to N (about 728,688, z bar 5.27). Code `src/scalper/cpi1.py`, `ment1.py`, `candlefield.py`; `workers/CPIMENT_RERUN_RESULT.md`.
