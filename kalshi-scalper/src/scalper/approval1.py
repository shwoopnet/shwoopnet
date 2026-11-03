"""APPROVAL1 (workers/APPROVAL1_REGISTRATION.md): cheap side only in the RCP approval and VoteHub generic ballot daily ladders.
Research only: nothing here places an order. Usage: python -m scalper.approval1 span|fetch|gate|run
The frozen last third of the span (by date) is dropped in memory at listing time and never stored or scored.
Cache lives outside the repo. No favourite-side result is computed or printed anywhere (owner rule, Nov 3)."""
from __future__ import annotations

import math
import os
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from . import api, backfill
from .calibration import cluster_mean_z

CACHE = Path(os.environ.get("APPROVAL1_CACHE", "/tmp/claude-0/-home-user-shwoopnet/026f6e8f-6dc4-5e3b-8c3b-e0089b12fb94/scratchpad/approval1"))
DB = CACHE / "approval1.sqlite"
SERIES = ("KXTRUMPAPPROVE", "KXVHGCB")
SIGMA_FLOOR = {"KXTRUMPAPPROVE": 0.15, "KXVHGCB": 0.25}
SPAN_LO = int(datetime(2026, 5, 1, tzinfo=timezone.utc).timestamp())
SPAN_HI = int(datetime(2026, 11, 3, tzinfo=timezone.utc).timestamp())      # closes up to 2026-11-02 UTC inclusive
LOOK_BEFORE_S = 23 * 3600
HALF = 0.05
ASK_MIN, ASK_MAX, RATIO, MAX_PER_EVENT = 0.03, 0.30, 3.0, 2
C = 10
MIN_TRADES = 150
BATCH = 20
HIST_N, MIN_HIST, SIG_N, MIN_SIG = 21, 21, 30, 20


def ncdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def fee_per_contract(p: float, mult: float = 1.0) -> float:
    """7% x C x p x (1-p), rounded up to the cent for the order, per contract."""
    return math.ceil(round(0.07 * mult * C * p * (1 - p) * 100, 9)) / 100 / C


def num(x):
    try:
        return float(str(x).replace("%", "").replace("$", "").replace(",", "")) if x not in (None, "") else None
    except ValueError:
        return None


def yes_by_value(stype, fl, cp, v) -> bool | None:
    """Does a recorded one-decimal value fall inside the bracket (the consistency gate's reference)."""
    if v is None:
        return None
    if stype == "less":
        return v < cp - 1e-9 if cp is not None else None
    if stype == "greater":
        return v > fl + 1e-9 if fl is not None else None
    if stype == "between":
        return fl - 1e-9 <= v <= cp + 1e-9 if fl is not None and cp is not None else None
    return None


def p_yes(stype, fl, cp, mu, sd) -> float | None:
    """P(round(X,1) in bracket) for X ~ N(mu, sd), with the half-step correction."""
    if stype == "less" and cp is not None:
        return ncdf((cp - HALF - mu) / sd)
    if stype == "greater" and fl is not None:
        return 1 - ncdf((fl + HALF - mu) / sd)
    if stype == "between" and fl is not None and cp is not None:
        return ncdf((cp + HALF - mu) / sd) - ncdf((fl - HALF - mu) / sd)
    return None


def connect() -> sqlite3.Connection:
    CACHE.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB)
    db.executescript("""CREATE TABLE IF NOT EXISTS market(ticker TEXT PRIMARY KEY, series TEXT, close_ts INTEGER, result TEXT, strike_type TEXT, floor REAL, cap REAL, value TEXT);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INTEGER, bid REAL, ask REAL, PRIMARY KEY(ticker, end_ts));
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);""")
    return db


def span(series: str) -> tuple[int, int]:
    """(first date used, frozen-from ts). Reads the listing only to take the earliest close time; nothing else is kept."""
    lo = None
    for m in api.settled_markets(series, SPAN_LO, SPAN_HI):
        t = backfill.iso_ts(m.get("close_time"))
        if t and (lo is None or t < lo):
            lo = t
    if lo is None:
        raise SystemExit(f"{series}: no settled markets")
    lo_day = lo - lo % 86400
    days = (SPAN_HI - lo_day) // 86400
    frozen_from = lo_day + (days * 2 // 3) * 86400
    return lo_day, frozen_from


def fetch() -> None:
    db = connect()
    for series in SERIES:
        lo_day, frozen_from = span(series)
        db.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (series + ":lo", str(lo_day)))
        db.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (series + ":frozen", str(frozen_from)))
        db.commit()
        print(f"{series}: span from {datetime.fromtimestamp(lo_day, timezone.utc):%Y-%m-%d}, frozen from {datetime.fromtimestamp(frozen_from, timezone.utc):%Y-%m-%d}", flush=True)
        have = {r[0] for r in db.execute("SELECT ticker FROM market")}
        listed = []
        for m in api.settled_markets(series, lo_day, frozen_from - 1):       # the frozen third is not requested
            t = backfill.iso_ts(m.get("close_time"))
            if m.get("result") in ("yes", "no") and t and t < frozen_from and m["ticker"] not in have:
                listed.append((t, m))
        print(f"{series}: {len(listed)} settled markets to fetch", flush=True)
        by_close: dict = defaultdict(list)
        for t, m in listed:
            by_close[t].append(m)
        n = 0
        for t in sorted(by_close):
            ms = by_close[t]
            for i in range(0, len(ms), BATCH):
                chunk = ms[i:i + BATCH]
                got = api._get("/markets/candlesticks", {"market_tickers": ",".join(m["ticker"] for m in chunk), "start_ts": t - LOOK_BEFORE_S - 4 * 3600,
                                                          "end_ts": t - LOOK_BEFORE_S, "period_interval": 60})
                by_t = {x.get("market_ticker"): x.get("candlesticks", []) for x in got.get("markets", [])}
                for m in chunk:
                    for c in by_t.get(m["ticker"], []):
                        r = backfill.parse_candle(c, m["ticker"], series)
                        if r:
                            db.execute("INSERT OR REPLACE INTO candle VALUES(?,?,?,?)", (m["ticker"], r[2], r[6], r[10]))
                    db.execute("INSERT OR REPLACE INTO market VALUES(?,?,?,?,?,?,?,?)", (m["ticker"], series, t, m["result"], m.get("strike_type"),
                                                                                        m.get("floor_strike"), m.get("cap_strike"), m.get("expiration_value")))
                    n += 1
            db.commit()
            time.sleep(0.4)
        print(f"{series}: stored {n}", flush=True)
    print("done", flush=True)


def load(db):
    q: dict = defaultdict(dict)
    for t, e, b, a in db.execute("SELECT ticker, end_ts, bid, ask FROM candle"):
        q[t][e] = (b, a)
    ev: dict = defaultdict(lambda: defaultdict(list))
    for t, s, ct, res, st_, fl, cp, v in db.execute("SELECT ticker, series, close_ts, result, strike_type, floor, cap, value FROM market"):
        ev[s][ct].append({"ticker": t, "result": res, "type": st_, "floor": fl, "cap": cp, "value": num(v), "q": q.get(t, {})})
    return ev


def event_value(ms) -> float | None:
    vals = [m["value"] for m in ms if m["value"] is not None]
    return vals[0] if vals else None


def gate() -> dict:
    db = connect()
    ev = load(db)
    out = {}
    for s in SERIES:
        ok = tot = 0
        for ct, ms in ev[s].items():
            for m in ms:
                y = yes_by_value(m["type"], m["floor"], m["cap"], m["value"])
                if y is None:
                    continue
                tot += 1
                ok += (y == (m["result"] == "yes"))
        days = sorted(ev[s])
        gaps = defaultdict(int)
        for a, b in zip(days, days[1:]):
            gaps[round((b - a) / 3600)] += 1
        out[s] = {"consistent": ok, "total": tot, "share": ok / tot if tot else 0.0, "events": len(days), "gap_hours_hist": dict(sorted(gaps.items()))}
        print(s, out[s], flush=True)
    return out


def scored_events(ev_s: dict, series: str):
    """Yield (close_ts, mu, sd, markets) for events with a previous event 24h +- 1h earlier and >= 21 earlier consecutive values."""
    days = sorted(ev_s)
    vals = {d: event_value(ev_s[d]) for d in days}
    for i, d in enumerate(days):
        if i == 0 or abs((d - days[i - 1]) - 86400) > 3600:
            continue
        # earlier consecutive chain ending at the previous event
        j = i - 1
        seq = []
        while j >= 0 and vals[days[j]] is not None:
            seq.append(vals[days[j]])
            if j > 0 and abs((days[j] - days[j - 1]) - 86400) > 3600:
                break
            j -= 1
        seq = seq[::-1]
        if len(seq) < MIN_HIST:
            continue
        ch = [b - a for a, b in zip(seq, seq[1:])][-SIG_N:]
        if len(ch) < MIN_SIG:
            continue
        m_ = sum(ch) / len(ch)
        sd = max(math.sqrt(sum((x - m_) ** 2 for x in ch) / len(ch)), SIGMA_FLOOR[series])
        yield d, seq[-1], sd, ev_s[d]


def look_quote(m, close_ts):
    lim = close_ts - LOOK_BEFORE_S
    ends = [e for e in m["q"] if e <= lim]
    if not ends:
        return None
    b, a = m["q"][max(ends)]
    return (b, a) if b is not None and a is not None else None


def sides_at_look(m, close_ts):
    """Cheap sides only: (side, ask) for ask in [0.03, 0.30]. Nothing above the limit is ever returned."""
    q = look_quote(m, close_ts)
    if q is None:
        return []
    b, a = q
    out = []
    for side, ask in (("yes", a), ("no", 1 - b)):
        ask = round(ask, 4)
        if ASK_MIN <= ask <= ASK_MAX:
            out.append((side, ask))
    return out


def trade_rows(ev_s: dict, series: str):
    """(close_ts, ticker, side, ask, model_p, won, treated) for every cheap side at the look."""
    rows = []
    for d, mu, sd, ms in scored_events(ev_s, series):
        cands = []
        for m in ms:
            py = p_yes(m["type"], m["floor"], m["cap"], mu, sd)
            if py is None:
                continue
            for side, ask in sides_at_look(m, d):
                p = py if side == "yes" else 1 - py
                won = (m["result"] == side)
                cands.append([d, m["ticker"], side, ask, p, won, False])
        sel = sorted((c for c in cands if c[4] >= RATIO * c[3]), key=lambda c: (-c[4] / c[3], c[1]))[:MAX_PER_EVENT]
        for c in sel:
            c[6] = True
        rows += cands
    return rows


def net(row, mult=1.0):
    _, _, _, ask, _, won, _ = row
    return (1.0 if won else 0.0) - ask - fee_per_contract(ask, mult)


def stats(rows, mult=1.0):
    n = len(rows)
    if not n:
        return {"n": 0}
    nets = [net(r, mult) for r in rows]
    gains = sum(x for x in nets if x > 0)
    losses = -sum(x for x in nets if x < 0)
    mean, se, z = cluster_mean_z([(str(r[0] // 86400), x) for r, x in zip(rows, nets)])
    return {"n": n, "days": len({r[0] // 86400 for r in rows}), "win": sum(r[5] for r in rows) / n, "price": sum(r[3] for r in rows) / n,
            "net_c": 100 * mean, "z": z, "pf": gains / losses if losses > 0 else float("inf")}


def run() -> None:
    db = connect()
    ev = load(db)
    lines = []
    allt = []
    for s in SERIES:
        rows = trade_rows(ev[s], s)
        lo = int(db.execute("SELECT v FROM meta WHERE k=?", (s + ":lo",)).fetchone()[0])
        fz = int(db.execute("SELECT v FROM meta WHERE k=?", (s + ":frozen",)).fetchone()[0])
        mid = lo + (fz - lo) // 2
        tr = [r for r in rows if r[6]]
        ct = rows
        w1 = [r for r in tr if r[0] < mid]
        w2 = [r for r in tr if r[0] >= mid]
        print(s, "treated", stats(tr), "x1.2", stats(tr, 1.2), flush=True)
        print(s, "W1", stats(w1), "W2", stats(w2), flush=True)
        print(s, "control (all cheap sides)", stats(ct), flush=True)
        b = defaultdict(list)
        for r in tr:
            b["ratio<5" if r[4] / r[3] < 5 else "ratio>=5"].append(r)
        for k in sorted(b):
            print(s, k, stats(b[k]), flush=True)
        allt += tr
    print("pooled treated", stats(allt), "events", len({(r[0]) for r in allt}), flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"fetch": fetch, "gate": gate, "run": run}.get(cmd, lambda: print(__doc__))()
