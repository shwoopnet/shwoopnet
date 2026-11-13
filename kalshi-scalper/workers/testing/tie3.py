#!/usr/bin/env python3
"""TIE3 (Desk B card 18) MEASUREMENT reader, job builders and scorer on scorekit. Testing Desk, Nov 12, 2026.
Built to Desk B's REGISTRATION (kalshi-scalper/workers/tie3/TIE3_REGISTRATION.md, commit 9b37bd6 on claude/idea-desk-b; the registration wins over the card) and its frozen cells file
(tie3_series_frozen.json here, byte for byte TIE3_SERIES.json at 9b37bd6, sha256 below). Research only: reads files, sends nothing. ZERO TRIES: no rule scored, no outcome of a priced game read.
Enforced in code: base block = events closing before 2026-10-27T00:00Z (results read there for one count); price block = 2026-10-27T00:00Z to before 2026-11-13T00:00Z, carries NO result field (tested);
held-out from 2026-11-13T00:00Z is never listed or requested; the cells file must match CELLS_SHA256; prices only from the one-minute candle ENDING at T (never a list quote); thin, one-sided or missing minutes counted, not filled.
Instant (registration): start = the Tie market's occurrence_datetime minus 180 minutes; GUARD: the game's first-period market (cell field first_period_series; the Tie market itself where the cell says 'same series') must have closed
20 to 120 minutes after that start, else 'start not derivable'; T = start minus 30 minutes; if the minute ending at T is missing or one-sided, step back one minute at a time to T minus 30 minutes, take the first two-sided minute, else 'not two-sided'.
A game = the suffix after the series prefix of the event ticker, the same in each series of one game (ASSUMED; the first lists answer must confirm, else games are dropped and counted).
Commands: build-lists | events <lists folders...> | build-candles <lists folders...> | measure <lists folders...> --candles <candle folders...>
"""
import calendar, hashlib, json, os, statistics as st, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k

HERE = os.path.dirname(os.path.abspath(__file__))
CELLS_FILE = os.path.join(HERE, "tie3_series_frozen.json")
CELLS_SHA256 = "dc177a9da637fc9be0a5a8582d6073f9d2ffad8e5f8dc7b6778b8d0cb142e3ef"      # TIE3_SERIES.json at 9b37bd6 (Desk B, frozen 2026-11-12)
BASE_END = calendar.timegm((2026, 10, 27, 0, 0, 0))
HELD_OUT_FROM = calendar.timegm((2026, 11, 13, 0, 0, 0))
OFFSET_S, BEFORE_S, STEP_BACK = 180 * 60, 30 * 60, 30
GUARD_LO, GUARD_HI = 30 * 60, 120 * 60
MIN_BASE, MIN_PRICED, EDGE, SPREAD_MAX, RULE_EDGE = 150, 40, 0.08, 0.04, 0.10
PACK_LIMIT, PACK_SPAN_S = 9000, 3 * 3600
HISTORY_SERIES = {"KXNHL1P", "KXNHL2P", "KXNHL3P", "KXNHLOT", "KXNFL1Q", "KXNFL2Q", "KXNFL3Q", "KXNFL4Q"}       # the 8 series Desk B lists on /historical too
REG = "kalshi-scalper/workers/testing/TIE3_MEASUREMENT.md"
FRESH = "candle freshness measured on Bitcoin 15 minute only, not on sports"
RUN = {"status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0,
       "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}}


def load_cells(path=CELLS_FILE, sha=None):
    raw = open(path, "rb").read()
    want = CELLS_SHA256 if sha is None else sha
    if hashlib.sha256(raw).hexdigest() != want:
        raise SystemExit("refused: the cells file does not match the frozen sha256")
    return json.loads(raw)


def job(job_id, purpose, eps, reqs, series, tickers):
    j = {"job_id": job_id, "owner": "MAIN", "registration": REG, "purpose": purpose,
         "heldout": "none read; nothing closing on or after 2026-11-13T00:00Z is listed or requested; a measurement: no rule scored, no try",
         "allowed_endpoints": eps, "series_allowlist": sorted(series), "ticker_allowlist": sorted(tickers), "max_requests": len(reqs), "notes": "TIE3 measurement"}
    j.update(RUN); j["requests"] = reqs
    return j


def all_series(spec): return sorted({s for c in spec["cells"] for s in c["series"]} | {c["first_period_series"] for c in spec["cells"] if c["first_period_series"] != "same series"})


def build_lists(spec):
    """Registered: each series' settled markets on the live endpoint, the 8 NHL and NFL series also on /historical, and the fee-field read /series/{ticker} for the 4 listed series. 32 requests."""
    reqs = []
    for s in all_series(spec):
        reqs.append({"id": "live_" + s, "path": "/markets", "params": {"series_ticker": s, "status": "settled", "limit": 1000, "max_close_ts": HELD_OUT_FROM - 1}, "max_pages": 3})
        if s in HISTORY_SERIES:
            reqs.append({"id": "hist_" + s, "path": "/historical/markets", "params": {"series_ticker": s, "limit": 1000}, "max_pages": 3})
    for s in spec["fee_field_reads"]:
        reqs.append({"id": "fee_" + s, "path": "/series/" + s})
    eps = [{"name": "markets_list", "method": "GET", "path_pattern": "/markets", "params_allowed": ["series_ticker", "status", "limit", "cursor", "min_close_ts", "max_close_ts"]},
           {"name": "hist_markets_list", "method": "GET", "path_pattern": "/historical/markets", "params_allowed": ["series_ticker", "limit", "cursor"]},
           {"name": "series", "method": "GET", "path_pattern": "/series/(?P<series>[A-Z0-9]{2,32})", "params_allowed": []}]
    j = job("TIE3_LISTS", "TIE3 measurement stage 1: settled lists of the three-way period series and the fee fields (times and, for the base block only, results are used; no price).", eps, reqs, all_series(spec), [])
    j["max_requests"] = len(reqs) + 28            # 32 requests registered, about 50 pages: the runner counts pages against the cap, so the cap leaves slack for them
    return j


def game_key(event): return event.split("-", 1)[1] if "-" in event else event


def events(spec, list_folders):
    """-> ({cell: {"base": [..], "price": [..]}}, counts). Price-block records carry NO result field."""
    ms = k.markets(list_folders)
    by = {}
    for t, m in ms.items():
        by.setdefault((m["series"], game_key(m["event"])), []).append(m)
    counts = {"events_listed": 0, "held_out_dropped": 0, "dropped_not_all_settled": 0, "dropped_no_tie_market": 0, "start_not_derivable": 0, "no_such_series": 0, "note_not_all_settled": "dropped_not_all_settled tests only whether each market has a yes or no result field (presence), for base-block AND price-block games; the VALUE of a price-block result is never read (Auditor B minor note, Nov 13)"}
    listed = {m["series"] for m in ms.values()}
    counts["no_such_series"] = sum(1 for s in all_series(spec) if s not in listed)
    out = {}
    for c in spec["cells"]:
        out[c["cell"]] = {"base": [], "price": []}
        reg = c["cell"] == "NHL_REG"
        need = 1 if reg else 3
        for s in c["series"]:
            for (ser, gk), mk in by.items():
                if ser != s: continue
                counts["events_listed"] += 1
                close = max(m["close"] for m in mk if m["close"])
                if close >= HELD_OUT_FROM: counts["held_out_dropped"] += 1; continue
                if len(mk) != need or any(m["result"] not in ("yes", "no") for m in mk): counts["dropped_not_all_settled"] += 1; continue
                tie = [m for m in mk if (m["ticker"].endswith("-1") if reg else m["ticker"].endswith("-TIE"))]
                if len(tie) != 1: counts["dropped_no_tie_market"] += 1; continue
                tie = tie[0]
                key = s if c["cell"] in ("NFL_Q", "SOC_1H") else c["cell"]            # base rate per quarter (series) in NFL_Q and per series in SOC_1H
                if close < BASE_END:
                    out[c["cell"]]["base"].append({"event": gk, "key": key, "level": tie["result"] == "yes"})
                else:
                    occ = iso_(tie, "occurrence_datetime")
                    start = None if occ is None else occ - OFFSET_S
                    fp = tie if c["first_period_series"] == "same series" else next(iter(by.get((c["first_period_series"], gk), [])), None)
                    if start is None or fp is None or not fp.get("close") or not (GUARD_LO <= fp["close"] - start <= GUARD_HI):
                        counts["start_not_derivable"] += 1; continue
                    out[c["cell"]]["price"].append({"event": gk, "key": key, "tie_ticker": tie["ticker"], "T": start - BEFORE_S})          # no result key
    return out, counts


def iso_(m, name):
    return k.iso((m.get("times") or {}).get(name) or "")


def build_candles(spec, list_folders):
    """The Tie contract only, the 31 minutes ending at T, batched by T (span at most 3 hours, minutes x tickers at most 9,000). Live endpoint (price block closes after the 2026-09-12 cutover)."""
    ev, counts = events(spec, list_folders)
    items = sorted(((e["T"], e["tie_ticker"]) for v in ev.values() for e in v["price"]), key=lambda x: x[0])
    packs, cur = [], []
    for T, t in items:
        trial = cur + [(T, t)]
        span = trial[-1][0] - trial[0][0] + (STEP_BACK + 1) * 60
        if cur and (span > PACK_SPAN_S + (STEP_BACK + 1) * 60 or span / 60 * len(trial) > PACK_LIMIT):
            packs.append(cur); cur = [(T, t)]
        else:
            cur = trial
    if cur: packs.append(cur)
    reqs = [{"id": "c%04d" % i, "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(t for _, t in p), "start_ts": p[0][0] - STEP_BACK * 60 - 60, "end_ts": p[-1][0], "period_interval": 1}} for i, p in enumerate(packs)]
    eps = [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}]
    return job("TIE3_CANDLES", "TIE3 measurement stage 2: the one minute candles of each Tie contract for the 31 minutes ending at T, price block only.", eps, reqs, all_series(spec), [t for _, t in items]), counts


def q(xs):
    if len(xs) < 2: return None
    a = st.quantiles(xs, n=4, method="inclusive"); return [round(a[0], 4), round(st.median(xs), 4), round(a[2], 4)]


def measure(spec, list_folders, candle_folders):
    ev, counts = events(spec, list_folders)
    idx = {t: {c["ts"]: c for c in v} for t, v in k.candles(candle_folders).items()}
    res = {}
    for c in spec["cells"]:
        b, p = ev[c["cell"]]["base"], ev[c["cell"]]["price"]
        rates = {}
        for key in sorted({e["key"] for e in b} | {e["key"] for e in p}):
            bb = [e for e in b if e["key"] == key]; n = len(bb)
            r = sum(1 for e in bb if e["level"]) / n if n else None
            rates[key] = {"n": n, "rate": None if r is None else round(r, 4), "se": None if not n else round((r * (1 - r) / n) ** 0.5, 4)}
        gaps, spreads, fires, two = [], [], 0, 0
        games_two = set()
        for e in p:
            r = rates[e["key"]]["rate"]; series = idx.get(e["tie_ticker"], {}); got = None
            for j in range(0, STEP_BACK + 1):
                cd = series.get(e["T"] - 60 * j)
                if cd and cd["bid"] is not None and cd["ask"] is not None and 0 < cd["bid"] < cd["ask"] < 1: got = cd; break
            if got is None: continue
            two += 1; games_two.add(e["event"]); sp = got["ask"] - got["bid"]; spreads.append(sp)
            if r is not None:
                gaps.append(r - got["ask"])
                if r - got["ask"] >= RULE_EDGE and sp <= SPREAD_MAX: fires += 1
        nb, npd = len(b), len(p)
        res[c["cell"]] = {"base_events": nb, "base_rates_by_key": rates, "price_block_games_with_derivable_start": npd, "two_sided": two, "distinct_games_two_sided": len(games_two), "distinct_games_price_block": len({e["event"] for e in p}), "share_two_sided": None if not npd else round(two / npd, 3),
                          "median_spread": None if not spreads else round(st.median(spreads), 4), "gap_q1_median_q3": q(gaps), "share_two_sided_games_with_ask_10c_under_and_spread_le_4c": None if not two else round(fires / two, 3),
                          "status": "no evidence at n = %d base events / %d two-sided games" % (nb, two) if (nb < MIN_BASE or two < MIN_PRICED) else "measured"}
    meas = {n: r for n, r in res.items() if r["status"] == "measured"}
    survive = [n for n, r in meas.items() if r["gap_q1_median_q3"] and r["gap_q1_median_q3"][1] >= EDGE and r["median_spread"] is not None and r["median_spread"] <= SPREAD_MAX]
    if survive: verdict = "SURVIVES the measurement in %d cell(s) %s: a separate registration, tries = surviving cells" % (len(survive), survive)
    elif meas and all((r["share_two_sided"] or 0) < 0.5 for r in meas.values()): verdict = "CLOSED: nothing to buy (under half of the price-block games are two-sided in every measured cell)"
    elif meas:
        best = max((r["gap_q1_median_q3"][1] for r in meas.values() if r["gap_q1_median_q3"]), default=None)
        verdict = "CLOSED: efficient, move on. The one number: the best cell's median gap %s" % best
    else: verdict = "no evidence: no cell has %d base events and %d two-sided games" % (MIN_BASE, MIN_PRICED)
    return {"counts_first": counts, "cells": res, "verdict": verdict, "tries_added": 0, "rule_scored": False, "result_of_priced_game_read": False, "freshness": FRESH,
            "direction": "fixed: a Tie OVERPRICED closes the card; it is not turned round"}


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__)
    else:
        spec = load_cells()
        if a[0] == "build-lists": print(json.dumps(build_lists(spec), indent=1))
        elif a[0] == "events": print(json.dumps(events(spec, a[1:])[1], indent=1))
        elif a[0] == "build-candles": j, c = build_candles(spec, a[1:]); print(json.dumps(j, indent=1)); print(json.dumps(c), file=sys.stderr)
        elif a[0] == "measure": i = a.index("--candles"); print(json.dumps(measure(spec, a[1:i], a[i + 1:]), indent=1))
