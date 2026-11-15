# Cut extracts (Forensics desk, Nov 15, 2026; the Head's order of 14:34Z)

One extract per card from the research-data archive (parts and whole sha256 verified against MANIFEST.txt). Built by `extract_card.py` from `<CARD>_spec.json`; each `<CARD>_cutlog.json` holds the spec and the markets dropped per cut. Hashes: `SHA256SUMS.txt` (of the .xz files). Binance folders and any live order export were not opened.

Tables: `market(ticker, series, open_ts, close_ts, result, strike, src)` and `candle(ticker, end_ts, bid_c, ask_c, volume, oi)` (FLIPS0X also bid_h, bid_l, ask_h, ask_l, price_c). First source wins on a duplicate ticker. Every kept market carries ALL its candles (the full path after entry).

**Reader rules.** Drop candles whose end_ts is after the market's close_ts (the archive holds a few post-close candles; Auditor B). Label every recompute "same rule, window reduced by held-out cuts to <dates in the cut log>". Halves are taken on the reduced set. Under 30 trades is "no evidence at n = x".

| Extract | Series | Window | Cuts |
|---|---|---|---|
| OIREL (also the OICORE rule extract: same series, window, cuts) | KXBTC15M | 2026-08-06 to before 2026-10-03 | XOI1 from 2026-10-03; QSTALE1/TSLM1 (Oct 5) and FILLHAIRCUT1 (Oct 29) are later |
| XRPFAV (XRPFAV6, XRPFAV10) | KXXRP15M (alts2) | same | same |
| SEARCH1 | KXBTC15M, KXETH15M | same | same |
| FLIPS0X | the card's loader only (ideas20.SOURCES); 8 of its 16 series have data inside the cuts | 2026-08-06 to before 2026-10-24 (own forward held out) | XOI1 Oct 3 (XRP, HYPE, BNB, NEAR, ZEC); FXREF1 2026-10-03T16:00Z (WTI, EURUSD, GBPUSD, USDJPY); Oct 5 (gold, silver, copper, natgas, platinum, palladium) |
| BAND2 (history rows; live aggregates NOT extracted) | gold, DOGE, ETH, BTC, XRP | 2026-08-06 to before 2026-10-28 | XOI1 Oct 3 (BTC, XRP); TIECOND1 Oct 5 (gold); no registered W3 found for ETH or DOGE |

Not extracted: HRSEAS1 night lull ("data unavailable": conf2_lad.sqlite is in neither archive), USWEEP and the other cards the Head dropped. SPOTLEAD1 pending its registration.
Open-held-out check of INX1, RO1, OVN2, WXDEAD1, SLOTEX-ETH: none holds an open window before Oct 3 on Bitcoin, Ethereum or XRP (registration text; sent to Auditor B and the Head).
`CENSUS_LISTING_ECONOMICS_SERIES.tsv`: Economics series rows from the truncated CENSUS_LISTING series answer (224 rows; a floor).

## OIREL-X (Nov 15, 2026; Desk A's request, the Head's order)
Every 15 minute series in the archive with open interest candles, EXCEPT KXBTC15M (OIREL). Same tables and columns as OIREL; sources in hs1 order (alts2, alts3, alts4, book, l1b, e3b), then fresh, then rep; first source wins; all candles kept. Window: closes 2026-08-06 to before 2026-10-03T00:00Z; SOL's own cut 2026-09-30T09:30Z applied (242 markets). `OIRELX_table.md`: markets kept, first and last close and the share of candles with oi, per series. Series whose archive history starts after Oct 3 (AUDUSD, USDCAD, BRENT and the four rates series, all in rep.sqlite) keep 0 markets. Archive oi is populated on every candle of every series (oi not null 100%); a few series have some oi = 0 (EUR, GBP, JPY pairs about 4% to 5%). Readers drop candles ending after close.
