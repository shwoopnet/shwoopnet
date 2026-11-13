# Every recorded dataset: what can be read today (Forensics desk, Nov 13, 2026)

For the Head's owner order (rnd-queue 9dcfeee1): 20 to 30 completely unique strategies above cash PF 1.3 on development data, read only on data already recorded or merged. **Counts and names only; no value was opened; zero Kalshi requests.** Taken from tree listings of the data branches at about 21:50Z Nov 13 (file counts and folder dates), the recorder scripts and workflows on main, `WHEEL_PLACES_COVERAGE_NOV13.md` and `RECORDED_FIELD_INVENTORY_NOV13.md` (this folder). Split: this table covers the live recorder branches and the landed pull runs; the History Miner covers the archived history (`research-data`, the local candle files).

**Held-out column.** From `HELDOUT_REGISTRY.md` (Desk A, `rnd-queue`) and `HELDOUT_PULL_RUNS.md` (main), by first reading of the registry's table; it is conservative and partly from file names. **It is not complete: check the registry row of any card before reading a window.** A window listed here is not readable by a development read. "Fill check" means: can a resting or taker order's fill be judged from this data (book levels with sizes plus the trade tape).

## 1. Live recorders (poll rate, span, fill check, held-out windows)

| Dataset (branch, folder) | Series | Span in files | Rate and size | Fill check | Held-out or counted windows (from the registry) |
|---|---|---|---|---|---|
| **R6**, `quote-data` `book15r6/` (340 files, 85 runs, 16 dates) | KXBTC15M, KXETH15M, KXXRP15M, KXDOGE15M, KXGOLD15M | closes Oct 29 22:15Z to Nov 13 20:00Z, 1,223 windows per series (a full day is 96; short days Oct 30, 31, Nov 2, 9, 10) | 2 s book (levels 1 to 5 both sides, sizes) plus the whole tape with taker side, per window | YES: books plus tape (ids not stored) | DEPTH1 block C Nov 9 to 13 (gold, Bitcoin; read from Nov 14); CFRTI-B and CFRTI-K held-out closes from Nov 5 (Bitcoin); FILLHAIRCUT1 period B from Nov 9; GOLDHAIRCUT1 period B Nov 9 to 11; BOOKCH1 forward freeze Nov 4 (last third of the forward period); MMMAP1 R6 part and the wheel replay count Nov 11 to 13. XRP, Dogecoin and gold stop after Nov 13; Bitcoin and Ethereum run to Nov 20 |
| **NC15**, `nc-data` `nc15/` (48 files, 12 runs, 3 dates) | 11 non-crypto series (silver, copper, WTI, EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CAD, natural gas, HYPE, BNB) | Nov 11 19:45Z to Nov 13 20:00Z, 181 windows per series (about 13 short of 194) | 5 s book, levels 1 to 5, tape, same columns as R6 | YES, as R6 | NC15DEPTH1 scoring windows from Nov 19; the wheel replay's frozen sheet counts all recorded windows. No weekend yet in the data |
| **NC15 KXINX15M** (same folder) | S&P 500 15 minute | Nov 13 17:00Z to 20:00Z, 13 windows, one run | 5 s | YES | none registered on these books; SPXOI1 and SPXEVENT1 use other inputs |
| **book**, `quote-data` `book/` (258 files, 16 dates) | KXBTCD hourly ladder, 7 strikes nearest the money | Oct 29 to Nov 13 | 3 s book levels 1 to 5, tape every 30 s with trade ids | YES (ladder; not a 15 minute series) | MMSIM1 held-out from 2026-11-07T15:00Z (refuses read before Nov 24); MMMAP1 keeps events closing before Nov 7 15:00Z; BOOKIMB1 holdout Nov 2 to 3 |
| **quotes**, `quote-data` `quotes/` (641 files, 111 runs, 23 dates) | five crypto 15 minute series, gold 15 minute, hourly ladders (86 runs carry ladder files) | Oct 22 to Nov 13 | about 0.5 s top of book in the last 150 s of each window; SPOT (Coinbase ticker, Kraken, Bitstamp: price, size, time) in the last 600 s | PARTIAL: top of book with sizes only, no tape; the stale-quote audit voided list-copy quote reads | CFRTI1-BTC held-out from Nov 9 (spot lead); RECORD1 and the older spot cards used it |
| **book15** (R2, superseded), `quote-data` `book15/` | Bitcoin, Ethereum, gold | 3 files, Oct 29 only | 3 s | YES | none |
| **combo**, `combo-data` `combo/` (168 files) | multivariate combos | Nov 12 to 13 | 30 min quotes, books of the 40 tightest, trades of the 15 most traded | PARTIAL (books of a sample) | none registered; expects little data (stop rule at 14 days) |
| **politics**, `pol-data` `polrec/` (60 files) | 42 politics series | Nov 11 to 13 | 30 min quotes with sizes, volume, open interest; no book | NO | none registered; accruing |
| **in-game**, `sports-data` `ingame/` (56 files) | NBA, NHL, NFL moneyline, spread, total | Nov 8 to 13 | about 20 s while a game is hot (2 min before), top of book with sizes | NO (top of book only) | in-game lag family closed |
| **daily**, `quote-data` `daily/` (80 files, 10 dates) | RECDAILY watchlist (rates, SOFR, indices, commodities) | Nov 4 to 13 | per run quotes with open interest, results, REF rows (NY Fed SOFR table) | NO | SOFR1 and ONRRPCAL read the REF rows; none frozen in these files that I found |
| **ref**, `quote-data` `ref/` (107 files, 10 dates) | KXSTEAMTOPSELLER and the Kalshi count and entertainment series | Nov 4 to 13 | 2 h | NO | none found; Yahoo bars stopped, Rotten Tomatoes, Metacritic, Billboard, kworb removed (terms) |
| **wxens**, `quote-data` `wxens/` (206 files, 10 dates) | weather brackets (NWS forecast, grid, station observation, IEM extremes) | Nov 4 to 13 | two starts an hour | NO (quotes only) | WXENS1 closed; WXDAYEND reads observed extremes |
| **raincal**, `quote-data` `raincal/` (240 files, 11 dates, Nov 2 to 12) | rain calibration | Nov 2 to 12 | per run | NO | not in the registry slices I read |
| **oklq**, `quote-data` `oklq/` (24 files, 3 dates) | OKX Bitcoin swap liquidations | Nov 11 to 13 | 4 starts a day | NO (not a Kalshi market) | none; forward only, no card |
| **deribit**, `quote-data` `deribit/` (335 files, 12 dates) | Deribit options | Nov 2 to 13 (stopped; W-DERIBIT1 retired) | per run | NO | none |
| **sportspre**, `quote-data` `sportspre/` (336 files, 10 dates) | sports pre-game quotes with ESPN reference | Nov 2 to 11 | STOPPED Nov 11: ESPN terms forbid automated reads; do not extend | NO | W-CAT-SPORTS1 uses a different source |
| **perps**, `perp-data` `perps/` (24 files, Oct 21 to Nov 13); `perps30/` (1 file, Nov 6); `kalshi1m/` (6, Nov 6 to 12); `funding/` (6, Nov 6 to 12); `cash1m/` (4, Nov 6 to 11) | 88 perpetuals (21 crypto, 67 stocks, indices, metals, oil) | see counts | hourly list; 30 s at open and close windows (so far one weekday file); 1 minute candles and funding history; `cash1m` is Yahoo (stopped, do not extend) | NO (top of book only) | PERPGEN and BINPATH frozen lists named in the registry, not read by me |

## 2. Landed pull runs on `kalshi-pull-data` (9,102 files under `pull/`, 58 job folders, all landed Nov 12 or 13)

Counts are answer files per job folder (a job may hold several runs and pages). **What each run covers (series and span) is in its job file on main and its manifest; I did not open any answer file.** Do not open a folder in `HELDOUT_PULL_RUNS.md` (listed: `POLGAPH_LISTS/2026-11-13T0627Z_43378777252`).

| Group | Job folders (files) | Kind |
|---|---|---|
| Crypto, gold, wheel candles | WHEEL0_CANDLES_DOGE 248, _ETH 189, _GOLD 181, _XRP 248; WHEEL0_LISTS 24; CFRTI_K_CANDLES 217, _LISTS 22, _PROBE 3, _R6SLICE 22; PERPBTC1M 165 | 1 minute candles and market lists (candles carry open_interest_fp and bid, ask, volume); no book or tape |
| Politics | POLAPPR1_CANDLES 1,039, _P2 1,008, _P3 1,008; POLGAPH_LISTS 71 (listed held-out run); NOSIDE1_CANDLES 1,036; RULESREAD_LISTS 36; SOCDERIV_LISTS 72; CENSUS_LISTING 89 | candles and lists |
| Sports and esports | INPLAYJUMP_T_CH1..CH5 (125, 121, 133, 128, 106), _T_ITF1..ITF5 (161, 168, 159, 159, 89), _C_ESOCCER 115, _C_TTEBB 173, _LISTS 39, _PILOTVAL 24; INGAMELAG_M1A 110, _M1B 109; ESOCTIE_CANDLES_P1..P4 (62 each), _LISTS 27; MAPBREAK_CANDLES 167, _M2 67, _REST 119, _LISTS 54; NHLOT_CANDLES 88, _LISTS 9; REMATCH_STAGE1_CANDLES 122; TIE3_CANDLES 56; VOIDSNAP_CANDLES 81; CANDLEGAP2_TTEBB 5, CANDLEGAP_CS2 3; SPREADCELL1 240, _REST 38; SPREADLISTS 13 | candles and lists |
| Other | HOURLYTEMP_LISTS 15, HISTCUTOFF1 4, COMBO1_OPENBOOK 5, ROLLOFF_PROXY 9, TESTING_LISTS_BUNDLE 135 | lists, a few books |

**What the pull runs can and cannot do for a new strategy:** candles give a one minute bid and ask, volume and open interest per market and a result; they cannot judge a fill (no book or tape), and a stale last-trade price is not a fill. Any new pull needs Main and the Head (the owner order says no new jobs now).

## 3. Archived history (the Miner's side, listed for completeness)

`research-data` branch: 26 files, mostly xz-compressed sqlite databases of the old research branch (`l1b`, `book`, `alts2` to `alts4`, `arb1`, `e3b`, `flb1`, `ladders`, `pm1`, `pm2`, `sports`, `weather`, `xm1`, `json_prices_ohlc`) and `research-data.tar.gz` in six parts. Per the registry these hold the 15 minute and ladder candle history from 2026-08-06 and are the source of the discovery and validation windows (for example Aug 6 to Sep 20 and Sep 21 to Oct 27 for several NEWH cards). Row counts and held-out cuts are the History Miner's to report.

## 4. What this means for "readable today"

- **Fill-checkable and not held out:** R6 closes Oct 29 to Nov 8 (all five series) except the cards' own cuts; NC15 Nov 11 to Nov 13 (small, 181 windows per series); the hourly ladder up to Nov 7 15:00Z.
- **Short or small N:** NC15 (two and a half days, no weekend), KXINX15M (13 windows), combo and politics (accruing, no book), perps 30 s (one file).
- **No fill check possible:** quotes and the pull candles, daily, ref, wxens, politics, in-game, perps.
- **Do not extend:** sportspre (ESPN terms), `cash1m` (Yahoo terms), Polymarket, Rotten Tomatoes, Metacritic, Billboard, kworb.
- The DEPTH1 read is still due at 00:00Z Nov 14 on the Head's word; until then no one reads R6 block C (Nov 9 to 13, gold and Bitcoin).
