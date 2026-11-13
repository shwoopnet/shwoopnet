#!/usr/bin/env python3
"""Hourly city temperature: a COST AND TIMING MEASUREMENT, zero tries. Built from
workers/HOURLYTEMP_MEASUREMENT_NOTE.md and its amendment of Nov 13, 2026 (pins 1 to 12), before any list or
candle of these series was pulled. Kalshi's own data only. No result field is read; no rule is scored.

  job     <lists run> <out dir>                    builds the candle job and markets.json. Tickers, strikes and times only.
  measure <markets.json> <lists run> <candle run>  the settlement source, then the figures and the one line.

Standard library only. Every command refuses a path in a HELDOUT_ folder.
"""
import glob
import gzip
import json
import math
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from deskb_guard import refuse_all, refuse_heldout  # noqa: E402

EPS = 1e-9
SERIES = ("KXTEMPCHIHS", "KXTEMPLAXHS", "KXTEMPMIAH", "KXTEMPNYCHS")
FROM, TO = "2026-11-05T00:00:00Z", "2026-11-11T23:59:59Z"
LOOKS = (55, 30, 10)
LIFE_S = 3600
NEAR = 2
COST_LINE = 0.04
FEE = 0.07
SLIP = 0.01
DECIDED = (0.95, 0.05)
MAX_TICKERS, MAX_CANDLES, MAX_REQUESTS = 100, 9800, 110
TAG = " [measurement, not a rule]"
LABEL = "candle freshness measured on Bitcoin 15 minute only, not on this family; one-minute resolution, no seconds-level claim"
REG = "kalshi-scalper/workers/HOURLYTEMP_MEASUREMENT_NOTE.md"


def ts(iso):
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())


THRESHOLD_TYPES = ("greater", "greater_or_equal")     # YES above a strike: a lower strike is the likelier YES


def inside(run, name):
    """The path of a file of a run. Refused if it lies in or resolves into a HELDOUT_ folder, or outside the run."""
    path = os.path.join(run, str(name))
    refuse_heldout(path)
    root = os.path.realpath(run)
    if not os.path.realpath(path).startswith(root + os.sep):
        sys.exit("REFUSED: %s is not a file of the run %s" % (path, run))
    return path


def manifest(run):
    refuse_heldout(run)
    return json.load(open(inside(run, "manifest.json")))


def read_lists(run, prefix):
    man = manifest(run)
    out = []
    for row in man.get("rows", []):
        if row.get("status") != 200 or not str(row.get("id", "")).startswith(prefix):
            continue
        body = json.load(gzip.open(inside(run, row["file"]), "rt"))
        out += [m for m in (body.get("markets", []) if isinstance(body, dict) else []) if str(m.get("ticker", "")).split("-")[0] in SERIES]
    return out


def cut_lists(run):
    """Pin 1, 'never cut': the ids of settled_ lists whose answers are not whole. A list is whole when every page was
    answered (status 200, not truncated) and its last page carries no cursor."""
    man = manifest(run)
    last, bad = {}, set()
    for row in man.get("rows", []):
        rid = str(row.get("id", ""))
        if not rid.startswith("settled_"):
            continue
        if row.get("status") != 200 or row.get("truncated"):
            bad.add(rid)
            continue
        if rid not in last or int(row.get("page") or 1) >= int(last[rid].get("page") or 1):
            last[rid] = row
    for rid, row in last.items():
        body = json.load(gzip.open(inside(run, row["file"]), "rt"))
        if not isinstance(body, dict) or body.get("cursor"):
            bad.add(rid)
    return sorted(bad | {"settled_" + s for s in SERIES if "settled_" + s not in last})


def sample(run):
    """Pin 1: the settled markets of the four series inside the fixed seven days. No result or price field is read.
    Returns the markets and the reasons, if any, why this sample must not be used (pins 1, 4 and 5)."""
    mk, skipped, types, odd_life = {}, 0, {}, 0
    for m in read_lists(run, "settled_"):
        types[str(m.get("strike_type"))] = types.get(str(m.get("strike_type")), 0) + 1
        try:
            row = {"ticker": m["ticker"], "event": m["event_ticker"], "series": m["ticker"].split("-")[0],
                   "strike": float(m["floor_strike"]), "open_ts": ts(m["open_time"]), "close_ts": ts(m["close_time"])}
        except (KeyError, TypeError, ValueError, AttributeError):
            skipped += 1
            continue
        if not ts(FROM) <= row["close_ts"] <= ts(TO):
            sys.exit("REFUSED: %s closes outside the fixed seven days" % row["ticker"])
        odd_life += row["close_ts"] - row["open_ts"] != LIFE_S
        mk[row["ticker"]] = row
    why = []
    cut = cut_lists(run)
    if cut:
        why.append("A LIST IS MISSING OR NOT WHOLE (%s)" % ", ".join(cut))
    if skipped:
        why.append("%d LISTED MARKETS LACK A STRIKE, AN EVENT OR A TIME" % skipped)
    if odd_life:
        why.append("%d MARKETS DID NOT LIVE EXACTLY 60 MINUTES" % odd_life)
    if len(types) != 1 or next(iter(types)) not in THRESHOLD_TYPES:
        why.append("THE STRIKES ARE NOT ONE LADDER OF 'ABOVE' THRESHOLDS (strike types listed: %s)" % ", ".join("%s x %d" % kv for kv in sorted(types.items())))
    return mk, why


def cmd_job(run, out):
    mk, why = sample(run)
    hours = {}
    for m in mk.values():
        hours.setdefault(m["close_ts"], []).append(m["ticker"])
    groups, keys, i = [], sorted(hours), 0
    while i < len(keys):
        a = keys[i]
        b = keys[i + 1] if i + 1 < len(keys) else None
        n2 = len(hours[a]) + (len(hours[b]) if b is not None else 0)
        if b is not None and b - a <= LIFE_S and n2 <= MAX_TICKERS and n2 * ((b - (a - LIFE_S)) // 60 + 1) <= MAX_CANDLES:
            groups.append((a - LIFE_S, b, sorted(hours[a] + hours[b])))
            i += 2
        else:
            groups.append((a - LIFE_S, a, sorted(hours[a])))
            i += 1
    print("settled markets in the sample %d | clock hours %d | requests %d (cap %d)" % (len(mk), len(keys), len(groups), MAX_REQUESTS))
    if why:
        for w in why:
            print("%s: no job written. The sample is never cut and no pin is bent; this goes to the Head of R&D." % w)
        return
    if not mk:
        print("NO MARKET IN THE SAMPLE: no job written.")
        return
    if len(groups) > MAX_REQUESTS or any(len(g[2]) > MAX_TICKERS or len(g[2]) * ((g[1] - g[0]) // 60 + 1) > MAX_CANDLES for g in groups):
        print("OVER THE CAP: no job written. The sample is never cut; the count goes to the Head of R&D.")
        return
    kept = sorted(mk)
    reqs = [{"id": "h%03d" % (k + 1), "path": "/markets/candlesticks",
             "params": {"market_tickers": ",".join(g[2]), "start_ts": g[0], "end_ts": g[1], "period_interval": 1}} for k, g in enumerate(groups)]
    job = {"job_id": "HOURLYTEMP_CANDLES", "owner": "DESK_B", "registration": REG,
           "purpose": "Hourly city temperature, cost and timing measurement (zero tries), stage 2: one minute candles of every strike of the four hourly temperature series for the 60 minutes each market lived, seven fixed days.",
           "heldout": "none (a cost measurement; no result is read and no rule is scored)",
           "allowed_endpoints": [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
           "series_allowlist": list(SERIES), "ticker_allowlist": kept, "max_requests": MAX_REQUESTS, "requests": reqs,
           "notes": "Built by workers/hourlytemp/hourlytemp.py job from the HOURLYTEMP_LISTS answers; the seven days are never extended and the sample is never cut.",
           "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0,
           "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3,
                          "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}}
    os.makedirs(out, exist_ok=True)
    json.dump([mk[t] for t in kept], open(os.path.join(out, "markets.json"), "w"))
    json.dump(job, open(os.path.join(out, "HOURLYTEMP_CANDLES.json"), "w"), indent=1)
    print("written: markets.json and HOURLYTEMP_CANDLES.json in %s" % out)


def price(side):
    if not isinstance(side, dict):
        return None
    for k in ("close_dollars", "close"):
        v = side.get(k)
        if v in (None, ""):
            continue
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        return v / 100.0 if k == "close" else v
    return None


def walk(node, found, hint=None):
    if isinstance(node, dict):
        tk = node.get("market_ticker") or node.get("ticker") or hint
        c = node.get("candlesticks")
        if isinstance(c, list) and c and isinstance(c[0], dict) and "end_period_ts" in c[0]:
            if tk:
                found.setdefault(tk, []).extend(c)
        for v in node.values():
            walk(v, found, tk)
    elif isinstance(node, list):
        for v in node:
            walk(v, found, hint)


def read_candles(run):
    """Candles by ticker and end time, and the count of candles that carry no volume field at all."""
    refuse_heldout(run)
    found, no_volume = {}, 0
    for f in sorted(glob.glob(os.path.join(run, "[0-9]*.json.gz"))):
        walk(json.load(gzip.open(inside(run, os.path.basename(f)), "rt")), found)
    out = {}
    for tk, cs in found.items():
        d = out.setdefault(tk, {})
        for c in cs:
            no_volume += "volume_fp" not in c and "volume" not in c
            try:
                v = float(c.get("volume_fp", c.get("volume")))
            except (TypeError, ValueError):
                v = 0.0
            d[int(c["end_period_ts"])] = (price(c.get("yes_bid")), price(c.get("yes_ask")), v)
    return out, no_volume


def whole_run(run):
    """(True if the candle run finished and every request of its job was answered whole (pin 10), answered, asked,
    the tickers its job asked for). A run whose manifest does not carry its job is refused: it cannot be tied to the sample."""
    man = manifest(run)
    rows = man.get("rows", [])
    reqs = (man.get("job") or {}).get("requests")
    if not isinstance(reqs, list) or not reqs:
        sys.exit("REFUSED: the candle run's manifest does not carry its job, so it cannot be tied to the sample")
    asked = {r.get("id") for r in reqs}
    tickers = {t for r in reqs for t in str((r.get("params") or {}).get("market_tickers", "")).split(",") if t}
    good = {r.get("id") for r in rows if r.get("status") == 200 and not r.get("truncated")}
    bad = {r.get("id") for r in rows if r.get("status") != 200 or r.get("truncated")}
    return man.get("status") == "complete" and not bad and asked <= good, len(good - bad), len(asked), tickers


def two_sided(c):
    return c is not None and c[0] is not None and c[1] is not None and EPS < c[0] and c[0] < c[1] - EPS and c[1] < 1 - EPS


def quote(q, t, open_ts, carried):
    """Pin 4. Returns (two-sided candle or None, True if a candle was found at all)."""
    if t in q:
        return (q[t] if two_sided(q[t]) else None), True
    if not carried:
        return None, False
    u = t - 60
    while u > open_ts:
        if u in q:
            return (q[u] if two_sided(q[u]) else None), True
        u -= 60
    return None, False


def med(v):
    v = sorted(v)
    if not v:
        return None
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0


def fee_up(p):
    return math.ceil(FEE * p * (1 - p) * 100 - EPS) / 100.0


def cents(x):
    return "n/a" if x is None else "%.2fc" % (100 * x + 1e-7)        # a half prints up, whatever the float holds


def share(a, b):
    return "n/a" if not b else "%.1f%%" % (100.0 * a / b + 1e-7)


def reading(events, cand, carried, name):
    """All figures under one reading of the quote; returns 'closed', 'not closed' or 'cannot say' (pin 10)."""
    print("--- %s%s" % (name, TAG))
    medians = []
    for series in SERIES:
        for look in LOOKS:
            found = two = decided = 0
            spreads, trips, near_trips, near_one = [], [], [], []
            side = {1: [], 2: [], 3: []}
            for (s, _), ms in sorted(events.items()):
                if s != series:
                    continue
                rows = []
                for m in sorted(ms, key=lambda m: (m["strike"], m["ticker"])):
                    c, any_candle = quote(cand.get(m["ticker"], {}), m["close_ts"] - look * 60, m["open_ts"], carried)
                    found += any_candle
                    if c is None:
                        continue
                    two += 1
                    b, a = c[0], c[1]
                    mid = (a + b) / 2
                    spreads.append(a - b)
                    trips.append((a - b) + 2 * FEE * mid * (1 - mid))
                    decided += mid >= DECIDED[0] - EPS or mid <= DECIDED[1] + EPS
                    rows.append((b, a, mid))
                if not rows:
                    continue
                k0 = 0
                for i in range(1, len(rows)):                      # nearest 50c; on a tie the lower strike stays
                    if abs(rows[i][2] - 0.5) < abs(rows[k0][2] - 0.5) - EPS:
                        k0 = i
                for i, (b, a, mid) in enumerate(rows):
                    r = abs(i - k0)
                    if r <= NEAR:
                        near_trips.append((a - b) + 2 * FEE * mid * (1 - mid))
                        near_one.append((a - b) / 2 + fee_up(min(0.99, a + SLIP)))
                    if r >= 1:
                        side[min(r, 3)].append(a if i < k0 else 1 - b)
            one = med(near_one)
            medians.append(one)
            print("%s %2d min before the hour: strikes with a quote candle %d | two-sided %d (%s) | median spread %s | median round trip %s | near the money n %d: round trip %s, ONE-WAY entry cost %s | priced 95c or 5c and beyond %s | ask of the nearer-certain side at rank 1, 2, 3+: %s, %s, %s%s"
                  % (series, look, found, two, share(two, found), cents(med(spreads)), cents(med(trips)), len(near_one), cents(med(near_trips)), cents(one),
                     share(decided, two), cents(med(side[1])), cents(med(side[2])), cents(med(side[3])), TAG))
    if any(x is not None and x <= COST_LINE + EPS for x in medians):
        return "not closed"
    return "closed" if all(x is not None for x in medians) else "cannot say"


def cmd_measure(markets_path, lists_run, candle_run):
    refuse_heldout(markets_path)
    markets = json.load(open(markets_path))
    for m in markets:
        if m["series"] not in SERIES or not ts(FROM) <= m["close_ts"] <= ts(TO):
            sys.exit("REFUSED: %s is outside the fixed sample" % m["ticker"])
    mk, why = sample(lists_run)
    if why:
        sys.exit("REFUSED: " + "; ".join(why))
    if markets != [mk[t] for t in sorted(mk)]:
        sys.exit("REFUSED: markets.json is not the sample this lists run gives (%d markets here, %d in the lists)" % (len(markets), len(mk)))
    whole, answered, asked, job_tickers = whole_run(candle_run)
    if job_tickers != set(mk):
        sys.exit("REFUSED: the candle run's job asked for %d tickers, the sample has %d, and the two sets differ" % (len(job_tickers), len(mk)))
    cand, no_volume = read_candles(candle_run)
    print("HOURLY TEMPERATURE cost and timing measurement, zero tries | %s%s" % (LABEL, TAG))
    seen = set()
    for m in sorted(read_lists(lists_run, "settled_"), key=lambda m: m["ticker"]):   # pin 2: the settlement source first; rules text only
        s = m["ticker"].split("-")[0]
        if s not in seen:
            seen.add(s)
            for k in ("rules_primary", "rules_secondary"):
                print("SETTLEMENT SOURCE, %s %s (market %s): %s" % (s, k, m["ticker"], " ".join(str(m.get(k) or "(empty)").split())))
    events = {}
    for m in markets:
        events.setdefault((m["series"], m["event"]), []).append(m)
    print("markets in the fixed sample %d | events (a city and an hour) %d | markets with any candle %d%s" % (len(markets), len(events), sum(1 for m in markets if cand.get(m["ticker"])), TAG))
    r1 = reading(events, cand, True, "CARRIED quote (the last candle inside the market's 60 minute life)")
    r2 = reading(events, cand, False, "EXACT quote (only a candle ending at the look)")
    print("candles with no volume field at all: %d (each counts as a minute with no trade)%s" % (no_volume, TAG))
    for series in SERIES:
        ms = [m for m in markets if m["series"] == series]
        traded = sum(1 for m in ms for t, c in cand.get(m["ticker"], {}).items() if m["open_ts"] < t <= m["close_ts"] and c[2] > EPS)
        print("%s: market-minutes with a trade %s (%d of %d)%s" % (series, share(traded, 60 * len(ms)), traded, 60 * len(ms), TAG))
    sizes = {}
    for m in read_lists(lists_run, "open_"):
        for k in ("yes_ask_size_fp", "yes_bid_size_fp"):
            try:
                v = float(m.get(k))
            except (TypeError, ValueError):
                continue
            if v > EPS:
                sizes.setdefault(m["ticker"].split("-")[0], []).append(v)
    for s in SERIES:
        v = sizes.get(s, [])
        print("%s: size at the touch on open markets (a list copy, one level only): median %s contracts over %d quoted sides%s" % (s, "n/a" if not v else "%.0f" % (med(v) + 1e-7), len(v), TAG))
    print("the line under the carried quote: %s | under the exact quote: %s | candle requests answered whole %d of %d%s" % (r1, r2, answered, asked, TAG))
    if not whole:
        verdict = "the candle pull is not whole: not decided"
    elif r1 == r2 == "closed":
        verdict = "CLOSED as too costly: the median one-way entry cost near the money is above 4c at every look in every city, under both readings of the quote"
    elif r1 == r2 == "not closed":
        verdict = "NOT closed on cost: at least one city and look has a median one-way entry cost near the money of 4c or less, under both readings. Nothing beyond this measurement is approved"
    else:
        verdict = "depends on the reading of a missing minute: not decided"
    print("VERDICT: %s%s" % (verdict, TAG))
    print("a carried ask is a quote last seen, not a quote that can be paid; no result was read%s" % TAG)


def main():
    refuse_all()
    cmds = {"job": (cmd_job, 2), "measure": (cmd_measure, 3)}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds or len(sys.argv) - 2 != cmds[sys.argv[1]][1]:
        sys.exit(__doc__)
    cmds[sys.argv[1]][0](*sys.argv[2:])


if __name__ == "__main__":
    main()
