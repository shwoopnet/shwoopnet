#!/usr/bin/env python3
"""POLGAPH: builders and scorer. Written Nov 13, 2026, before any list, candle, price path or result of this
card was requested or read. The text it follows: polgap/POLGAPH_REGISTRATION.md with Amendment 1.

Four commands, in the order they are used:
  hourly-job <lists run> <out.json>                 builds the hourly candle job. Reads tickers, events, open and close times only.
  decide     <lists run> <hourly run> <out.json>    every decision (rule steps 1 to 7, before fills). Reads NO result.
  minute-job <decisions.json> <out.json>            builds the fill job: the minute ending 07:01 Eastern for each decision.
  score      <lists run> <hourly run> <minute run> <decisions.json>    fills, results, the registered lines.

Only `score` reads a result field. Every command refuses a path in a HELDOUT_ folder and any market closing
after the development window. Standard library only.
"""
import glob
import gzip
import json
import math
import os
import statistics
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from deskb_guard import refuse_all, refuse_heldout  # noqa: E402

ET = ZoneInfo("America/New_York")
EPS = 1e-9
DEV_FROM = "2026-09-12T00:00:00Z"
DEV_TO = "2026-11-12T23:59:59Z"            # closes after this are held out and must never appear
HALF_FROM = "2026-10-13"                   # Eastern date of the gap morning: second half from this date
GAP = 0.05
STEADY = 0.01
BAND = (0.10, 0.64)
SPREAD_MAX = 0.04
LIQUID = 200.0
LIQUID_DAYS = 7
SLIP = 0.01
BASELINE_GAP = 0.02
COST_KILL = 0.04
MIN_BETS, MIN_HALF = 150, 40
PF_LINE, HALF_LINE = 1.5, 1.0
LIFE_CAP_S = 35 * 86400                    # hourly candles asked for at most this long before a market's close
GROUP_TICKERS, MAX_CANDLES = 100, 8500
HOURLY_CAP, MINUTE_CAP = 240, 61
LABEL = "candle freshness measured on Bitcoin 15 minute only, not on these markets"
HERE = os.path.dirname(os.path.abspath(__file__))
SERIES_FILE = os.path.join(HERE, "POLGAPH_SERIES.json")
REG = "kalshi-scalper/workers/polgap/POLGAPH_REGISTRATION.md"
STOP = {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3,
        "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}


def ts(iso):
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())


def et_epoch(day, hour):
    """Epoch of `hour`:00 Eastern on the date `day` (a date object)."""
    return int(datetime(day.year, day.month, day.day, hour, 0, tzinfo=ET).timestamp())


def fee(price):
    """0.07 x p x (1 - p), rounded UP to the next whole cent, one contract."""
    return math.ceil(0.07 * price * (1 - price) * 100 - EPS) / 100.0


def families():
    d = json.load(open(SERIES_FILE))
    fam = {s: f for f, ss in d["families"].items() for s in ss}
    if sorted(fam) != sorted(d["series"]):
        sys.exit("REFUSED: the family map does not cover the series list exactly")
    return d["series"], fam


def read_markets(run):
    """Markets of the registered series from a lists run. Returns {ticker: row}. No result is looked at here."""
    refuse_heldout(run)
    series, fam = families()
    man = json.load(open(os.path.join(run, "manifest.json")))
    out, asked = {}, set()
    for row in man.get("rows", []):
        s = row.get("params", {}).get("series_ticker")
        if row.get("status") != 200 or s not in fam:
            continue
        asked.add(s)
        body = json.load(gzip.open(os.path.join(run, row["file"]), "rt"))
        for m in body.get("markets", []) if isinstance(body, dict) else []:
            tk, ev = m.get("ticker", ""), m.get("event_ticker", "")
            if not tk.startswith(s + "-") or not ev:
                continue
            try:
                o, c = ts(m["open_time"]), ts(m["close_time"])
            except (KeyError, ValueError, TypeError, AttributeError):
                continue
            out[tk] = {"ticker": tk, "event": ev, "series": s, "family": fam[s], "open": o, "close": c, "raw": m}
    late = [m["ticker"] for m in out.values() if m["close"] > ts(DEV_TO)]
    if late:
        sys.exit("REFUSED: %d listed markets close after the development window (standing rule (h)); first %s" % (len(late), late[0]))
    out = {k: v for k, v in out.items() if v["close"] >= ts(DEV_FROM)}
    return out, sorted(asked)


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
    """{ticker: {end_ts: (yes_bid, yes_ask, volume)}} from every answered request of a candle run."""
    refuse_heldout(run)
    found = {}
    for f in sorted(glob.glob(os.path.join(run, "[0-9]*.json.gz"))):
        walk(json.load(gzip.open(f, "rt")), found)
    out, novol = {}, 0
    for tk, cs in found.items():
        d = out.setdefault(tk, {})
        for c in cs:
            try:
                v = float(c.get("volume_fp", c.get("volume")))
            except (TypeError, ValueError):
                v, novol = 0.0, novol + 1
            d[int(c["end_period_ts"])] = (price(c.get("yes_bid")), price(c.get("yes_ask")), v)
    return out, novol


def two_sided(q):
    """A quote: 0 < bid < ask < 1. A book of 0.00 and 1.00 is empty, not a quote."""
    return q is not None and q[0] is not None and q[1] is not None and 0 < q[0] < q[1] < 1


def side_quote(q, side):
    """(bid, ask) of the bought side from a YES quote."""
    return (q[0], q[1]) if side == "yes" else (1 - q[1], 1 - q[0])


def mornings(m):
    """Every Eastern date D whose 07:00 look lies strictly inside the market's life."""
    d = datetime.fromtimestamp(m["open"], ET).date()
    last = datetime.fromtimestamp(m["close"], ET).date()
    while d <= last:
        look = et_epoch(d, 7)
        if m["open"] < look < m["close"]:
            yield d, look
        d += timedelta(days=1)


def group_requests(items, interval_s):
    """Batches (ticker, start, end) into requests of at most GROUP_TICKERS tickers and MAX_CANDLES candles, one time range each."""
    items = sorted(items, key=lambda r: (r[1], r[2], r[0]))
    groups = []
    for tk, s, e in items:
        g = groups[-1] if groups else None
        if g:
            s2, e2, n = min(g["start"], s), max(g["end"], e), len(g["tickers"]) + 1
            if n <= GROUP_TICKERS and n * ((e2 - s2) // interval_s + 1) <= MAX_CANDLES:
                g["tickers"].append(tk)
                g["start"], g["end"] = s2, e2
                continue
        groups.append({"tickers": [tk], "start": s, "end": e})
    return groups


def job(job_id, purpose, reqs, cap, tickers, notes):
    series, _ = families()
    return {"job_id": job_id, "owner": "DESK_B", "registration": REG, "purpose": purpose,
            "heldout": "none: every market closes on or before 2026-11-12 23:59:59Z and no request ends after it; closes from 2026-11-13 are held out and not pulled",
            "allowed_endpoints": [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks",
                                   "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}],
            "series_allowlist": series, "ticker_allowlist": sorted(tickers), "max_requests": cap, "requests": reqs, "notes": notes,
            "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0, "stop_rules": STOP}


def cmd_hourly_job(lists_run, out_path):
    mk, asked = read_markets(lists_run)
    items = []
    for m in mk.values():
        if not any(True for _ in mornings(m)):
            continue
        start = max(m["open"], m["close"] - LIFE_CAP_S) // 3600 * 3600
        items.append((m["ticker"], start, min(m["close"], ts(DEV_TO))))
    groups = group_requests(items, 3600)
    print("series answered %d | markets in the window %d | with a 07:00 Eastern look inside their life %d | hourly requests %d (cap %d)"
          % (len(asked), len(mk), len(items), len(groups), HOURLY_CAP))
    if len(groups) > HOURLY_CAP:
        print("OVER THE CAP: no job written. The sample is not cut here; the count goes to the Head of R&D.")
        return
    reqs = [{"id": "h%03d" % (k + 1), "path": "/markets/candlesticks",
             "params": {"market_tickers": ",".join(g["tickers"]), "start_ts": g["start"], "end_ts": g["end"], "period_interval": 60}} for k, g in enumerate(groups)]
    json.dump(job("POLGAPH_HOURLY", "POLGAPH development, stage 2: hourly candles of every listed market over its life (at most 35 days), for the overnight gap, the steady hour and the 7 day volume.",
                  reqs, HOURLY_CAP, [i[0] for i in items], "Built by polgap/polgaph.py hourly-job from the lists answer; tickers and times only."), open(out_path, "w"), indent=1)


def look_quotes(q, d, look):
    """The three hourly quotes of a morning, or None if any candle is missing."""
    t22 = et_epoch(d - timedelta(days=1), 22)
    t06 = et_epoch(d, 6)
    if t22 not in q or t06 not in q or look not in q:
        return None
    return q[t22], q[t06], q[look], t22


def steps_3_to_6(q22, q06, q07, t22, q, side):
    """Rule steps 3 to 6 for one side. Returns the name of the first step that fails, or None."""
    b07, a07 = side_quote(q07, side)
    _, a06 = side_quote(q06, side)
    if abs(a07 - a06) > STEADY + EPS:
        return "steady"
    if a07 < BAND[0] - EPS or a07 > BAND[1] + EPS:
        return "band"
    if a07 - b07 > SPREAD_MAX + EPS:
        return "spread"
    vol = sum(v[2] for t, v in q.items() if t22 - LIQUID_DAYS * 86400 < t <= t22)
    if vol < LIQUID - EPS:
        return "liquid"
    return None


def cmd_decide(lists_run, hourly_run, out_path):
    mk, asked = read_markets(lists_run)
    candles, novol = read_candles(hourly_run)
    n = dict(markets=len(mk), with_candles=0, market_mornings=0, no_look=0, one_sided=0, three_two_sided=0, gap=0,
             fail_steady=0, fail_band=0, fail_spread=0, fail_liquid=0, qualify=0)
    cost_rows, cands, base = [], {}, {}
    byfam = {}
    for m in mk.values():
        ff = byfam.setdefault(m["family"], dict(three_two_sided=0, gap=0, qualify=0))
        q = candles.get(m["ticker"])
        if q:
            n["with_candles"] += 1
        for d, look in mornings(m):
            n["market_mornings"] += 1
            lq = look_quotes(q or {}, d, look)
            if lq is None:
                n["no_look"] += 1
                continue
            q22, q06, q07, t22 = lq
            if not (two_sided(q22) and two_sided(q06) and two_sided(q07)):
                n["one_sided"] += 1
                continue
            n["three_two_sided"] += 1
            ff["three_two_sided"] += 1
            gap = (q07[0] + q07[1]) / 2 - (q22[0] + q22[1]) / 2
            key = (m["event"], d.isoformat())
            if abs(gap) < BASELINE_GAP - EPS:
                best = None
                for side in ("yes", "no"):
                    if steps_3_to_6(q22, q06, q07, t22, q, side) is None:
                        a = side_quote(q07, side)[1]
                        if best is None or abs(a - 0.5) < abs(best[1] - 0.5) - EPS:
                            best = (side, a)
                if best:
                    row = {"ticker": m["ticker"], "event": m["event"], "family": m["family"], "morning": d.isoformat(), "look": look, "side": best[0], "ask": best[1]}
                    cur = base.get(key)
                    if cur is None or abs(row["ask"] - 0.5) < abs(cur["ask"] - 0.5) - EPS or (abs(abs(row["ask"] - 0.5) - abs(cur["ask"] - 0.5)) <= EPS and row["ticker"] < cur["ticker"]):
                        base[key] = row
            if abs(gap) < GAP - EPS:
                continue
            n["gap"] += 1
            ff["gap"] += 1
            side = "yes" if gap > 0 else "no"
            b07, a07 = side_quote(q07, side)
            cost_rows.append({"family": m["family"], "ask": a07, "mid": (a07 + b07) / 2})
            why = steps_3_to_6(q22, q06, q07, t22, q, side)
            if why:
                n["fail_" + why] += 1
                continue
            n["qualify"] += 1
            ff["qualify"] += 1
            row = {"ticker": m["ticker"], "event": m["event"], "series": m["series"], "family": m["family"], "morning": d.isoformat(), "look": look,
                   "side": side, "ask": a07, "bid": b07, "gap": gap, "close": m["close"]}
            cur = cands.get(key)
            if cur is None or abs(a07 - 0.5) < abs(cur["ask"] - 0.5) - EPS or (abs(abs(a07 - 0.5) - abs(cur["ask"] - 0.5)) <= EPS and row["ticker"] < cur["ticker"]):
                cands[key] = row
    dec = sorted(cands.values(), key=lambda r: (r["look"], r["ticker"]))
    json.dump({"counts": n, "counts_by_family": byfam, "series_answered": len(asked), "candles_without_volume": novol, "cost_rows": cost_rows, "decisions": dec,
               "baseline": sorted(base.values(), key=lambda r: (r["look"], r["ticker"]))}, open(out_path, "w"), indent=1)
    print("POLGAPH decide (no result read) | %s" % LABEL)
    print("series answered %d | markets %d | with any hourly candle %d | candles without a volume field %d" % (len(asked), n["markets"], n["with_candles"], novol))
    print("market-mornings %d | no look (a candle missing) %d | a candle not two-sided %d | three two-sided candles %d | gap of 5c or more %d"
          % (n["market_mornings"], n["no_look"], n["one_sided"], n["three_two_sided"], n["gap"]))
    print("left after steady %d | after band %d | after spread %d | after liquid (qualifying market-mornings) %d | decisions, one per event and morning %d"
          % (n["gap"] - n["fail_steady"], n["gap"] - n["fail_steady"] - n["fail_band"], n["gap"] - n["fail_steady"] - n["fail_band"] - n["fail_spread"], n["qualify"], len(dec)))
    for f in sorted(byfam):
        print("   %s: three two-sided candles %d | gap of 5c or more %d | qualifying market-mornings %d | decisions %d"
              % (f, byfam[f]["three_two_sided"], byfam[f]["gap"], byfam[f]["qualify"], sum(1 for r in dec if r["family"] == f)))
    print("note: the steps are applied in order, so each failing market-morning is counted at its first failing step")


def cmd_minute_job(dec_path, out_path):
    refuse_heldout(dec_path)
    dec = json.load(open(dec_path))["decisions"]
    by = {}
    for r in dec:
        by.setdefault(r["look"], []).append(r["ticker"])
    reqs, tickers = [], set()
    for look in sorted(by):
        tks = sorted(set(by[look]))
        for i in range(0, len(tks), GROUP_TICKERS):
            reqs.append({"id": "m%d_%d" % (look, i // GROUP_TICKERS), "path": "/markets/candlesticks",
                         "params": {"market_tickers": ",".join(tks[i:i + GROUP_TICKERS]), "start_ts": look, "end_ts": look + 60, "period_interval": 1}})
            tickers.update(tks[i:i + GROUP_TICKERS])
    print("decisions %d | mornings with a decision %d | minute requests %d (cap %d)" % (len(dec), len(by), len(reqs), MINUTE_CAP + 10))
    if any(r["params"]["end_ts"] > ts(DEV_TO) for r in reqs):
        sys.exit("REFUSED: a request would end after the development window")
    if len(reqs) > MINUTE_CAP + 10:
        print("OVER THE CAP: no job written; the count goes to the Head of R&D.")
        return
    json.dump(job("POLGAPH_MINUTE", "POLGAPH development, stage 3: the one minute candle ending 07:01 Eastern for each decision, to judge the fill.",
                  reqs, MINUTE_CAP + 10, tickers, "Built by polgap/polgaph.py minute-job from decisions made without any result."), open(out_path, "w"), indent=1)


def minute_cover(run):
    """{ticker: [(start, end)]} for every minute request that was answered with status 200 and not cut short."""
    refuse_heldout(run)
    man = json.load(open(os.path.join(run, "manifest.json")))
    cover = {}
    for row in man.get("rows", []):
        p = row.get("params", {})
        if row.get("status") == 200 and p.get("period_interval") == 1 and not row.get("truncated"):
            for tk in str(p.get("market_tickers", "")).split(","):
                cover.setdefault(tk, []).append((int(p["start_ts"]), int(p["end_ts"])))
    return cover


def has_fill_data(cover, ticker, look):
    """Fill data exists if an answered minute request names the ticker and its range holds the minute ending 07:01."""
    return any(a <= look + 60 <= b for a, b in cover.get(ticker, []))


def stats(rows):
    """n, wins, net, profit factor, mean and the event-clustered z of a list of bets with 'cash' and 'event'."""
    if not rows:
        return dict(n=0, wins=0, net=0.0, pf=None, mean=None, z=None)
    cash = [r["cash"] for r in rows]
    won, lost = sum(c for c in cash if c > 0), -sum(c for c in cash if c < 0)
    cl = {}
    for r in rows:
        cl[r["event"]] = cl.get(r["event"], 0.0) + r["cash"]
    den = math.sqrt(sum(v * v for v in cl.values()))
    return dict(n=len(rows), wins=sum(1 for c in cash if c > 0), net=sum(cash), pf=(won / lost if lost > EPS else float("inf")),
                mean=sum(cash) / len(cash), z=(sum(cash) / den if den > EPS else None))


def fmt(s):
    if s["n"] == 0:
        return "n 0"
    pf = "no losses" if s["pf"] == float("inf") else "%.2f" % s["pf"]
    return "n %d, wins %d, cash PF %s, net %+.2f, mean %+.4f, event-clustered z %s" % (s["n"], s["wins"], pf, s["net"], s["mean"], "n/a" if s["z"] is None else "%+.2f" % s["z"])


def settle(m, side, paid, f, with_value=False):
    """Cash result of one contract. A result that is neither yes nor no is a void: price refunded, fee kept."""
    res = (m["raw"].get("result") or "").lower()
    if res in ("yes", "no"):
        return (1 - paid - f) if res == side else -(paid + f), False
    if with_value:
        try:
            v = float(m["raw"].get("settlement_value_dollars"))
            return ((v if side == "yes" else 1 - v) - paid - f), True
        except (TypeError, ValueError):
            pass
    return -f, True


def verdict(dev, h1, h2, label):
    if dev["n"] < MIN_BETS or h1["n"] < MIN_HALF or h2["n"] < MIN_HALF:
        return "%s: no evidence at n = %d (halves %d and %d; minimums %d and %d)" % (label, dev["n"], h1["n"], h2["n"], MIN_BETS, MIN_HALF)
    ok = dev["pf"] >= PF_LINE - EPS and h1["pf"] >= HALF_LINE - EPS and h2["pf"] >= HALF_LINE - EPS
    return "%s: %s" % (label, "survives development" if ok else "FALSIFIED")


def cmd_score(lists_run, hourly_run, minute_run, dec_path):
    refuse_heldout(dec_path)
    mk, _ = read_markets(lists_run)
    d = json.load(open(dec_path))
    minute, _ = read_candles(minute_run)
    cover = minute_cover(minute_run)
    _, fam = families()
    fams = sorted(set(fam.values()))
    print("POLGAPH score | %s" % LABEL)
    print("counts from the decide step: %s" % json.dumps(d["counts"], sort_keys=True))
    # the one-way cost line, before any result
    def cost_line(rows):
        if not rows:
            return None, None
        return (statistics.median([r["ask"] - r["mid"] + fee(r["ask"] + SLIP) for r in rows]),
                statistics.median([r["ask"] + SLIP - r["mid"] + fee(r["ask"] + SLIP) for r in rows]))
    c_all = cost_line(d["cost_rows"])
    print("one-way cost, median over %d market-mornings with a gap and three two-sided candles: %s (the kill line reads this); cost as paid at the limit, information only: %s"
          % (len(d["cost_rows"]), "n/a" if c_all[0] is None else "%.4f" % c_all[0], "n/a" if c_all[1] is None else "%.4f" % c_all[1]))
    for f in fams:
        c = cost_line([r for r in d["cost_rows"] if r["family"] == f])
        print("   %s: %d market-mornings, %s" % (f, sum(1 for r in d["cost_rows"] if r["family"] == f), "n/a" if c[0] is None else "%.4f" % c[0]))
    if c_all[0] is None or c_all[0] > COST_KILL + EPS:
        print("VERDICT: %s. No result was read." % ("no gap morning to measure" if c_all[0] is None else "CLOSED on cost (above 4c)"))
        return
    # fills, walking the decisions in time order; a filled bet blocks its event until its market closes
    n = dict(decisions=len(d["decisions"]), blocked=0, no_fill_data=0, not_filled=0, filled_present=0, filled_unchanged=0, void=0)
    open_until, bets, optimistic = {}, [], []
    for r in d["decisions"]:
        m = mk.get(r["ticker"])
        if m is None:
            continue
        limit = r["ask"] + SLIP
        f = fee(limit)
        cash_o, _ = settle(m, r["side"], limit, f)
        optimistic.append(dict(r, cash=cash_o))
        if open_until.get(r["event"], 0) > r["look"]:
            n["blocked"] += 1
            continue
        if not has_fill_data(cover, r["ticker"], r["look"]):
            n["no_fill_data"] += 1
            continue
        c = minute.get(r["ticker"], {}).get(r["look"] + 60)
        if c is None:
            kind = "unchanged"
        else:
            ask = c[1] if r["side"] == "yes" else (None if c[0] is None else 1 - c[0])
            empty = c[0] is not None and c[1] is not None and c[0] <= EPS and c[1] >= 1 - EPS
            if ask is None or empty or ask > limit + EPS:
                n["not_filled"] += 1
                continue
            kind = "present"
        n["filled_" + kind] += 1
        cash, void = settle(m, r["side"], limit, f)
        cash_v, _ = settle(m, r["side"], limit, f, with_value=True)
        n["void"] += void
        open_until[r["event"]] = m["close"]
        bets.append(dict(r, cash=cash, cash_value=cash_v, fill=kind))
    print("decisions, one per event and morning %d | blocked by an open bet on the event %d | fired %d | no fill data %d | not filled %d | filled on a present candle %d | filled on an unchanged minute %d | voids among filled %d"
          % (n["decisions"], n["blocked"], n["decisions"] - n["blocked"], n["no_fill_data"], n["not_filled"], n["filled_present"], n["filled_unchanged"], n["void"]))
    half = lambda rows, second: [r for r in rows if (r["morning"] >= HALF_FROM) == second]   # noqa: E731
    events = sorted((r["look"], r["close"]) for r in bets)
    peak = max((sum(1 for a, b in events if a <= t < b) for t, _ in events), default=0)
    for name, rows in (("first half", half(bets, False)), ("second half", half(bets, True))):
        print("%s: filled %d | distinct events %d | series %d | mornings %d" % (name, len(rows), len({r["event"] for r in rows}), len({r["series"] for r in rows}), len({r["morning"] for r in rows})))
    print("largest number of bets open at once: %d (the rulebook allows 10)" % peak)
    dev, h1, h2 = stats(bets), stats(half(bets, False)), stats(half(bets, True))
    print("POOLED development: %s" % fmt(dev))
    print("   first half: %s" % fmt(h1))
    print("   second half: %s" % fmt(h2))
    by = {}
    for f in fams:
        rows = [r for r in bets if r["family"] == f]
        by[f] = (stats(rows), stats(half(rows, False)), stats(half(rows, True)))
        print("FAMILY %s: decisions %d | %s" % (f, sum(1 for r in d["decisions"] if r["family"] == f), fmt(by[f][0])))
        print("   first half: %s | second half: %s" % (fmt(by[f][1]), fmt(by[f][2])))
    print("information only, fills on a present candle: %s" % fmt(stats([r for r in bets if r["fill"] == "present"])))
    print("information only, optimistic, same-candle fill (every decision booked at the limit, no block): %s" % fmt(stats(optimistic)))
    print("information only, voids paid at their settlement value instead: %s" % fmt(stats([dict(r, cash=r["cash_value"]) for r in bets])))
    base = []
    for r in d["baseline"]:
        m = mk.get(r["ticker"])
        if m:
            limit = r["ask"] + SLIP
            base.append(dict(r, cash=settle(m, r["side"], limit, fee(limit))[0]))
    print("information only, price-matched baseline (gap under 2c, same steps, same-candle basis): %s" % fmt(stats(base)))
    # the registered lines
    lead = [f for f in fams if dev["net"] > EPS and by[f][0]["net"] > 0.5 * dev["net"] + EPS]
    if lead:
        f = lead[0]
        print("POOLING CONDITION: %s supplies more than half of the pooled net (%.2f of %.2f), so a pooled pass does not count; the card is read as that family's alone." % (f, by[f][0]["net"], dev["net"]))
        print("VERDICT: " + verdict(by[f][0], by[f][1], by[f][2], f))
    else:
        print("VERDICT: " + verdict(dev, h1, h2, "pooled"))
    print("A survival is a candidate for a wheel shadow place only. The shared deflated bar (one-sided z 5.46) is not claimed.")


def main():
    refuse_all()
    cmds = {"hourly-job": (cmd_hourly_job, 2), "decide": (cmd_decide, 3), "minute-job": (cmd_minute_job, 2), "score": (cmd_score, 4)}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds or len(sys.argv) - 2 != cmds[sys.argv[1]][1]:
        sys.exit(__doc__)
    cmds[sys.argv[1]][0](*sys.argv[2:])


if __name__ == "__main__":
    main()
