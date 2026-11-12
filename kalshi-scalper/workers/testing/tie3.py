#!/usr/bin/env python3
"""TIE3 (Desk B card 18) MEASUREMENT reader, job builders and scorer on scorekit. Testing Desk, Nov 12, 2026.
Research only: reads files, sends nothing. ZERO TRIES: this stage scores no rule and adds no try. Built against synthetic data; the registration (Desk B) and the frozen cells file must exist before any data is opened.
Head's conditions, enforced in code:
  - base rates use ONLY settlements dated strictly before the price block (base block: events closing before BASE_END); the price block never carries a result field (test asserts it);
  - prices come from minute-end candles at one stated instant (never a list quote); a thin, one-sided or stale minute is COUNTED, not filled;
  - cutoffs are date constants: BASE_END 2026-10-20T00:00Z, HELD_OUT_FROM 2026-11-13T00:00Z (nothing closing on or after it is listed, requested or counted);
  - cells are fixed before data: the cells file is a committed JSON and its sha256 must match the constant in the registration (CELLS_SHA256, set when Desk B freezes it; None = not frozen, the code refuses to build jobs).
Cells file (tie3_cells.json), one object per cell: {"league","period","series","tie_suffix":"TIE","start_rule":{...}}; start_rule (Desk B decides, the card is silent):
  {"kind":"ticker_local","tz":"America/New_York","offset_s":3600}  parse YYMMMDDHHMM from the event ticker, instant = start - offset_s;
  {"kind":"field","name":"<market field>","offset_s":N}              instant = that market field (ISO time) minus offset_s (N may be negative);
  no derivable start = the event is SKIPPED and counted.
Commands: build-lists <cells.json> | events <cells.json> <lists folders...> | build-candles <cells.json> <lists folders...> | measure <cells.json> <lists folders...> <candle folders...>
"""
import calendar, hashlib, json, os, re, statistics as st, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k

BASE_END = calendar.timegm((2026, 10, 20, 0, 0, 0))
HELD_OUT_FROM = calendar.timegm((2026, 11, 13, 0, 0, 0))
CUTOVER = calendar.timegm((2026, 9, 12, 0, 0, 0))
CELLS_SHA256 = None            # set to the sha256 of tie3_cells.json when Desk B freezes the cells (the registration carries the same value)
MIN_BASE, MIN_PRICED, EDGE, SPREAD_MAX, PACK_MIN_X_TICKERS, PACK_SPAN_S = 150, 40, 0.08, 0.04, 9000, 3 * 3600
REG = "kalshi-scalper/workers/testing/TIE3_MEASUREMENT.md"      # my build note; Desk B's registration text is the authority and is cited inside it
RUN = {"status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0,
       "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}}
MONTHS = {m.upper(): i for i, m in enumerate(calendar.month_abbr) if m}


def load_cells(path, require_frozen=True):
    if require_frozen and CELLS_SHA256 is None:
        raise SystemExit("refused: CELLS_SHA256 is not set; the cells are not frozen (Desk B's registration must carry the hash)")
    raw = open(path, "rb").read()
    if require_frozen:
        if hashlib.sha256(raw).hexdigest() != CELLS_SHA256:
            raise SystemExit("refused: the cells file does not match the frozen sha256")
    return json.loads(raw)


def job(job_id, purpose, eps, reqs, series, tickers):
    j = {"job_id": job_id, "owner": "MAIN", "registration": REG, "purpose": purpose,
         "heldout": "none read; nothing closing on or after 2026-11-13T00:00Z is listed or requested; a measurement: no rule scored, no try",
         "allowed_endpoints": eps, "series_allowlist": sorted(series), "ticker_allowlist": sorted(tickers), "max_requests": len(reqs), "notes": "TIE3 measurement"}
    j.update(RUN); j["requests"] = reqs
    return j


def build_lists(cells, require_frozen=True):
    """Lists job: for every cell series one live list (closes after the cutover) and one /historical list (older). Closes are bounded above by HELD_OUT_FROM - 1."""
    reqs, series = [], sorted({c["series"] for c in cells})
    for s in series:
        reqs.append({"id": "live_" + s, "path": "/markets", "params": {"series_ticker": s, "status": "settled", "limit": 1000, "min_close_ts": CUTOVER, "max_close_ts": HELD_OUT_FROM - 1}, "max_pages": 6})
        reqs.append({"id": "hist_" + s, "path": "/historical/markets", "params": {"series_ticker": s, "limit": 1000}, "max_pages": 6})
    eps = [{"name": "markets_list", "method": "GET", "path_pattern": "/markets", "params_allowed": ["series_ticker", "status", "limit", "cursor", "min_close_ts", "max_close_ts"]},
           {"name": "hist_markets_list", "method": "GET", "path_pattern": "/historical/markets", "params_allowed": ["series_ticker", "limit", "cursor"]}]
    return job("TIE3_LISTS", "TIE3 measurement stage 1: settled lists of the three-way period series (times, results of the base block only are used; no price).", eps, reqs, series, [])


def iso(s): return k.iso(s) if s else None


def start_ts(event, markets, rule):
    """Instant for the price: start minus offset, or None (skip and count)."""
    if not rule:
        return None
    if rule["kind"] == "field":
        for m in markets:
            t = iso(m.get(rule["name"]) or "")
            if t:
                return t - rule.get("offset_s", 0)
        return None
    if rule["kind"] == "ticker_local":
        m = re.fullmatch(r"[A-Z0-9]+-(\d\d)([A-Z]{3})(\d\d)(\d\d)(\d\d)[A-Z0-9]*", event)
        if not m or m.group(2) not in MONTHS:
            return None
        from datetime import datetime
        from zoneinfo import ZoneInfo
        d = datetime(2000 + int(m.group(1)), MONTHS[m.group(2)], int(m.group(3)), int(m.group(4)), int(m.group(5)), tzinfo=ZoneInfo(rule.get("tz", "America/New_York")))
        return int(d.timestamp()) - rule.get("offset_s", 0)
    return None


def events(cells, list_folders):
    """-> {cell_key: {"base": [ {event, close, level} ], "price": [ {event, close, tie_ticker, instant} ]}}, counts.
    Base block: events closing before BASE_END, with the Tie result (level = Tie settled yes). Price block: events closing in [BASE_END, HELD_OUT_FROM): NO RESULT FIELD is kept."""
    ms = k.markets(list_folders)
    by = {}
    counts = {"events_listed": 0, "dropped_not_three_settled": 0, "dropped_no_tie": 0, "held_out_dropped": 0, "no_start": 0}
    for t, m in ms.items():
        by.setdefault((m["series"], m["event"]), []).append(m)
    out = {}
    for c in cells:
        key = "%s|%s" % (c["league"], c["period"]); out[key] = {"base": [], "price": []}
    cell_of = {c["series"]: c for c in cells}
    for (series, ev), mk in by.items():
        c = cell_of.get(series)
        if not c:
            continue
        counts["events_listed"] += 1
        close = max(m["close"] for m in mk if m["close"])
        if close >= HELD_OUT_FROM:
            counts["held_out_dropped"] += 1; continue
        ties = [m for m in mk if m["ticker"].endswith("-" + c.get("tie_suffix", "TIE"))]
        if len(mk) != 3 or any(m["result"] not in ("yes", "no") for m in mk):
            counts["dropped_not_three_settled"] += 1; continue
        if len(ties) != 1:
            counts["dropped_no_tie"] += 1; continue
        key = "%s|%s" % (c["league"], c["period"])
        if close < BASE_END:
            out[key]["base"].append({"event": ev, "close": close, "level": ties[0]["result"] == "yes"})
        else:
            inst = start_ts(ev, mk, c.get("start_rule"))
            if inst is None:
                counts["no_start"] += 1; continue
            out[key]["price"].append({"event": ev, "close": close, "tie_ticker": ties[0]["ticker"], "instant": inst})       # no result key: never read for this block
    return out, counts


def build_candles(cells, list_folders):
    """Candle job: 1 minute candles around each price-block instant, packed by time (span at most 3 hours, minutes x tickers at most 9,000), live endpoint only (closes after the cutover);
    older price-block events (closing 2026-10-20 or later are all after the cutover) so no /historical call is needed."""
    ev, counts = events(cells, list_folders)
    items = sorted(((e["instant"], e["tie_ticker"]) for v in ev.values() for e in v["price"]), key=lambda x: x[0])
    packs, cur = [], []
    for inst, t in items:
        trial = cur + [(inst, t)]
        span = trial[-1][0] - trial[0][0] + 360
        if cur and (span > PACK_SPAN_S or span / 60 * len(trial) > PACK_MIN_X_TICKERS):
            packs.append(cur); cur = [(inst, t)]
        else:
            cur = trial
    if cur: packs.append(cur)
    reqs = [{"id": "c%04d" % i, "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(t for _, t in p), "start_ts": p[0][0] - 300, "end_ts": p[-1][0] + 60, "period_interval": 1}} for i, p in enumerate(packs)]
    eps = [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}]
    return job("TIE3_CANDLES", "TIE3 measurement stage 2: one minute candles of each Tie contract around its pre-game instant, price block only.", eps, reqs, {c["series"] for c in cells}, [t for _, t in items]), counts


def quartiles(xs):
    if len(xs) < 2: return None
    q = st.quantiles(xs, n=4, method="inclusive"); return [round(q[0], 4), round(st.median(xs), 4), round(q[2], 4)]


def measure(cells, list_folders, candle_folders):
    ev, counts = events(cells, list_folders)
    cs = k.candles(candle_folders)
    res = {}
    for cell in cells:
        key = "%s|%s" % (cell["league"], cell["period"]); b, p = ev[key]["base"], ev[key]["price"]
        nb = len(b); rate = (sum(1 for e in b if e["level"]) / nb) if nb else None
        se = (rate * (1 - rate) / nb) ** 0.5 if nb else None
        gaps, spreads, two, stale = [], [], 0, 0
        for e in p:
            series = cs.get(e["tie_ticker"], [])
            ok = [c for c in series if e["instant"] - 120 <= c["ts"] <= e["instant"]]       # the last candle ending at or just before the instant, no older than 2 minutes
            if not ok: stale += 1; continue
            c = ok[-1]
            if c["bid"] is None or c["ask"] is None or not (0 < c["bid"] < c["ask"] < 1): continue
            two += 1; spreads.append(c["ask"] - c["bid"])
            if rate is not None: gaps.append(rate - c["ask"])
        npriced = len(p)
        res[key] = {"n_base_events": nb, "base_rate": None if rate is None else round(rate, 4), "base_rate_se": None if se is None else round(se, 4), "n_priced_games": npriced, "no_candle_in_window": stale,
                    "n_two_sided": two, "share_two_sided": None if not npriced else round(two / npriced, 3), "gap_q1_median_q3": quartiles(gaps), "median_spread": None if not spreads else round(st.median(spreads), 4),
                    "cell_status": "no evidence" if (nb < MIN_BASE or npriced < MIN_PRICED) else "measured"}
    meas = [r for r in res.values() if r["cell_status"] == "measured"]
    survive = [r for r in meas if r["gap_q1_median_q3"] and r["gap_q1_median_q3"][1] >= EDGE and r["median_spread"] is not None and r["median_spread"] <= SPREAD_MAX]
    nothing_to_buy = meas and all((r["share_two_sided"] or 0) < 0.5 for r in meas)
    if survive: verdict = "SURVIVES the measurement in %d cell(s): the registered try is then separate (1 try, date constants, base rate from earlier games only)" % len(survive)
    elif nothing_to_buy: verdict = "CLOSED: under half of the games have a two-sided Tie quote in every measured cell (nothing to buy)"
    elif meas: verdict = "CLOSED: efficient, move on. The one number is the median gap per cell, above"
    else: verdict = "no evidence: no cell has %d base events and %d priced games" % (MIN_BASE, MIN_PRICED)
    return {"counts_first": counts, "cells": res, "verdict": verdict, "tries_added": 0, "rule_scored": False,
            "price_source": "1 minute candle ask close at the last minute ending at or before the instant (not a list quote); candle freshness measured on KXBTC15M only (CANDLEVSBOOK1), assumed elsewhere",
            "direction": "fixed: a Tie priced OVER its base rate closes the card; it is not turned round"}


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__)
    elif a[0] == "build-lists": print(json.dumps(build_lists(load_cells(a[1])), indent=1))
    elif a[0] == "events": print(json.dumps(events(load_cells(a[1]), a[2:])[1], indent=1))
    elif a[0] == "build-candles": j, c = build_candles(load_cells(a[1]), a[2:]); print(json.dumps(j, indent=1)); print(json.dumps(c), file=sys.stderr)
    elif a[0] == "measure":
        cells = load_cells(a[1]); i = next(n for n, x in enumerate(a) if n > 1 and x == "--candles")
        print(json.dumps(measure(cells, a[2:i], a[i + 1:]), indent=1))
