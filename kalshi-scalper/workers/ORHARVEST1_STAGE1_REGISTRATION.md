# ORHARVEST1 stage 1 registration (counts only), Nov 12, 2026

Written and committed BEFORE any count was run. Protocol: `IDEA_DESK_A_PROTOCOLS.md` section P5 (branch `claude/idea-desk-a`), reproduced here.

**Owner constraint (Nov 11):** Open-Meteo is stopped and its data is a barred source. `quote-data:wxens` files were built by a recorder that also read Open-Meteo ensembles. This stage uses ONLY the Kalshi quote and market columns of `wxens/quotes/` and `wxens/quotes_low/`. It does not open `ens*`, `nws*`, `obs*`, `events*`, `runs*` or `results*` (results are an outcome file; stage 1 reads no outcome).

**Header of a quotes file (read once, 18 columns):** `slot_ts, poll_ts, server_date_header, city, look, target_date, series, ticker, event_ticker, close_time, strike_type, floor_strike, cap_strike, yes_bid, yes_ask, last, volume, status`.
- USED (Kalshi market and quote columns): `slot_ts, poll_ts, city, target_date, series, ticker, event_ticker, close_time, strike_type, floor_strike, cap_strike, yes_bid, yes_ask, status`.
- IGNORED (never joined or printed): `look` (a recorder label), `server_date_header`, `last`, `volume` (stage 1 does not need them). No forecast, ensemble, model-probability or observation column exists in these files; if one had, it would be ignored. Over-round and in-band legs ARE computable from Kalshi columns alone, so no stop.
- Frozen-window key (DATA_INVENTORY): the wxens rows are H10 (Nov 4 to Nov 11), no frozen window applies.

**Stage 1 rules (as written in P5):**
0. Fee: weather series fee type is taken from COST1 (15,468 of 15,663 series plain `quadratic`, maker multiplier 0; the 0.0175 maker rate sits on about 160 sports and futures series). No API call is made to verify the weather series individually; stated as presumed plain `quadratic`, maker fee 0, unverified.
1. A snapshot (event_ticker x slot_ts) is COMPLETE when its brackets tile the line (contiguous `floor_strike`/`cap_strike`, an open-ended `less` bracket at the bottom and `greater` at the top, none missing) and every bracket has a bid and ask. Report the complete share.
2. Per complete snapshot: `over = sum(yes_ask) - 1`, `under = 1 - sum(yes_bid)`, number of IN-BAND legs, sum of their asks. **In-band leg:** YES ask 0.13 to 0.88 inclusive and ask minus bid at least 0.02.
3. Median and 10th to 90th percentile of `over`, `under` and in-band count by hours to close (24+, 12 to 24, 6 to 12, 2 to 6, under 2), by city, highs and lows apart.
4. Snapshots per event.

**Kill:** CLOSED if the median `over` is under 4c in every hours-to-close bucket holding at least 100 complete snapshots, or if the median in-band leg count is under 2. Hours to close = `close_time` minus `slot_ts`.

**Count of tests:** 0 new. Stage 1 is descriptive counts, no rule scored, no outcome read, no try. It adds nothing to the 1.1M ledger (N unchanged, bars stay at z about 5.34 and, at N 8,795, about 4.39). The scored stage 2 stays queued behind MMSIM1's held-out read (about Nov 24).

Deviation rule: if the bracket tiling check needs a definition detail not above (for example how a duplicated poll in one slot is handled), take the last poll in the slot and say so in the result.
