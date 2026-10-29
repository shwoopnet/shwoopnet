"""CORR1 (README, Pre-registration: CORR1): G3H1 and G3H2 re-read on a look-ahead-free hourly ladder file. Research only.
    python -m scalper.corr1 fetch   (resumable; strikes chosen from quotes 55 to 52 minutes before each close)
    python -m scalper.corr1 run     (once)
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from collections import defaultdict

from . import api, backfill
from . import gen3
from .lad1 import chunks
from .paths import DATA_DIR

DB = DATA_DIR / "lad2.sqlite"
SERIES, DAYS, PAUSE = "KXBTCD", 30, 0.4
PROBE_S = (3300, 3120)   # 55 to 52 minutes before the close: before any G3H1 or G3H2 entry
WINDOW_S = (3300, 60)
RESULT = DATA_DIR / "corr1_result.txt"


def fetch(shard=0, shards=1):
    db = sqlite3.connect(DB if shards == 1 else DATA_DIR / f"lad2_{shard}.sqlite")
    db.executescript(backfill.SCHEMA)
    done = {r[0] for r in db.execute("SELECT DISTINCT close_ts FROM market")}
    lad1_closes = sorted({r[0] for r in sqlite3.connect(DATA_DIR / "lad1.sqlite").execute("SELECT DISTINCT close_ts FROM market")})
    lo, hi = lad1_closes[0], lad1_closes[-1]
    listed = list(api.settled_markets(SERIES, lo - 3600, hi + 3600))
    by_close = defaultdict(list)
    for m in listed:
        c = backfill.iso_ts(m.get("close_time"))
        if c is not None and lo <= c <= hi and m.get("result") in ("yes", "no"):
            by_close[c].append(m)
    print(f"{len(listed)} markets, {len(by_close)} closes ({len(lad1_closes)} in lad1); {len(by_close) - len(done)} to fetch", flush=True)
    for n, close_ts in enumerate(sorted(by_close)[shard::shards]):
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
    print("done", db.execute("SELECT COUNT(*) FROM market").fetchone()[0], "markets", flush=True)


def merge():
    db = sqlite3.connect(DB)
    db.executescript(backfill.SCHEMA)
    for f in sorted(DATA_DIR.glob("lad2_*.sqlite")):
        db.execute(f"ATTACH DATABASE '{f}' AS s")
        db.execute("INSERT OR REPLACE INTO market SELECT * FROM s.market")
        db.execute("INSERT OR REPLACE INTO candle SELECT * FROM s.candle")
        db.commit(); db.execute("DETACH DATABASE s")
    print("merged", db.execute("SELECT COUNT(DISTINCT close_ts), COUNT(*) FROM market").fetchone(), flush=True)


def run():
    if RESULT.exists():
        print("Refusing to run again"); return
    import numpy as np
    fz = json.loads((DATA_DIR.parent / "studies" / "gen3_survivors_FROZEN_2026-10-29.json").read_text())["survivors"]
    gen3.DB = DB
    gen3.NPZ = DATA_DIR / "corr1_rows.npz"
    lines = ["CORR1: G3H1 and G3H2 on the look-ahead-free file (strikes chosen 55 to 52 minutes before the close)"]
    res = {}
    for name, hold in (("disc+valid", False), ("holdout", True)):
        gen3.build(holdout=hold)
        z = np.load(DATA_DIR / ("gen3_hold_rows.npz" if hold else "corr1_rows.npz")); D = {k: z[k] for k in z.files}
        if hold:
            splits = {"holdout": np.ones(len(D["X"]), bool)}
        else:
            splits = {"discovery": D["day"] < gen3.DISC_D, "validation": (D["day"] >= gen3.DISC_D) & (D["day"] < gen3.VAL_D)}
        for wn, sp in splits.items():
            for k, s in enumerate(fz):
                s["conds"] = [tuple(c) for c in s["conds"]]
                net, days, _, cl, zv = gen3.evaluate(D, s, sp); st = gen3.stats(net, days, cl)
                st["pfs"] = gen3.pf(gen3.evaluate(D, s, sp, m=1.2)[0]); st["pf1"] = gen3.pf(gen3.evaluate(D, s, sp, c=1)[0]); st["zv"] = zv
                res[(k, wn)] = st
                lines.append(f"  {'G3H1 (TP +3c)' if gen3.EXITS[s['ex']][1] == 0.03 else 'G3H2 (TP +8c)'} {wn}: PF {st['pf']:.2f} (1 contract {st['pf1']:.2f}, stress {st['pfs']:.2f}) n={st['n']} closes {st['closes']} days {st['days']} mean {st['mean_c']:+.2f}c z {st['z']:+.2f} zero-volume {zv:.0%}")
    mins = {"discovery": (150, 10), "validation": (60, 6), "holdout": (40, 5)}
    verdicts = []
    for k, s in enumerate(fz):
        ok = all(res[(k, w)]["pf"] >= 1.5 and res[(k, w)]["n"] >= mins[w][0] and res[(k, w)]["days"] >= mins[w][1] and res[(k, w)]["pfs"] >= 1.2 and res[(k, w)]["zv"] <= 0.2 for w in mins) and res[(k, "validation")]["z"] >= 5.17
        verdicts.append(f"{gen3.desc(s)}: {'NOT_YET_FALSIFIED' if ok else 'FALSIFIED'}")
    lines.insert(1, "VERDICTS: " + " | ".join(verdicts))
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "fetch":
        fetch(*(int(x) for x in sys.argv[2:4])) if len(sys.argv) >= 4 else fetch()
    else:
        {"run": run, "merge": merge}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
