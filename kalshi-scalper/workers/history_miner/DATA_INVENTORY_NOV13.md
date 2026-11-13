# Recorded data that can support a development read today: inventory (History Miner, 2026-11-13 21:45Z)

At the Head of R&D's order of 21:37Z (owner order, rnd-queue 9dcfeee1: only completely unique strategies count).
- **Counts only.** Every number is from a git tree listing (file names, date folders) or from a kalshi-pull run's manifest (its job requests and row statuses). No data file, answer, price or result was opened.
- **Fill-check limits** are from each recorder's own description (CLAUDE.md and the scripts on main), not from data.
- **Not re-checked here:** whether any test's held-out window overlaps a set. Rule 17 and HELDOUT_REGISTRY decide that per card.
- **Split with Forensics:** I asked Forensics to take the live-account side and anything it has already listed; no answer yet.

## A. Continuous recorders, on their data branches

| Set (branch:folder) | What | Files | Days, span | Fill check it supports | What it lacks for a fill check |
|---|---|---|---|---|---|
| quote-data:book15r6 (R6) | 15 minute KXBTC15M, KXETH15M, KXGOLD15M, KXDOGE15M, KXXRP15M (to Nov 13; Bitcoin, Ethereum and gold after it): 5-level book of both sides every 2 s, the public tape after each close, coverage with result, clock | 340 (85 runs x book, trades, coverage, clock) | 16, Oct 29 to Nov 13 | Full: decision poll and next poll within 4 s, depth to 5 levels, walked price | Nothing for a taker check. Queue position for a resting order is not recorded. Only 16 days on the branch. |
| quote-data:book | KXBTCD hourly ladder, 7 strikes near the money, 5 levels every 3 s from 55 min before each close, tape every 30 s | 258 (86 runs x book, trades, coverage) | 16, Oct 29 to Nov 13 | Full taker check at 3 s | Only 7 strikes; hourly Bitcoin only |
| quote-data:quotes (record_quotes) | 15 minute crypto (BTC, ETH, SOL, XRP, DOGE) plus KXGOLD15M: best bid and ask with sizes about twice a second in the last 150 s; hourly and daily ladders (ladder.csv); spot trades of Coinbase, Kraken, Bitstamp; results; clock | 641 (111 runs: quotes, coverage, results, spot, clock; 86 with ladder) | 23, Oct 22 to Nov 13 | Top of book only: the size at the touch | No depth beyond level 1, so no walk for an order larger than the touch. Only the last 150 s of each window. The spot reads carry an owner-accepted terms risk (Coinbase unread, Bitstamp licence). |
| nc-data:nc15 (NC15) | 11 non-crypto 15 minute series (silver, copper, WTI, EUR/USD, GBP/USD, USD/JPY, HYPE, BNB, AUD/USD, USD/CAD, natural gas): 5-level book every 5 s, tape, coverage, clock | 48 (12 runs) | 3, Nov 11 to 13 | Full, with a 6 s second look | Only 3 days, so far too short for 100 trades on most cards. The first seconds of a window may be missing (discovery lag, not flagged). |
| quote-data:deribit | deribit, index, kalshi, results and coverage files per run | 335 (67 runs) | 12, Nov 2 to 13 | Unknown | Not described in CLAUDE.md; whatever "kalshi" holds needs reading before any claim |
| combo-data:combo | Combo markets: quotes of up to 5,000 listed, 5-level book of the 40 tightest, trades of the 15 most traded, every 30 min | 168 (42 runs x books, coverage, quotes, trades) | 2, Nov 12 to 13 | 5-level book on 40 combos a run | 30 min between snapshots, so no second look; 2 days only |
| pol-data:polrec | 45 politics series: yes and no bid and ask with sizes every 30 min; results of markets closed in the last 48 h | 60 (40 quotes, 20 results) | 3, Nov 11 to 13 | Top of book with size, every 30 min | No depth; 30 min resolution; 3 days |
| sports-data:ingame | NBA, NHL, NFL moneyline plus 2 spread and 2 total markets: bid and ask with sizes at about 20 s while hot | 56 (28 obs, 28 coverage) | 6, Nov 8 to 13 | Top of book with size, at 20 s | No depth; no second look within a few seconds |
| quote-data:daily | the daily recorder's watchlist (NOWCAST1, FEDIMPL1, BARRIER1, SOFR) | 80 (quotes, ref, results, runs) | 10, Nov 4 to 13 | Top of book at its cadence | No depth |
| quote-data:ref | Kalshi entertainment and count markets with reference pages (Steam only after Nov 11; the Yahoo bars stopped) | 107 (bars, quotes, refvals, results, runs) | 10, Nov 4 to 13 | Top of book at its cadence | No depth; most of its series were parked on Nov 11 (terms) |
| quote-data:wxens | weather brackets with NWS forecast and observations (the Open-Meteo `ens` tables stop Nov 11) | 206 | 10, Nov 4 to 13 | Top of book | No depth. The weather forecast family is closed (declined list). |
| quote-data:oklq | OKX Bitcoin swap liquidations and coverage | 24 (12 runs) | 3, Nov 11 to 13 | n/a (no Kalshi quotes) | LIQREV's own source; its development read is not before Nov 30 |
| quote-data:raincal | rain recorder (deleted Nov 12): quotes, obs, pop, results, coverage | 245 (49 runs) | 11, Nov 2 to 12 | Top of book | Recorder deleted; RAINCAL retired unread |
| quote-data:sportspre | ESPN pre-game (stopped Nov 11, terms): quotes, results, predictor, games | 336 (56 runs) | 10, Nov 2 to 11 | Top of book | Cannot be extended; ESPN-derived fields carry the terms stop |
| perp-data | perps hourly (24 day files, Oct 21 to Nov 13); perps30 (1 file, Nov 6); kalshi1m candles (6, Nov 6 to 12); funding (6, Nov 6 to 12); cash1m (4, Nov 6 to 11, Yahoo, research reads stopped) | 41 | as listed | Candles and hourly snapshots only | No book |
| quote-data:book15 (R2) | replaced by R6 | 3 | 1, Oct 29 | (as R6) | One day |

## B. Landed kalshi-pull runs (manifests only; all complete with 0 non-200 rows unless stated)
1-minute candles carry the bid and ask close (and high and low), volume and open interest. **No size at all**, so a fill check on them is at best "filled at the ask seen" (an upper bound), with the next candle as the only second look.

| Run | Requests | Span | Series |
|---|---|---|---|
| CFRTI_K_CANDLES | 215 | Sep 12 to Nov 4 | KXBTC15M (5,127 tickers) |
| CFRTI_K_R6SLICE | 20 | Oct 30 to Nov 4 | KXBTC15M (407, inside the above) |
| CFRTI_K_PROBE | 1 | Aug 20 | KXBTC15M (24) |
| CFRTI_K_LISTS | 2 | settled Jun 1 to Nov 5 | KXBTC15M list |
| WHEEL0_CANDLES_DOGE, _XRP, _GOLD, _ETH | 246, 246, 179, 187 | Sep 11 to Nov 12 (ETH to Oct 28) | KXDOGE15M, KXXRP15M, KXGOLD15M, KXETH15M |
| WHEEL0_LISTS | 4 | Sep 12 to Nov 12 | the four series' lists |
| PERPBTC1M | 163 | Jun 3 to Nov 13 | KXBTCPERP |
| INGAMELAG_M1A, M1B | 108, 107 | Oct 19 to Nov 11 | KXNBAGAME, KXNFLGAME, KXNHLGAME |
| NHLOT_CANDLES, NHLOT_LISTS | 86, 4 | Oct 21 to Nov 12 | KXNHLGAME (NHLOT closed on two builds) |
| ESOCTIE_CANDLES_P1 to P4, ESOCTIE_LISTS | 60 x 4, 4 | Oct 7 to Oct 22 | KXESOCCERGAME |
| INPLAYJUMP_T_CH1 to CH5, T_ITF1 to ITF5, C_ESOCCER, C_TTEBB, PILOTVAL, LISTS | about 1,450 candle requests | Sep 11 to Oct 22 | tennis challengers and ITF, esoccer, e-basketball and Liga Pro |
| MAPBREAK_CANDLES (**stopped_size**), _M2, _REST, _LISTS | 282, 65, 117, 20 | Sep 11 to Oct 22 | CS2, Dota 2, LoL, Valorant games and maps |
| VOIDSNAP_CANDLES | 79 | Sep 12 to Oct 22 | KXCS2GAME |
| REMATCH_STAGE1_CANDLES | 120 | Oct 14 to Oct 22 | KXESOCCERGAME |
| CANDLEGAP_CS2, CANDLEGAP2_TTEBB | 1, 3 | Nov 12 to 13 | CS2; e-basketball and Liga Pro (CANDLEGAP-2 closed) |
| TIE3_CANDLES | 54 | Oct 26 to Nov 12 | first-half soccer (Brasileiro, Bundesliga, EPL and others) |
| SPREADCELL1 (**stopped_size**), _REST, SPREADLISTS | 274, 36, 11 | Sep 7 to Nov 11 | MLB, NBA, NCAAF, NCAAMB, NFL spreads (the sports spread cell is retired after its FAIL) |
| NOSIDE1_CANDLES | 1,034 | Oct 20 to Oct 22 | KXTRUMPAPPROVE, KXVHGCB and historical markets |
| POLAPPR1_CANDLES, _P2, _P3 | 1,006 x 3 | Jun 23 to Feb 15 | approval markets (POLAPPR1 closed on two builds). One earlier folder of POLAPPR1_CANDLES (0641Z) has an unreadable manifest. |
| Lists only: CENSUS_LISTING, HOURLYTEMP_LISTS, RULESREAD_LISTS, SOCDERIV_LISTS, TESTING_LISTS_BUNDLE (also 18 weather candles), ROLLOFF_PROXY, HISTCUTOFF1, COMBO1_OPENBOOK | 40, 9, 29, 67, 133, 6, 2, 3 | as their jobs | |
| POLGAPH_LISTS | 69 | Sep 12 to Nov 12 | **listed in HELDOUT_PULL_RUNS.md: not opened by any reader without the Head's go** |

## C. What follows for a development read TODAY (counts, not results)
- **A full taker fill check** (depth, a second look within seconds) exists only on R6 (5 crypto 15 minute series and gold, 16 days), the hourly Bitcoin ladder book (16 days) and NC15 (11 series, 3 days). Combos have depth but no second look.
- **Long history** (weeks to months) exists only as 1-minute candles: no size, so "filled at the ask seen" is an upper bound. The candle sets are the 15 minute crypto and gold (Sep 11 to Nov 12), Bitcoin perps (Jun 3 to Nov 13), sports and esports games (Sep to Oct), and politics approval (Jun to Feb).
- **About a new card:** any card on a 15 minute crypto or gold market needs a field that is NOT price or Kalshi's own tape, or the declined list closes it (taker flow, cheap-side grammar, favourite-late, spot lead).
