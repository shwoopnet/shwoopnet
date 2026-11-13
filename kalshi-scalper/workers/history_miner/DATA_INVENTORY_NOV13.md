# Recorded data that can support a development read today: inventory (History Miner, 2026-11-13 21:45Z)

At the Head of R&D's order of 21:37Z (owner order, rnd-queue 9dcfeee1: only completely unique strategies count).
- **Counts only.** Every number is from a git tree listing (file names, date folders) or from a kalshi-pull run's manifest (its job requests and row statuses). No data file, answer, price or result was opened.
- **Fill-check limits** are from each recorder's own description (CLAUDE.md and the scripts on main), not from data.
- **Not re-checked here:** whether any test's held-out window overlaps a set. Rule 17 and HELDOUT_REGISTRY decide that per card.
- **Split with Forensics (agreed 21:39Z):** Forensics holds the recorder datasets. This file fills its three gaps: B (pull runs: series and spans from manifests), C (the research-data branch) and D (pull runs against the held-out registry).

## A. Continuous recorders: SUPERSEDED by Forensics' table
Forensics had already inventoried the recorder side: `kalshi-scalper/workers/forensics/inventory/DATASET_TABLE_NOV13.md` on claude/forensics-desk at b756dbac, with WHEEL_PLACES_COVERAGE_NOV13.md and RECORDED_FIELD_INVENTORY_NOV13.md beside it. My first draft of this section (in git history at 82edf740) duplicated it and is withdrawn. Use Forensics' rows.

The one note from my draft not in Forensics' scope: quote-data:deribit (67 runs, Nov 2 to 13) is not described in CLAUDE.md.

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

## C. The research-data branch (from its own MANIFEST.md, MANIFEST.txt and FILES.txt only; no archive opened)
- **The Oct 20, 2026 archive:** 14 SQLite databases plus a price-file tarball, xz-compressed. Row counts and spans are from MANIFEST.md, counting the `market` table rows.
  - alts2: 19,139 rows, closes Sep 3 to Oct 13.
  - alts3 (commodities, Zcash, NEAR, XRP, Dogecoin): 32,314 rows, Aug 6 to Oct 13.
  - alts4: 5,442 rows, Aug 6 to Sep 3.
  - book (the 40 days L1 was found on: Bitcoin, Ethereum, gold): 10,293 rows, Sep 2 to Oct 12.
  - e3b (XRP, Dogecoin): 13,062 rows, Aug 6 to Oct 13.
  - flb1 (long-dated favourites): 28,005 rows, Aug 14 to Oct 13.
  - **l1b (the L1 holdout: Bitcoin, Ethereum, gold): 7,213 rows, Aug 6 to Sep 2.**
  - ladders (hourly Bitcoin, Ethereum, S&P ladders): 166,479 rows, Sep 4 to Oct 13.
  - sports: 9,118 rows, Sep 3 to Oct 13.
  - weather: 2,898 rows, Aug 6 to Oct 13.
  - xm1: 1,896 window rows, Sep 2 to Oct 12.
  - arb1, pm1 and pm2: test outputs; pm1 and pm2 are Polymarket-derived and parked.
  - SPY, QQQ, VIX, SCHD and JEPQ price files: Yahoo-derived; research reads are stopped.
- **The Oct 29, 2026 archive:** one 280 MB gzipped tar in 6 parts. FILES.txt lists 20 databases (alts2-4, arb2-4, book, crypto1, e3b, fresh, iv1, l1b, lad1, lad2, ladders, ladl1, rep, search5k, sports1, theta1), 6 folders (binance, binance_carry, cpi1, maker4, ment1, quote1) and many derived JSON and result files. No row counts are in its manifest.
- **The LADL1 partial:** gold daily 38 closes, weekly 9; Bitcoin hourly 138 closes.
- **What it is:** Kalshi's history reached back only about 69 days when it was made, so the August days cannot be pulled again. These are 1-minute candles: no size, so any fill on them is "at the ask seen". Many registered tests already read these windows (NEWH1 to NEWH16, GEN4 to GEN13, FALS1 to FALS5, FLOW1, MECHOI1 and others), so a new card on these series and dates must check HELDOUT_REGISTRY for spent holdouts.
- **Not done:** row counts inside the Oct 29 archive. Opening it is a data read; I will not do it without the Head's go.

## D. Pull runs against the held-out registry (rnd-queue:HELDOUT_REGISTRY.md at d29e0da1, 670 table lines)
- **Method:** a SERIES-NAME match only. For each run, the cards whose registry line names one of the run's series (from the request parameters and paths). It says which cards share a series, NOT whether their dates overlap; a reader must check dates per card. Counts of matching cards:
  - Bitcoin 15 minute runs (CFRTI_K_CANDLES, _LISTS, _PROBE, _R6SLICE): 69 cards each.
  - WHEEL0_LISTS: 54. WHEEL0_CANDLES_GOLD: 43. _ETH: 17. _XRP: 15. _DOGE: 12.
  - TESTING_LISTS_BUNDLE: 13.
  - MAPBREAK_CANDLES, _REST, _LISTS: 7 each. _M2: 2.
  - POLGAPH_LISTS: 7, and the run itself is on HELDOUT_PULL_RUNS.md.
  - The ESOCTIE, INPLAYJUMP esoccer and REMATCH runs: 6 each.
  - INGAMELAG_M1A and M1B: 6 each.
  - NHLOT_CANDLES: 5. NHLOT_LISTS: 4.
  - VOIDSNAP and CANDLEGAP_CS2: 5 each.
  - NOSIDE1_CANDLES, ROLLOFF_PROXY and POLAPPR1_CANDLES: 3 each.
  - TIE3_CANDLES: 3.
  - INPLAYJUMP tennis challenger runs: 3 each. ITF runs: 1 each. e-basketball runs: 2.
  - RULESREAD_LISTS: 1 (GOLF1). SPREADCELL1 and _REST: 1 (BOOKS2). HOURLYTEMP_LISTS: 1 (WXNEW1).
  - 0 for CENSUS_LISTING, COMBO1_OPENBOOK, HISTCUTOFF1, SOCDERIV_LISTS, SPREADLISTS.
  - 0 by this method for PERPBTC1M, POLAPPR1_CANDLES_P2 and _P3, whose request paths name tickers without a KX series prefix. Those three need a reader.
- **What follows:** the least-read ground for a NEW card is the runs with 0 or 1 matching cards. Those are lists and combos, golf, the sports spreads (the spread cell itself is retired), the ITF tennis candles (only INPLAYJUMP) and the perps candles. That is a count of names, not a judgement of any idea.
