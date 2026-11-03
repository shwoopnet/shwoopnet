"""NEWLIST1: cheap sides (ask 5c to 30c) in the first hours after a market is listed.

Stage `meta`   : metadata only (ticker, series, open/close/created times). The result is saved in a
                 separate table that universe selection never reads.
Stage `choose` : universe from metadata only, written to data/newlist1_universe.json.
Stage `fetch`  : hourly candles per market (open - 1h .. close), local sqlite.
Stage `score`  : run once, refuses a second run. See workers/NEWLIST1_REGISTRATION.md.
Public keyless reads only. No order, no key, no live code.
"""
from __future__ import annotations

import datetime
import json
import math
import os
import sqlite3
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "..", "data"))
DB = os.path.join(DATA, "newlist1.sqlite")
UNIVERSE = os.path.join(DATA, "newlist1_universe.json")
SCORE = os.path.join(DATA, "newlist1_score.json")
SERIES_JSON = os.path.join(DATA, "newlist1_series.json")

START_CLOSE = int(datetime.datetime(2026, 9, 4, tzinfo=datetime.timezone.utc).timestamp())
MIN_LIFE_H = 12.0          # market lifetime needed so the 6h look and the later-life look are distinct
MIN_MARKETS = 200
MAX_PAGES = 3               # at most 3,000 listed markets per series in the metadata scan
SCAN_FREQ = {"daily", "weekly", "monthly", "hourly", "quarterly"}
SCAN_CUSTOM_CATS = {"Sports", "Financials", "Economics", "Climate and Weather", "Crypto", "Commodities",
                    "Mentions", "Transportation", "Exotics", "Social"}
LOOK_H = (1, 3, 6)          # age looks, hours after open_time
ASK_LO, ASK_HI = 0.05, 0.30  # cheap side band; hard limit at 0.30
LATE_LEAD_H = 3             # later-life control look: candle ending 3h before the close
C = 10


def iso(s: str) -> int:
    return int(datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def fee_per_contract(p: float, c: int = C) -> float:
    """7% x C x p x (1-p) rounded UP to the cent, per order, divided by C (dollars per contract)."""
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100.0 / c


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB, timeout=60)
    c.execute("create table if not exists mk(ticker text primary key, series text, event text, category text,"
              " created integer, open_ts integer, close_ts integer)")
    c.execute("create table if not exists res(ticker text primary key, result text)")
    c.execute("create table if not exists sdone(series text primary key, n integer)")
    c.execute("create table if not exists cdone(ticker text primary key, n integer)")
    c.execute("create table if not exists cd(ticker text, end_ts integer, bid real, ask real, vol real, oi real,"
              " primary key(ticker, end_ts))")
    return c


def _f(x):
    try:
        return float(x) if x not in (None, "") else None
    except ValueError:
        return None


# ---------------------------------------------------------------- meta

def run_pool(items, work, write, threads=2, sleep=0.25, label=""):
    """work(item) -> payload (network only, threads); write(conn, item, payload) in ONE thread (sqlite)."""
    import queue
    q = queue.Queue(maxsize=200)
    lock = threading.Lock()
    idx = [0]

    def net():
        while True:
            with lock:
                i = idx[0]; idx[0] += 1
            if i >= len(items):
                return
            try:
                q.put((i, work(items[i]), None))
            except Exception as e:
                q.put((i, None, e))
            time.sleep(sleep)

    ts = [threading.Thread(target=net, daemon=True) for _ in range(threads)]
    [t.start() for t in ts]
    c = conn()
    for k in range(len(items)):
        i, payload, err = q.get()
        if err is not None:
            print("fail", items[i], err, flush=True)
            continue
        write(c, items[i], payload)
        if k % 100 == 0:
            c.commit()
        if k % 500 == 0:
            print(label, "progress", k, "/", len(items), flush=True)
    c.commit()

import re
SPORT_PAT = re.compile(r"^KX(NBA|NFL|NHL|MLB|NCAAF|NCAAB|NCAAM|NCAAW|WNBA|ATP|WTA|UFC|MLS|EPL|UCL|LALIGA|SERIEA|BUNDES|"
                       r"LIGUE|ESOCCER|CS2|VALORANT|LOL|DOTA|CFB|CBB).*(GAME|MATCH|TOTAL|SPREAD|FIGHT)$")


def scan_wanted(ticker, freq, cat):
    """Frozen scan list (metadata only): every daily, weekly and hourly series; monthly Economics, Financials and
    Commodities; Sports 'custom' series that are a game, match, total, spread or fight of a named league.
    The full list of 4,957 recurring series was too many calls for the shared API limit."""
    if freq in ("daily", "weekly", "hourly"):
        return True
    if freq == "monthly" and cat in ("Economics", "Financials", "Commodities"):
        return True
    return freq == "custom" and cat == "Sports" and bool(SPORT_PAT.match(ticker))


def meta(threads: int = 1, sleep: float = 0.6):
    from scalper import api
    ser = api._get("/series", {})["series"]
    keep = []
    for x in ser:
        t, fr, cat = x["ticker"], x.get("frequency"), x.get("category")
        if t.startswith("KXMVE") or "15M" in t or t.startswith("KXGOLD"):
            continue
        if scan_wanted(t, fr, cat):
            keep.append({"ticker": t, "category": cat, "frequency": fr})
    json.dump(keep, open(SERIES_JSON, "w"))
    c0 = conn()
    done = {r[0] for r in c0.execute("select series from sdone")}
    todo = [k for k in keep if k["ticker"] not in done]
    c0.close()
    print("series", len(keep), "todo", len(todo), flush=True)

    def work(k):
        rows, res, cur, pages = [], [], None, 0
        while True:
            pages += 1
            p = {"series_ticker": k["ticker"], "status": "settled", "min_close_ts": START_CLOSE, "limit": 1000}
            if cur:
                p["cursor"] = cur
            d = api._get("/markets", p)
            for m in d.get("markets", []):
                if m.get("result") not in ("yes", "no"):
                    continue
                rows.append((m["ticker"], k["ticker"], m.get("event_ticker"), k["category"],
                             iso(m["created_time"]), iso(m["open_time"]), iso(m["close_time"])))
                res.append((m["ticker"], m["result"]))
            cur = d.get("cursor")
            if not cur or pages >= MAX_PAGES:
                return rows, res
            time.sleep(sleep)

    def write(c, k, payload):
        rows, res = payload
        c.executemany("insert or ignore into mk values (?,?,?,?,?,?,?)", rows)
        c.executemany("insert or ignore into res values (?,?)", res)
        c.execute("insert or replace into sdone values (?,?)", (k["ticker"], len(rows)))

    run_pool(todo, work, write, threads, sleep, "meta")


# ---------------------------------------------------------------- choose (metadata only)
def choose():
    c = conn()
    rows = c.execute("select series, count(*), min(open_ts), max(close_ts), sum((close_ts-open_ts)>=?) "
                     "from mk group by series", (MIN_LIFE_H * 3600,)).fetchall()
    uni = {}
    for s, n, lo, hi, n_long in rows:
        if n_long >= MIN_MARKETS:
            uni[s] = {"n": n, "n_long": n_long}
    json.dump(uni, open(UNIVERSE, "w"), indent=1, sort_keys=True)
    picked = pick_markets(c, uni)
    cl = sorted(m[3] for m in picked)
    cuts = {"t1": cl[len(cl) // 3], "t2": cl[2 * len(cl) // 3], "n_picked": len(cl), "read_holdout": False}
    json.dump(cuts, open(os.path.join(DATA, "newlist1_cuts.json"), "w"), indent=1)
    iso_ = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
    print(len(uni), "families; markets", sum(v["n_long"] for v in uni.values()), "picked", len(cl),
          "cuts", iso_(cuts["t1"]), iso_(cuts["t2"]))
    for s_, v in sorted(uni.items(), key=lambda kv: -kv[1]["n_long"]):
        print(s_, v["n_long"])
    return uni


# ---------------------------------------------------------------- fetch
CAP_PER_FAMILY = 40


def pick_markets(c, uni):
    """Frozen subsample: per family the CAP_PER_FAMILY markets with the smallest md5(ticker) among those
    with life >= MIN_LIFE_H. The hash ignores every outcome."""
    import hashlib
    out = []
    for s in sorted(uni):
        rows = c.execute("select ticker, open_ts, close_ts from mk where series=? and (close_ts-open_ts)>=?",
                         (s, MIN_LIFE_H * 3600)).fetchall()
        rows.sort(key=lambda r: hashlib.md5(r[0].encode()).hexdigest())
        out += [(r[0], s, r[1], r[2]) for r in rows[:CAP_PER_FAMILY]]
    return out


def fetch(threads: int = 1, sleep: float = 0.8):
    from scalper import api
    uni = json.load(open(UNIVERSE))
    c0 = conn()
    todo = [m for m in pick_markets(c0, uni)
            if not c0.execute("select 1 from cdone where ticker=?", (m[0],)).fetchone()]
    c0.close()
    print("markets to fetch", len(todo), flush=True)

    def work(m):
        t, s, o, cl = m
        d = api._get(f"/series/{s}/markets/{t}/candlesticks", {"start_ts": o, "end_ts": cl, "period_interval": 60})
        rows = []
        for k in d.get("candlesticks", []):
            ya, yb = k.get("yes_ask") or {}, k.get("yes_bid") or {}
            rows.append((t, k["end_period_ts"], _f(yb.get("close_dollars")), _f(ya.get("close_dollars")),
                         _f(k.get("volume_fp")), _f(k.get("open_interest_fp"))))
        return rows

    def write(c, m, rows):
        c.executemany("insert or ignore into cd values (?,?,?,?,?,?)", rows)
        c.execute("insert or replace into cdone values (?,?)", (m[0], len(rows)))

    run_pool(todo, work, write, threads, sleep, "fetch")


# ---------------------------------------------------------------- score
def priced(bid, ask):
    """A real two-sided quote: an empty Kalshi book reads bid 0 and ask 0.99 or 1."""
    return bid is not None and ask is not None and bid >= 0.01 and ask <= 0.99 and ask > bid


def side_entry(bid, ask, lo, hi):
    """Side whose ask lies in [lo, hi] (YES ask = ask, NO ask = 1 - bid). Returns (side, price) or None."""
    cands = []
    if lo - 1e-9 <= ask <= hi + 1e-9:
        cands.append(("yes", ask))
    na = round(1 - bid, 4)
    if lo - 1e-9 <= na <= hi + 1e-9:
        cands.append(("no", na))
    return min(cands, key=lambda x: x[1]) if cands else None


def look_candle(cs, t_lo, t_hi):
    """First candle ending in [t_lo, t_hi). cs sorted by end_ts."""
    for e, b, a in cs:
        if e >= t_hi:
            return None
        if e >= t_lo:
            return (e, b, a)
    return None


def late_candle(cs, t_max):
    last = None
    for e, b, a in cs:
        if e > t_max:
            break
        last = (e, b, a)
    return last


def trade_net(side, price, result):
    win = 1.0 if side == result else 0.0
    return win - price - fee_per_contract(price), win


def summarize(rows):
    """rows: (cluster, close_ts, net, win, price). Returns dict."""
    from scalper.calibration import cluster_mean_z
    n = len(rows)
    if n == 0:
        return {"n": 0}
    net = [r[2] for r in rows]
    gw = sum(x for x in net if x > 0)
    gl = -sum(x for x in net if x < 0)
    mean, se, z = cluster_mean_z([(r[0], r[2]) for r in rows])
    return {"n": n, "win": round(sum(r[3] for r in rows) / n, 4), "price": round(sum(r[4] for r in rows) / n, 4),
            "gap": round(sum(r[3] - r[4] for r in rows) / n, 4), "net_c": round(100 * mean, 3),
            "pf": round(gw / gl, 3) if gl > 0 else None, "z": round(z, 2)}


def build_rows(c, uni, rule):
    """rule 'A' cheap side [0.05,0.30]; rule 'B' tail [0.85,0.97]. Returns {(family, look): rows}."""
    lo, hi = (ASK_LO, ASK_HI) if rule == "A" else (0.85, 0.97)
    res = dict(c.execute("select ticker, result from res"))
    mk = {r[0]: r for r in c.execute("select ticker, series, open_ts, close_ts from mk")}
    cds = {}
    for t, e, b, a in c.execute("select ticker, end_ts, bid, ask from cd order by ticker, end_ts"):
        cds.setdefault(t, []).append((e, b, a))
    out = {}
    stat = {"markets": 0, "unpriced": {}}
    for t, cs in cds.items():
        _, s, o, cl = mk[t]
        if s not in uni or t not in res:
            continue
        stat["markets"] += 1
        day = datetime.datetime.fromtimestamp(o, datetime.timezone.utc).strftime("%Y-%m-%d")
        looks = {h: look_candle(cs, o + h * 3600, o + (h + 1) * 3600) for h in LOOK_H}
        looks["late"] = late_candle(cs, cl - LATE_LEAD_H * 3600)
        for k, cdl in looks.items():
            if cdl is None or not priced(cdl[1], cdl[2]):
                stat["unpriced"][k] = stat["unpriced"].get(k, 0) + 1
                continue
            en = side_entry(cdl[1], cdl[2], lo, hi)
            if en is None:
                continue
            net, win = trade_net(en[0], en[1], res[t])
            out.setdefault((s, k), []).append((day, cl, net, win, en[1], t))
    return out, stat


def score(force=False):
    if os.path.exists(SCORE) and not force:
        raise SystemExit("already run: data/newlist1_score.json exists (run once)")
    c = conn()
    uni = json.load(open(UNIVERSE))
    cuts = json.load(open(os.path.join(DATA, "newlist1_cuts.json")))
    res_all = {}
    for rule in ("A", "B"):
        rows, stat = build_rows(c, uni, rule)
        res_all[rule] = {"stat": stat, "cells": {}}
        keys = sorted(set(rows))
        fam = sorted({k[0] for k in keys})
        for look in list(LOOK_H) + ["late"]:
            pooled = [r for k in keys if k[1] == look for r in rows[k]]
            for name, rr in [("ALL", pooled)] + [(f, rows[(f, look)]) for f in fam if (f, look) in rows]:
                cell = {}
                for part, (a, b) in {"D": (0, cuts["t1"]), "V": (cuts["t1"], cuts["t2"]),
                                     "H": (cuts["t2"], 1 << 60)}.items():
                    if part == "H" and not cuts.get("read_holdout"):
                        cell[part] = {"n": sum(1 for r in rr if a <= r[1] < b), "unread": True}
                        continue
                    cell[part] = summarize([r[:5] for r in rr if a <= r[1] < b])
                res_all[rule]["cells"][f"{name}|{look}"] = cell
    json.dump(res_all, open(SCORE, "w"), indent=1)
    return res_all



CENSUS = os.environ.get("NEWLIST1_CENSUS", "")  # USWEEP1 census.jsonl (metadata only, no results)


def choose_census(path=None):
    """Amendment 1: families come from the USWEEP1 census (metadata only: ticker, open, close, expiration, volume),
    not from a separate scan. Rebuilds mk from it, then the universe and cuts as in choose()."""
    path = path or CENSUS
    c = conn()
    c.execute("delete from mk"); c.execute("delete from res"); c.execute("delete from sdone")
    for line in open(path):
        d = json.loads(line)
        t = d["ticker"]
        if t.startswith("KXMVE") or "15M" in t or t.startswith("KXGOLD"):
            continue
        c.executemany("insert or ignore into mk values (?,?,?,?,?,?,?)",
                      [(m[0], t, m[0].rsplit("-", 1)[0], d.get("cat"), 0, m[1], m[2]) for m in d["markets"]])
    c.commit()
    return choose()


def results():
    """After Amendment 1 only: settled results for the picked markets, one listing call per family."""
    from scalper import api
    uni = json.load(open(UNIVERSE))
    c = conn()
    picked = {m[0] for m in pick_markets(c, uni)}
    for s in sorted(uni):
        cur, n, pages = None, 0, 0
        while pages < MAX_PAGES:
            p = {"series_ticker": s, "status": "settled", "min_close_ts": START_CLOSE, "limit": 1000}
            if cur:
                p["cursor"] = cur
            d = api._get("/markets", p); pages += 1
            for m in d.get("markets", []):
                if m["ticker"] in picked and m.get("result") in ("yes", "no"):
                    c.execute("insert or ignore into res values (?,?)", (m["ticker"], m["result"])); n += 1
            cur = d.get("cursor")
            if not cur:
                break
            time.sleep(0.6)
        c.commit()
        print("results", s, n, flush=True)


if __name__ == "__main__":
    sys.path.insert(0, os.path.join(HERE, ".."))
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "meta":
        meta()
    elif cmd == "choose":
        choose()
    elif cmd == "choose_census":
        choose_census()
    elif cmd == "results":
        results()
    elif cmd == "fetch":
        fetch()
    elif cmd == "score":
        score()
    else:
        print(__doc__)
