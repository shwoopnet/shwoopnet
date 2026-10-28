"""ARB2 (README, Pre-registration: ARB2): full-set and crossed-ladder locks across every open Kalshi event. Research only: nothing here places an order.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
Usage: python -m scalper.arb2 scan (one snapshot; 12 times, at least 15 minutes apart)   then   python -m scalper.arb2 report (once)
"""
from __future__ import annotations

import json
import math
import sqlite3
import sys
import time

from . import api
from .paths import DATA_DIR

DB = DATA_DIR / "arb2.sqlite"
RESULT = DATA_DIR / "arb2_result.txt"
C, MIN_LOCK, MIN_CAP, CAP, PERSIST_S, MIN_SCANS = 10, 0.01, 10.0, 50.0, 15 * 60, 8
LOW, HIGH = ("less", "less_or_equal"), ("greater", "greater_or_equal")


def fee(p):
    return math.ceil(0.07 * C * p * (1 - p) * 100 - 1e-9) / 100 / C


def f(m, k):
    try:
        return float(m.get(k) or 0)
    except (TypeError, ValueError):
        return 0.0


def q(m):
    return f(m, "yes_bid_dollars"), f(m, "yes_ask_dollars"), f(m, "yes_bid_size_fp"), f(m, "yes_ask_size_fp")


def meets(a, b, whole):
    return abs(b - a) < 1e-9 or (0 < b - a <= (1.0 if whole else 0.011) + 1e-9)


def full_set(ms):
    lo = [m for m in ms if m.get("strike_type") in LOW]
    hi = [m for m in ms if m.get("strike_type") in HIGH]
    br = sorted((m for m in ms if m.get("strike_type") == "between"), key=lambda m: f(m, "floor_strike"))
    if len(lo) != 1 or len(hi) != 1 or not br or len(lo) + len(hi) + len(br) != len(ms):
        return None
    strikes = [f(lo[0], "cap_strike"), f(hi[0], "floor_strike")] + [f(m, k) for m in br for k in ("floor_strike", "cap_strike")]
    whole = all(abs(s - round(s)) < 1e-9 for s in strikes)
    chain = [f(lo[0], "cap_strike")]
    for m in br:
        if not meets(chain[-1], f(m, "floor_strike"), whole):
            return None
        chain.append(f(m, "cap_strike"))
    if not meets(chain[-1], f(hi[0], "floor_strike"), whole):
        return None
    legs = lo + br + hi
    asks = [q(m)[1] for m in legs]
    if any(a <= 0 or a >= 1 for a in asks):
        return None
    lock = 1 - sum(asks) - sum(fee(a) for a in asks)
    return {"kind": "full", "key": "full", "legs": len(legs), "lock": lock, "cap": min(q(m)[3] for m in legs), "sum": sum(asks)}


def stem(m):
    """One ladder = same ticker prefix and the same letters in the last segment (KXBTCD-26OCT2817-T113000 and -T114000 match;
    spread markets for two different teams, props for two players, or one strike on two dates do not)."""
    pre, _, last = m["ticker"].rpartition("-")
    return pre, "".join(ch for ch in last if ch.isalpha())


def crossed(ms):
    out = []
    groups = {}
    for m in ms:
        groups.setdefault(stem(m), []).append(m)
    for types, sign in ((HIGH, 1), (LOW, -1)):
      for g in groups.values():
        sk = "floor_strike" if sign == 1 else "cap_strike"
        lad = sorted((m for m in g if m.get("strike_type") in types and m.get(sk) is not None), key=lambda m: f(m, sk))
        if len({f(m, sk) for m in lad}) != len(lad):
            continue
        best = None
        for i, a in enumerate(lad):
            for b in lad[i + 1:]:
                # sign 1: P(above K) falls with K, so buy YES at the lower strike (a), NO at the higher (b)
                cheap, dear = (a, b) if sign == 1 else (b, a)
                ask, bid = q(cheap)[1], q(dear)[0]
                if not (0 < ask < 1 and 0 < bid < 1):
                    continue
                lock = bid - ask - fee(ask) - fee(1 - bid)
                cap = min(q(cheap)[3], q(dear)[2])
                if best is None or lock > best["lock"]:
                    best = {"kind": "ladder", "key": cheap["ticker"] + "|" + dear["ticker"], "legs": 2, "lock": lock, "cap": cap, "sum": bid - ask}
        if best:
            out.append(best)
    return out


def scan():
    db = sqlite3.connect(DB)
    db.executescript("""CREATE TABLE IF NOT EXISTS scan(scan_id INTEGER PRIMARY KEY, ts INTEGER, n_events INTEGER, n_full INTEGER, n_ladder INTEGER);
CREATE TABLE IF NOT EXISTS row(scan_id INTEGER, event TEXT, kind TEXT, key TEXT, legs INTEGER, lock REAL, cap REAL, sum REAL, PRIMARY KEY(scan_id, event, kind, key));""")
    ts = int(time.time()); cur = None; n = 0; rows = []
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
            if "15M" in (e.get("series_ticker") or ""):
                continue
            r = full_set(ms)
            if r: rows.append((e["event_ticker"], r))
            for r in crossed(ms):
                rows.append((e["event_ticker"], r))
        cur = d.get("cursor")
        if not cur:
            break
    sid = db.execute("SELECT COALESCE(MAX(scan_id), 0) FROM scan").fetchone()[0] + 1
    nf = sum(1 for _, r in rows if r["kind"] == "full"); nl = len(rows) - nf
    db.execute("INSERT INTO scan VALUES(?,?,?,?,?)", (sid, ts, n, nf, nl))
    db.executemany("INSERT OR REPLACE INTO row VALUES(?,?,?,?,?,?,?,?)", [(sid, ev, r["kind"], r["key"], r["legs"], r["lock"], r["cap"], r["sum"]) for ev, r in rows])
    db.commit()
    opp = [(ev, r) for ev, r in rows if r["lock"] >= MIN_LOCK and r["cap"] >= MIN_CAP]
    best = {k: max((r for _, r in rows if r["kind"] == k), key=lambda r: r["lock"], default=None) for k in ("full", "ladder")}
    print(f"scan {sid}: {n} events, {nf} exhaustive range events, {nl} ladders, {len(opp)} opportunities; best full {best['full'] and round(100 * best['full']['lock'], 2)}c, best ladder {best['ladder'] and round(100 * best['ladder']['lock'], 2)}c", flush=True)
    for ev, r in opp:
        print("   OPPORTUNITY", ev, json.dumps(r), flush=True)


def report():
    if RESULT.exists():
        print("Refusing to run again"); return
    db = sqlite3.connect(DB)
    scans = db.execute("SELECT scan_id, ts, n_events, n_full, n_ladder FROM scan ORDER BY ts").fetchall()
    seen = {}
    for sid, ts, *_ in scans:
        for ev, kind, key, legs, lock, cap, s in db.execute("SELECT event, kind, key, legs, lock, cap, sum FROM row WHERE scan_id=?", (sid,)):
            if lock >= MIN_LOCK and cap >= MIN_CAP:
                seen.setdefault((ev, kind, key), []).append((ts, lock, cap))
    pers = {k: v for k, v in seen.items() if v[-1][0] - v[0][0] >= PERSIST_S}
    span_days = max((scans[-1][1] - scans[0][1]) / 86400, 1 / 24) if scans else 1
    value = sum(v[0][1] * min(v[0][2], CAP) for v in pers.values())
    lines = [f"ARB2: {len(scans)} scans over {(scans[-1][1] - scans[0][1]) / 3600:.1f} h; events per scan {min(s[2] for s in scans)} to {max(s[2] for s in scans)}; exhaustive range events {min(s[3] for s in scans)} to {max(s[3] for s in scans)}; ladders {min(s[4] for s in scans)} to {max(s[4] for s in scans)}"]
    for kind in ("full", "ladder"):
        locks = sorted(r[0] for r in db.execute("SELECT lock FROM row WHERE kind=?", (kind,)))
        if locks:
            lines.append(f"  {kind}: {len(locks)} event-scans; lock median {100 * locks[len(locks) // 2]:+.2f}c, best {100 * locks[-1]:+.2f}c; opportunities {sum(1 for k in seen if k[1] == kind)}, persistent {sum(1 for k in pers if k[1] == kind)}")
    for k, v in pers.items():
        lines.append(f"  PERSISTENT {k}: first lock {100 * v[0][1]:.2f}c capacity {v[0][2]:.0f}, seen {len(v)} times")
    if len(scans) < MIN_SCANS:
        verdict = "NOT_ENOUGH_DATA"
    elif len(pers) >= 3 and value / span_days >= 1.0:
        verdict = "NOT_YET_FALSIFIED (pending the rules-text check of each lock)"
    else:
        verdict = "FALSIFIED"
    lines.insert(0, f"VERDICT {verdict}; persistent events {len(pers)}, capacity-limited value ${value:.2f} over {span_days:.2f} days")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    {"scan": scan, "report": report}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
