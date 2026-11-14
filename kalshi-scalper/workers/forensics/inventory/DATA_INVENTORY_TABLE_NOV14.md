# Data inventory for the desks: what each recorded source holds (Forensics desk, Nov 14, 2026; the Head's overnight item 3)

Counts only. Built with `inventory_counts.py` (this folder; it reads a time, a series or ticker, and the best bid and ask columns of each row, nothing else: no result, trade price or size, volume, open interest; no price is printed). **Taken at about 02:00Z to 02:40Z Nov 14** from each data branch's tip (nc-data 51f6581 00:01Z, pol-data b8114cf 02:08Z, combo-data fedfd5e 02:15Z, sports-data 158d4de 00:00Z, perp-data 68f3c35 02:00Z, quote-data 6853872 01:42Z; R6 from the DEPTH1 pin 2b4ff395, 00:03Z), so recorders that are still running hold more now.

**Definitions.** Rows = polls (one row per market per poll), not windows. **Two-sided share** = rule 18: 0 < yes bid < yes ask < 1 in whole cents. A book row uses the best YES bid and the best NO bid (YES ask = 1 minus the NO bid): two-sided means both exist and their sum is under 1. A quote row uses yes_bid and yes_ask. A perpetual: bid > 0, ask > 0 and bid < ask. **Gap** = time between two rows of the same series longer than 30 minutes, counted in the files read; for a source whose cadence is 30 minutes or more, or that records only in set windows, nearly every gap is the schedule and only the longest gap tells you about an outage (noted in each row).
**Held out.** A window whose close is on or after a cut is NOT counted here (the row says which cut, from `HELDOUT_REGISTRY.md` and `HELDOUT_PULL_RUNS.md`); the registry is Desk A's first reading and partial, so a card's own row governs before anyone reads a window listed as development here. HELDOUT_PULL_RUNS.md on main now lists 3 runs (sha256 974f2713...): POLGAPH_LISTS/0627Z, LIVEDATA_PROBE_A4/0048Z, LIVEDATA_PROBE_B/0054Z.

## 1. Book recorders (levels 1 to 5, rule 18 from level 1)

| Source (branch, folder) | Series | First to last row counted | Rows | Two-sided | Gaps over 30 min (count, longest) | Held out and cut applied |
|---|---|---|---|---|---|---|
| **R6**, quote-data `book15r6/` (86 runs) | KXBTC15M | 2026-10-29 22:04Z to 2026-11-04 23:44Z | 178,540 | 69.1% | 15, 5.1 h | closes from 2026-11-05T00:00Z not counted: CFRTI-B and CFRTI-K (Bitcoin), FILLHAIRCUT1 period B from Nov 9, BOOKCH1 forward freeze Nov 4. The DEPTH1 read (blocks A to C, gold and Bitcoin) was made Nov 14 |
| | KXETH15M | same | 177,227 | 69.4% | 12, 5.4 h | same cut |
| | KXXRP15M | same | 181,207 | 71.3% | 12, 5.1 h | same cut |
| | KXDOGE15M | same | 180,348 | 70.2% | 14, 5.1 h | same cut |
| | KXGOLD15M | 2026-10-29 22:15Z to 2026-11-04 23:44Z | 119,839 | 72.8% | 9, 51.3 h (the weekend close) | GOLDHAIRCUT1 period B Nov 9 to 11, MKTTIME1-F forward; same cut |
| **NC15**, nc-data `nc15/` (13 runs) | KXSILVER15M | 2026-11-11 19:32Z to 2026-11-13 21:29Z | 19,741 | 78.3% | 19, 2.0 h | NC15DEPTH1 scoring windows from Nov 19 (none recorded yet); the wheel replay counts all of Nov 11 to 13 as development |
| | KXCOPPER15M | to 21:59Z | 22,554 | 90.9% | 13, 2.3 h | same |
| | KXWTI15M | to 23:44Z | 25,724 | 80.4% | 14, 2.0 h | same |
| | KXEURUSD15M | to 21:59Z | 23,596 | 89.9% | 13, 2.0 h | same |
| | KXGBPUSD15M | to 21:59Z | 24,471 | 90.9% | 11, 2.0 h | same |
| | KXUSDJPY15M | to 21:59Z | 25,845 | 91.9% | 10, 2.0 h | same |
| | KXAUDUSD15M | to 21:59Z | 27,770 | 89.9% | 7, 2.0 h | same |
| | KXUSDCAD15M | to 21:59Z | 28,068 | 90.7% | 7, 2.0 h | same |
| | KXNATGAS15M | to 23:59Z | 30,370 | 95.0% | 6, 2.0 h | same |
| | KXHYPE15M | to 23:59Z | 29,046 | 76.0% | 7, 2.3 h | same |
| | KXBNB15M | to 23:44Z | 30,406 | 73.9% | 6, 2.0 h | same |
| | KXINX15M | 2026-11-13 16:46Z to 20:59Z | 2,945 | 92.1% | 0 | none (13 windows in one run) |
| **book**, quote-data `book/` (Bitcoin hourly ladder, 7 strikes, 87 files) | KXBTCD | 2026-10-29 10:26Z to 2026-11-07 13:59Z | 1,257,284 | 74.9% | 18, 6.0 h | MMSIM1 held-out from 2026-11-07T15:00Z (refuses read before Nov 24): closes from then not counted; MMMAP1 keeps events closing before it |
| **combo**, combo-data `combo/` (52 files, quotes) | combos (exchange index 1) | 2026-11-12 14:36Z to 2026-11-14 02:11Z | 20,800 | 2.3% | 28, 7.0 h (cadence 30 minutes) | none registered |

NC15 note: gaps are the 4 hour block structure (two blocks missing before the first run and between runs, as in the coverage note); no weekend yet. Each NC15 and R6 row is a poll at 5 s and 2 s inside a window.

## 2. Quote and snapshot recorders (best bid and ask, rule 18)

| Source | Series | First to last | Rows | Two-sided | Gaps over 30 min | Held out and cut |
|---|---|---|---|---|---|---|
| **quotes**, quote-data `quotes/` (84 runs; about 0.5 s but only in the last 150 s of each window) | KXBTC15M, KXETH15M, KXXRP15M, KXDOGE15M, KXSOL15M (same row count each: 232,082) | 2026-10-22 19:57Z to 2026-11-08 23:59Z | 232,082 each | 22.2%, 23.4%, 26.3%, 24.7%, 24.2% | 45 each, longest 9.0 h | closes from 2026-11-09T00:00Z not counted (CFRTI1-BTC held-out, spot lead); 92,634 later rows skipped. The low two-sided share is by design: the rows are the last minutes before the close, when one side is near 0 or 1 |
| | KXGOLD15M | 2026-10-28 17:27Z to 2026-11-08 23:59Z | 107,234 | 33.2% | 22, longest 51.5 h (weekend) | same cut |
| **pol-data** `polrec/` (24 series with rows, 30 minute cadence; 49 files) | politics series (KXTRUMPAPPROVE, KXTRUTHSOCIAL, KXHORMUZ*, KXPANAMAWEEKLY, KXSUEZWEEKLY and others) | 2026-11-11 19:32Z to 2026-11-14 02:02Z | 8,913 in all (3 to 1,274 per series) | 83.7% | 507 in all (cadence); longest 17.0 h | none registered; politics recorder rows are not cut |
| **sports-data** `ingame/` (29 files, about 20 s while a game is hot) | moneyline (ml), spread, total | 2026-11-08 23:55Z to 2026-11-14 00:00Z | ml 563,678; spread 243,332; total 243,332 | 99.1%, 97.9%, 97.2% | 10 each, longest 6.2 h | in-game lag family closed; no cut |
| **daily**, quote-data `daily/quotes/` (41 files) | 49 series (monthly max/min crypto, daily and weekly FX and commodity ladders, KXUST*, KXCPI, KXSOFRD) | 2026-11-04 01:37Z to 2026-11-14 01:42Z | 26,864 | 58.0% | 1,195 in all (hourly and daily cadence); longest 144.4 h | none registered in the slices I read (SOFR1 and ONRRPCAL read the REF rows) |
| **wxens**, quote-data `wxens/quotes/` (21 files) | 14 KXHIGH temperature series | 2026-11-04 13:19Z to 2026-11-13 17:23Z | 684 | 82.0% | 80 in all; longest 191.8 h (sampled looks) | WXENS1 closed; no cut |
| **ref**, **raincal**, **deribit**, **oklq**, **sportspre** | not counted here (not on the list; ref has no price book, raincal and deribit are not Kalshi books, oklq is OKX, sportspre stopped Nov 11 for ESPN's terms) | | | | | |

## 3. Perpetuals (prices not on a 0 to 1 scale; rule 18 as bid > 0, ask > 0, bid < ask)

| Source | Series | First to last | Rows | Two-sided | Gaps and note |
|---|---|---|---|---|---|
| perp-data `perps/` (hourly, 25 files) | Crypto, Energy, Equities, Indices, Metals (by class) | 2026-10-21 16:56Z to 2026-11-14 02:00Z | 2,109 / 202 / 4,088 / 316 / 636 | 95.5% / 52.5% / 46.2% / 67.1% / 97.5% | cadence is 60 minutes, so every gap exceeds 30 minutes (about 105); longest 11.0 h. The Equities share counts the days before stock perps traded (listed Nov 5 18:39Z) |
| perp-data `perps30/` (30 s, two files) | same classes | 2026-11-06 20:46Z to 2026-11-13 21:59Z | 6,000 / 788 / 23,624 / 924 / 1,848 | 97.5% / 39.1% / 75.6% / 66.7% / 100.0% | recorded in the open and close windows only (the 166.7 h gap is the week between the two files) |
| perp-data `perps10/` (Sunday 10 s) | | none yet: first Sunday run is Nov 15 | | | |
| perp-data `kalshi1m/` (1 minute candles of the public candlestick endpoint, 6 files) | 66 perpetual tickers (stocks, indices and others) | 2026-11-06 00:00Z to 2026-11-13 00:00Z | 365,198 | 99.9% | 439 gaps in all (nights and weekends), longest 50.3 h; candles, not polls |

## 4. Other sources named in the order

- **signals** (REGISTRY.json logger): no data files exist; no registry entry is enabled.
- **kalshi-pull-data runs** (58 job folders at the Nov 13 count, 9,102 files, now more): rule 18 on candle minutes is NOT computed here, because these runs belong to cards with held-out thirds and reading their price fields for a table would be a read; the series, spans and held-out matches are in the History Miner's `workers/history_miner/DATA_INVENTORY_NOV13.md` (145d92a4), the file counts in `DATASET_TABLE_NOV13.md`. The one two-sided profile on a pull run is the KXINX15M profile on SPXOI1_CANDLES (n 133 windows, see my message of Nov 14), which the Head ordered.

## 5. What this says about which new cards fit the data

- **Book depth and fill checks are possible only on R6 (five crypto and gold series, Oct 29 to Nov 4 for development), NC15 (11 series, 2.5 days), the Bitcoin hourly ladder (to Nov 7 15:00Z) and the S&P 15 minute market (13 windows).** Two-sided share is 69% to 72% on R6 development rows, 74% to 95% on NC15 rows (lowest on HYPE, BNB and silver), 75% on the ladder.
- **The quotes recorder cannot judge a fill** (top of book only, last 150 s, two-sided 22% to 33%, held out after Nov 9).
- **Short data:** NC15 is two and a half days with no weekend, KXINX15M three hours, combo 36 hours with only 2.3% of rows two-sided, politics three days of 30 minute snapshots, perps 30 s one week in two windows, in-game six days.
- **Largest unread two-sided sets:** in-game moneyline (563,678 rows at 99% two-sided, six days) and the perps candles (365,198 rows, 99.9%) have no committed card of ours reading them as of the field inventory.
