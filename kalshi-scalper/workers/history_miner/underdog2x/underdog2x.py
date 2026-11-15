#!/usr/bin/env python3
"""UNDERDOG2X development read (History Miner, Nov 15, 2026). Registration UNDERDOG2X_REGISTRATION_NOV15.md with Amendment 1; hand case
UNDERDOG2X_HAND_CASE_NOV15.md. Reads the archive's .sqlite files (market, candle). Markets closing on or after 2026-10-03 and every third-3
market are dropped BEFORE any candle or result is read. Upper bound, not fill-checked.

Usage (python3 -I, from outside the data folder):
  python3 -I underdog2x.py <data folder> <out.json>"""
import calendar, json, math, os, sqlite3, statistics, sys
from collections import defaultdict
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hm_guard  # noqa: E402

SOURCES = ("l1b", "book", "e3b", "alts4", "alts2", "alts3", "rep")
CUT = calendar.timegm((2026, 10, 3, 0, 0, 0))
D = lambda m, d: calendar.timegm((2026, m, d, 0, 0, 0))
_A = (D(8, 25), D(9, 13))
THIRDS = {s: _A for s in ("KXBTC15M", "KXETH15M", "KXDOGE15M", "KXXRP15M", "KXNEAR15M", "KXZEC15M", "KXBNB15M", "KXHYPE15M",
                          "KXGOLD15M", "KXSILVER15M", "KXWTI15M")}
THIRDS.update({"KXSOL15M": (D(9, 1), D(9, 17)), "KXCOPPER15M": (D(9, 8), D(9, 20)), "KXNATGAS15M": (D(9, 8), D(9, 20)),
               "KXPALLADIUM15M": (D(9, 22), D(9, 27)), "KXPLATINUM15M": (D(9, 22), D(9, 27)),
               "KXEURUSD15M": (D(9, 26), D(9, 29)), "KXGBPUSD15M": (D(9, 26), D(9, 29)), "KXUSDJPY15M": (D(9, 26), D(9, 29))})
NC15 = {"KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXNATGAS15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXHYPE15M", "KXBNB15M"}
HS = (0.0, 0.01, 0.02)
VARIANTS = ("a", "b", "c")
LO, HI, LEFT_MIN = 0.20, 0.25, 600
EPS = 1e-9
MIN_N = 30


def fee(p, c):
    return math.ceil(round(100 * 0.07 * c * p * (1 - p), 9)) / 100


def third(series, close):
    t1, t2 = THIRDS[series]
    return 1 if close < t1 else (2 if close < t2 else 3)


def two_sided(q):
    return q is not None and q[0] is not None and q[1] is not None and 0 < q[0] < q[1] < 1


def side_bid(q, side):
    if side == "yes":
        return q[0]
    return None if q[1] is None else round(1 - q[1], 6)


def sellable(q, side):
    v = side_bid(q, side)
    return v is not None and 0 < v < 1


def entry(cands, close):
    for k in sorted(cands):
        if close - k < LEFT_MIN:
            break
        q = cands[k]
        if not two_sided(q):
            continue
        for side, a in (("yes", q[1]), ("no", round(1 - q[0], 6))):
            if LO - EPS <= a <= HI + EPS:
                return {"side": side, "e": float(a), "end": k}
    return None


def first_sale(marks, cands, side, start_idx, pred, last_ts):
    """index of the first sellable mark at or after the first mark (from start_idx, end <= last_ts) where pred(bid) holds; trigger then sale."""
    trig = None
    for i in range(start_idx, len(marks)):
        k = marks[i]
        if k > last_ts:
            break
        b = side_bid(cands[k], side)
        if b is not None and pred(b):
            trig = i; break
    if trig is None:
        return None
    for i in range(trig, len(marks)):
        if sellable(cands[marks[i]], side):
            return i
    return None


def plan(cands, close, en, variant):
    """Returns a list of (contracts, sale bid or None for held) legs, and the buy size."""
    side, e = en["side"], en["e"]
    marks = sorted(k for k in cands if en["end"] < k <= close - 60)
    two = lambda b: b >= 2 * e - EPS
    if variant == "a":
        i = first_sale(marks, cands, side, 0, two, close - 180)
        if i is not None and marks[i] <= close - 180:
            return 1, [(1, side_bid(cands[marks[i]], side), "2x")]
        j = next((x for x, k in enumerate(marks) if k >= close - 180 and sellable(cands[k], side)), None)
        if j is not None:
            return 1, [(1, side_bid(cands[marks[j]], side), "time")]
        return 1, [(1, None, "held")]
    if variant == "b":
        i = first_sale(marks, cands, side, 0, two, close - 60)
        return 1, [(1, side_bid(cands[marks[i]], side), "2x") if i is not None else (1, None, "held")]
    i = first_sale(marks, cands, side, 0, two, close - 60)
    if i is None:
        return 2, [(2, None, "held")]
    j = first_sale(marks, cands, side, i, lambda b: b >= 0.80 - EPS, close - 60)
    return 2, [(1, side_bid(cands[marks[i]], side), "2x"), (1, side_bid(cands[marks[j]], side), "0.80") if j is not None else (1, None, "held")]


def net_per_contract(e, h, buy_n, legs, result, side):
    ent = min(0.99, e + h)
    tot = -buy_n * ent - fee(ent, buy_n)
    for n, sale, _why in legs:
        if sale is not None:
            s = max(0.01, sale - h)
            tot += n * s - fee(s, n)
        elif result in ("yes", "no"):
            tot += n * (1.0 if result == side else 0.0)
        else:
            tot += n * ent                                  # void: price refunded, fee kept
    return tot / buy_n


def pf(xs):
    g = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return float("inf") if l == 0 else g / l


def dayz(days, xs):
    d = defaultdict(float)
    for k, x in zip(days, xs):
        d[k] += x
    v = list(d.values())
    if len(v) < 3:
        return None
    sd = statistics.stdev(v)
    return statistics.mean(v) / (sd / math.sqrt(len(v))) if sd else None


def summarise(tr):
    tr = sorted(tr, key=lambda t: (t["close"], t["ticker"]))
    xs = [t["net"] for t in tr]; n = len(xs); h = n // 2
    t1 = [t["net"] for t in tr if t["third"] == 1]; t2 = [t["net"] for t in tr if t["third"] == 2]
    return {"n": n, "n_third1": len(t1), "n_third2": len(t2), "pf": pf(xs) if n else None, "pf_third1": pf(t1) if t1 else None,
            "pf_third2": pf(t2) if t2 else None, "pf_half1_info": pf(xs[:h]) if h else None, "pf_half2_info": pf(xs[h:]) if n - h else None,
            "mean_c": 100 * statistics.mean(xs) if n else None, "z_day": dayz([t["day"] for t in tr], xs)}


def load(folder):
    """{ticker: (series, close, result)} for markets before CUT and in thirds 1 or 2 (third 3 dropped here); candles of kept markets only."""
    mk, src = {}, {}
    dropped = defaultdict(int)
    for s in SOURCES:
        con = sqlite3.connect("file:%s?mode=ro" % os.path.join(folder, s + ".sqlite"), uri=True)
        for t, ser, cl in con.execute("select ticker, series, close_ts from market where series like '%15M'"):
            if t in src:
                dropped["dup_later_source"] += 1; continue
            src[t] = s
            if cl >= CUT or ser not in THIRDS:
                dropped["on_or_after_cut"] += 1; continue
            if third(ser, cl) == 3:
                dropped["third3_heldout"] += 1; continue
            mk[t] = [ser, cl, None]
    cd = defaultdict(dict)
    for s in SOURCES:
        con = sqlite3.connect("file:%s?mode=ro" % os.path.join(folder, s + ".sqlite"), uri=True)
        keep = [t for t in mk if src[t] == s]
        for i in range(0, len(keep), 500):
            chunk = keep[i:i + 500]; ph = ",".join("?" * len(chunk))
            for t, res in con.execute("select ticker, result from market where ticker in (%s)" % ph, chunk):
                mk[t][2] = res
            for t, e, b, a in con.execute("select ticker, end_ts, bid_c, ask_c from candle where ticker in (%s)" % ph, chunk):
                if e <= mk[t][1]:
                    cd[t][e] = (b, a)
    return mk, cd, dict(dropped)


def run(folder):
    mk, cd, dropped = load(folder)
    trades = {v: {h: [] for h in HS} for v in VARIANTS}
    reasons = {v: defaultdict(int) for v in VARIANTS}
    nent = defaultdict(int)
    for t in sorted(mk, key=lambda x: (mk[x][1], x)):
        ser, close, res = mk[t]
        en = entry(cd.get(t, {}), close)
        if not en:
            continue
        nent[ser] += 1
        for v in VARIANTS:
            buy_n, legs = plan(cd[t], close, en, v)
            for _n, _s, why in legs:
                reasons[v][why] += 1
            for h in HS:
                trades[v][h].append({"ticker": t, "series": ser, "close": close, "third": third(ser, close),
                                     "day": datetime.fromtimestamp(close, timezone.utc).strftime("%Y-%m-%d"),
                                     "net": net_per_contract(en["e"], h, buy_n, legs, res, en["side"])})
    out = {"label": "UNDERDOG2X development read (thirds 1 and 2 only); upper bound, not fill-checked; per-order rounded fee",
           "dropped_before_read": dropped, "markets_read": len(mk), "entries_by_series": dict(nent), "variants": {}}
    for v in VARIANTS:
        V = {"exits_by_reason": dict(reasons[v]), "pooled": {}, "by_series": {}}
        for h in HS:
            V["pooled"]["h%d" % round(h * 100)] = summarise(trades[v][h])
            for ser in sorted(THIRDS):
                st = summarise([x for x in trades[v][h] if x["series"] == ser])
                st["no_evidence"] = min(st["n_third1"], st["n_third2"]) < MIN_N
                V["by_series"].setdefault(ser, {})["h%d" % round(h * 100)] = st
        out["variants"][v] = V
    out["primary_h"] = {ser: {"a": 0.02 if ser in NC15 else 0.01, "b": 0.02, "c": 0.02} for ser in THIRDS}
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 2:
        print(__doc__); sys.exit(2)
    hm_guard.refuse_all(a)
    res = run(a[0])
    json.dump(res, open(a[1], "w"), indent=1, sort_keys=True)
    print(json.dumps({"markets_read": res["markets_read"], "entries": res["entries_by_series"]}, sort_keys=True))
