#!/usr/bin/env python3
"""Scorer for the three ALL-KALSHI VERSION cards (Idea Desk C, Nov 15, 2026), build 1. Standard library only, no network.

Cards (each card file is the rule; this script follows it):
  NBA_O  KXNBAPTS (O) fade a 3 h pre-game move   ../nbapts/KXNBAPTS_OL_CARD.md
  NBA_L  KXNBAPTS (L) follow the last pre-game hour
  MENT   MENTDRIFT, follow a 5 h move before a Trump speech   ../mentdrift/MENTDRIFT_CARD.md
Each card has four tries: hold, T, S, M (EXITS3, with the M time stated in its card).

Inputs: a folder holding the pull runs (pull/<JOB>/<run>/manifest.json and NNNN.json.gz) for the card's list job(s) and candle job(s).
Order of reading, so no reserved window is read: markets are kept or dropped by their time fields alone; the result of a kept market
is read only after the window filter; the candle files are opened only for kept tickers.

Usage: python3 -I ol_score.py <card NBA_O|NBA_L|MENT> <root> [--check-only]
"""
import calendar
import hashlib
import gzip
import json
import math
import os
import sys
import time

EPS = 1e-9
LABEL = "candle replay, upper bound, not fill-checked"
H_LINES = (("raw", 0.0), ("1c", 0.01), ("2c", 0.02))


def iso(s):
    s = (s or "").strip()
    if not s:
        return None
    s = s.split(".")[0].rstrip("Z")
    try:
        return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%S"))
    except ValueError:
        return None


def T(s):
    return iso(s)


CARDS = {
    "NBA_O": {"series": ("KXNBAPTS",), "win_on": "close", "dev": (T("2026-10-21T00:00:00Z"), T("2026-11-06T00:00:00Z")),
              "move_min": 180, "thr": 0.10, "follow": False, "band": (0.40, 0.60), "cap_event": None, "list_jobs": ("KXNBAPTS_LISTS_A",)},
    "NBA_L": {"series": ("KXNBAPTS",), "win_on": "close", "dev": (T("2026-10-21T00:00:00Z"), T("2026-11-06T00:00:00Z")),
              "move_min": 60, "thr": 0.06, "follow": True, "band": (0.40, 0.60), "cap_event": None, "list_jobs": ("KXNBAPTS_LISTS_A",)},
    "MENT": {"series": ("KXTRUMPMENTION", "KXTRUMPMENTIONB"), "win_on": "occurrence", "dev": (T("2026-04-17T00:00:00Z"), T("2026-08-06T00:00:00Z")),
             "move_min": 300, "thr": 0.08, "follow": True, "band": (0.30, 0.70), "cap_event": 3, "list_jobs": ("MENTDRIFT_LISTS_A",)},
}
MENT_SEED = "MENTDRIFT-2026-11-15"     # the Head of R&D, Nov 15 14:51Z: fixed md5 sample of 1,400
MENT_SAMPLE_N = 1400
NBA_TIP_FROM_OCC_S = 3 * 3600        # tip proxy P = occurrence - 3 h
NBA_BUFFER_S = 30 * 60               # last pre-game mark G = P - 30 min
NBA_PROXY_MAX_EARLY = 0.02           # stop before any result read if more than 2% of markets close before G


def fee(p):
    return math.ceil(0.07 * p * (1 - p) * 100 - EPS) / 100


def num(x):
    try:
        v = float(x)
        return v if v == v else None
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ files
def run_dirs(root, job):
    base = os.path.join(root, "pull", job)
    if not os.path.isdir(base):
        return []
    out = []
    for r in sorted(os.listdir(base)):
        mp = os.path.join(base, r, "manifest.json")
        if os.path.isfile(mp):
            with open(mp) as f:
                man = json.load(f)
            if man.get("status") in ("complete", "stopped_size", "stopped_cap"):
                out.append((os.path.join(base, r), man))
    return out


def bodies(rdir, man):
    for row in man.get("rows", []):
        f = os.path.join(rdir, "%04d.json.gz" % int(row["index"]))
        if os.path.isfile(f):
            with gzip.open(f, "rt") as fh:
                yield row, json.load(fh)


def list_markets(root, card):
    """Every market of the card's series from its list jobs, keyed by ticker. Time and identity fields only; result kept raw, not read here."""
    out = {}
    for job in card["list_jobs"]:
        for rdir, man in run_dirs(root, job):
            for _row, b in bodies(rdir, man):
                for m in (b.get("markets") or []) if isinstance(b, dict) else []:
                    t = m.get("ticker") or ""
                    if t.split("-")[0] in card["series"]:
                        out.setdefault(t, m)
    return out


def candle_quotes(root, jobs, keep):
    """ticker -> {end_ts: (yes_bid, yes_ask)} from batched (/markets/candlesticks) or single (.../{ticker}/candlesticks) answers, kept tickers only."""
    q = {}

    def add(t, cs):
        if t not in keep:
            return
        d = q.setdefault(t, {})
        for c in cs or []:
            ts = c.get("end_period_ts")
            yb, ya = side_px(c.get("yes_bid")), side_px(c.get("yes_ask"))
            if isinstance(ts, int):
                d.setdefault(ts, (yb, ya))

    for job in jobs:
        for rdir, man in run_dirs(root, job):
            for row, b in bodies(rdir, man):
                if not isinstance(b, dict):
                    continue
                if "markets" in b and isinstance(b["markets"], list):
                    for m in b["markets"]:
                        add(m.get("market_ticker") or m.get("ticker"), m.get("candlesticks"))
                elif "candlesticks" in b:
                    parts = row.get("path", "").split("/")
                    t = b.get("ticker") or (parts[-2] if len(parts) >= 2 else "")
                    add(t, b.get("candlesticks"))
    return q


def side_px(o):
    if not isinstance(o, dict):
        return None
    if "close_dollars" in o:
        return num(o.get("close_dollars"))
    v = num(o.get("close"))
    return None if v is None else v / 100.0


def two_sided(yb, ya):
    return yb is not None and ya is not None and yb > EPS and ya < 1 - EPS and ya - yb > EPS


# ------------------------------------------------------------------ the rule
def clock(card_id, m, event_occ):
    """(D, anchor, M_ts) in unix seconds, or None. Time fields only."""
    card = CARDS[card_id]
    if card_id in ("NBA_O", "NBA_L"):
        occ = iso(m.get("occurrence_datetime"))
        if occ is None:
            return None
        G = occ - NBA_TIP_FROM_OCC_S - NBA_BUFFER_S
        D = G - 3600
        return D, D - card["move_min"] * 60, G
    O = event_occ
    if O is None:
        return None
    D = O - 3600
    return D, D - card["move_min"] * 60, O - 300


def signal(card_id, qt, D, anchor):
    """(side, raw ask, move) or (None, reason, None)."""
    card = CARDS[card_id]
    a, b = qt.get(D), qt.get(anchor)
    if a is None or b is None or not two_sided(*a) or not two_sided(*b):
        return None, "not_two_sided", None
    m = (a[0] + a[1]) / 2 - (b[0] + b[1]) / 2
    if abs(m) < card["thr"] - EPS:
        return None, "no_move", m
    rose_yes = m > 0
    buy_yes = rose_yes if card["follow"] else not rose_yes
    yb, ya = a
    side, ask = ("yes", round(ya, 6)) if buy_yes else ("no", round(1 - yb, 6))
    lo, hi = card["band"]
    if not (lo - EPS <= ask <= hi + EPS):
        return None, "out_of_band", m
    return (side, ask, m)


def side_bid(side, yb, ya):
    if side == "yes":
        return yb
    return None if ya is None else round(1 - ya, 6)


def sellable(bid):
    return bid is not None and EPS < bid < 1 - EPS


def exit_for(variant, qt, D, close, M_ts, side, e):
    """('hold', None, None) or (reason, mark_ts, raw bid)."""
    if variant == "hold":
        return ("held", None, None)
    last = close - 60
    marks = sorted(ts for ts in qt if D < ts <= last)
    if variant == "M":
        if M_ts <= D:
            return ("held_no_M", None, None)
        for ts in marks:
            if ts < M_ts:
                continue
            bid = side_bid(side, *qt[ts])
            if sellable(bid):
                return ("M", ts, bid)
        return ("held", None, None)
    tp = min(2 * e, 0.90)
    for ts in marks:
        bid = side_bid(side, *qt[ts])
        if not sellable(bid):
            continue
        if variant == "T" and bid >= tp - EPS:
            return ("T", ts, bid)
        if variant == "S" and bid <= e / 2 + EPS:
            return ("S", ts, bid)
    return ("held", None, None)


def pnl(e, h, won, void, ex_ts, ex_bid, entry_ts, close, primary=False):
    """1 contract. primary: h becomes 2c on a leg inside the last 2 minutes before close (C8)."""
    he = 0.02 if (primary and close - entry_ts <= 120) else h
    a = round(e + he, 6)
    cost = a + fee(a)
    if ex_ts is not None:
        hx = 0.02 if (primary and close - ex_ts <= 120) else h
        s = max(0.01, round(ex_bid - hx, 6))
        return round(s - fee(s) - cost, 6)
    if void:
        return round(-fee(a), 6)
    return round((1 - cost) if won else -cost, 6)


def pf_raw(xs):
    if not xs:
        return None
    w = sum(x for x in xs if x > EPS)
    l = -sum(x for x in xs if x < -EPS)
    return float("inf") if l == 0 else w / l


def cluster_z(xs, keys):
    c = {}
    for x, k in zip(xs, keys):
        c[k] = c.get(k, 0.0) + x
    v = list(c.values())
    k = len(v)
    if k < 2:
        return None
    mu = sum(v) / k
    ss = sum((x - mu) ** 2 for x in v)
    return None if ss <= 0 else sum(v) / math.sqrt(k / (k - 1) * ss)


def shown(v):
    return None if v is None else ("inf" if v == float("inf") else round(v, 4))


def bar_ok(pf1, h1, h2, pf2):
    z = lambda x: 0.0 if x is None else x
    return z(pf1) >= 1.3 and z(h1) >= 1.0 and z(h2) >= 1.0 and z(pf2) >= 1.0


# ------------------------------------------------------------------ main
def select(card_id, mk):
    """Window filter on time fields only. Returns (kept dict, counts, event occurrence map)."""
    card = CARDS[card_id]
    lo, hi = card["dev"]
    counts = {"listed": len(mk), "outside_window": 0, "no_time": 0, "not_qualify_word": 0, "kept": 0}
    ev_occ = {}
    for t, m in mk.items():
        o = iso(m.get("occurrence_datetime"))
        if o is not None:
            e = m.get("event_ticker") or ""
            ev_occ[e] = o if e not in ev_occ else min(ev_occ[e], o)
    kept = {}
    for t, m in mk.items():
        key = iso(m.get("close_time")) if card["win_on"] == "close" else ev_occ.get(m.get("event_ticker") or "")
        if key is None or iso(m.get("close_time")) is None:
            counts["no_time"] += 1
            continue
        if not (lo <= key < hi):
            counts["outside_window"] += 1
            continue
        if card_id == "MENT" and "does not qualify" in ((m.get("yes_sub_title") or "") + " " + (m.get("title") or "")).lower():
            counts["not_qualify_word"] += 1
            continue
        kept[t] = m
    if card_id == "MENT":
        order = sorted(kept, key=lambda t: (hashlib.md5((MENT_SEED + t).encode("ascii")).hexdigest(), t))
        counts["not_sampled"] = max(0, len(order) - MENT_SAMPLE_N)
        kept = {t: kept[t] for t in order[:MENT_SAMPLE_N]}
    counts["kept"] = len(kept)
    return kept, counts, ev_occ


def ment_sample_order(kept_all):
    """The sample order for the stage B builder: md5(SEED + ticker) ascending, ticker as the tie break."""
    return sorted(kept_all, key=lambda t: (hashlib.md5((MENT_SEED + t).encode("ascii")).hexdigest(), t))


def score(card_id, root, candle_jobs, check_only=False):
    card = CARDS[card_id]
    mk = list_markets(root, card)
    kept, counts, ev_occ = select(card_id, mk)
    out = {"card": card_id, "label": LABEL, "counts": counts}
    clocks = {t: clock(card_id, m, ev_occ.get(m.get("event_ticker") or "")) for t, m in kept.items()}
    if card_id in ("NBA_O", "NBA_L"):
        early = sum(1 for t, m in kept.items() if clocks[t] and iso(m["close_time"]) < clocks[t][2])
        share = early / len(kept) if kept else None
        out["proxy_check"] = {"closed_before_G": early, "share": share, "max": NBA_PROXY_MAX_EARLY}
        if share is None or share > NBA_PROXY_MAX_EARLY:
            out["stopped"] = "tip proxy check failed: no result read"
            return out
    if check_only:
        return out
    q = candle_quotes(root, candle_jobs, set(kept))
    drops = {"no_clock": 0, "closed_before_D": 0, "no_candles": 0, "not_two_sided": 0, "no_move": 0, "out_of_band": 0, "no_result": 0, "event_cap": 0}
    two = {"at_D": 0, "at_anchor": 0, "of": 0}
    cands = []
    for t in sorted(kept):
        m, ck = kept[t], clocks[t]
        if ck is None:
            drops["no_clock"] += 1
            continue
        D, anc, M_ts = ck
        close = iso(m["close_time"])
        if close <= D:
            drops["closed_before_D"] += 1
            continue
        qt = q.get(t)
        if not qt:
            drops["no_candles"] += 1
            continue
        two["of"] += 1
        two["at_D"] += 1 if (qt.get(D) and two_sided(*qt[D])) else 0
        two["at_anchor"] += 1 if (qt.get(anc) and two_sided(*qt[anc])) else 0
        s = signal(card_id, qt, D, anc)
        if s[0] is None:
            drops[s[1]] += 1
            continue
        cands.append((t, m, D, M_ts, close, s))
    if card["cap_event"]:
        by = {}
        for c in cands:
            by.setdefault(c[1].get("event_ticker") or "", []).append(c)
        keep = []
        for ev, cs in by.items():
            cs.sort(key=lambda c: (-abs(c[5][2]), c[0]))
            keep += cs[:card["cap_event"]]
            drops["event_cap"] += max(0, len(cs) - card["cap_event"])
        cands = keep
    trades = []
    for t, m, D, M_ts, close, (side, e, mv) in cands:
        res = (m.get("result") or "").strip().lower()      # read only now, for a kept development market with a signal
        if res not in ("yes", "no", "void"):
            drops["no_result"] += 1
            continue
        trades.append((D, t, m, M_ts, close, side, e, res))
    trades.sort(key=lambda r: (r[0], r[1]))
    out["drops"] = drops
    out["two_sided_share"] = {k: (two[k] / two["of"] if two["of"] else None) for k in ("at_D", "at_anchor")}
    raw_bar = {}
    for v in ("hold", "T", "S", "M"):
        rows = []
        reasons = {}
        for D, t, m, M_ts, close, side, e, res in trades:
            why, ts, bid = exit_for(v, q[t], D, close, M_ts, side, e)
            reasons[why] = reasons.get(why, 0) + 1
            won, void = res == side, res == "void"
            if v in ("hold",) or ts is None:
                ts_, bid_ = None, None
            else:
                ts_, bid_ = ts, bid
            r = {k: pnl(e, h, won, void, ts_, bid_, D, close) for k, h in H_LINES}
            r["primary"] = pnl(e, 0.01, won, void, ts_, bid_, D, close, primary=True)
            day = time.strftime("%Y-%m-%d", time.gmtime(D))
            r["cluster"] = (m.get("event_ticker") or t) if card_id == "MENT" else day
            rows.append(r)
        n = len(rows)
        h = n // 2
        blk = {"n": n, "exits": reasons}
        for k in ("raw", "1c", "2c", "primary"):
            xs = [r[k] for r in rows]
            pf, a, b = pf_raw(xs), pf_raw(xs[:h]), pf_raw(xs[h:])
            blk[k] = {"pf": shown(pf), "half1": shown(a), "half2": shown(b), "mean_c": None if not n else round(100 * sum(xs) / n, 3),
                      "z": shown(cluster_z(xs, [r["cluster"] for r in rows]))}
            raw_bar[(v, k)] = (pf, a, b)
        p1, p2 = raw_bar[(v, "primary")], raw_bar[(v, "2c")]
        blk["bar"] = "meets the bar (paper)" if bar_ok(p1[0], p1[1], p1[2], p2[0]) else "does not count"
        out[v] = blk
    out["clusters"] = "event" if card_id == "MENT" else "UTC day of D"
    return out


CANDLE_JOBS = {"NBA_O": ("KXNBAPTS_CANDLES_B1", "KXNBAPTS_CANDLES_B2", "KXNBAPTS_CANDLES_B3", "KXNBAPTS_CANDLES_B4"),
               "NBA_L": ("KXNBAPTS_CANDLES_B1", "KXNBAPTS_CANDLES_B2", "KXNBAPTS_CANDLES_B3", "KXNBAPTS_CANDLES_B4"),
               "MENT": tuple("MENTDRIFT_CANDLES_P%d" % i for i in range(1, 8))}

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in CARDS:
        print(__doc__)
        sys.exit(2)
    print(json.dumps(score(a[0], a[1], CANDLE_JOBS[a[0]], "--check-only" in a), indent=1, sort_keys=True, default=str))
