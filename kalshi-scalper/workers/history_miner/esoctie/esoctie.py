#!/usr/bin/env python3
"""ESOCTIE reader, measurement, candle-job builder and scorer (History Miner, Nov 12, 2026). Research only; sends nothing.
Registration: ESOCTIE_REGISTRATION.md (this folder). Series and constants: ESOCTIE_SERIES.json (hash-checked below).
scorekit.py in this folder is a byte copy of claude/testing-desk 04af31f1 workers/testing/scorekit.py (sha256 checked below).

CLI:
  python3 -I esoctie.py build-candles <lists_folder>...            -> writes ESOCTIE_CANDLES.json (a job file for review)
  python3 -I esoctie.py measure --lists <f>... --candles <f>...    -> counts, cost, gap and placebo shares, the kill lines (no bet booked)
  python3 -I esoctie.py score   --lists <f>... --candles <f>...    -> the registered rule on DEVELOPMENT only (refuses any held-out event)
"""
import calendar, hashlib, json, math, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scorekit as sk  # noqa: E402

SCOREKIT_SHA = "c22d52e1c6df1343ae9691a7dc916464ff7d26e26cc22b27e131ecc11c1fa9d2"
CFG = json.load(open(os.path.join(HERE, "ESOCTIE_SERIES.json")))
DEV_FROM = sk.iso(CFG["blocks"]["development_closes_from"])
DEV_BEFORE = sk.iso(CFG["blocks"]["development_closes_before"])
HALF = sk.iso(CFG["blocks"]["development_half_split"])
EDGES = CFG["strength_buckets_on_f"]
MIN_BASE = CFG["base_rate_minimum_earlier_events"]
GAP, SPREAD = CFG["gap_line"], CFG["spread_line"]
OPEN_LO, OPEN_HI = [m * 60 for m in CFG["open_guard_minutes_before_S"]]
PRE_BACK_MAX = 10   # minutes
SETTLE_GAP_S = CFG["settle_gap_seconds"]  # NOTE 3
ONE_WAY_COST_KILL = CFG["cost_kill_one_way_entry"]  # NOTE 3
FRESH = "candle freshness measured on Bitcoin 15 minute only, not on e-soccer"
MONTHS = {m: i for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}


def check_hashes():
    h = hashlib.sha256(open(os.path.join(HERE, "scorekit.py"), "rb").read()).hexdigest()
    if h != SCOREKIT_SHA:
        raise SystemExit("scorekit.py is not the pinned copy")


def us_eastern_offset(y, mo, d, hh, mi):
    """Seconds to ADD to Eastern local time to get UTC: 4 h in daylight time (second Sunday of March 2:00 to first Sunday of November 2:00), else 5 h."""
    def nth_sunday(year, month, n):
        first = calendar.weekday(year, month, 1)  # Mon=0
        return 1 + (6 - first) % 7 + 7 * (n - 1)
    loc = (mo, d, hh, mi)
    start = (3, nth_sunday(y, 3, 2), 2, 0)
    end = (11, nth_sunday(y, 11, 1), 2, 0)
    return 4 * 3600 if start <= loc < end else 5 * 3600


def start_of(event):
    """S (epoch) from the event key 'YYMONDDHHMM...' read as US Eastern; None if unreadable."""
    try:
        k = event.split("-")[1]
        y, mon, d, hh, mi = 2000 + int(k[0:2]), MONTHS[k[2:5]], int(k[5:7]), int(k[7:9]), int(k[9:11])
    except (IndexError, KeyError, ValueError):
        return None
    return calendar.timegm((y, mon, d, hh, mi, 0)) + us_eastern_offset(y, mon, d, hh, mi)


def events(mk):
    """{event: dict(event, S, close, tie, teams[2], tie_result)} for KXESOCCERGAME events with exactly 3 markets (one -TIE). Counts dropped."""
    by = {}
    for t, m in mk.items():
        if m["series"] != "KXESOCCERGAME":
            continue
        by.setdefault(m["event"], []).append(m)
    out, drop = {}, {"shape": 0, "start not derivable": 0, "outside development": 0, "held-out (refused)": 0}
    for e, ms in by.items():
        ties = [m for m in ms if m["ticker"].endswith("-TIE")]
        teams = sorted(m["ticker"] for m in ms if not m["ticker"].endswith("-TIE"))
        if len(ms) != 3 or len(ties) != 1 or len(teams) != 2:
            drop["shape"] += 1
            continue
        close = max(m["close"] or 0 for m in ms)
        if close >= DEV_BEFORE:
            drop["held-out (refused)"] += 1
            continue
        if close < DEV_FROM:
            drop["outside development"] += 1
            continue
        S = start_of(e)
        op = ties[0]["open"]
        # NOTE 2 guard: decided only by what is known before the decision (the ticker clock and the Tie's open time), never by the close
        if S is None or op is None or not (OPEN_LO <= S - op <= OPEN_HI):
            drop["start not derivable"] += 1
            continue
        out[e] = {"event": e, "S": S, "close": close, "tie": ties[0]["ticker"], "teams": teams, "tie_result": ties[0]["result"]}
    return out, drop


def at(cs, ts):
    for c in cs or []:
        if c["ts"] == ts:
            return c
    return None


def two(c):
    return c is not None and c["bid"] is not None and c["ask"] is not None and 0 < c["bid"] < c["ask"] < 1


def pre_minute(ev, cd):
    """The candle end at S-60 stepping back to S-600 where the Tie and both team contracts are two-sided at the close; returns (ts, {ticker: candle}) or None."""
    base = ev["S"] - 60
    for back in range(0, PRE_BACK_MAX):
        ts = base - 60 * back
        cs = {t: at(cd.get(t), ts) for t in [ev["tie"]] + ev["teams"]}
        if all(two(c) for c in cs.values()):
            return ts, cs
    return None


def bucket(f):
    for i in range(len(EDGES) - 1):
        if EDGES[i] <= f < EDGES[i + 1] or (i == len(EDGES) - 2 and f == EDGES[-1]):
            return i
    return None


def fee_up(p):
    return math.ceil(round(0.07 * p * (1 - p) * 100, 9)) / 100.0


def walk(evs, cd):
    """Time-ordered pass over filled development events. Base rate b per bucket from EARLIER closes only (close < this event's S).
    Yields rows: dict(event, S, ts, f, k, b or None, ask, bid, spread, rt, gap, mirror, tie_result)."""
    filled = []
    nf = 0
    for e in evs.values():
        p = pre_minute(e, cd)
        if p is None:
            nf += 1
            continue
        ts, cs = p
        f = max((cs[t]["bid"] + cs[t]["ask"]) / 2 for t in e["teams"])
        tc = cs[e["tie"]]
        mid = (tc["bid"] + tc["ask"]) / 2
        filled.append(dict(event=e["event"], S=e["S"], close=e["close"], ts=ts, f=f, k=bucket(f), ask=tc["ask"], bid=tc["bid"], spread=round(tc["ask"] - tc["bid"], 4),
                           rt=round(tc["ask"] - tc["bid"] + 2 * 0.07 * mid * (1 - mid), 4), tie_result=e["tie_result"]))
    # NOTE 3: a game's result enters the base rate only if its close + SETTLE_GAP_S is at or before the bet's decision time (ts), so b is strictly point-in-time
    filled.sort(key=lambda r: (r["ts"], r["event"]))
    done = sorted(filled, key=lambda r: r["close"])
    rows, j, tally = [], 0, {}
    for r in filled:
        while j < len(done) and done[j]["close"] + SETTLE_GAP_S <= r["ts"]:
            d = done[j]
            if d["tie_result"] in ("yes", "no"):
                t = tally.setdefault(d["k"], [0, 0])
                t[0] += 1
                t[1] += d["tie_result"] == "yes"
            j += 1
        t = tally.get(r["k"], [0, 0])
        r = dict(r)
        r["n_base"] = t[0]
        r["b"] = (t[1] / t[0]) if t[0] >= MIN_BASE else None
        r["gap"] = None if r["b"] is None else round(r["b"] - r["ask"], 4)
        r["mirror"] = None if r["b"] is None else round(r["bid"] - r["b"], 4)
        r["entry_cost"] = round((r["ask"] - (r["ask"] + r["bid"]) / 2) + fee_up(round(min(r["ask"] + 0.01, 0.99), 4)), 4)
        rows.append(r)
    return rows, nf


def q(xs, p):
    xs = sorted(xs)
    if not xs:
        return None
    i = (len(xs) - 1) * p
    lo, hi = math.floor(i), math.ceil(i)
    return round(xs[lo] + (xs[hi] - xs[lo]) * (i - lo), 4)


def measure(lists, cands):
    mk = sk.markets(lists)
    evs, drop = events(mk)
    cd = sk.candles(cands)
    rows, nf = walk(evs, cd)
    elig = [r for r in rows if r["b"] is not None]
    share = lambda rs, key: (sum(1 for r in rs if r[key] is not None and r[key] >= GAP and r["spread"] <= SPREAD) / len(rs)) if rs else None
    rep = {"events_listed": len(set(m["event"] for m in mk.values() if m["series"] == "KXESOCCERGAME")), "dropped": drop, "events_kept": len(evs), "not_filled": nf, "filled": len(rows),
           "base_building": len(rows) - len(elig), "filled_eligible": len(elig), "median_spread": q([r["spread"] for r in elig], .5), "median_round_trip": q([r["rt"] for r in elig], .5),
           "gap": {p: q([r["gap"] for r in elig], p) for p in (.25, .5, .75, .9)}, "share_gap10_spread4": share(elig, "gap"), "placebo_share_mirror": share(elig, "mirror"),
           "by_bucket": {}, "freshness": FRESH}
    for k in range(len(EDGES) - 1):
        rs = [r for r in elig if r["k"] == k]
        rep["by_bucket"][k] = {"f": EDGES[k:k + 2], "n": len(rs), "share": share(rs, "gap"), "placebo": share(rs, "mirror"), "gap_median": q([r["gap"] for r in rs], .5)}
    kill = []
    if len(elig) < 150:
        kill.append("no evidence at n = %d" % len(elig))
    rep["median_one_way_entry_cost"] = q([r["entry_cost"] for r in elig], .5)
    rep["unsettled_or_void_eligible"] = sum(1 for r in elig if r["tie_result"] not in ("yes", "no"))
    if rep["median_one_way_entry_cost"] is not None and rep["median_one_way_entry_cost"] > ONE_WAY_COST_KILL:
        kill.append("closed on cost (median one-way entry cost %.3f over %.2f; a request-saving screen, not the bar)" % (rep["median_one_way_entry_cost"], ONE_WAY_COST_KILL))
    s, pl = rep["share_gap10_spread4"] or 0, rep["placebo_share_mirror"] or 0
    if not (s >= 0.03 and s >= 2 * pl):
        kill.append("efficient, move on (90th percentile gap %s)" % rep["gap"][.9])
    med_ask = q([r["ask"] for r in elig], .5)
    rep["median_tie_ask"] = med_ask
    if med_ask is not None and med_ask < 0.15:
        kill.append("closed as a cheap-tail contract (median Tie ask %.3f under 0.15; registration note 1)" % med_ask)
    rep["kill"] = kill
    rep["rule_may_be_scored"] = not kill
    return rep, rows


def score(lists, cands):
    rep, rows = measure(lists, cands)
    if not rep["rule_may_be_scored"]:
        return {"measurement": rep, "rule": "NOT SCORED: a kill line closed the card", "kill": rep["kill"]}
    trades = []
    for r in rows:
        if r["b"] is None or r["gap"] < GAP or r["spread"] > SPREAD or r["tie_result"] not in ("yes", "no"):
            continue
        p = round(min(r["ask"] + 0.01, 0.99), 4)
        fe = fee_up(p)
        win = r["tie_result"] == "yes"
        trades.append({"event": r["event"], "cluster": time.strftime("%Y-%m-%d", time.gmtime(r["S"])), "ts": r["ts"], "price": p, "win": win, "net": round((1 - p - fe) if win else (-p - fe), 4), "k": r["k"]})
    out = sk.score(trades, {"name": "ESOCTIE (development only)", "price_source": "minute-end candle close, two-sided, ask plus 1c", "freshness": FRESH})
    out["halves"] = [sk.stats([t for t in trades if t["ts"] < HALF]), sk.stats([t for t in trades if t["ts"] >= HALF])]
    out["by_bucket"] = {k: sk.stats([t for t in trades if t["k"] == k]) for k in range(len(EDGES) - 1)}
    n = len(trades)
    pf_all = out["all"]["pf"]
    halves_ok = all(h["pf"] is not None and h["pf"] > 1.0 for h in out["halves"] if h["n"])
    if n < 100:
        verdict = "no evidence at n = %d" % n
    elif (pf_all is not None and pf_all < 1.0) or any(h["n"] and h["pf"] is not None and h["pf"] < 1.0 for h in out["halves"]):
        verdict = "FALSIFIED"
    elif pf_all is not None and pf_all >= 1.5 and halves_ok:
        verdict = "development bar met (ask the Head for the held-out pull)"
    else:
        verdict = "below the bar at n = %d, PF %s" % (n, pf_all)
    out["registered_verdict"] = verdict
    return {"measurement": rep, "rule": out}


def build_candles(lists, out_path, max_cells=9000, max_tickers=100, span_s=7200):
    mk = sk.markets(lists)
    evs, drop = events(mk)
    order = sorted(evs.values(), key=lambda e: (e["S"], e["event"]))
    reqs, i = [], 0
    while i < len(order):
        g = [order[i]]
        j = i + 1
        while j < len(order):
            cand = g + [order[j]]
            lo = min(e["S"] for e in cand) - 60 * (PRE_BACK_MAX + 1)
            hi = max(e["S"] for e in cand)
            tk = sum(3 for _ in cand)
            if order[j]["S"] - g[0]["S"] > span_s or tk > max_tickers or tk * ((hi - lo) // 60 + 1) > max_cells:
                break
            g = cand
            j += 1
        lo = min(e["S"] for e in g) - 60 * (PRE_BACK_MAX + 1)
        hi = max(e["S"] for e in g)
        tick = [t for e in g for t in [e["tie"]] + e["teams"]]
        reqs.append({"id": "c%05d" % len(reqs), "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(tick), "start_ts": lo, "end_ts": hi, "period_interval": 1}})
        i = j
    job = {"job_id": "ESOCTIE_CANDLES", "status": "active", "owner": "MAIN", "registration": "kalshi-scalper/workers/history_miner/esoctie/ESOCTIE_REGISTRATION.md",
           "purpose": "ESOCTIE candles: the three contracts of every development event, 1 minute, from S minus 11 minutes to S; packed by S (minutes x tickers at most 9,000).",
           "heldout": "none: development events only (closes before 2026-10-23T00:00Z); held-out events are refused by the builder",
           "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2",
           "allowed_endpoints": [{"name": "candles_batched", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
           "ticker_allowlist": sorted({t for r in reqs for t in r["params"]["market_tickers"].split(",")}), "series_allowlist": ["KXESOCCERGAME"], "pacing_seconds": 1.0,
           "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "three 429s in a row end the run; no retry around a refusal"},
           "max_requests": len(reqs), "requests": reqs, "notes": "built by esoctie.py build-candles from ESOCTIE_LISTS; %d events kept, drops %s" % (len(evs), json.dumps(drop))}
    open(out_path, "w").write(json.dumps(job, indent=1) + "\n")
    return len(reqs), len(evs), drop


def main(argv):
    check_hashes()
    if argv and argv[0] == "build-candles":
        n, ne, drop = build_candles(argv[1:], os.path.join(HERE, "ESOCTIE_CANDLES.json"))
        print(json.dumps({"requests": n, "events": ne, "dropped": drop}))
        return
    if argv and argv[0] in ("measure", "score"):
        lists = argv[argv.index("--lists") + 1: argv.index("--candles")]
        cands = argv[argv.index("--candles") + 1:]
        res = measure(lists, cands)[0] if argv[0] == "measure" else score(lists, cands)
        print(json.dumps(res, indent=1, default=str))
        return
    print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
