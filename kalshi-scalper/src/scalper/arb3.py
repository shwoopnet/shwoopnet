"""ARB3 (README, Pre-registration: ARB3): deadline-ladder locks ("before D1" vs "before D2") across every open Kalshi event. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
Usage: python -m scalper.arb3 scan (12 times, at least 15 minutes apart)   then   python -m scalper.arb3 report (once)
"""
from __future__ import annotations

import re
import sqlite3
import sys
import time
from datetime import datetime

from . import api
from .arb2 import fee, f, q, MIN_LOCK, MIN_CAP, CAP, PERSIST_S, MIN_SCANS
from .paths import DATA_DIR

DB = DATA_DIR / "arb3.sqlite"
RESULT = DATA_DIR / "arb3_result.txt"
MIN_YEARLY = 0.05
MONTHS = r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b"


def norm(t):
    t = (t or "").lower()
    return re.sub(r"\s+", " ", re.sub(MONTHS, "", re.sub(r"[0-9]", "", t))).strip()


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def pairs(ms, now):
    out = []
    ok = [m for m in ms if m.get("close_time") and re.search(r"before| by ", (m.get("rules_primary") or "").lower())]
    for i, a in enumerate(ok):
        for b in ok[i + 1:]:
            if a.get("strike_type") != b.get("strike_type") or f(a, "floor_strike") != f(b, "floor_strike") or f(a, "cap_strike") != f(b, "cap_strike"):
                continue
            if a["close_time"] == b["close_time"] or norm(a.get("rules_primary")) != norm(b.get("rules_primary")):
                continue
            early, late = (a, b) if ts(a["close_time"]) < ts(b["close_time"]) else (b, a)
            bid, ask = q(early)[0], q(late)[1]
            if not (0 < bid < 1 and 0 < ask < 1):
                continue
            lock = bid - ask - fee(ask) - fee(1 - bid)
            cost = ask + (1 - bid) + fee(ask) + fee(1 - bid)
            years = max((ts(late["close_time"]) - now) / (365.25 * 86400), 1 / 365.25)
            out.append({"key": early["ticker"] + "|" + late["ticker"], "lock": lock, "cap": min(q(late)[3], q(early)[2]), "yearly": lock / cost / years})
    return out


def scan():
    db = sqlite3.connect(DB)
    db.executescript("""CREATE TABLE IF NOT EXISTS scan(scan_id INTEGER PRIMARY KEY, ts INTEGER, n_events INTEGER, n_pairs INTEGER);
CREATE TABLE IF NOT EXISTS row(scan_id INTEGER, event TEXT, key TEXT, lock REAL, cap REAL, yearly REAL, PRIMARY KEY(scan_id, key));""")
    now = time.time(); cur = None; n = 0; rows = []
    while True:
        p = {"status": "open", "with_nested_markets": "true", "limit": 200}
        if cur:
            p["cursor"] = cur
        try:
            d = api._get("/events", p)
        except Exception:
            time.sleep(5); continue
        for e in d.get("events", []):
            n += 1
            ms = [m for m in e.get("markets", []) if m.get("status") == "active"]
            if len(ms) >= 2:
                rows += [(e["event_ticker"], r) for r in pairs(ms, now)]
        cur = d.get("cursor")
        if not cur:
            break
    sid = db.execute("SELECT COALESCE(MAX(scan_id), 0) FROM scan").fetchone()[0] + 1
    db.execute("INSERT INTO scan VALUES(?,?,?,?)", (sid, int(now), n, len(rows)))
    db.executemany("INSERT OR REPLACE INTO row VALUES(?,?,?,?,?,?)", [(sid, ev, r["key"], r["lock"], r["cap"], r["yearly"]) for ev, r in rows])
    db.commit()
    opp = [(ev, r) for ev, r in rows if r["lock"] >= MIN_LOCK and r["cap"] >= MIN_CAP and r["yearly"] >= MIN_YEARLY]
    best = max((r for _, r in rows), key=lambda r: r["lock"], default=None)
    print(f"scan {sid}: {n} events, {len(rows)} deadline pairs, {len(opp)} opportunities; best lock {best and round(100 * best['lock'], 2)}c", flush=True)
    for ev, r in opp:
        print("   OPPORTUNITY", ev, r, flush=True)


def report():
    if RESULT.exists():
        print("Refusing to run again"); return
    db = sqlite3.connect(DB)
    scans = db.execute("SELECT scan_id, ts, n_events, n_pairs FROM scan ORDER BY ts").fetchall()
    seen = {}
    for sid, t, *_ in scans:
        for ev, key, lock, cap, yr in db.execute("SELECT event, key, lock, cap, yearly FROM row WHERE scan_id=?", (sid,)):
            if lock >= MIN_LOCK and cap >= MIN_CAP and yr >= MIN_YEARLY:
                seen.setdefault(key, []).append((t, lock, cap, yr, ev))
    pers = {k: v for k, v in seen.items() if v[-1][0] - v[0][0] >= PERSIST_S}
    span = max((scans[-1][1] - scans[0][1]) / 86400, 1 / 24) if scans else 1
    value = sum(v[0][1] * min(v[0][2], CAP) for v in pers.values())
    locks = sorted(r[0] for r in db.execute("SELECT lock FROM row"))
    lines = [f"ARB3: {len(scans)} scans over {(scans[-1][1] - scans[0][1]) / 3600:.1f} h; deadline pairs per scan {min(s[3] for s in scans)} to {max(s[3] for s in scans)}; lock median {100 * locks[len(locks) // 2]:+.2f}c, best {100 * locks[-1]:+.2f}c; opportunities {len(seen)}, persistent {len(pers)}"]
    for k, v in pers.items():
        lines.append(f"  PERSISTENT {k}: lock {100 * v[0][1]:.2f}c capacity {v[0][2]:.0f} yearly {100 * v[0][3]:.1f}%, seen {len(v)} times")
    verdict = "NOT_ENOUGH_DATA" if len(scans) < MIN_SCANS else ("NOT_YET_FALSIFIED (pending a rules check of each pair)" if len(pers) >= 3 and value / span >= 1.0 else "FALSIFIED")
    lines.insert(0, f"VERDICT {verdict}; persistent pairs {len(pers)}, capacity-limited value ${value:.2f} over {span:.2f} days")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    {"scan": scan, "report": report}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
