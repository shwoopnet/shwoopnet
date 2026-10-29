"""LADL1 (README, Pre-registration: LADL1): L1's own rule on longer clocks (gold daily and weekly ladders, Bitcoin and Ethereum hourly
ladders), strikes chosen from quotes 30 to 27 minutes before the close. Research only; nothing here places an order.
    python -m scalper.ladl1 fetch   (resumable)
    python -m scalper.ladl1 run     (once)
"""
from __future__ import annotations

import math
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

from . import api, backfill
from .calibration import cluster_mean_z
from .gen1 import _norm_ppf
from .lad1 import chunks
from .paths import DATA_DIR

DB = DATA_DIR / "ladl1.sqlite"
RESULT = DATA_DIR / "ladl1_result.txt"
GROUPS = {"KXGOLDD": 200, "KXGOLDW": 400, "KXBTCD": 30, "KXETHD": 30}   # days of history
PROBE = (1800, 1620)
LOOKS = (600, 360)
BAND = (0.88, 0.97)
N_PRIOR = 438_605


def fetch():
    db = sqlite3.connect(DB)
    db.executescript("""CREATE TABLE IF NOT EXISTS mk(ticker TEXT PRIMARY KEY, series TEXT, close_ts INTEGER, result TEXT);
CREATE TABLE IF NOT EXISTS q(ticker TEXT, look INTEGER, bid REAL, ask REAL, PRIMARY KEY(ticker, look));
CREATE TABLE IF NOT EXISTS done(series TEXT, close_ts INTEGER, PRIMARY KEY(series, close_ts));""")
    now = int(time.time())
    for series, days in GROUPS.items():
        done = {r[0] for r in db.execute("SELECT close_ts FROM done WHERE series=?", (series,))}
        listed = list(api.settled_markets(series, now - days * 86400, now))
        by = defaultdict(list)
        for m in listed:
            c = backfill.iso_ts(m.get("close_time"))
            if c and m.get("result") in ("yes", "no"):
                by[c].append(m)
        print(series, len(listed), "markets", len(by), "closes", flush=True)
        for n, close in enumerate(sorted(by)):
            if close in done:
                continue
            keep = []
            for ch in chunks(by[close], 100):
                got = api.batch_candlesticks([m["ticker"] for m in ch], close - PROBE[0], close - PROBE[1])
                for m in ch:
                    rows = [r for r in (backfill.parse_candle(x, m["ticker"], series) for x in got.get(m["ticker"], [])) if r and r[6] is not None and r[10] is not None]
                    if rows and 0.01 <= (rows[-1][6] + rows[-1][10]) / 2 <= 0.99:
                        keep.append(m)
                time.sleep(0.35)
            for ch in chunks(keep, 100):
                got = api.batch_candlesticks([m["ticker"] for m in ch], close - LOOKS[0] - 120, close - LOOKS[1])
                for m in ch:
                    rows = {r[2]: r for r in (backfill.parse_candle(x, m["ticker"], series) for x in got.get(m["ticker"], [])) if r}
                    db.execute("INSERT OR REPLACE INTO mk VALUES(?,?,?,?)", (m["ticker"], series, close, m["result"]))
                    for look in LOOKS:
                        r = rows.get(close - look)
                        if r and r[6] is not None and r[10] is not None:
                            db.execute("INSERT OR REPLACE INTO q VALUES(?,?,?,?)", (m["ticker"], look, r[6], r[10]))
                time.sleep(0.35)
            db.execute("INSERT OR REPLACE INTO done VALUES(?,?)", (series, close))
            db.commit()
            if n % 50 == 0:
                print(f"  {series} {n}/{len(by)}", flush=True)
    print("done", flush=True)


def fee(p, c=1, m=1.0):
    return math.ceil(m * 0.07 * c * p * (1 - p) * 100 - 1e-9) / 100 / c


def run():
    if RESULT.exists():
        print("Refusing to run again"); return
    db = sqlite3.connect(DB)
    mk = {t: (s, c, r) for t, s, c, r in db.execute("SELECT ticker, series, close_ts, result FROM mk")}
    q = {(t, l): (b, a) for t, l, b, a in db.execute("SELECT ticker, look, bid, ask FROM q")}
    zbar = _norm_ppf(1 - 0.05 / (N_PRIOR + 8))
    lines = [f"LADL1: Bonferroni z bar {zbar:.2f}"]
    overlap = []
    for series in GROUPS:
        closes = sorted({c for s, c, _ in mk.values() if s == series})
        if not closes:
            lines.append(f"  {series}: no data"); continue
        cut = (closes[len(closes) // 3], closes[2 * len(closes) // 3])
        for look in LOOKS:
            W = {0: [], 1: [], 2: []}
            for t, (s, c, res) in mk.items():
                if s != series or (t, look) not in q:
                    continue
                b, a = q[(t, look)]
                if BAND[0] - 1e-9 <= a <= BAND[1] + 1e-9:
                    side, p = "yes", a
                elif BAND[0] - 1e-9 <= 1 - b <= BAND[1] + 1e-9:
                    side, p = "no", round(1 - b, 4)
                else:
                    continue
                won = 1.0 if res == side else 0.0
                w = 0 if c < cut[0] else (1 if c < cut[1] else 2)
                W[w].append((c, won - p - fee(p), won - p - fee(p, m=1.2), won - p - fee(p, 10)))
                if series == "KXGOLDD" and look == 360:
                    overlap.append((c, side))
            parts, ok = [], True
            for w in range(3):
                v = W[w]
                n_close = len({c for c, *_ in v})
                pfv = lambda xs: (sum(x for x in xs if x > 0) / -sum(x for x in xs if x < 0)) if any(x < 0 for x in xs) else 99.0
                net = [x for _, x, _, _ in v]; st = [y for _, _, y, _ in v]; n10 = [z for _, _, _, z in v]
                _, _, z = cluster_mean_z([(c, x) for c, x, _, _ in v]) if len(v) > 1 else (0, 0, 0.0)
                p = pfv(net) if net else 0.0
                parts.append(f"{['discovery', 'validation', 'holdout'][w]} PF {p:.2f} (10 contracts {pfv(n10) if n10 else 0:.2f}, stress {pfv(st) if st else 0:.2f}) n={len(v)} closes {n_close} mean {100 * sum(net) / max(len(net), 1):+.2f}c z {z:+.2f}")
                ok = ok and n_close >= 30 and p >= 1.5 and (pfv(st) if st else 0) >= 1.2 and (w != 1 or z >= zbar)
                if n_close < 30:
                    ok = None if ok is not False else False
            verdict = "NOT_ENOUGH_DATA" if any(len({c for c, *_ in W[w]}) < 30 for w in range(3)) and ok is not False else ("NOT_YET_FALSIFIED" if ok else "FALSIFIED")
            lines.append(f"  {series} at {look // 60} min: {verdict} | " + " | ".join(parts))
    lines.append(f"  gold overlap: LADL1 daily-ladder entries at 6 min before 21:00 UTC closes: {len(overlap)} (L1 gold trades KXGOLD15M in the window closing at the same 21:00 UTC; the side match needs L1's own order log, not on file here: reported as a count of shared windows only)")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    {"fetch": fetch, "run": run}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
