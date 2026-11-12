#!/usr/bin/env python3
"""ESOCTIE (History Miner, registration 4678cec0 on claude/history-miner incl. NOTES 1 to 4) reader, candle-job builder and scorer on scorekit and tie3's job format. Testing Desk, Nov 12, 2026.
An independent build: it must agree with the History Miner's reference esoctie.py on the same input (cross-check run recorded in ESOCTIE_BUILD.md). Research only: reads files, sends nothing.
Constants come from esoctie_series_frozen.json (byte copy of ESOCTIE_SERIES.json, sha256 below); nothing is fitted. ONE try. Development only: the held-out (closes from 2026-10-23T00:00Z) is refused in code.
Universe (NOTE 2): KXESOCCERGAME events with exactly three markets (two teams and one ending -TIE); S = the key's date and HHMM as US Eastern (zoneinfo); the Tie market must have OPENED 10 to 240 minutes before S; the close time is used ONLY to place an event in the development block (calendar split) and in the base rate.
Pre-match instant: candle ending S-60 s, stepping back a minute at a time to S-600 s; all three contracts two-sided (0<bid<ask<1) in the SAME minute; else not filled.
f = larger team mid; buckets from the frozen edges. Base rate b (walk-forward, NOTE 3): the Tie share of earlier FILLED events in the same bucket whose close + 300 s is at or before THIS decision's candle end (the settled result is known); needs 300, else base-building (never re-entered).
Rule: b minus Tie ask >= 10c and Tie spread <= 4c -> buy 1 Tie at ask + 1c, fee 0.07 x p x (1-p) rounded UP, hold; a fired bet with no yes/no result is booked as a loss of the fee only (NOTE 4), counted. Placebo: Tie bid >= b + 10c, spread <= 4c.
Kill lines (read first, no bet scored if any closes the card): under 150 filled eligible; median ONE-WAY entry cost (Tie ask minus mid plus the entry fee at ask + 1c, rounded up) above 4c; 10c share under 3% or under twice the placebo; median Tie ask under 15c (cheap tail). The round trip is printed as information.
Every figure is labelled 'selected on development' (it can falsify, it cannot support). Commands: build-lists-check | build-candles <lists...> | measure <lists...> --candles <c...> | score <lists...> --candles <c...>
"""
import hashlib, heapq, json, math, os, statistics as st, sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import calendar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k
import tie3

HERE = os.path.dirname(os.path.abspath(__file__))
CELLS_FILE = os.path.join(HERE, "esoctie_series_frozen.json")
CELLS_SHA256 = "c80cd418844a92c7df693a546baa3c230f800f9f908118cb1cea901c5920728b"
REG = "kalshi-scalper/workers/history_miner/esoctie/ESOCTIE_REGISTRATION.md"
NY = ZoneInfo("America/New_York")
MONTHS = {m.upper(): i for i, m in enumerate(calendar.month_abbr) if m}
FRESH = "candle freshness measured on Bitcoin 15 minute only, not on e-soccer"
PRICE_THROUGH, MIN_FILLED, CHEAP_ASK = 0.01, 150, 0.15


def load_cells(path=CELLS_FILE):
    raw = open(path, "rb").read()
    if hashlib.sha256(raw).hexdigest() != CELLS_SHA256: raise SystemExit("refused: the series file does not match the frozen sha256")
    return json.loads(raw)


def ts_of(s): return calendar.timegm(datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").timetuple())


def fee_up(p): return math.ceil(round(0.07 * p * (1 - p) * 100, 6)) / 100


def start_ts(event):
    key = event.split("-", 1)[1] if "-" in event else ""
    try:
        return int(datetime(2000 + int(key[0:2]), MONTHS[key[2:5]], int(key[5:7]), int(key[7:9]), int(key[9:11]), tzinfo=NY).timestamp())
    except (KeyError, ValueError, IndexError): return None


def events(spec, list_folders):
    raw = k.markets(list_folders); by = {}
    b = spec["blocks"]; dev_from, dev_to = ts_of(b["development_closes_from"]), ts_of(b["development_closes_before"])
    for t, m in raw.items():
        if m["series"] in spec["series"]: by.setdefault(m["event"], []).append(m)
    out, c = {}, {"events_listed": len(by), "bad_shape": 0, "held_out_refused": 0, "before_development": 0, "start_not_derivable": 0}
    lo, hi = [x * 60 for x in spec["open_guard_minutes_before_S"]]
    for e, ms in sorted(by.items()):
        ties = [m for m in ms if m["ticker"].endswith("-TIE")]; teams = sorted(m["ticker"] for m in ms if not m["ticker"].endswith("-TIE"))
        if len(ms) != 3 or len(ties) != 1 or len(teams) != 2: c["bad_shape"] += 1; continue
        close = max((m["close"] or 0) for m in ms)
        if close >= dev_to: c["held_out_refused"] += 1; continue
        if close < dev_from: c["before_development"] += 1; continue
        S = start_ts(e); op = ties[0]["open"]
        if S is None or op is None or not (lo <= S - op <= hi): c["start_not_derivable"] += 1; continue          # decided only by the ticker clock and the Tie's open time
        out[e] = {"event": e, "S": S, "close": close, "tie": ties[0]["ticker"], "teams": teams, "result": ties[0]["result"]}
    c["kept"] = len(out); return out, c


def two(idx, t, ts):
    c = idx.get(t, {}).get(ts)
    return (c["bid"], c["ask"]) if c and c["bid"] is not None and c["ask"] is not None and 0 < c["bid"] < c["ask"] < 1 else None


def bucket(edges, f):
    for i in range(len(edges) - 1):
        if edges[i] <= f < edges[i + 1] or (i == len(edges) - 2 and f == edges[-1]): return i


def walk(spec, evs, idx):
    """-> (rows in decision order, not_filled). Each row carries b (None = base-building) from results that were public at its decision candle."""
    edges, need, settle = spec["strength_buckets_on_f"], spec["base_rate_minimum_earlier_events"], spec["settle_gap_seconds"]
    filled, nf = [], 0
    for e in evs.values():
        got = None
        for back in range(60, 601, 60):
            ts = e["S"] - back; q = {t: two(idx, t, ts) for t in [e["tie"]] + e["teams"]}
            if all(q.values()): got = (ts, q); break
        if got is None: nf += 1; continue
        ts, q = got; f = max(sum(q[t]) / 2 for t in e["teams"]); (tb, ta) = q[e["tie"]]
        filled.append({"event": e["event"], "S": e["S"], "close": e["close"], "ts": ts, "f": f, "bk": bucket(edges, f), "bid": tb, "ask": ta, "spread": round(ta - tb, 4), "result": e["result"]})
    filled.sort(key=lambda r: (r["ts"], r["event"]))
    pending = [(r["close"] + settle, r["event"], r) for r in filled]; heapq.heapify(pending)
    tally = {}; rows = []
    for r in filled:
        while pending and pending[0][0] <= r["ts"]:
            _, _, d = heapq.heappop(pending)
            if d["result"] in ("yes", "no"): t = tally.setdefault(d["bk"], [0, 0]); t[0] += 1; t[1] += d["result"] == "yes"
        n, y = tally.get(r["bk"], [0, 0]); b = y / n if n >= need else None
        mid = (r["ask"] + r["bid"]) / 2
        rows.append(dict(r, n_base=n, b=b, gap=None if b is None else round(b - r["ask"], 4), mirror=None if b is None else round(r["bid"] - b, 4),
                         rt=(r["ask"] - r["bid"]) + 2 * 0.07 * mid * (1 - mid), one_way=(r["ask"] - mid) + fee_up(round(r["ask"] + PRICE_THROUGH, 4))))
    return rows, nf


def _q(xs, p):
    xs = sorted(xs)
    if not xs: return None
    i = (len(xs) - 1) * p; lo, hi = math.floor(i), math.ceil(i); return round(xs[lo] + (xs[hi] - xs[lo]) * (i - lo), 4)


def measure(spec, list_folders, candle_folders):
    evs, c = events(spec, list_folders); idx = {t: {x["ts"]: x for x in v} for t, v in k.candles(candle_folders).items()}
    rows, nf = walk(spec, evs, idx); el = [r for r in rows if r["b"] is not None]
    gl, sl, edges = spec["gap_line"], spec["spread_line"], spec["strength_buckets_on_f"]
    share = lambda rs, key: None if not rs else sum(1 for r in rs if r[key] >= gl - 1e-9 and r["spread"] <= sl + 1e-9) / len(rs)
    rep = {"counts_first": dict(c, not_filled=nf, filled=len(rows), base_building=len(rows) - len(el), filled_eligible=len(el)), "label": "selected on development: this figure can falsify, it cannot support; only the frozen held-out read can",
           "median_spread": _q([r["spread"] for r in el], .5), "median_round_trip_information_only": _q([r["rt"] for r in el], .5), "median_one_way_entry_cost": _q([r["one_way"] for r in el], .5), "median_tie_ask": _q([r["ask"] for r in el], .5),
           "gap_q25_q50_q75_p90": [_q([r["gap"] for r in el], p) for p in (.25, .5, .75, .9)], "share_gap10_spread4": share(el, "gap"), "placebo_share": share(el, "mirror"), "by_bucket": {}, "freshness": FRESH}
    for i in range(len(edges) - 1):
        rs = [r for r in el if r["bk"] == i]; rep["by_bucket"][i] = {"f": edges[i:i + 2], "n": len(rs), "share": share(rs, "gap"), "placebo": share(rs, "mirror"), "median_gap": _q([r["gap"] for r in rs], .5)}
    kill = []
    if len(el) < MIN_FILLED: kill.append("no evidence at n = %d filled eligible" % len(el))
    if rep["median_one_way_entry_cost"] is not None and rep["median_one_way_entry_cost"] > spec["cost_kill_one_way_entry"] + 1e-9: kill.append("CLOSED on cost: median one-way entry cost %.1fc above 4c" % (100 * rep["median_one_way_entry_cost"]))
    s, p = rep["share_gap10_spread4"] or 0, rep["placebo_share"] or 0
    if not (s >= 0.03 and s >= 2 * p) and el: kill.append("CLOSED: efficient, move on (90th percentile gap %s)" % rep["gap_q25_q50_q75_p90"][3])
    if rep["median_tie_ask"] is not None and rep["median_tie_ask"] < CHEAP_ASK: kill.append("CLOSED as a cheap-tail contract (median Tie ask %.3f under 0.15)" % rep["median_tie_ask"])
    rep["kill"] = kill; rep["rule_may_be_scored"] = not kill and bool(el)
    rep["eligible_void_or_unsettled"] = sum(1 for r in el if r["result"] not in ("yes", "no"))
    return rep, rows


def verdict(n, pf_all, halves):
    if n < 100: return "no evidence at n = %d" % n
    if (pf_all is not None and pf_all < 1.0) or any(h is not None and h < 1.0 for h in halves): return "FALSIFIED"
    if (pf_all is None or pf_all >= 1.5) and all(h is None or h > 1.0 for h in halves): return "development bar met (ask the Head for the held-out pull)"
    return "below the bar at n = %d, PF %s" % (n, None if pf_all is None else round(pf_all, 3))


def score(spec, list_folders, candle_folders):
    rep, rows = measure(spec, list_folders, candle_folders)
    if not rep["rule_may_be_scored"]: return {"measurement": rep, "rule": "NOT SCORED: a kill line closed the card (no bet booked)"}
    half = ts_of(spec["blocks"]["development_half_split"]); gl, sl = spec["gap_line"], spec["spread_line"]; tr = []
    for r in rows:
        if r["b"] is None or r["gap"] < gl - 1e-9 or r["spread"] > sl + 1e-9: continue
        p = round(r["ask"] + PRICE_THROUGH, 4); f = fee_up(p); void = r["result"] not in ("yes", "no"); win = r["result"] == "yes"
        tr.append({"event": r["event"], "cluster": datetime.fromtimestamp(r["S"], timezone.utc).strftime("%Y-%m-%d"), "ts": r["ts"], "price": p, "fee": f, "win": win,
                   "net": (-f) if void else ((1 - p - f) if win else (-p - f)), "bk": r["bk"], "void": void})
    if not tr: return {"measurement": rep, "rule": {"bets": 0, "verdict": "no evidence at n = 0"}}
    out = k.score(tr, {"name": "ESOCTIE (development only, selected on development)", "price_source": "minute-end candle ask, two-sided, plus 1c; not a list quote", "freshness": FRESH})
    halves = [k.stats([t for t in tr if t["ts"] < half]), k.stats([t for t in tr if t["ts"] >= half])]
    wins = sum(1 for t in tr if t["win"]); byday = {}
    for t in tr: byday[t["cluster"]] = byday.get(t["cluster"], 0) + t["net"]
    tot = sum(byday.values())
    out.update({"bets": len(tr), "wins": wins, "mean_price_paid": round(sum(t["price"] for t in tr) / len(tr), 4), "halves": halves, "by_bucket": {i: k.stats([t for t in tr if t["bk"] == i]) for i in sorted({t["bk"] for t in tr})},
                "largest_day_share_of_net": None if tot <= 0 else round(max(byday.values()) / tot, 3), "void_bets_booked_as_fee_loss": sum(1 for t in tr if t["void"]),
                "registered_verdict": verdict(len(tr), out["all"]["pf"], [h["pf"] for h in halves if h["n"]]) + " (selected on development: can falsify, cannot support)"})
    return {"measurement": rep, "rule": out}


def build_candles(spec, list_folders, max_cells=9000, max_tickers=100, span_s=7200):
    evs, c = events(spec, list_folders); order = sorted(evs.values(), key=lambda e: (e["S"], e["event"])); packs, cur = [], []
    for e in order:
        trial = cur + [e]; lo = min(x["S"] for x in trial) - 660; hi = max(x["S"] for x in trial)
        if cur and (e["S"] - cur[0]["S"] > span_s or 3 * len(trial) > max_tickers or 3 * len(trial) * ((hi - lo) // 60 + 1) > max_cells): packs.append(cur); cur = [e]
        else: cur = trial
    if cur: packs.append(cur)
    reqs = [{"id": "c%05d" % i, "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(t for e in g for t in [e["tie"]] + e["teams"]), "start_ts": min(e["S"] for e in g) - 660, "end_ts": max(e["S"] for e in g), "period_interval": 1}} for i, g in enumerate(packs)]
    eps = [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}]
    j = tie3.job("ESOCTIE_CANDLES", "ESOCTIE candles: the three contracts of every development event, 1 minute, S minus 11 minutes to S.", eps, reqs, spec["series"], [t for e in order for t in [e["tie"]] + e["teams"]])
    j["registration"] = REG; j["heldout"] = "none: development events only (closes before 2026-10-23T00:00Z); held-out events are refused"; j["notes"] = "ESOCTIE candles built from ESOCTIE_LISTS; %d events kept, counts %s" % (len(evs), json.dumps(c))
    return j, c


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__)
    else:
        spec = load_cells()
        if a[0] == "build-candles": j, c = build_candles(spec, a[1:]); print(json.dumps(j, indent=1)); print(json.dumps(c), file=sys.stderr)
        elif a[0] in ("measure", "score"):
            i = a.index("--candles"); f = measure if a[0] == "measure" else score
            r = f(spec, a[1:i], a[i + 1:]); print(json.dumps(r[0] if a[0] == "measure" else r, indent=1, default=str))
