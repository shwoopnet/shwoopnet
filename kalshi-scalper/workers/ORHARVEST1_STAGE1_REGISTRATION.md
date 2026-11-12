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

---

# RESULT (stage 1, run Nov 12, 2026; counts only, zero Kalshi calls)

Data: `quote-data:wxens/quotes/` and `quotes_low/`, Kalshi quote columns only (listed above), fetched through the GitHub contents API. Open-Meteo columns never opened. 1,248 bracket rows, 148 events, 208 snapshots (104 highs, 104 lows), 14 cities, 6 brackets per event (a `less`, four 2-degree `between`, a `greater`). Nothing was scored; no try; ledger N unchanged.

**Definition detail fixed while coding (disclosed, not a result choice):** the brackets are 2 degrees wide with the open ends at `less cap = first between floor` and `greater floor = last between cap`, so contiguity was tested on that grid. A first pass with the wrong grid marked every snapshot incomplete; the second pass used the grid above. Hours to close = `close_time` minus `slot_ts`; the first pass also had a unit slip (microseconds), caught because every snapshot landed in "under 2". Final numbers below are the corrected run.

**Complete share:** 208 of 208 (100%). **Snapshots per event: median 1, min 1, max 3** (148 events). Fee: weather series presumed plain `quadratic`, maker multiplier 0 (COST1: 15,468 of 15,663 series; not individually verified, no API call made).

Hours to close: only the 12-24 and 24+ buckets exist (the recorder's looks are the day before settlement). Median [p10 to p90] of over-round and in-band legs:

| kind | bucket | n | over median | over p10-p90 | under median | in-band median | in-band p10-p90 |
|---|---|---|---|---|---|---|---|
| high | 24+ | 68 | 6.0c | 1.7 to 10.0c | 5c | 1 | 0 to 2.3 |
| high | 12-24 | 36 | 5.0c | 1.5 to 8.0c | 3c | 1 | 0 to 2 |
| low | 24+ | 68 | 36.5c | 15.7 to 49.3c | 29c | 3 | 2 to 4 |
| low | 12-24 | 36 | 11.5c | 5.0 to 31.0c | 10c | 0 | 0 to 3 |
| pooled | 24+ | 136 | 10c | 3 to 46c | 13c | 2 | 0 to 4 |
| pooled | 12-24 | 72 | 7c | 3 to 24.9c | 4c | 1 | 0 to 2.9 |

Pooled overall: median over-round 9c, median in-band legs 2.0. By city the cells hold 2 to 15 snapshots, so none is readable alone (table in the run output; highs median over 4c to 8c in every city, lows 12c to 38c).

**Kill gate.** "Median over under 4c in every bucket with at least 100 complete snapshots": the only bucket with 100 or more is pooled 24+ (n 136), median 10c, so this arm did NOT fire (highs and lows apart, no bucket reaches 100). "Median in-band legs under 2": pooled 2.0 does not fire; highs alone are 1 (would fire) and lows 12-24 is 0, lows 24+ is 3. So the registered literal kill did not fire, but only because the lows carry it; the highs alone fail the leg count.

**Reading, honestly.** The lows' large over-round (a median of 36c at 24+ hours) is mostly wide spreads and thin books on illiquid lows brackets, which says what a taker pays, not what a resting offer at ask minus 1c would collect. The highs' 5c to 6c over-round is above the 4c bar but split across about 1 in-band leg. The decisive limit is the data: **a median of one snapshot per event means no STRICT fill inference is possible** (a fill needs a LATER snapshot of the same market), so stage 2 as registered cannot be scored on this recorder. It needs a tape or a denser snapshot cadence for the same markets.

**Verdict: NOT_KILLED_BUT_UNSCORABLE (stage 1 passes the literal gates; highs alone would fail the leg count; stage 2 blocked on data until a tape or repeated snapshots exist and the family slot opens after MMSIM1's Nov 24 read).**
