"""NEWH7: three new mechanisms on Kalshi's 15 minute gold and Bitcoin markets (research only).

Registration: workers/NEWH7_REGISTRATION.md (pushed before any scoring).
H1 IVGAP (implied volatility far above realised: buy the cheap side and hold; gold with CBOE GVZ, Bitcoin with Deribit DVOL),
H2 COINPREM (Coinbase over Binance spot premium change: buy the side it points to while that side is 50c or less, hold),
H3 VEGALAG (a 5 minute DVOL jump: buy the cheap side, sell 3 minutes later).

    PYTHONPATH=src python -m scalper.newh7 fetch     (public data only, into data/newh7.sqlite; nothing closing on or after Oct 28)
    PYTHONPATH=src python -m scalper.newh7 run       (scores the four tries once)
"""
from __future__ import annotations

import csv
import io
import json
import math
import sqlite3
import statistics
import sys
import time
import urllib.request
import zipfile
from bisect import bisect_right
from datetime import datetime, timezone, timedelta

from .newh2 import START, DISC_END, END, day, fee, pf, dayz
from .newh6 import load, ask, round_trip, GOLD, BTC
from .paths import DATA_DIR

DB = DATA_DIR / "newh7.sqlite"
FETCH_START = int(datetime(2026, 8, 3, tzinfo=timezone.utc).timestamp())
UA = {"User-Agent": "Mozilla/5.0"}


# ---------------------------------------------------------------- fetch

def _get(url, tries=6):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if i == tries - 1:
                raise
            time.sleep(2 + 3 * i)


def _db():
    db = sqlite3.connect(DB)
    db.execute("create table if not exists daily(src text, d text, v real, primary key(src, d))")
    db.execute("create table if not exists m1(src text, ts integer, v real, primary key(src, ts))")
    return db


def fetch():
    db = _db()
    # GVZ daily
    raw = _get("https://cdn.cboe.com/api/global/us_indices/daily_prices/GVZ_History.csv").decode()
    rows = []
    for r in csv.DictReader(io.StringIO(raw)):
        m, d_, y = r["DATE"].split("/")
        ds = f"{y}-{int(m):02d}-{int(d_):02d}"
        if "2026-04-01" <= ds < "2026-10-28":
            rows.append(("GVZ", ds, float(r["GVZ"])))
    db.executemany("insert or replace into daily values(?,?,?)", rows)
    print("GVZ", len(rows))
    # GC=F daily
    p1 = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp())
    js = json.loads(_get(f"https://query1.finance.yahoo.com/v8/finance/chart/GC=F?period1={p1}&period2={END}&interval=1d"))
    res = js["chart"]["result"][0]
    ts, cl = res["timestamp"], res["indicators"]["quote"][0]["close"]
    rows = []
    for t, c in zip(ts, cl):
        if c is None:
            continue
        # Yahoo stamps a daily COMEX bar at the session's start in exchange time; take the New York date of the stamp + 6 h
        ds = (datetime.fromtimestamp(t, timezone.utc) + timedelta(hours=6)).strftime("%Y-%m-%d")
        if ds < "2026-10-28":
            rows.append(("GC", ds, float(c)))
    db.executemany("insert or replace into daily values(?,?,?)", rows)
    print("GC", len(rows), rows[-1])
    db.commit()
    # Deribit DVOL and BTC-PERPETUAL, 1 minute, stamped by start
    for src in ("DVOL", "PERP"):
        have = db.execute("select max(ts) from m1 where src=?", (src,)).fetchone()[0]
        t0 = (have + 60) if have else FETCH_START
        while t0 < END:
            t1 = min(t0 + 999 * 60, END - 60)
            if src == "DVOL":
                u = ("https://www.deribit.com/api/v2/public/get_volatility_index_data?currency=BTC"
                     f"&start_timestamp={t0 * 1000}&end_timestamp={t1 * 1000}&resolution=60")
                d = json.loads(_get(u))["result"]["data"]
                rows = [(src, int(x[0] // 1000), float(x[4])) for x in d]
            else:
                u = ("https://www.deribit.com/api/v2/public/get_tradingview_chart_data?instrument_name=BTC-PERPETUAL"
                     f"&start_timestamp={t0 * 1000}&end_timestamp={t1 * 1000}&resolution=1")
                d = json.loads(_get(u))["result"]
                rows = [(src, int(a // 1000), float(c)) for a, c in zip(d["ticks"], d["close"])]
            rows = [r for r in rows if r[1] < END]
            db.executemany("insert or replace into m1 values(?,?,?)", rows)
            db.commit()
            t0 = t1 + 60
            time.sleep(0.3)
        print(src, db.execute("select count(*), min(ts), max(ts) from m1 where src=?", (src,)).fetchone())
    # Coinbase BTC-USD 1 minute (300 a request)
    have = db.execute("select max(ts) from m1 where src='CB'").fetchone()[0]
    t0 = (have + 60) if have else FETCH_START
    while t0 < END:
        t1 = min(t0 + 299 * 60, END - 60)
        a = datetime.fromtimestamp(t0, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        b = datetime.fromtimestamp(t1, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        d = json.loads(_get(f"https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=60&start={a}&end={b}"))
        rows = [("CB", int(x[0]), float(x[4])) for x in d if t0 <= x[0] <= t1]
        db.executemany("insert or replace into m1 values(?,?,?)", rows)
        db.commit()
        t0 = t1 + 60
        time.sleep(0.25)
    print("CB", db.execute("select count(*), min(ts), max(ts) from m1 where src='CB'").fetchone())
    # Binance spot BTCUSDT 1 minute zips
    names = ["monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2026-08", "monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2026-09"]
    names += [f"daily/klines/BTCUSDT/1m/BTCUSDT-1m-2026-10-{d:02d}" for d in range(1, 28)]
    for n in names:
        z = zipfile.ZipFile(io.BytesIO(_get(f"https://data.binance.vision/data/spot/{n}.zip")))
        rows = []
        for line in z.read(z.namelist()[0]).decode().splitlines():
            f = line.split(",")
            if not f[0].isdigit():
                continue
            t = int(f[0])
            t = t // 1_000_000 if t > 10 ** 14 else t // 1000   # spot files moved to microseconds in 2025
            if FETCH_START <= t < END:
                rows.append(("BN", t, float(f[4])))
        db.executemany("insert or replace into m1 values(?,?,?)", rows)
        db.commit()
    print("BN", db.execute("select count(*), min(ts), max(ts) from m1 where src='BN'").fetchone())


# ---------------------------------------------------------------- inputs

class Series:
    """1 minute series stamped by start; value usable at time t is the last bar with start <= t - 60."""

    def __init__(self, db, src):
        rows = db.execute("select ts, v from m1 where src=? order by ts", (src,)).fetchall()
        self.ts = [r[0] for r in rows]
        self.v = [r[1] for r in rows]
        self.at = dict(rows)

    def usable(self, t, max_age=180):
        i = bisect_right(self.ts, t - 60) - 1
        if i < 0 or t - 60 - self.ts[i] > max_age:
            return None
        return self.v[i]


def daily(db, src):
    return sorted(db.execute("select d, v from daily where src=?", (src,)).fetchall())


def gold_ratio_by_date(db):
    """{utc date D: R} using the latest GVZ date strictly before D and GC=F closes up to that date."""
    gvz, gc = daily(db, "GVZ"), daily(db, "GC")
    gcd = [d for d, _ in gc]
    out = {}
    d = datetime(2026, 8, 6, tzinfo=timezone.utc)
    while d < datetime(2026, 10, 28, tzinfo=timezone.utc):
        ds = d.strftime("%Y-%m-%d")
        prev = [x for x in gvz if x[0] < ds]
        if prev:
            gd, gv = prev[-1]
            j = bisect_right(gcd, gd)            # GC=F closes dated <= gd
            closes = [v for _, v in gc[max(0, j - 21):j]]
            if len(closes) == 21:
                r = [math.log(closes[i + 1] / closes[i]) for i in range(20)]
                rv = statistics.stdev(r) * math.sqrt(252)
                out[ds] = (gv / 100) / rv
        d += timedelta(days=1)
    return out


def btc_ratio(dvol, perp, D):
    dv = dvol.usable(D)
    if dv is None:
        return None
    i = bisect_right(perp.ts, D - 60)
    seg = list(zip(perp.ts[max(0, i - 1441):i], perp.v[max(0, i - 1441):i]))
    seg = [x for x in seg if x[0] > D - 60 - 1441 * 60]
    rets = [math.log(seg[k + 1][1] / seg[k][1]) for k in range(len(seg) - 1) if seg[k + 1][0] - seg[k][0] == 60]
    if len(rets) < 1300:
        return None
    rv = statistics.pstdev(rets) * math.sqrt(525600)
    return (dv / 100) / rv if rv > 0 else None


def quantile(xs, q):
    xs = sorted(xs)
    k = (len(xs) - 1) * q
    lo = math.floor(k)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


# ---------------------------------------------------------------- trades

def held(w, side, fill_off, lo, hi):
    fr = w["c"].get(fill_off)
    a = ask(fr, side)
    if a is None or not (lo - 1e-9 <= a <= hi + 1e-9):
        return None
    won = w["result"] == side
    t = {"close": w["close"], "day": day(w["close"]), "side": side, "fill": a, "won": won, "vol0": fr["v"] == 0,
         "nosale": False}
    for key, cc, m in (("n1", 1, 1.0), ("n10", 10, 1.0), ("n10x", 10, 1.2)):
        t[key] = cc * ((1.0 if won else 0.0) - a) - fee(a, cc, m)
    return t


def cheap_side(r, lo, hi):
    for side in ("yes", "no"):
        a = ask(r, side)
        if a is not None and lo - 1e-9 <= a <= hi + 1e-9:
            return side
    return None


def ivgap_trade(w):
    """H1 trade given a signal window: (trade | None) or 'gap'."""
    r = w["c"].get(-600)
    if r is None or w["c"].get(-540) is None:
        return "gap"
    s = cheap_side(r, 0.10, 0.40)
    if s is None:
        return None
    return held(w, s, -540, 0.05, 0.50)


def coinprem_trade(w, side):
    r = w["c"].get(-600)
    if r is None or w["c"].get(-540) is None:
        return "gap"
    a = ask(r, side)
    if a is None or not (0.20 - 1e-9 <= a <= 0.50 + 1e-9):
        return None
    return held(w, side, -540, 0.15, 0.55)


def vegalag_trade(w, dvol, cut):
    """H3: first candle ending 780..420 s before the close with dvol5 >= cut; returns trade, None or 'gap'."""
    c = w["c"]
    for s in range(-780, -419, 60):
        t = w["close"] + s
        a, b = dvol.usable(t), dvol.usable(t - 300)
        if a is None or b is None:
            return "gap"
        if a - b >= cut - 1e-12:
            r = c.get(s)
            if r is None or c.get(s + 60) is None:
                return "gap"
            side = cheap_side(r, 0.10, 0.40)
            if side is None:
                return None
            return round_trip(w, side, s + 60, s + 240, 0.05, 0.45)
    return None


# ---------------------------------------------------------------- scoring

def summ(tr):
    if not tr:
        return {"n": 0}
    o = {"n": len(tr), "pf10": pf([t["n10"] for t in tr]), "pf1": pf([t["n1"] for t in tr]),
         "pf10x": pf([t["n10x"] for t in tr]), "net10": sum(t["n10"] for t in tr), "net10x": sum(t["n10x"] for t in tr),
         "z": dayz(tr), "win": sum(t["won"] for t in tr) / len(tr), "fill": statistics.mean(t["fill"] for t in tr),
         "days": len({t["day"] for t in tr}), "nosale": sum(t["nosale"] for t in tr)}
    nz = [t for t in tr if not t["vol0"]]
    o["n_nz"], o["pf10_nz"] = len(nz), (pf([t["n10"] for t in nz]) if nz else float("nan"))
    return o


def line(name, s):
    if not s.get("n"):
        return f"{name}: n 0"
    return (f"{name}: n {s['n']} days {s['days']} | PF10 {s['pf10']:.2f} PF1 {s['pf1']:.2f} PF10x1.2 {s['pf10x']:.2f} | "
            f"net10 ${s['net10']:+.2f} (x1.2 ${s['net10x']:+.2f}) per-trade {100 * s['net10'] / s['n'] / 10:+.2f}c/ct | "
            f"win {100 * s['win']:.1f}% avg fill {s['fill']:.3f} | day z {s['z']:+.2f} | no-sale {s['nosale']} | "
            f"vol>0 only n {s['n_nz']} PF10 {s['pf10_nz']:.2f}")


def verdict(d, v):
    if d.get("n", 0) < 100:
        return "NOT_ENOUGH_DATA"
    if d["pf10"] < 1.5 or d["net10x"] <= 0:
        return "FALSIFIED"
    if v.get("n", 0) < 50:
        return "NOT_ENOUGH_DATA"
    if v["pf10"] < 1.3 or v["net10x"] <= 0:
        return "FALSIFIED"
    return "NOT_YET_FALSIFIED"


def split(tr):
    return [t for t in tr if t["close"] < DISC_END], [t for t in tr if t["close"] >= DISC_END]


def report(name, tr, gaps, info=None):
    d, v = split(tr)
    sd, sv = summ(d), summ(v)
    out = [f"== {name}", "  DISC " + line("", sd), "  VAL  " + line("", sv),
           f"  data gaps: disc {gaps[0]} val {gaps[1]}", f"  VERDICT: {verdict(sd, sv)}"]
    for k, x in (info or {}).items():
        a, b = split(x)
        out.append(f"  info {k}: DISC " + line("", summ(a)))
        out.append(f"  info {k}: VAL  " + line("", summ(b)))
    return "\n".join(out), verdict(sd, sv), sd, sv


def run():
    db = _db()
    out = [f"NEWH7 run {datetime.now(timezone.utc).isoformat(timespec='seconds')} (registration workers/NEWH7_REGISTRATION.md)"]
    verdicts = {}

    # ---- H1 gold
    gw = load(GOLD)
    gr = gold_ratio_by_date(db)
    disc_days = [v for k, v in gr.items() if k < "2026-09-21"]
    gcut = quantile(disc_days, 2 / 3)
    out.append(f"H1 gold: R days {len(gr)} (disc {len(disc_days)}), 2/3 cut {gcut:.4f}; windows {len(gw)}")
    sig, lo, allw, gaps = [], [], [], [0, 0]
    for close, w in sorted(gw.items()):
        R = gr.get(day(close))
        k = 0 if close < DISC_END else 1
        if R is None:
            gaps[k] += 1
            continue
        t = ivgap_trade(w)
        if t == "gap":
            gaps[k] += 1
            continue
        if t is None:
            continue
        allw.append(t)
        (sig if R > gcut else lo).append(t)
    txt, v, *_ = report("H1 IVGAP gold (GVZ / RV20 top third, cheap side 10-40c at 600 s, held)", sig, gaps,
                        {"bottom two thirds": lo, "all windows": allw})
    out.append(txt)
    verdicts["IVGAP gold"] = v

    # ---- H1 Bitcoin
    bw = load(BTC)
    dvol, perp = Series(db, "DVOL"), Series(db, "PERP")
    Rs = {}
    for close in bw:
        Rs[close] = btc_ratio(dvol, perp, close - 600)
    disc = [r for c, r in Rs.items() if r is not None and c < DISC_END]
    bcut = quantile(disc, 2 / 3)
    out.append(f"H1 Bitcoin: windows {len(bw)}, R known {sum(r is not None for r in Rs.values())}, 2/3 cut {bcut:.4f}")
    sig, lo, allw, gaps = [], [], [], [0, 0]
    for close, w in sorted(bw.items()):
        R = Rs[close]
        k = 0 if close < DISC_END else 1
        if R is None:
            gaps[k] += 1
            continue
        t = ivgap_trade(w)
        if t == "gap":
            gaps[k] += 1
            continue
        if t is None:
            continue
        allw.append(t)
        (sig if R > bcut else lo).append(t)
    txt, v, *_ = report("H1 IVGAP Bitcoin (DVOL / RV24h top third, cheap side 10-40c at 600 s, held)", sig, gaps,
                        {"bottom two thirds": lo, "all windows": allw})
    out.append(txt)
    verdicts["IVGAP Bitcoin"] = v

    # ---- H2 COINPREM
    cb, bn = Series(db, "CB"), Series(db, "BN")

    def dprem(D):
        a1, b1, a0, b0 = cb.usable(D, 120), bn.usable(D, 120), cb.usable(D - 900, 120), bn.usable(D - 900, 120)
        if None in (a1, b1, a0, b0):
            return None
        return math.log(a1 / b1) - math.log(a0 / b0)

    dp = {c: dprem(c - 600) for c in bw}
    dd = [x for c, x in dp.items() if x is not None and c < DISC_END]
    hi_cut, lo_cut = quantile(dd, 0.90), quantile(dd, 0.10)
    out.append(f"H2: dprem known {sum(x is not None for x in dp.values())} of {len(bw)}; cuts 10% {lo_cut * 1e4:.2f} bp, "
               f"90% {hi_cut * 1e4:.2f} bp")
    tr, gaps = [], [0, 0]
    for close, w in sorted(bw.items()):
        x = dp[close]
        k = 0 if close < DISC_END else 1
        if x is None:
            gaps[k] += 1
            continue
        side = "yes" if x > hi_cut else ("no" if x < lo_cut else None)
        if side is None:
            continue
        t = coinprem_trade(w, side)
        if t == "gap":
            gaps[k] += 1
            continue
        if t is not None:
            tr.append(t)
    txt, v, *_ = report("H2 COINPREM Bitcoin (15 min premium change top/bottom decile, that side at 20-50c, held)", tr, gaps)
    out.append(txt)
    verdicts["COINPREM Bitcoin"] = v

    # ---- H3 VEGALAG
    ch = []
    t = START - (START % 60)
    while t < DISC_END:
        a, b = dvol.usable(t), dvol.usable(t - 300)
        if a is not None and b is not None:
            ch.append(a - b)
        t += 60
    vcut = quantile(ch, 0.99)
    out.append(f"H3: discovery minutes {len(ch)}, dvol5 0.99 cut {vcut:.3f} points")
    tr, gaps = [], [0, 0]
    for close, w in sorted(bw.items()):
        k = 0 if close < DISC_END else 1
        x = vegalag_trade(w, dvol, vcut)
        if x == "gap":
            gaps[k] += 1
            continue
        if x is not None:
            tr.append(x)
    txt, v, *_ = report("H3 VEGALAG Bitcoin (dvol5 >= 99th pct at 780-420 s, cheap side 10-40c, sold 3 min later)", tr, gaps)
    out.append(txt)
    verdicts["VEGALAG Bitcoin"] = v

    out.append("VERDICTS: " + json.dumps(verdicts))
    print("\n".join(out))


# ---------------------------------------------------------------- forward evaluator (only used if a rule survives)

def forward_eval(window, params):  # pragma: no cover - only for a survivor; none expected
    from .fwdeval import NoData
    raise NoData("NEWH7 rules need outside series (GVZ, DVOL, Coinbase, Binance) the forward ledger does not load")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    {"fetch": fetch, "run": run}[cmd]()
