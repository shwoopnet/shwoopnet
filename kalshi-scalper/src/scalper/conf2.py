"""CONF2 (README, Pre-registration: CONF2): CONF1's ladder confluence on the whole L1 history and forward. Research only.
    python -m scalper.conf2 fetch LO HI   (resumable; LO and HI are unix seconds of closes; strikes chosen 55 to 52 minutes before each close, as CORR1)
    python -m scalper.conf2 run           (windows A and B, once)
    python -m scalper.conf2 holdout       (window C, once, when it holds at least 30 kept closes)
"""
from __future__ import annotations

import math
import sqlite3
import statistics as st
import sys
import time
from collections import defaultdict

from . import api, backfill
from .fees import taker_fee
from .lad1 import chunks
from .paths import DATA_DIR

DB = DATA_DIR / "conf2_lad.sqlite"
LADDER_FILES = (DATA_DIR / "lad2.sqlite", DB)
FILES15 = ("l1b.sqlite", "book.sqlite", "fresh.sqlite", "five.sqlite")
SERIES, PAUSE = "KXBTCD", 0.5
PROBE_S, WINDOW_S = (3300, 3120), (3300, 60)
LEFT = 360
A_END, B_END = 1790380800, 1793059200   # 2026-09-26 00:00 UTC, 2026-10-27 00:00 UTC


def fetch(lo: int, hi: int) -> None:
    db = sqlite3.connect(DB)
    db.executescript(backfill.SCHEMA)
    done = {r[0] for r in db.execute("SELECT DISTINCT close_ts FROM market")}
    by_close = defaultdict(list)
    for m in api.settled_markets(SERIES, lo - 3600, hi + 3600):
        c = backfill.iso_ts(m.get("close_time"))
        if c is not None and lo <= c <= hi and c % 3600 == 0 and m.get("result") in ("yes", "no"):
            by_close[c].append(m)
    print(f"{len(by_close)} closes listed, {len(done)} already stored", flush=True)
    for n, close_ts in enumerate(sorted(by_close)):
        if close_ts in done:
            continue
        keep = []
        for ch in chunks(by_close[close_ts], 100):
            got = api.batch_candlesticks([m["ticker"] for m in ch], close_ts - PROBE_S[0], close_ts - PROBE_S[1])
            for m in ch:
                rows = [r for r in (backfill.parse_candle(x, m["ticker"], SERIES) for x in got.get(m["ticker"], [])) if r]
                q = [r for r in rows if r[6] is not None and r[10] is not None]
                if q and 0.01 <= (q[-1][6] + q[-1][10]) / 2 <= 0.99:
                    keep.append(m)
            time.sleep(PAUSE)
        for ch in chunks(keep, 100):
            got = api.batch_candlesticks([m["ticker"] for m in ch], close_ts - WINDOW_S[0], close_ts - WINDOW_S[1])
            for m in ch:
                t = m["ticker"]
                rows = [r for r in (backfill.parse_candle(x, t, SERIES) for x in got.get(t, [])) if r]
                db.executemany("INSERT OR REPLACE INTO candle VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
                db.execute("INSERT OR REPLACE INTO market VALUES(?,?,?,?,?,?,?)", (t, SERIES, backfill.iso_ts(m.get("open_time")), close_ts, m.get("result"), m.get("floor_strike"), len(rows)))
            time.sleep(PAUSE)
        db.commit()
        if n % 25 == 0:
            print(f"  {n}/{len(by_close)} closes, {len(keep)} strikes kept", flush=True)
    print("done", db.execute("SELECT COUNT(DISTINCT close_ts) FROM market").fetchone()[0], "closes", flush=True)


def ladder_at():
    """close -> [(strike, bid, ask)] at the candle ending LEFT seconds before the close."""
    out = defaultdict(dict)
    for f in LADDER_FILES:
        if not f.exists():
            continue
        db = sqlite3.connect(f)
        for tk, close, strike in db.execute("select ticker, close_ts, strike from market"):
            r = db.execute("select bid_c, ask_c from candle where ticker=? and end_ts=?", (tk, close - LEFT)).fetchone()
            if r and r[0] is not None and r[1] is not None and strike is not None:
                out[close][tk] = (strike, r[0], r[1])
    return {c: list(v.values()) for c, v in out.items()}, sorted(out)


def entries():
    mk, q = {}, {}
    for f in FILES15:
        p = DATA_DIR / f
        if not p.exists():
            continue
        db = sqlite3.connect(p)
        for t, c, k, r in db.execute("select ticker, close_ts, strike, result from market where series='KXBTC15M'"):
            if c % 3600 == 0 and r in ("yes", "no") and k:
                mk[t] = (c, k, r)
        for t, e, b, a in db.execute("select ticker, end_ts, bid_c, ask_c from candle where series='KXBTC15M'"):
            if t in mk and e == mk[t][0] - LEFT:
                q[t] = (b, a)
    out = []
    for t, (c, k, r) in mk.items():
        if t not in q:
            continue
        b, a = q[t]
        for side, p in (("yes", a), ("no", None if b is None or b <= 0 else round(1 - b, 4))):
            if p is not None and 0.88 <= p <= 0.97:
                out.append(dict(close=c, strike=k, side=side, p=p, won=side == r))
    return out


def pf(x):
    w, l = sum(v for v in x if v > 0), -sum(v for v in x if v < 0)
    return w / l if l > 0 else (99.0 if w > 0 else 0.0)


def zday(rows):
    d = defaultdict(float)
    for c, v in rows:
        d[c // 86400] += v
    v = list(d.values())
    return st.mean(v) / (st.pstdev(v) / math.sqrt(len(v))) if len(v) > 1 and st.pstdev(v) > 0 else 0.0


def score(windows):
    L, lc = ladder_at()
    E = entries()
    net = lambda e, m=1.0: (1 - e["p"] if e["won"] else -e["p"]) - m * taker_fee(e["p"], 1)
    first = lc[0] if lc else None
    print(f"CONF2: {len(E)} Bitcoin top-of-hour L1 entries; ladder closes {len(lc)} from {first}")
    for name, lo, hi in windows:
        ew = [e for e in E if lo <= e["close"] < hi and (first is None or e["close"] >= first)]
        kept, rem, und = [], [], 0
        for e in ew:
            lad = L.get(e["close"])
            if not lad:
                und += 1
                continue
            k, b, a = min(lad, key=lambda x: abs(x[0] - e["strike"]))
            price = a if e["side"] == "yes" else 1 - b
            (kept if price >= 0.88 else rem).append(e)
        kv = [net(e) for e in kept]
        print(f"  {name}: parent PF {pf([net(e) for e in kept + rem]):.2f} n={len(kept) + len(rem)} (undefined {und}) | kept PF {pf(kv):.2f} n={len(kept)} "
              f"closes {len({e['close'] for e in kept})} fees1.2 {pf([net(e, 1.2) for e in kept]):.2f} z {zday([(e['close'], v) for e, v in zip(kept, kv)]):+.2f} "
              f"mean {100 * sum(kv) / max(1, len(kv)):+.2f}c | removed PF {pf([net(e) for e in rem]):.2f} n={len(rem)} net {100 * sum(net(e) for e in rem) / max(1, len(rem)):+.2f}c")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["fetch"] and len(a) == 3:
        fetch(int(a[1]), int(a[2]))
    elif a == ["run"]:
        score([("A discovery (Aug to Sep 25)", 0, A_END), ("B seen (Sep 26 to Oct 26)", A_END, B_END)])
    elif a == ["holdout"]:
        score([("C forward holdout (from Oct 27)", B_END, 2 ** 31)])
    else:
        print(__doc__)
