#!/usr/bin/env python3
"""VOIDSNAP stage 1: a hindsight MEASUREMENT, zero tries. Written Nov 13, 2026, before any candle of these
markets was requested or read. The text it follows: voidsnap/VOIDSNAP_CARD.md, Amendment 1 (rules 1 to 21).

  sample  <lists run> <out sample.json>             names the voids and their matched played events. Reads results, no price.
  job     <sample.json> <out job.json>              builds the 1-minute candle job for the sample. Reads the sample only.
  measure <lists run> <candles run> <sample.json>   the three questions and the three lines.

The sample is chosen by the void result, so every figure is hindsight: it can design a rule, never support one.
Standard library only. Every command refuses a path in a HELDOUT_ folder.
"""
import glob
import gzip
import json
import math
import os
import re
import statistics
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from deskb_guard import refuse_all, refuse_heldout  # noqa: E402

ET = ZoneInfo("America/New_York")
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
EPS = 1e-9
SERIES, LIVE_ID = "KXCS2GAME", "live_KXCS2GAME"
DEV_FROM, DEV_TO = "2026-09-12T00:00:00Z", "2026-10-22T23:59:59Z"
LEAD_S, TAIL_S = 185 * 60, 480 * 60        # rule 6
CARRY_INFO_S = 60 * 60                      # rule 7: the registered carry has no limit inside the window; 60 minutes and none are information only
REFS = {"S-180": -180 * 60, "S-60": -60 * 60, "S": 0}
SPREAD_MAX, SHORT = 0.04, 0.10              # rule 11
RUN_MIN = 5
BAND = (0.15, 0.64)
D_MIN = {"D1": 60 * 60, "D2": 60 * 60, "D3": 0}
D_REFS = {"D1": ("S-180", "S-60", "S"), "D2": ("S-180", "S-60", "S"), "D3": ("S-180", "S-60")}
FROZEN, QUIET_VOL, RAN = 0.02, 10.0, 0.10
LINE1, LINE2, LINE3, NEAR = 40, 0.30, 0.70, 0.03
SLIP = 0.01
GROUP_TICKERS, MAX_CANDLES, CAP = 100, 8500, 300
TAG = " [hindsight measurement, not a rule]"
REG_NAME = "REGISTERED (carry inside the window, no limit)"
LABEL = "candle freshness measured on Bitcoin 15 minute only, not on esports"
REG = "kalshi-scalper/workers/voidsnap/VOIDSNAP_CARD.md"


def ts(iso):
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())


def start_from_ticker(event_ticker):
    m = re.match(r"(\d{2})([A-Z]{3})(\d{2})(\d{2})(\d{2})", event_ticker.split("-", 1)[1] if "-" in event_ticker else "")
    if not m or m.group(2) not in MON:
        return None
    yy, mon, dd, hh, mi = m.groups()
    try:
        return int(datetime(2000 + int(yy), MON[mon], int(dd), int(hh), int(mi), tzinfo=ET).timestamp())
    except ValueError:
        return None


def fee(price):
    return math.ceil(0.07 * price * (1 - price) * 100 - EPS) / 100.0


def read_events(run):
    """Events from the live_KXCS2GAME answers only (rule 1). The hist_ answers are never opened."""
    refuse_heldout(run)
    man = json.load(open(os.path.join(run, "manifest.json")))
    raw = {}
    for row in man.get("rows", []):
        if row.get("id") != LIVE_ID or row.get("status") != 200:
            continue
        body = json.load(gzip.open(os.path.join(run, row["file"]), "rt"))
        for m in body.get("markets", []) if isinstance(body, dict) else []:
            ev, tk = m.get("event_ticker", ""), m.get("ticker", "")
            if ev.startswith(SERIES + "-") and tk.startswith(ev + "-"):
                raw.setdefault(ev, {})[tk] = m
    drops = {"not_two_contracts": 0, "no_close_time": 0, "no_ticker_clock": 0, "outside_window": 0, "neither_void_nor_played": 0}
    events = {}
    for ev, ms in raw.items():
        if len(ms) != 2:
            drops["not_two_contracts"] += 1
            continue
        try:
            close = max(ts(m["close_time"]) for m in ms.values())
        except (KeyError, ValueError, TypeError, AttributeError):
            drops["no_close_time"] += 1
            continue
        s = start_from_ticker(ev)
        if s is None:
            drops["no_ticker_clock"] += 1
            continue
        if not ts(DEV_FROM) <= close <= ts(DEV_TO):
            drops["outside_window"] += 1
            continue
        res = sorted((m.get("result") or "").lower() for m in ms.values())
        if all(r not in ("yes", "no") for r in res):
            kind = "void"
        elif res == ["no", "yes"]:
            kind = "played"
        else:
            drops["neither_void_nor_played"] += 1
            continue
        events[ev] = {"event": ev, "tickers": sorted(ms), "S": s, "close": close, "kind": kind, "markets": ms}
    return events, drops


def cmd_sample(lists_run, out_path):
    events, drops = read_events(lists_run)
    voids = sorted((e for e in events.values() if e["kind"] == "void"), key=lambda e: (e["S"], e["event"]))
    played = sorted((e for e in events.values() if e["kind"] == "played"), key=lambda e: (e["S"], e["event"]))
    free, pairs = {e["event"]: e for e in played}, []
    for v in voids:
        if not free:
            break
        m = min(free.values(), key=lambda e: (abs(e["S"] - v["S"]), e["S"], e["event"]))     # rule 4
        del free[m["event"]]
        slim = lambda e: {k: e[k] for k in ("event", "tickers", "S", "close")}               # noqa: E731
        pairs.append({"void": slim(v), "played": slim(m)})
    json.dump({"window": [DEV_FROM, DEV_TO], "base": {"void": len(voids), "played": len(played)}, "drops": drops, "pairs": pairs}, open(out_path, "w"), indent=1)
    print("events in the window %d | void %d | played %d | pairs made %d | dropped: %s" % (len(events), len(voids), len(played), len(pairs), ", ".join("%s %d" % kv for kv in drops.items())))


def load_sample(path):
    refuse_heldout(path)
    s = json.load(open(path))
    for p in s["pairs"]:
        for e in (p["void"], p["played"]):
            if not ts(DEV_FROM) <= e["close"] <= ts(DEV_TO):
                sys.exit("REFUSED: the sample holds an event closing outside the development window: %s" % e["event"])
    return s


def window(e):
    """Rule 6: (start, end) of the candle window, or None when the market closed at or before S minus 185 minutes."""
    start, end = e["S"] - LEAD_S, min(e["close"], e["S"] + TAIL_S)
    return (start, end) if end > start else None


def cmd_job(sample_path, out_path):
    s = load_sample(sample_path)
    items, nowin = [], 0
    for p in s["pairs"]:
        for e in (p["void"], p["played"]):
            w = window(e)
            if w is None:
                nowin += 1
                continue
            items.append((e["tickers"], w[0], w[1]))
    items.sort(key=lambda r: (r[1], r[2], r[0][0]))
    groups = []
    for tks, a, b in items:
        g = groups[-1] if groups else None
        if g:
            a2, b2, n = min(g["start"], a), max(g["end"], b), len(g["tickers"]) + len(tks)
            if n <= GROUP_TICKERS and n * ((b2 - a2) // 60 + 1) <= MAX_CANDLES:
                g["tickers"] += tks
                g["start"], g["end"] = a2, b2
                continue
        groups.append({"tickers": list(tks), "start": a, "end": b})
    print("sampled events %d | with no window (closed 185 minutes or more before the start) %d | requests needed %d (ceiling %d)" % (2 * len(s["pairs"]), nowin, len(groups), CAP))
    if any(g["end"] > ts(DEV_TO) for g in groups):
        sys.exit("REFUSED: a request would end after the development window")
    if len(groups) > CAP:
        print("OVER THE CEILING: no job written. The sample is not cut; the count goes to the Head of R&D.")
        return
    reqs = [{"id": "v%03d" % (k + 1), "path": "/markets/candlesticks",
             "params": {"market_tickers": ",".join(g["tickers"]), "start_ts": g["start"], "end_ts": g["end"], "period_interval": 1}} for k, g in enumerate(groups)]
    job = {"job_id": "VOIDSNAP_CANDLES", "owner": "DESK_B", "registration": REG,
           "purpose": "VOIDSNAP stage 1 (zero tries, hindsight measurement): one minute candles of both contracts of each voided CS2 match in the development window and of its matched played match.",
           "heldout": "none: every event closes 2026-09-12 to 2026-10-22; the voids before 2026-09-12 are the held-out set of a later rule and no ticker of theirs is requested",
           "allowed_endpoints": [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
           "series_allowlist": [SERIES], "ticker_allowlist": sorted(t for g in groups for t in g["tickers"]), "max_requests": CAP, "requests": reqs,
           "notes": "Built by voidsnap/voidsnap.py job from the sample file; the sample was named from lists already landed, before any price.",
           "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0,
           "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3,
                          "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}}
    json.dump(job, open(out_path, "w"), indent=1)


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
        return v / 100.0 if v > 1.0 else v
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
    refuse_heldout(run)
    found = {}
    for f in sorted(glob.glob(os.path.join(run, "[0-9]*.json.gz"))):
        walk(json.load(gzip.open(f, "rt")), found)
    out = {}
    for tk, cs in found.items():
        d = out.setdefault(tk, {})
        for c in cs:
            try:
                v = float(c.get("volume_fp", c.get("volume")))
            except (TypeError, ValueError):
                v = 0.0
            d[int(c["end_period_ts"])] = (price(c.get("yes_bid")), price(c.get("yes_ask")), v)
    return out


def two_sided(c):
    return c is not None and c[0] is not None and c[1] is not None and 0 < c[0] < c[1] < 1


def quote_at(q, t, carry, floor):
    """Rule 7: the candle ending at t, else the last candle before it no more than `carry` seconds earlier (None = no limit,
    back to `floor`, the window's first minute). The candle found must be two-sided, else there is no quote."""
    if t in q:
        return q[t] if two_sided(q[t]) else None
    if carry == 0:
        return None
    lo = floor if carry is None else max(floor, t - carry)
    u = t - 60
    while u >= lo:
        if u in q:
            return q[u] if two_sided(q[u]) else None
        u -= 60
    return None


def mid(c):
    return None if c is None else (c[0] + c[1]) / 2


def measure_event(e, values, candles, carry):
    """Everything stage 1 needs from one event under one carry rule. Uses no candle ending after the minute it describes."""
    w = window(e)
    out = {"window": w is not None, "refs": {}, "last_mid": None, "D": {"D1": False, "D2": False, "D3": False}, "runs": {}, "buyable_minutes": 0, "short": [], "cost": []}
    if w is None:
        return out
    S, floor, end = e["S"], w[0], w[1]
    first, both = e["tickers"][0], e["tickers"]
    q = {tk: candles.get(tk, {}) for tk in both}
    for name, off in REFS.items():
        if S + off <= end:
            out["refs"][name] = mid(quote_at(q[first], S + off, carry, floor))
    pres = [t for t in sorted(q[first]) if floor <= t <= end and two_sided(q[first][t])]
    out["last_mid"] = mid(q[first][pres[-1]]) if pres else None
    # detectors (rules 13 to 15); an event closed at or before the detector's minute is not flagged
    if e["close"] > S + D_MIN["D1"]:
        m0 = out["refs"].get("S")
        after = [q[first][t] for t in q[first] if S < t <= S + D_MIN["D1"]]
        out["D"]["D1"] = m0 is not None and all(two_sided(c) and abs(mid(c) - m0) <= FROZEN + EPS for c in after)
        vol = sum(c[2] for tk in both for t, c in q[tk].items() if S < t <= S + D_MIN["D2"])
        out["D"]["D2"] = vol < QUIET_VOL - EPS
    if e["close"] > S:
        for tk in both:
            a, b = mid(quote_at(q[tk], S, carry, floor)), mid(quote_at(q[tk], S - 180 * 60, carry, floor))
            if a is not None and b is not None and a <= b - RAN + EPS:
                out["D"]["D3"] = True
    # buyable minutes and runs (rules 11 and 12); only a void has a settlement value under which a side can stand
    if values is None:
        return out
    for dname, dmin in list(D_MIN.items()) + [("any", -LEAD_S)]:
        out["runs"][dname] = {"run": False, "run_band": False, "first": None}
    t = S - 180 * 60
    streak = {tk: 0 for tk in both}
    streak_band = {tk: 0 for tk in both}
    since = {d: {tk: 0 for tk in both} for d in D_MIN}
    since_band = {d: {tk: 0 for tk in both} for d in D_MIN}
    while t <= end:
        for tk in both:
            c = quote_at(q[tk], t, carry, floor)
            ok = c is not None and c[1] - c[0] <= SPREAD_MAX + EPS and values[tk] - c[1] >= SHORT - EPS
            band = ok and BAND[0] - EPS <= c[1] <= BAND[1] + EPS
            if ok:
                out["buyable_minutes"] += 1
                out["short"].append(values[tk] - c[1])
                out["cost"].append(c[1] - mid(c) + fee(c[1] + SLIP))
            streak[tk] = streak[tk] + 1 if ok else 0
            streak_band[tk] = streak_band[tk] + 1 if band else 0
            if streak[tk] >= RUN_MIN and not out["runs"]["any"]["run"]:
                out["runs"]["any"]["run"], out["runs"]["any"]["first"] = True, (t - (RUN_MIN - 1) * 60 - S) // 60
            if streak_band[tk] >= RUN_MIN:
                out["runs"]["any"]["run_band"] = True
            for d, dmin in D_MIN.items():
                if t >= S + dmin:
                    since[d][tk] = since[d][tk] + 1 if ok else 0
                    since_band[d][tk] = since_band[d][tk] + 1 if band else 0
                    if since[d][tk] >= RUN_MIN:
                        out["runs"][d]["run"] = True
                    if since_band[d][tk] >= RUN_MIN:
                        out["runs"][d]["run_band"] = True
        t += 60
    return out


def cmd_measure(lists_run, candles_run, sample_path):
    events, _ = read_events(lists_run)
    s = load_sample(sample_path)
    candles = read_candles(candles_run)
    voids = [p["void"] for p in s["pairs"]]
    played = [p["played"] for p in s["pairs"]]
    b = s["base"]["void"] / float(s["base"]["void"] + s["base"]["played"])
    vals = {}
    for e in voids:
        ms = events[e["event"]]["markets"]
        try:
            vals[e["event"]] = {tk: float(ms[tk].get("settlement_value_dollars")) for tk in e["tickers"]}
        except (TypeError, ValueError):
            vals[e["event"]] = None
    print("VOIDSNAP stage 1 | %s%s" % (LABEL, TAG))
    print("sampled voids %d | matched played events %d | base rate of voids in the window %.4f (%d of %d)%s"
          % (len(voids), len(played), b, s["base"]["void"], s["base"]["void"] + s["base"]["played"], TAG))
    print("voids with no settlement value listed %d | voids with no window %d | voids with any candle %d | played with any candle %d%s"
          % (sum(1 for v in vals.values() if v is None), sum(1 for e in voids if window(e) is None),
             sum(1 for e in voids if any(candles.get(tk) for tk in e["tickers"])), sum(1 for e in played if any(candles.get(tk) for tk in e["tickers"])), TAG))
    verdicts = {}
    for cname, carry in ((REG_NAME, None), ("information only, carry of at most 60 minutes", CARRY_INFO_S), ("information only, no carry", 0)):
        mv = {e["event"]: measure_event(e, vals[e["event"]] or {tk: float("nan") for tk in e["tickers"]}, candles, carry) for e in voids}
        mp = {e["event"]: measure_event(e, None, candles, carry) for e in played}
        n = len(voids)
        print("--- %s%s" % (cname, TAG))
        # question 1
        near = {}
        for name in list(REFS) + ["last two-sided mid"]:
            have = w1 = w3 = 0
            for e in voids:
                v = vals[e["event"]]
                r = mv[e["event"]]["last_mid"] if name == "last two-sided mid" else mv[e["event"]]["refs"].get(name)
                if r is None or v is None:
                    continue
                have += 1
                d = abs(v[e["tickers"][0]] - r)
                w1 += d <= 0.01 + EPS
                w3 += d <= NEAR + EPS
            near[name] = w3
            print("Q1 reference %s: available in %d of %d voids | within 1c of the settlement value %d | within 3c %d (%.1f%% of all sampled voids)%s"
                  % (name, have, n, w1, w3, 100.0 * w3 / n if n else 0, TAG))
        # question 2
        runs = [m for m in mv.values() if m["runs"] and m["runs"]["any"]["run"]]
        firsts = sorted(m["runs"]["any"]["first"] for m in runs)
        short = [x for m in mv.values() for x in m["short"]]
        cost = [x for m in mv.values() for x in m["cost"]]
        print("Q2 voids with a run of 5 buyable minutes or more: %d of %d (with the ask also at 15c to 64c: %d) | first minute of the first run against the start, quartiles: %s | buyable minutes in all %d | median shortfall %s | one-way cost, median %s%s"
              % (len(runs), n, sum(1 for m in mv.values() if m["runs"] and m["runs"]["any"]["run_band"]),
                 "n/a" if not firsts else "%d, %d, %d" % (firsts[len(firsts) // 4], firsts[len(firsts) // 2], firsts[3 * len(firsts) // 4]),
                 len(short), "n/a" if not short else "%.4f" % statistics.median(short), "n/a" if not cost else "%.4f" % statistics.median(cost), TAG))
        # question 3 and the three lines
        res = {}
        for d in ("D1", "D2", "D3"):
            fv = sum(1 for m in mv.values() if m["D"][d])
            fp = sum(1 for m in mp.values() if m["D"][d])
            tv, tp = fv / float(n) if n else 0.0, fp / float(len(played)) if played else 0.0
            den = tv * b + tp * (1 - b)
            share = tv * b / den if den > EPS else 0.0
            l1 = sum(1 for m in mv.values() if m["D"][d] and m["runs"] and m["runs"][d]["run"])
            l1b = sum(1 for m in mv.values() if m["D"][d] and m["runs"] and m["runs"][d]["run_band"])
            best = max(D_REFS[d], key=lambda r: (near[r], r))
            l3 = near[best] / float(n) if n else 0.0
            ok1, ok2, ok3 = l1 >= LINE1, share >= LINE2 - EPS, l3 >= LINE3 - EPS
            res[d] = ok1 and ok2 and ok3
            print("%s: flags %d of %d voids and %d of %d matched played events | implied share of voids among flagged %.3f (line 2, 0.30 or more: %s)%s"
                  % (d, fv, n, fp, len(played), share, "met" if ok2 else "FAILED", TAG))
            print("   line 1: flagged voids with 5 buyable minutes in a row at or after its minute: %d (40 or more: %s); with the ask at 15c to 64c, information only: %d%s"
                  % (l1, "met" if ok1 else "FAILED", l1b, TAG))
            print("   line 3: best allowed reference %s (the best of %d), within 3c in %.3f of all sampled voids (0.70 or more: %s)%s"
                  % (best, len(D_REFS[d]), l3, "met" if ok3 else "FAILED", TAG))
        verdicts[cname] = res
    # the reading (Amendment 2): a detector must pass its three lines under ALL three carries
    worth = [d for d in ("D1", "D2", "D3") if all(v[d] for v in verdicts.values())]
    mixed = [d for d in ("D1", "D2", "D3") if d not in worth and any(v[d] for v in verdicts.values())]
    for d in ("D1", "D2", "D3"):
        print("%s passes its three lines under: %s%s" % (d, ", ".join(k for k, v in verdicts.items() if v[d]) or "no carry rule", TAG))
    if worth:
        reading = "worth a rule, by " + ", ".join(worth) + " (its three lines pass under all three carries)"
    elif mixed:
        reading = "depends on the carry: not decided (" + ", ".join(mixed) + " passes under some carries and not others); no rule is registered"
    else:
        reading = "CLOSED, no try spent: no detector meets lines 1, 2 and 3 together under any carry"
    print("READING: %s%s" % (reading, TAG))
    print("a carried ask is a quote last seen, not a quote that can be paid: these figures say whether the price stood, not whether an order would have filled%s" % TAG)

def main():
    refuse_all()
    cmds = {"sample": (cmd_sample, 2), "job": (cmd_job, 2), "measure": (cmd_measure, 3)}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds or len(sys.argv) - 2 != cmds[sys.argv[1]][1]:
        sys.exit(__doc__)
    cmds[sys.argv[1]][0](*sys.argv[2:])


if __name__ == "__main__":
    main()
