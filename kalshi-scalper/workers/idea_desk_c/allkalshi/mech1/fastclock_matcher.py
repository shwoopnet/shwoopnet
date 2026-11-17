#!/usr/bin/env python3
"""MECH1 fast-clock feasibility list, matcher part (Idea Desk C, Nov 17, 2026). No data is read here: it enumerates the (market family, signal field, clock) combinations of the held fast-clock sources
that are NOT under H20 or H21, computes the expected signals a day at a fixed 10% tail trigger from the clock alone, and runs Desk A's matcher (claude/idea-desk-a 424fb9f60, workers/mech) on each.
Usage: python3 -I fastclock_matcher.py <dir with mech_schema.py and mech_registry_build.py> > FASTCLOCK_COMBOS.json"""
import json, os, sys
sys.path.insert(0, sys.argv[1])
import mech_schema as S, mech_registry_build as B

TAIL = 0.10
ONE_PER = 15 * 60                                                      # at most one entry per name per 15 minutes (the same cooldown as the other perps cards)
def blocks(n_min):                                                     # 15 minute blocks a day inside n_min observed minutes
    return n_min / 15.0
def perps_rate(n_min):                                                 # P(at least one 10% tail event among 15 observations in a block), blocks a day times it; independence assumed
    return blocks(n_min) * (1 - (1 - TAIL) ** 15)

# (family label, matcher market, signal, clock, source path, held names, observation unit, signals a day at a 10% tail, basis)
FAM = []
def add(label, market, signal, clock, path, unit, per_day, basis, side="follow"):
    FAM.append(dict(label=label, market=market, signal=signal, clock=clock, path=path, unit=unit, signals_per_day=round(per_day, 2), basis=basis, side=side))

NC = "nc-data nc15/<date>/<HHMM>/book.csv.gz (KXHYPE15M, KXBNB15M, KXNATGAS15M only: the other nine series are held)"
for sig in ("price_level", "spread", "book_depth_imbalance"):
    add("15m non-crypto unheld (HYPE, BNB, NATGAS)", "15m_noncrypto", sig, "fixed_time_to_close", NC, "one decision a window per series at a fixed time to close",
        3 * 96 * TAIL, "3 series x 96 windows a day x 10% (NATGAS shuts at weekends, so a weekday figure)")
add("15m non-crypto unheld (HYPE, BNB, NATGAS)", "15m_noncrypto", "tape_flow", "fixed_time_to_close", "nc-data nc15/.../trades.csv.gz (same three series)", "one decision a window per series", 3 * 96 * TAIL, "3 x 96 x 10%")
add("15m non-crypto unheld (HYPE, BNB, NATGAS)", "15m_noncrypto", "price_change", "any_minute", NC, "up to one entry a window per series (any time inside the window)", 3 * 96 * TAIL * (1 - (1 - TAIL) ** 30) / TAIL / 1.0 if False else 3 * 96 * (1 - (1 - TAIL) ** 30),
    "3 x 96 windows x P(at least one tail event among about 30 polls a window at 5 s over 2.5 minutes), independence assumed; an upper bound")

PK = "perp-data kalshi1m/<date>[.only].csv.gz (ticker, end_period_ts, bid_*, ask_*, price_*, open_interest, volume)"
for market, mins, names in (("crypto_perp", 1440, "BTC, ETH"), ("metal_perp", 1380, "gold and the metals"), ("index_perp", 1380, "US 500, US Tech 100"), ("stock_perp", 390, "stocks, regular hours")):
    for sig in ("price_change", "price_level", "spread", "volume", "open_interest"):
        add("%s 1 minute bars (%s)" % (market, names), market, sig, "any_minute", PK, "one entry per name per 15 minutes", perps_rate(mins),
            "per name: %d minutes a day in 15 minute blocks x P(at least one tail event in a block)=0.794, independence assumed (clustered signals give fewer)" % mins)
    add("%s 1 minute bars (%s)" % (market, names), market, "price_level", "time_of_day", PK, "one entry per name at a fixed time of day", 1 * 4 * TAIL, "4 fixed times a day x 10%", side="any")
add("crypto perps funding print", "crypto_perp", "funding_rate", "print", "perp-data funding/<date>[.only].csv.gz (funding_rate, mark_price)", "hourly prints per name", 24 * TAIL, "24 prints a day x 10%, per name", side="fade")
add("stock perps funding print", "stock_perp", "funding_rate", "print", "perp-data funding/ (daily 16:00 ET)", "one print a day per name", 1 * TAIL, "1 a day x 10%: UNDER 10, listed for completeness", side="fade")
add("perps windows (open and close, 30 s)", "stock_perp", "settlement_mark", "reopen", "perp-data perps30/<date>/{open,close}.csv.gz and perps/perps-<date>.csv", "two windows a weekday per name", 2 * TAIL, "UNDER 10: two windows a day", side="fade")
add("BTC liquidations (OKX)", "crypto_perp", "tape_flow", "any_minute", "quote-data oklq/<date>/<HHMM>/liquidations.csv.gz", "one entry per 15 minutes", perps_rate(1440), "same as a 1 minute bar family; the feed is event driven so fewer in quiet hours")
add("in-game NBA, NHL, NFL books", "sports", "price_change", "any_minute", "sports-data ingame/<date>/<HHMM>/obs.csv.gz (yes_bid, yes_ask, sizes, last, volume)", "per game, about 20 s while hot", 10 * 3 * TAIL * 4,
    "assumes about 10 games a day in season, 4 independent entries a game, 10%; LOW CONFIDENCE (the schedule is seasonal)")
add("in-game NBA, NHL, NFL books", "sports", "spread", "any_minute", "sports-data ingame/.../obs.csv.gz", "per game", 10 * 3 * TAIL * 4, "as above, LOW CONFIDENCE")
add("Bitcoin hourly ladder (KXBTCD, 7 strikes)", "hourly_ladder", "book_depth_imbalance", "fixed_time_to_close", "quote-data book/<date>/<HHMM>/book.csv.gz (hold check of BOOKIMB1 pending)", "7 strikes x 24 closes", 7 * 24 * TAIL,
    "7 strikes x 24 hourly closes x 10%; HOLD CHECK PENDING (H20 names a BOOKIMB1 holdout on this recorder)")
add("Bitcoin hourly ladder (KXBTCD, 7 strikes)", "hourly_ladder", "price_level", "fixed_time_to_close", "quote-data book/.../book.csv.gz", "7 strikes x 24 closes", 7 * 24 * TAIL, "as above; HOLD CHECK PENDING")

EXITS = [e for e in S.EXIT]
SIDES = [s for s in S.SIDE]
ENTRIES = [e for e in S.ENTRY]
canon = {"15m_noncrypto": "hold_to_settle", "hourly_ladder": "hold_to_settle", "sports": "fixed_time"}
reg = B.build()
out = []
for f in FAM:
    cand = dict(market=f["market"], signal=f["signal"], clock=f["clock"], entry="taker", exit=canon.get(f["market"], "fixed_time"), side=f["side"])
    v = S.classify(cand, reg)
    declined = sorted({(e, s) for e in EXITS for s in SIDES for en in ENTRIES for vv in [S.classify(dict(cand, exit=e, side=s, entry=en), reg)] if vv[0] == "DECLINED"})
    ids = sorted({S.classify(dict(cand, exit=e, side=s, entry=en), reg)[1] for e in EXITS for s in SIDES for en in ENTRIES if S.classify(dict(cand, exit=e, side=s, entry=en), reg)[0] == "DECLINED"})
    f.update(verdict=v[0], matched=v[1], why=v[2], declined_variants=len(declined), declined_by=ids, canonical=cand)
    out.append(f)
out.sort(key=lambda r: (-r["signals_per_day"], r["label"], r["signal"], r["clock"]))
json.dump(out, sys.stdout, indent=1, sort_keys=True)
