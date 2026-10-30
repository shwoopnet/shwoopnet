"""NEWH2: four new mechanisms on gold's 15 minute market (research only).

Registration: workers/NEWH2_REGISTRATION.md (pushed before any scoring).
H1 GBREAK (CME daily break), H2 GREOPEN (first 90 minutes after the reopen), H3 GSILV (Kalshi silver as information for gold),
H4 GLADH (15 minute gold against the hourly gold ladder KXGOLDH at a coincident close).
Fill at the next candle's closing ask, held, C = 10 screen, fee rounded up per order.

    PYTHONPATH=src python -m scalper.newh2 fetch     (KXGOLDH candles for top-of-hour gold closes, resumable)
    PYTHONPATH=src python -m scalper.newh2 run       (both windows, once)
"""
from __future__ import annotations

import math
import sqlite3
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

from . import api, backfill
from .lad1 import chunks
from .paths import DATA_DIR

GOLD, SILVER, LADDER = "KXGOLD15M", "KXSILVER15M", "KXGOLDH"
FILES = ("l1b", "book", "fresh", "five")
START = int(datetime(2026, 8, 6, tzinfo=timezone.utc).timestamp())
DISC_END = int(datetime(2026, 9, 21, tzinfo=timezone.utc).timestamp())
END = int(datetime(2026, 10, 28, tzinfo=timezone.utc).timestamp())
LDB = DATA_DIR / "newh2_goldh.sqlite"
STRIKE_BAND = 12.0
PAUSE = 0.6


def day(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def load(series, files, start=START, end=END):
    """{close: {ticker, close, result, strike, c: {offset: (bid, ask, vol)}}}; first file wins (gen7 order)."""
    win = {}
    for name in files:
        p = DATA_DIR / f"{name}.sqlite"
        if not p.exists():
            continue
        db = sqlite3.connect(p)
        for tk, close, res, k in db.execute(
                "select ticker, close_ts, result, strike from market where series=? and close_ts>=? and close_ts<?",
                (series, start, end)).fetchall():
            if close in win or res not in ("yes", "no"):
                continue
            cs = {e - close: (b, a, v or 0.0) for e, b, a, v in db.execute(
                "select end_ts, bid_c, ask_c, volume from candle where ticker=? and bid_c is not null and ask_c is not null", (tk,))}
            if not cs:
                continue
            win[close] = {"ticker": tk, "close": close, "result": res, "strike": k, "c": cs}
    return win


# ---------- fetch KXGOLDH ----------

def fetch():
    gold = load(GOLD, FILES)
    tops = {c: w["strike"] for c, w in gold.items() if c % 3600 == 0 and w["strike"] is not None}
    db = sqlite3.connect(LDB)
    db.executescript(backfill.SCHEMA)
    db.execute("create table if not exists done(close_ts integer primary key, n integer)")
    done = {r[0] for r in db.execute("select close_ts from done")}
    by_close = defaultdict(list)
    for m in api.settled_markets(LADDER, START - 3600, END + 3600):
        c = backfill.iso_ts(m.get("close_time"))
        if c in tops and m.get("result") in ("yes", "no") and m.get("floor_strike") is not None:
            if abs(float(m["floor_strike"]) - tops[c]) <= STRIKE_BAND:
                by_close[c].append(m)
    print(f"{len(tops)} top-of-hour gold closes, {len(by_close)} with ladder strikes, {len(done)} done", flush=True)
    for n, c in enumerate(sorted(by_close)):
        if c in done:
            continue
        stored = 0
        for ch in chunks(by_close[c], 20):
            got = api.batch_candlesticks([m["ticker"] for m in ch], c - 900, c - 60)
            for m in ch:
                t = m["ticker"]
                rows = [r for r in (backfill.parse_candle(x, t, LADDER) for x in got.get(t, [])) if r]
                db.executemany("insert or replace into candle values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
                db.execute("insert or replace into market values(?,?,?,?,?,?,?)",
                           (t, LADDER, backfill.iso_ts(m.get("open_time")), c, m.get("result"), float(m["floor_strike"]), len(rows)))
                stored += len(rows) > 0
            time.sleep(PAUSE)
        db.execute("insert or replace into done values(?,?)", (c, stored))
        db.commit()
        if n % 50 == 0:
            print(f"  {n}/{len(by_close)} {day(c)} strikes with candles {stored}", flush=True)
    print("done", flush=True)


def ladder():
    """close -> {offset: [(strike, bid, ask)]}"""
    out = defaultdict(lambda: defaultdict(list))
    if not LDB.exists():
        return out
    db = sqlite3.connect(LDB)
    ks = {t: (c, k) for t, c, k in db.execute("select ticker, close_ts, strike from market")}
    for t, e, b, a in db.execute("select ticker, end_ts, bid_c, ask_c from candle where bid_c is not null and ask_c is not null"):
        c, k = ks[t]
        out[c][e - c].append((k, b, a))
    return out


# ---------- money ----------

def fee(p, c=10, mult=1.0):
    return math.ceil(round(0.07 * c * p * (1 - p) * mult * 100, 9)) / 100


def net(fill, won, c=10, mult=1.0):
    return c * ((1.0 if won else 0.0) - fill) - fee(fill, c, mult)


def pf(nets):
    g = sum(x for x in nets if x > 0)
    l = -sum(x for x in nets if x < 0)
    return float("inf") if l == 0 else (g / l if g or l else float("nan"))


def side_ask(row, side):
    if row is None:
        return None
    a = row[1] if side == "yes" else round(1 - row[0], 6)
    return a if 0 < a < 1 else None


def mid(row):
    return None if row is None else (row[0] + row[1]) / 2


def make_trade(w, side, sig_off, lo, hi):
    fr = w["c"].get(sig_off + 60)
    a = side_ask(fr, side)
    if a is None or not (lo <= a <= hi):
        return None
    won = w["result"] == side
    return {"close": w["close"], "day": day(w["close"]), "side": side, "fill": a, "won": won, "vol0": fr[2] == 0,
            "n1": net(a, won, 1), "n10": net(a, won, 10), "n10x": net(a, won, 10, 1.2)}


def pick_side(row, lo, hi):
    for s in ("yes", "no"):
        a = side_ask(row, s)
        if a is not None and lo <= a <= hi:
            return s
    return None


def hm(ts):
    d = datetime.fromtimestamp(ts, timezone.utc)
    return d.strftime("%H:%M"), d.weekday()   # Mon = 0 ... Sun = 6


# ---------- the rules (each returns trades, gaps) ----------

def rule_side(win, keep, look, band, fill_band):
    out, gaps = [], 0
    for c, w in sorted(win.items()):
        if not keep(c):
            continue
        r = w["c"].get(-look)
        if r is None or w["c"].get(-look + 60) is None:
            gaps += 1
            continue
        s = pick_side(r, *band)
        if s:
            t = make_trade(w, s, -look, *fill_band)
            if t:
                out.append(t)
    return out, gaps


def keep_break(c):
    h, wd = hm(c)
    return wd <= 4 and h in ("21:15", "21:30", "21:45", "22:00")


def keep_reopen(c):
    h, wd = hm(c)
    return wd in (6, 0, 1, 2, 3) and h in ("22:15", "22:30", "22:45", "23:00", "23:15", "23:30")


def h1(win):
    return rule_side(win, keep_break, 360, (0.55, 0.88), (0.50, 0.92))


def h2(win, control=False):
    keep = (lambda c: not keep_reopen(c)) if control else keep_reopen
    return rule_side(win, keep, 480, (0.08, 0.45), (0.05, 0.50))


def h3(win, silver):
    out, gaps = [], 0
    for c, w in sorted(win.items()):
        s = silver.get(c)
        if s is None:
            continue
        rows = [s["c"].get(-360), s["c"].get(-540), w["c"].get(-360), w["c"].get(-540), w["c"].get(-300)]
        if any(r is None for r in rows):
            gaps += 1
            continue
        dS = mid(rows[0]) - mid(rows[1])
        dG = mid(rows[2]) - mid(rows[3])
        if abs(dS) < 0.20:
            continue
        sg = 1 if dS > 0 else -1
        if sg * dG > 0.05:
            continue
        t = make_trade(w, "yes" if sg > 0 else "no", -360, 0.25, 0.80)
        if t:
            out.append(t)
    return out, gaps


def ladder_p(rows, k15):
    lo = [r for r in rows if r[0] <= k15]
    hi = [r for r in rows if r[0] > k15]
    if not lo or not hi:
        return None
    a, b = max(lo, key=lambda r: r[0]), min(hi, key=lambda r: r[0])
    if b[0] - a[0] > 6.0:
        return None
    ma, mb = (a[1] + a[2]) / 2, (b[1] + b[2]) / 2
    return ma + (mb - ma) * (k15 - a[0]) / (b[0] - a[0])


def h4(win, lad):
    out, gaps, seen = [], 0, 0
    for c, w in sorted(win.items()):
        if c % 3600 or w["strike"] is None or c not in lad:
            continue
        seen += 1
        r = w["c"].get(-360)
        P = ladder_p(lad[c].get(-360, []), w["strike"])
        if r is None or w["c"].get(-300) is None or P is None:
            gaps += 1
            continue
        ay, an = side_ask(r, "yes"), side_ask(r, "no")
        side = None
        if ay is not None and P - ay >= 0.06:
            side = "yes"
        elif an is not None and (1 - P) - an >= 0.06:
            side = "no"
        if side:
            t = make_trade(w, side, -360, 0.05, 0.95)
            if t:
                out.append(t)
    return out, gaps


# ---------- report ----------

def dayz(tr, key="n10"):
    d = defaultdict(float)
    for t in tr:
        d[t["day"]] += t[key]
    v = list(d.values())
    if len(v) < 3:
        return float("nan")
    sd = statistics.stdev(v)
    return statistics.mean(v) / (sd / math.sqrt(len(v))) if sd else float("nan")


def summ(tr):
    if not tr:
        return {"n": 0}
    nv = [t for t in tr if not t["vol0"]]
    return {"n": len(tr), "days": len({t["day"] for t in tr}), "win": sum(t["won"] for t in tr) / len(tr),
            "fill": statistics.mean(t["fill"] for t in tr), "pf10": pf([t["n10"] for t in tr]), "pf1": pf([t["n1"] for t in tr]),
            "pfx": pf([t["n10x"] for t in tr]), "netx": sum(t["n10x"] for t in tr), "net10": sum(t["n10"] for t in tr),
            "z": dayz(tr), "n_v": len(nv), "pf10_v": pf([t["n10"] for t in nv])}


def line(name, s):
    if s["n"] == 0:
        return f"{name:<22} n 0"
    return (f"{name:<22} n {s['n']:4d} days {s['days']:3d} win {s['win']:.3f} fill {s['fill']:.3f} gap {100*(s['win']-s['fill']):+6.2f}pt "
            f"PF10 {s['pf10']:.2f} PF1 {s['pf1']:.2f} PFx1.2 {s['pfx']:.2f} net10 ${s['net10']:+.2f} netx ${s['netx']:+.2f} z {s['z']:+.2f} "
            f"| vol>0 n {s['n_v']} PF10 {s['pf10_v']:.2f}")


def verdict(d, v):
    if d["n"] < 100:
        return "NOT_ENOUGH_DATA"
    if not (d["pf10"] >= 1.5 and d["netx"] > 0):
        return "FALSIFIED"
    if v["n"] < 50:
        return "NOT_ENOUGH_DATA"
    if not (v["pf10"] >= 1.3 and v["netx"] > 0):
        return "FALSIFIED"
    return "NOT_YET_FALSIFIED"


def run():
    gold = load(GOLD, FILES)
    silver = load(SILVER, ("alts3",))
    lad = ladder()
    split = lambda tr: ([t for t in tr if t["close"] < DISC_END], [t for t in tr if t["close"] >= DISC_END])
    nd = sum(c < DISC_END for c in gold)
    print(f"gold windows {len(gold)} (disc {nd}, val {len(gold) - nd}); silver {len(silver)}; ladder closes {len(lad)}")
    rows = [("H1 GBREAK", h1(gold)), ("H2 GREOPEN", h2(gold)), ("H3 GSILV", h3(gold, silver)), ("H4 GLADH", h4(gold, lad)),
            ("H2 control (info)", h2(gold, control=True))]
    for name, (tr, gaps) in rows:
        d, v = split(tr)
        sd, sv = summ(d), summ(v)
        print(line(name + " disc", sd))
        print(line(name + " val", sv))
        print(f"{'':<22} data gaps {gaps}" + ("" if "control" in name else f"  VERDICT {verdict(sd, sv)}"))


if __name__ == "__main__":
    {"fetch": fetch, "run": run}[sys.argv[1]]()
