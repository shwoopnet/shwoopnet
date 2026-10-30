"""MECH1: who is on the other side of the Bitcoin open interest core (research only).

Core (GEN6 / FALS4): KXBTC15M, signal candle ending 180 s before the close, cheap side ask 5c to 50c,
open interest up more than 86,299.56 from the candle ending -360 to the signal candle, fill at the
-120 candle's ask, held. This file reads Kalshi's PUBLIC trade tape for the trades that make up that
open interest jump, (close - 360, close - 180], in every firing window and in matched controls.

    python -m scalper.mech1 windows        list firing windows and matched controls (no outcome read)
    python -m scalper.mech1 fetch K N      resumable shard K of N of the tape download
    python -m scalper.mech1 describe       descriptive tables (no outcome read)
    python -m scalper.mech1 score          the ONE scored look (refused before the registration commit)

Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE. Nothing here means trade.
"""
from __future__ import annotations

import json
import random
import sqlite3
import statistics as st
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

from .paths import DATA_DIR

FILES = ["l1b.sqlite", "book.sqlite", "fresh.sqlite"]
SERIES = "KXBTC15M"
FORWARD_TS = int(datetime(2026, 10, 28, tzinfo=timezone.utc).timestamp())
DISC_END = int(datetime(2026, 9, 21, tzinfo=timezone.utc).timestamp())
START = int(datetime(2026, 8, 6, tzinfo=timezone.utc).timestamp())
THRESH = 86299.56000000001
LO, HI = 0.05, 0.50
SEED = 30102601
D = DATA_DIR / "mech1"
TAPE_DB = D / "tape.sqlite"
BIG = 1000.0  # contracts: a "large print" for the size table


def stage(close):
    return "disc" if close < DISC_END else "val"


def side_ask(row, side):
    return row[1] if side == "yes" else (None if row[0] is None else round(1 - row[0], 6))


def side_bid(row, side):
    return row[0] if side == "yes" else (None if row[1] is None else round(1 - row[1], 6))


def cheap_side(row):
    for s in ("yes", "no"):
        a = side_ask(row, s)
        if a is not None and LO <= a <= HI:
            return s
    return None


def load_candles():
    """{ticker: {close, c: {offset: (bid, ask, vol, oi)}}}. The result column is NOT read here."""
    win = {}
    for f in FILES:
        con = sqlite3.connect(DATA_DIR / f)
        own = set()
        for t, close in con.execute(
                "select ticker, close_ts from market where series=? and close_ts>=? and close_ts<? "
                "and result in ('yes','no')", (SERIES, START, FORWARD_TS)):
            if t in win:
                continue
            win[t] = {"close": close, "c": {}}
            own.add(t)
        for (t, end, bid, ask, vol, oi) in con.execute(
                "select ticker, end_ts, bid_c, ask_c, volume, oi from candle where series=?", (SERIES,)):
            if t in own:
                win[t]["c"][end - win[t]["close"]] = (bid, ask, vol, oi)
    return win


def features(w):
    c = w["c"]
    s, p = c.get(-180), c.get(-360)
    if s is None or p is None or s[3] is None or p[3] is None:
        return None
    cs = cheap_side(s)
    if cs is None:
        return None
    fav = "no" if cs == "yes" else "yes"

    def mid(r, side):
        a, b = side_ask(r, side), side_bid(r, side)
        return None if a is None or b is None else (a + b) / 2

    vol3 = sum((c.get(o) or (0, 0, 0, 0))[2] or 0 for o in (-300, -240, -180))
    return {"doi": s[3] - p[3], "cheap": cs, "fav": fav, "cheap_ask": side_ask(s, cs),
            "fav_mid180": mid(s, fav), "fav_mid360": mid(p, fav), "vol3": vol3}


def windows():
    """Firing windows and one matched control each (same stage, same 5c cheap-ask bucket, doi not above
    the threshold), drawn with a fixed seed. Uses candles only."""
    win = load_candles()
    fire, pool = [], defaultdict(list)
    for t, w in sorted(win.items()):
        f = features(w)
        if f is None:
            continue
        b = min(8, int((f["cheap_ask"] - LO) / 0.05 + 1e-9))
        key = (stage(w["close"]), b)
        if f["doi"] > THRESH:
            fire.append((t, w["close"], key))
        else:
            pool[key].append((t, w["close"]))
    rng = random.Random(SEED)
    ctrl = []
    for k in pool:
        pool[k].sort()
        rng.shuffle(pool[k])
    used = defaultdict(int)
    for t, close, key in fire:
        i = used[key]
        if i < len(pool[key]):
            ctrl.append(pool[key][i] + (key,))
            used[key] += 1
    return win, fire, ctrl


# ---------------------------------------------------------------- tape

def _db():
    D.mkdir(exist_ok=True)
    db = sqlite3.connect(TAPE_DB, timeout=120)
    db.execute("CREATE TABLE IF NOT EXISTS trades(ticker TEXT, ts REAL, yes_c REAL, size REAL, taker TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS done(ticker TEXT PRIMARY KEY, n INTEGER, src TEXT)")
    db.execute("CREATE INDEX IF NOT EXISTS ix_t ON trades(ticker)")
    return db


def _maker4_cache():
    """MAKER4's cached tape (close-750 to close-115) covers our interval for some October windows."""
    out = {}
    for f in sorted((DATA_DIR / "maker4").glob("tape_*.json")):
        for k, v in json.loads(f.read_text()).items():
            if k.startswith(SERIES):
                out[k] = v
    return out


def _get(path, params):
    """Polite GET: a 429 waits 3 s and asks again (no escalation, which stalled the shared limit)."""
    import urllib.error
    import urllib.parse
    import urllib.request
    from . import api
    url = api.BASES[0] + path + "?" + urllib.parse.urlencode(params)
    for i in range(40):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            time.sleep(3.0 if e.code == 429 else 5.0)
        except Exception:
            time.sleep(5.0)
    raise RuntimeError("GET failed " + path)


def _fetch_one(tk, lo, hi):
    for path in ("/historical/trades", "/markets/trades"):
        cur, rows = None, []
        while True:
            p = {"ticker": tk, "limit": 1000, "min_ts": lo, "max_ts": hi}
            if cur:
                p["cursor"] = cur
            try:
                d = _get(path, p)
            except Exception:
                time.sleep(30)
                continue
            for t in d.get("trades", []):
                ts = datetime.fromisoformat(t["created_time"].replace("Z", "+00:00")).timestamp()
                rows.append((ts, round(float(t["yes_price_dollars"]) * 100, 2), float(t["count_fp"]),
                             t["taker_outcome_side"]))
            cur = d.get("cursor")
            time.sleep(0.5)
            if not cur or not d.get("trades"):
                break
        if rows:
            return rows, path
    return [], "empty"


def fetch(shard, shards):
    _, fire, ctrl = windows()
    # firing windows first (newest first), then controls
    jobs = sorted({(t, c) for t, c, _ in fire}, key=lambda x: -x[1])
    fset = {t for t, _ in jobs}
    cj = sorted({(t, c) for t, c, _ in ctrl if t not in fset})
    random.Random(SEED + 1).shuffle(cj)  # any prefix of the controls is a random matched sample
    jobs += cj
    jobs = jobs[shard::shards]
    db = _db()
    done = {r[0] for r in db.execute("select ticker from done")}
    cache = _maker4_cache()
    print(len(jobs), "jobs,", len(done), "done (all shards)", flush=True)
    for i, (tk, close) in enumerate(jobs):
        if tk in done:
            continue
        lo, hi = close - 360, close - 180
        if tk in cache:
            rows = [(r[0], float(r[1]), r[2], "yes" if r[3] == 1 else "no") for r in cache[tk] if lo < r[0] <= hi]
            src = "maker4"
        else:
            rows, src = _fetch_one(tk, lo, hi)
            rows = [r for r in rows if lo < r[0] <= hi + 1]
        db.executemany("insert into trades values(?,?,?,?,?)", [(tk,) + tuple(r) for r in rows])
        db.execute("insert or replace into done values(?,?,?)", (tk, len(rows), src))
        db.commit()
        if i % 20 == 0:
            print(shard, i, len(jobs), tk, len(rows), src, flush=True)
    print("shard", shard, "finished", flush=True)


# ---------------------------------------------------------------- measures (no outcome)

def measures(win, tk):
    """Tape measures for one window, or None if not fetched."""
    db = _db()
    r = db.execute("select n from done where ticker=?", (tk,)).fetchone()
    if r is None:
        return None
    w = win[tk]
    f = features(w)
    tr = db.execute("select ts, yes_c, size, taker from trades where ticker=?", (tk,)).fetchall()
    tot = sum(x[2] for x in tr)
    favb = sum(x[2] for x in tr if x[3] == f["fav"])
    sizes = sorted((x[2] for x in tr), reverse=True)
    top10 = sum(sizes[:10])
    big = sum(s for s in sizes if s >= BIG)
    # favourite price paid by favourite takers (VWAP, in the favourite's own cents)
    fp = [((x[1] if f["fav"] == "yes" else 100 - x[1]), x[2]) for x in tr if x[3] == f["fav"]]
    fvwap = sum(p * s for p, s in fp) / sum(s for _, s in fp) / 100 if fp else None
    def share(sel):
        v = sum(x[2] for x in sel)
        return sum(x[2] for x in sel if x[3] == f["fav"]) / v if v else None

    close = w["close"]
    extra = {"fav_share_big": share([x for x in tr if x[2] >= BIG]),
             "fav_share_small": share([x for x in tr if x[2] < 100]),
             "fav_share_last": share([x for x in tr if x[0] > close - 240]),
             "fav_share_first": share([x for x in tr if x[0] <= close - 300])}
    return {"t": tk, "close": w["close"], "stage": stage(w["close"]), **f, **extra,
            "n": len(tr), "vol": tot, "fav_share": favb / tot if tot else None,
            "fav_net": favb - (tot - favb), "med_size": st.median(sizes) if sizes else None,
            "top10": top10 / tot if tot else None, "big_share": big / tot if tot else None,
            "open_ratio": f["doi"] / tot if tot else None,
            "fav_rise": (None if f["fav_mid180"] is None or f["fav_mid360"] is None
                         else f["fav_mid180"] - f["fav_mid360"]),
            "fav_vwap": fvwap}


def q(v, p):
    v = sorted(x for x in v if x is not None)
    if not v:
        return float("nan")
    return v[min(len(v) - 1, int(p * (len(v) - 1) + 0.5))]


def table(rows, label):
    if not rows:
        print(label, "n 0")
        return
    fs = [r["fav_share"] for r in rows if r["fav_share"] is not None]
    rise = [r["fav_rise"] for r in rows if r["fav_rise"] is not None]
    print(f"{label:22s} n {len(rows):4d} | fav taker share median {q(fs,.5):.3f} mean {st.mean(fs):.3f} "
          f"(p25 {q(fs,.25):.3f}, p75 {q(fs,.75):.3f}) | vol median {q([r['vol'] for r in rows],.5):,.0f} "
          f"| trades median {q([r['n'] for r in rows],.5):,.0f} | print median {q([r['med_size'] for r in rows],.5):.1f} "
          f"| top10 share median {q([r['top10'] for r in rows],.5):.3f} | >=1000 share median "
          f"{q([r['big_share'] for r in rows],.5):.3f} | doi/vol median {q([r['open_ratio'] for r in rows],.5):.3f} "
          f"| fav mid rose in {sum(1 for x in rise if x > 0)/len(rise):.1%}, mean rise {st.mean(rise):+.4f} "
          f"| fav-taker VWAP minus fav mid180 median "
          f"{q([r['fav_vwap']-r['fav_mid180'] for r in rows if r['fav_vwap'] is not None and r['fav_mid180'] is not None],.5):+.4f}")


def describe():
    win, fire, ctrl = windows()
    F = [m for m in (measures(win, t) for t, _, _ in fire) if m]
    C = [m for m in (measures(win, t) for t, _, _ in ctrl) if m]
    db = _db()
    src = dict(db.execute("select src, count(*) from done group by src").fetchall())
    empty = db.execute("select count(*) from done where n=0").fetchone()[0]
    print(f"firing windows {len(fire)} (tape {len(F)}), controls {len(ctrl)} (tape {len(C)}); sources {src}; empty tape {empty}")
    for s in ("disc", "val"):
        table([r for r in F if r["stage"] == s], f"FIRE {s}")
        table([r for r in C if r["stage"] == s], f"CTRL {s}")
    print("\nfavourite taker share by print size and by minute (added after registration; descriptive, no outcome)")
    for s in ("disc", "val"):
        for lab, R in (("FIRE", F), ("CTRL", C)):
            x = [r for r in R if r["stage"] == s]
            if x:
                print(f"  {lab} {s}: prints >=1000 {q([r['fav_share_big'] for r in x],.5):.3f} | prints <100 "
                      f"{q([r['fav_share_small'] for r in x],.5):.3f} | first minute (-360,-300] "
                      f"{q([r['fav_share_first'] for r in x],.5):.3f} | last minute (-240,-180] "
                      f"{q([r['fav_share_last'] for r in x],.5):.3f} | volume-weighted share "
                      f"{sum(r['vol']*r['fav_share'] for r in x if r['fav_share'] is not None)/sum(r['vol'] for r in x):.3f}")
    print("\nby cheap-ask bucket (fire / ctrl median fav taker share)")
    for b in range(9):
        fb = [r["fav_share"] for r in F if min(8, int((r["cheap_ask"] - LO) / 0.05 + 1e-9)) == b and r["fav_share"] is not None]
        cb = [r["fav_share"] for r in C if min(8, int((r["cheap_ask"] - LO) / 0.05 + 1e-9)) == b and r["fav_share"] is not None]
        print(f"  {5+5*b:2d}-{10+5*b:2d}c  fire n {len(fb):3d} {q(fb,.5):.3f} | ctrl n {len(cb):3d} {q(cb,.5):.3f}")
    # whose volume: favourite-buying volume vs doi
    for s in ("disc", "val"):
        x = [r for r in F if r["stage"] == s and r["vol"]]
        if x:
            print(f"{s}: firing windows, total taker vol {sum(r['vol'] for r in x):,.0f}, fav-taker vol "
                  f"{sum(r['vol']*r['fav_share'] for r in x):,.0f}, doi {sum(r['doi'] for r in x):,.0f}; "
                  f"corr(doi, fav_net) {corr([r['doi'] for r in x],[r['fav_net'] for r in x]):.2f}, "
                  f"corr(doi, vol) {corr([r['doi'] for r in x],[r['vol'] for r in x]):.2f}")
    # concentration: share of firing windows whose top-10 prints are over half the volume
    for s in ("disc", "val"):
        x = [r for r in F if r["stage"] == s and r["top10"] is not None]
        if x:
            print(f"{s}: firing windows with top-10 prints > 50% of volume: {sum(r['top10'] > .5 for r in x)} of {len(x)}")
    return win, F, C


def corr(a, b):
    if len(a) < 3:
        return float("nan")
    ma, mb = st.mean(a), st.mean(b)
    sa = sum((x - ma) ** 2 for x in a) ** .5
    sb = sum((y - mb) ** 2 for y in b) ** .5
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb) if sa and sb else float("nan")


# ---------------------------------------------------------------- the one scored look

def score():
    reg = subprocess.run(["git", "log", "--oneline", "--", "workers/MECH1_REGISTRATION.md"],
                         capture_output=True, text=True).stdout.strip()
    if not reg:
        sys.exit("refused: registration not committed")
    flag = D / "scored.flag"
    if flag.exists():
        sys.exit("refused: the scored look was already run")
    from .fals4 import fee, pf, dayz
    win, F, C = describe()
    res = {}
    for f in FILES:
        con = sqlite3.connect(DATA_DIR / f)
        for t, r in con.execute("select ticker, result from market where series=?", (SERIES,)):
            res.setdefault(t, r)
    print("\n## Scored look: split firing windows at the stage median of favourite taker share")
    for s in ("disc", "val"):
        x = [r for r in F if r["stage"] == s and r["fav_share"] is not None]
        med = st.median(r["fav_share"] for r in x)
        for half, sel in (("HIGH", [r for r in x if r["fav_share"] > med]),
                          ("LOW", [r for r in x if r["fav_share"] <= med])):
            tr = []
            for r in sel:
                fr = win[r["t"]]["c"].get(-120)
                if fr is None:
                    continue
                fill = side_ask(fr, r["cheap"])
                if fill is None or not 0 < fill < 1:
                    continue
                won = res[r["t"]] == r["cheap"]
                for mult, key in ((1.0, "net"), (1.2, "net12")):
                    r[key] = 10 * ((1.0 if won else 0.0) - fill) - fee(fill, 10, mult)
                tr.append({"net": r["net"], "net12": r["net12"], "won": won, "fill": fill,
                           "day": datetime.fromtimestamp(r["close"], timezone.utc).strftime("%Y-%m-%d")})
            n = [t["net"] for t in tr]
            print(f"{s} {half:4s} (median {med:.3f}) n {len(tr)} PF {pf(n):.2f} PF x1.2 {pf([t['net12'] for t in tr]):.2f} "
                  f"win {sum(t['won'] for t in tr)/max(1,len(tr)):.1%} fill {st.mean(t['fill'] for t in tr):.3f} "
                  f"net ${sum(n):.2f} day z {dayz(tr):.2f}")
    flag.write_text(datetime.now(timezone.utc).isoformat())


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "windows":
        _, fire, ctrl = windows()
        print("fire", len(fire), "disc", sum(k[0] == "disc" for _, _, k in fire), "ctrl", len(ctrl))
    elif cmd == "fetch":
        fetch(int(sys.argv[2]), int(sys.argv[3]))
    elif cmd == "describe":
        describe()
    elif cmd == "score":
        score()
