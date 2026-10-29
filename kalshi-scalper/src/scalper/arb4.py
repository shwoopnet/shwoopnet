"""ARB4 (README, Pre-registration: ARB4): range brackets against the "above" ladder at the same close, Bitcoin and Ethereum. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
Usage: python -m scalper.arb4 scan (12 times, at least 15 minutes apart)   then   python -m scalper.arb4 report (once)
"""
from __future__ import annotations

import sqlite3
import sys
import time

from . import api
from .arb2 import fee, f, q, MIN_LOCK, MIN_CAP, CAP, PERSIST_S, MIN_SCANS

from .paths import DATA_DIR

DB = DATA_DIR / "arb4.sqlite"
RESULT = DATA_DIR / "arb4_result.txt"
PAIRS = (("KXBTC", "KXBTCD"), ("KXETH", "KXETHD"))
MAX_BR = 5


def events(series):
    out, cur = [], None
    while True:
        p = {"series_ticker": series, "status": "open", "with_nested_markets": "true", "limit": 200}
        if cur:
            p["cursor"] = cur
        d = api._get("/events", p)
        out += d.get("events", [])
        cur = d.get("cursor")
        if not cur:
            return out


def ok(p):
    return 0 < p < 1


def locks(rng, lad):
    br = {round(f(m, "floor_strike"), 2): m for m in rng if m.get("strike_type") == "between"}
    ld = {round(f(m, "floor_strike") + 0.01, 2): m for m in lad if m.get("strike_type") == "greater"}
    out = []
    for k1, a in ld.items():
        chain, k = [], k1
        for _ in range(MAX_BR):
            m = br.get(k)
            if m is None or abs(f(m, "cap_strike") + 0.01 - (k + 100)) > 0.02 and abs(f(m, "cap_strike") - f(m, "floor_strike") - 99.99) > 0.02:
                break
            chain.append(m)
            k = round(f(m, "cap_strike") + 0.01, 2)
            b = ld.get(k)
            if b is None:
                continue
            legs = chain + [b]
            # (+) YES above(k1), NO on the rest
            bids = [q(m)[0] for m in legs]; ask1 = q(a)[1]
            if all(ok(x) for x in bids) and ok(ask1):
                lock = sum(bids) - ask1 - fee(ask1) - sum(fee(1 - x) for x in bids)
                cap = min([q(a)[3]] + [q(m)[2] for m in legs])
                out.append(("plus", a["ticker"] + "|" + b["ticker"], len(chain), lock, cap))
            # (-) YES on the rest, NO above(k1)
            asks = [q(m)[1] for m in legs]; bid1 = q(a)[0]
            if all(ok(x) for x in asks) and ok(bid1):
                lock = bid1 - sum(asks) - fee(1 - bid1) - sum(fee(x) for x in asks)
                cap = min([q(a)[2]] + [q(m)[3] for m in legs])
                out.append(("minus", a["ticker"] + "|" + b["ticker"], len(chain), lock, cap))
    return out


def scan():
    db = sqlite3.connect(DB)
    db.executescript("""CREATE TABLE IF NOT EXISTS scan(scan_id INTEGER PRIMARY KEY, ts INTEGER, n_closes INTEGER, n_combos INTEGER);
CREATE TABLE IF NOT EXISTS row(scan_id INTEGER, kind TEXT, key TEXT, nbr INTEGER, lock REAL, cap REAL, PRIMARY KEY(scan_id, kind, key));""")
    now = int(time.time()); rows = []; nclose = 0
    for rs, ls in PAIRS:
        try:
            R, L = events(rs), events(ls)
        except Exception:
            time.sleep(5); R, L = events(rs), events(ls)
        byc = {}
        for e in L:
            ms = [m for m in e["markets"] if m.get("status") == "active"]
            if ms: byc[ms[0]["close_time"]] = ms
        for e in R:
            ms = [m for m in e["markets"] if m.get("status") == "active"]
            if ms and ms[0]["close_time"] in byc:
                nclose += 1
                rows += locks(ms, byc[ms[0]["close_time"]])
    sid = db.execute("SELECT COALESCE(MAX(scan_id), 0) FROM scan").fetchone()[0] + 1
    db.execute("INSERT INTO scan VALUES(?,?,?,?)", (sid, now, nclose, len(rows)))
    db.executemany("INSERT OR REPLACE INTO row VALUES(?,?,?,?,?,?)", [(sid,) + r for r in rows])
    db.commit()
    opp = [r for r in rows if r[3] >= MIN_LOCK and r[4] >= MIN_CAP]
    best = max(rows, key=lambda r: r[3], default=None)
    print(f"scan {sid}: {nclose} coincident closes, {len(rows)} combinations, {len(opp)} opportunities; best {best and (best[0], best[1], best[2], round(100 * best[3], 2), best[4])}", flush=True)
    for r in opp:
        print("   OPPORTUNITY", r, flush=True)


def report():
    if RESULT.exists():
        print("Refusing to run again"); return
    db = sqlite3.connect(DB)
    scans = db.execute("SELECT scan_id, ts, n_closes, n_combos FROM scan ORDER BY ts").fetchall()
    seen = {}
    for sid, t, *_ in scans:
        for kind, key, nbr, lock, cap in db.execute("SELECT kind, key, nbr, lock, cap FROM row WHERE scan_id=?", (sid,)):
            if lock >= MIN_LOCK and cap >= MIN_CAP:
                seen.setdefault((kind, key), []).append((t, lock, cap))
    pers = {k: v for k, v in seen.items() if v[-1][0] - v[0][0] >= PERSIST_S}
    span = max((scans[-1][1] - scans[0][1]) / 86400, 1 / 24) if scans else 1
    value = sum(v[0][1] * min(v[0][2], CAP) for v in pers.values())
    locks_ = sorted(r[0] for r in db.execute("SELECT lock FROM row"))
    lines = [f"ARB4: {len(scans)} scans over {(scans[-1][1] - scans[0][1]) / 3600:.1f} h; coincident closes per scan {min(s[2] for s in scans)} to {max(s[2] for s in scans)}; combinations {min(s[3] for s in scans)} to {max(s[3] for s in scans)}; lock median {100 * locks_[len(locks_) // 2]:+.2f}c, best {100 * locks_[-1]:+.2f}c; opportunities {len(seen)}, persistent {len(pers)}"]
    for k, v in pers.items():
        lines.append(f"  PERSISTENT {k}: lock {100 * v[0][1]:.2f}c capacity {v[0][2]:.0f}, seen {len(v)} times")
    verdict = "NOT_ENOUGH_DATA" if len(scans) < MIN_SCANS else ("NOT_YET_FALSIFIED (pending RULES1)" if len(pers) >= 3 and value / span >= 1.0 else "FALSIFIED")
    lines.insert(0, f"VERDICT {verdict}; persistent {len(pers)}, capacity-limited value ${value:.2f} over {span:.2f} days")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    {"scan": scan, "report": report}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
