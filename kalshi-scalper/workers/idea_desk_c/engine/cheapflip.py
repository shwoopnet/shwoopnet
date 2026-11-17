#!/usr/bin/env python3
"""CHEAPFLIP plugin (Idea Desk C, Nov 17, 2026), build 1. Card: ../allkalshi/cheapflip/CHEAPFLIP_CARD.md. An OWNER-REQUESTED DESCRIPTIVE READ (a version of CHEAPEXIT1); never a candidate path.
Reads only book.csv.gz and coverage.csv.gz under <base>/<date>/<HHMM>/ for the base directories given (R6 book15r6 and nc15). No network. Result read LAST."""
import calendar, csv, glob, gzip, math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine1_core as K

CUT = 1794787199                                   # windows closing on or before 2026-11-15 23:59:59Z
BANDS = (0.03, 0.05, 0.10)
KS = (2, 3, 5)
HS = (0.01, 0.02)
N_CONTRACTS = 10
MIN_LEFT_S = 120
EPS = 1e-9
BOOK_NEED = ("t_recv_ms", "ticker", "series", "close_time", "yes_bid_px_1", "yes_bid_sz_1", "no_bid_px_1", "no_bid_sz_1")
COV_NEED = ("ticker", "close_time", "result")
N_CELLS = len(BANDS) * len(KS)                     # 9 pooled cells (two haircuts are columns)


def best(row, side):
    """-> (price, size) of the side's best bid (the highest price among the 5 levels), or None"""
    lv = []
    for i in range(1, 6):
        p, s = row.get("%s_bid_px_%d" % (side, i), ""), row.get("%s_bid_sz_%d" % (side, i), "")
        if p not in ("", None) and s not in ("", None):
            try:
                lv.append((float(p), float(s)))
            except ValueError:
                pass
    return max(lv) if lv else None


def iso(s):
    return calendar.timegm(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S"))


def fee(p, n=N_CONTRACTS):
    return K.fee_up_order(p, n)


R6_FIVE = ("KXBTC15M", "KXETH15M", "KXXRP15M", "KXDOGE15M", "KXGOLD15M")
# HOLDS.json 2026-11-16T16Z+7, copied by hand: a window is dropped, before any outcome is read, if its series and close are inside [from, to) of an open or frozen row.
HOLDS = (("H20", R6_FIVE, 1793145600, None), ("H02", ("KXBTC15M",), 1793721600, None), ("H21", ("KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXAUDUSD15M", "KXUSDCAD15M"), 1793836800, 1798070400))
M_CARRIED = 7492484                                                    # Nov 17 value; any other is refused


def held_by(series, close):
    for hid, ser, a, b in HOLDS:
        if series in ser and close >= a and (b is None or close < b):
            return hid
    return None


def read_windows(bases, stats):
    """-> {ticker_window_key: {"series", "close", "polls": [(t_ms, yes_bid, yes_sz, no_bid, no_sz)]}}, keyed by (ticker, close epoch); duplicates by (key, t_recv_ms) keep the first."""
    wins, seen = {}, set()
    for base in bases:
        for fd in sorted(glob.glob(os.path.join(base, "*", "*", "book.csv.gz"))):
            with gzip.open(fd, "rt", newline="") as fh:
                rd = csv.DictReader(fh)
                miss = [c for c in BOOK_NEED if c not in (rd.fieldnames or ())]
                if miss:
                    raise ValueError("%s lacks %s" % (fd, miss))
                stats["book_files"] = stats.get("book_files", 0) + 1
                for r in rd:
                    try:
                        ct = iso(r["close_time"]); t = int(r["t_recv_ms"])
                    except ValueError:
                        stats["rows_unparsable"] = stats.get("rows_unparsable", 0) + 1
                        continue
                    if ct > CUT:
                        stats["rows_after_cut"] = stats.get("rows_after_cut", 0) + 1
                        continue
                    hid = held_by(r["series"], ct)
                    if hid:
                        stats.setdefault("_held", {}).setdefault(hid, {}).setdefault(r["series"], set()).add(r["ticker"])
                        continue
                    key = (r["ticker"], ct)
                    if (key, t) in seen:
                        stats["duplicate_polls"] = stats.get("duplicate_polls", 0) + 1
                        continue
                    seen.add((key, t))
                    if t / 1000.0 >= ct:
                        stats["polls_at_or_after_close"] = stats.get("polls_at_or_after_close", 0) + 1
                    w = wins.setdefault(key, {"series": r["series"], "close": ct, "polls": []})
                    yb, nb = best(r, "yes"), best(r, "no")
                    w["polls"].append((t, yb, nb))
    for w in wins.values():
        w["polls"].sort(key=lambda p: p[0])
    return wins


def read_results(bases, wins, stats):
    """coverage.csv.gz rows: ticker + close_time -> result (first non-empty); read LAST."""
    res = {}
    for base in bases:
        for fd in sorted(glob.glob(os.path.join(base, "*", "*", "coverage.csv.gz"))):
            with gzip.open(fd, "rt", newline="") as fh:
                rd = csv.DictReader(fh)
                miss = [c for c in COV_NEED if c not in (rd.fieldnames or ())]
                if miss:
                    raise ValueError("%s lacks %s" % (fd, miss))
                for r in rd:
                    try:
                        key = (r["ticker"], iso(r["close_time"]))
                    except ValueError:
                        continue
                    if key in wins and r["result"] in ("yes", "no", "void"):
                        if key in res and res[key] != r["result"]:
                            stats["result_conflicts"] = stats.get("result_conflicts", 0) + 1
                        res.setdefault(key, r["result"])
    return res


def entries(w, hi):
    """-> {side: dict(a, t, ask_sz, idx)} first poll with the side's ask in [0.01, hi] and at least 120 s to the close"""
    out = {}
    for idx, (t, yb, nb) in enumerate(w["polls"]):
        if w["close"] - t / 1000.0 < MIN_LEFT_S:
            break
        for side, opp in (("yes", nb), ("no", yb)):
            if side in out or opp is None:
                continue
            ask = round(1 - opp[0], 6)
            if 0.01 - EPS <= ask <= hi + EPS:
                out[side] = {"a": ask, "t": t, "ask_sz": opp[1], "idx": idx}
    return out


def touch(w, side, ent, k):
    """first later poll with the side's bid >= k x a -> (t_ms, bid, size) or None"""
    for t, yb, nb in w["polls"][ent["idx"] + 1:]:
        if t / 1000.0 >= w["close"]:
            break                                                     # only polls strictly before the close
        b = yb if side == "yes" else nb
        if b is not None and b[0] >= k * ent["a"] - EPS:
            return t, b[0], b[1]
    return None


def net(side, a, tch, result, h):
    cost = min(a + h, 0.99)
    fin = fee(cost)
    if tch is not None:
        pr = max(tch[1] - h, 0.01)
        return round(N_CONTRACTS * pr - N_CONTRACTS * cost - fin - fee(pr), 9)
    if result == "void":
        return round(-fin, 9)
    return round((N_CONTRACTS if result == side else 0) - N_CONTRACTS * cost - fin, 9)


def pf(xs):
    w = sum(x for x in xs if x > 1e-12)
    l = -sum(x for x in xs if x < -1e-12)
    return None if not xs else (float("inf") if l == 0 and w > 0 else (w / l if l else None))


def run(bases, m_carried=M_CARRIED):
    if m_carried != M_CARRIED:
        raise ValueError("m_carried must be %d" % M_CARRIED)
    stats = {}
    wins = read_windows(bases, stats)
    held = stats.pop("_held", {})
    stats["windows_dropped_by_hold"] = {h: {sr: len(v) for sr, v in sorted(d.items())} for h, d in sorted(held.items())}
    res = read_results(bases, wins, stats)                              # LAST
    rows = {}
    for key, w in wins.items():
        r = res.get(key)
        if r is None:
            stats["windows_without_result"] = stats.get("windows_without_result", 0) + 1
            nr = stats.setdefault("no_result_by_series", {}); nr[w["series"]] = nr.get(w["series"], 0) + 1
        day = time.strftime("%Y-%m-%d", time.gmtime(w["close"]))
        for hi in BANDS:
            for side, ent in entries(w, hi).items():
                for k in KS:
                    tch = touch(w, side, ent, k)
                    unscored = r is None and tch is None                           # would hold, no result: stays in n and the touch shares, no net
                    if unscored:
                        nh = stats.setdefault("held_entries_without_result", {}); nh[w["series"]] = nh.get(w["series"], 0) + 1
                    rec = {"series": w["series"], "day": day, "close": w["close"], "t": ent["t"], "a": ent["a"], "ask_sz5": ent["ask_sz"] >= 5, "touch": tch,
                           "dt": None if tch is None else (tch[0] - ent["t"]) / 1000.0, "bid_sz5": None if tch is None else tch[2] >= 5,
                           "net": {h: None if unscored else net(side, ent["a"], tch, r, h) for h in HS}}
                    rows.setdefault((hi, k), []).append(rec)
    def cell(L):
        n = len(L)
        t = [x for x in L if x["touch"] is not None]
        dts = sorted(x["dt"] for x in t)
        med = None if not dts else (dts[len(dts) // 2] if len(dts) % 2 else (dts[len(dts) // 2 - 1] + dts[len(dts) // 2]) / 2)
        o = {"n": n, "days": len({x["day"] for x in L}), "windows": len({x["close"] for x in L}), "first_day": min((x["day"] for x in L), default=None),
             "last_day": max((x["day"] for x in L), default=None), "reach_share": None if not n else len(t) / n, "median_touch_s": med,
             "bid_size_5_share_at_touch": None if not t else sum(1 for x in t if x["bid_sz5"]) / len(t),
             "ask_size_5_share_at_entry": None if not n else sum(1 for x in L if x["ask_sz5"]) / n}
        for h in HS:
            xs = [x["net"][h] for x in L if x["net"][h] is not None]
            o["pf_h%d" % round(h * 100)] = pf(xs)
            o["net_per_trade_h%d" % round(h * 100)] = None if not xs else sum(xs) / len(xs)
        o["n_scored"] = sum(1 for x in L if x["net"][HS[0]] is not None)
        return o
    table = []
    for (hi, k), L in sorted(rows.items()):
        by = {}
        for x in L:
            by.setdefault(x["series"], []).append(x)
        table.append({"band": hi, "k": k, "pooled": cell(L), "series": {s: cell(v) for s, v in sorted(by.items())}})
    return {"label": "OWNER-REQUESTED DESCRIPTIVE READ, a version of CHEAPEXIT1 (7e cheap-side row binds): never a shadow, candidate or strategy path; tick replay, upper bound, not fill-checked; "
                     "windows closing on or before 2026-11-15T23:59:59Z",
            "m_carried": m_carried, "m_new": N_CELLS, "m_total": m_carried + N_CELLS, "stats": stats, "windows": len(wins), "table": table}
