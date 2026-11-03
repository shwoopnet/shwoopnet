"""CALIB1 (README "CALIB1"; workers/CALIB1_REGISTRATION.md): a pooled, event-level calibration surface of the CHEAP side
(ask 3c to 30c) from candle caches that already exist. No Kalshi fetch, no order, no model, no threshold search.
Cheap side only (owner rule): no entry above 0.30 is ever built, counted, scored or printed.

Usage: python3 -I -m scalper.calib1 extract   build the entry table from the caches -> CALIB1_OUT/entries.jsonl; prints COUNTS ONLY (no outcome aggregate)
       python3 -I -m scalper.calib1 score     ONE run of the registered grid -> workers/CALIB1_RESULT.json (refuses a second run)
Caches (outside the repo): USWEEP1 sweep dir, USWEEP2 dir, USWEEP3 dir (CALIB1_SWEEP, CALIB1_US2, CALIB1_US3) and data/newlist1.sqlite.
Only development markets are in those caches (the frozen last thirds were never downloaded); NEWLIST1's frozen H part (close >= cuts t2) is dropped here.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import numpy as np
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORKERS, DATA = ROOT / "workers", ROOT / "data"
OUT = Path(os.environ.get("CALIB1_OUT", "/tmp/calib1"))
SRC = {
    "sweep": Path(os.environ.get("CALIB1_SWEEP", "/tmp/usweep1_cache")),
    "us2": Path(os.environ.get("CALIB1_US2", "/tmp/usweep2_cache")),
    "us3": Path(os.environ.get("CALIB1_US3", "/tmp/usweep3_cache")),
}

# ---- registered constants (workers/CALIB1_REGISTRATION.md) ----
ASK_LO, ASK_HI = 0.03, 0.30
BUCKETS = [(0.03, 0.05), (0.05, 0.10), (0.10, 0.15), (0.15, 0.20), (0.20, 0.30)]
BUCKET_NAMES = ["3-5c", "5-10c", "10-15c", "15-20c", "20-30c"]
FEE_RATE, C = 0.07, 10
LOOKS = {"H": (30, 15, 5), "D": (1440, 360, 60), "W": (4320, 1440, 360)}   # minutes before the anchor, as USWEEP1/2/3
AGE_LOOK_H, LATE_LEAD_H = (1, 3, 6), 3                                       # NEWLIST1's looks
MIN_EVENTS_HALF = 30
BOOT, SEED = 2000, 20261103
CATEGORIES = []          # filled in from the registration (see REGISTERED_CATEGORIES below)
REGISTERED_CATEGORIES: list[str] = []


def fee_per_contract(p: float, c: int = C) -> float:
    cents = math.ceil(round(FEE_RATE * c * p * (1 - p) * 100, 6))
    return cents / 100.0 / c


def net_per_contract(won: bool, p: float) -> float:
    return (1.0 if won else 0.0) - p - fee_per_contract(p)


def ask_bucket(p: float):
    """Index of the registered ask bucket, or None outside 3c-30c. Lower edge included, upper edge excluded, except 0.30 which is in the last bucket."""
    if p < ASK_LO - 1e-9 or p > ASK_HI + 1e-9:
        return None
    for i, (lo, hi) in enumerate(BUCKETS):
        if p < hi - 1e-9:
            return i if p >= lo - 1e-9 else None
    return len(BUCKETS) - 1


def ttc_bucket(minutes: float) -> str:
    if minutes <= 60:
        return "<=1h"
    if minutes <= 360:
        return "1-6h"
    if minutes <= 1440:
        return "6-24h"
    if minutes <= 4320:
        return "1-3d"
    return ">3d"


def life_class(life_s: float):
    if life_s <= 0:
        return None
    return "H" if life_s <= 4 * 3600 else ("D" if life_s <= 3 * 86400 else "W")


def norm_cat(c) -> str:
    return "Politics" if c == "Elections" else (c or "Other")


def event_of(ticker: str) -> str:
    return ticker.rsplit("-", 1)[0]


def cheap_side(bid, ask):
    """(side, price) for the side whose ask is in 3c-30c, else None. A two sided quote is required (0 < bid < ask < 1), as USWEEP1."""
    if bid is None or ask is None or not (0 < bid < ask < 1):
        return None
    for side, p in (("yes", ask), ("no", round(1 - bid, 4))):
        if ask_bucket(p) is not None:
            return side, p
    return None


def decision_quote(cs, target, interval):
    best = None
    for c in cs:
        if c[0] is None or c[0] > target:
            continue
        if best is None or c[0] > best[0]:
            best = c
    if best is None or target - best[0] > interval * 60:
        return None
    return best


def make_entry(src, series, cat, ticker, life_s, anchor, look_ts, side, p, result, look_tag):
    won = side == result
    return {"src": src, "series": series, "cat": norm_cat(cat), "life": life_class(life_s), "ttc": ttc_bucket((anchor - look_ts) / 60),
            "bk": ask_bucket(p), "ask": p, "won": 1 if won else 0, "fee": fee_per_contract(p), "net": net_per_contract(won, p),
            "event": event_of(ticker), "t": anchor, "market": ticker, "look": look_tag,
            "date": datetime.fromtimestamp(anchor, timezone.utc).strftime("%Y-%m-%d")}


# ---------------------------------------------------------------- extraction
def _jl(path):
    with open(path) as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def profile_class(rec):
    ms = [m for m in rec["markets"] if m[1] and m[2]]
    lives = sorted((m[3] or m[2]) - m[1] for m in ms if (m[3] or m[2]) > m[1])
    if not lives:
        return None
    return life_class(lives[len(lives) // 2] if len(lives) % 2 else (lives[len(lives) // 2 - 1] + lives[len(lives) // 2]) / 2)


def entries_candle_source(src, cdir):
    """sweep, us2, us3: census + candles + results of one USWEEP cache. Only markets that have a candle record are used (= development markets)."""
    cen = {}
    for r in _jl(cdir / "census.jsonl"):
        if r.get("markets"):
            cen.setdefault(r["ticker"], r)
    res = {}
    rpath = cdir / ("outcomes.jsonl" if src == "sweep" else "census_results.jsonl")
    for x in _jl(rpath):
        res.update(x["r"])
    meta = {}
    for s, r in cen.items():
        for m in r["markets"]:
            meta.setdefault(m[0], (s, m))
    cls = {s: profile_class(r) for s, r in cen.items()}
    seen, out = set(), []
    for x in _jl(cdir / "candles.jsonl"):
        t = x["t"]
        if t in seen or t not in meta or not x["c"]:
            continue
        seen.add(t)
        s, m = meta[t]
        k = cls.get(s)
        result = res.get(t)
        if k is None or result not in ("yes", "no"):
            continue
        open_ts, close_ts, anc = m[1], m[2], (m[3] or m[2])
        if not open_ts or not close_ts or not anc or anc <= open_ts:
            continue
        iv = x["iv"]
        for T in LOOKS[k]:
            target = anc - T * 60
            if target <= open_ts or target >= close_ts:
                continue
            q = decision_quote(x["c"], target, iv)
            if not q:
                continue
            cs = cheap_side(q[1], q[2])
            if cs:
                out.append(make_entry(src, s, cen[s].get("cat"), t, anc - open_ts, anc, target, cs[0], cs[1], result, f"T{T}"))
    return out


def entries_newlist1():
    cuts = json.loads((DATA / "newlist1_cuts.json").read_text())
    c = sqlite3.connect(str(DATA / "newlist1.sqlite"))
    res = dict(c.execute("select ticker, result from res"))
    mk = {r[0]: r for r in c.execute("select ticker, series, category, open_ts, close_ts from mk")}
    cds = {}
    for t, e, b, a in c.execute("select ticker, end_ts, bid, ask from cd order by ticker, end_ts"):
        cds.setdefault(t, []).append((e, b, a))
    out = []
    for t, cs in cds.items():
        if t not in mk or res.get(t) not in ("yes", "no"):
            continue
        _, s, cat, o, cl = mk[t]
        if not o or not cl or cl >= cuts["t2"]:          # H (frozen third) dropped by close time, as NEWLIST1
            continue
        looks = {}
        for h in AGE_LOOK_H:
            looks[f"A{h}h"] = next(((e, b, a) for e, b, a in cs if o + h * 3600 <= e < o + (h + 1) * 3600), None)
        late = None
        for e, b, a in cs:
            if e > cl - LATE_LEAD_H * 3600:
                break
            late = (e, b, a)
        looks["late"] = late
        for tag, q in looks.items():
            if q is None:
                continue
            sd = cheap_side(q[1], q[2])
            if sd:
                out.append(make_entry("newlist1", s, cat, t, cl - o, cl, q[0], sd[0], sd[1], res[t], tag))
    return out


def build_entries():
    allr = []
    for src in ("sweep", "us2", "us3"):
        part = entries_candle_source(src, SRC[src])
        for e in part:
            allr.append(e)
        print(f"  {src}: {len(part)} cheap-side entries", file=sys.stderr)
    part = entries_newlist1()
    print(f"  newlist1: {len(part)} cheap-side entries", file=sys.stderr)
    allr += part
    # one entry per (market, look decision time): the same market and look from two caches counts once (first source wins)
    out, seen = [], set()
    for e in allr:
        k = (e["market"], e["look"])
        if k in seen:
            continue
        seen.add(k)
        out.append(e)
    return out


def extract():
    OUT.mkdir(parents=True, exist_ok=True)
    ents = build_entries()
    with open(OUT / "entries.jsonl", "w") as f:
        for e in ents:
            f.write(json.dumps(e) + "\n")
    assert all(e["ask"] <= ASK_HI + 1e-9 for e in ents), "a favourite-side entry slipped in"
    ev = {}
    for e in ents:
        ev.setdefault(e["cat"], set()).add(e["event"])
    cnt = {}
    for e in ents:
        cnt[e["cat"]] = cnt.get(e["cat"], 0) + 1
    print(f"{len(ents)} entries, {len({e['event'] for e in ents})} events, {len({e['market'] for e in ents})} markets (COUNTS ONLY; no outcome aggregated)")
    print("category | entries | events (rank by events)")
    for c in sorted(ev, key=lambda c: -len(ev[c])):
        print(f"  {c} | {cnt[c]} | {len(ev[c])}")
    bk = {}
    for e in ents:
        bk[e["bk"]] = bk.get(e["bk"], 0) + 1
    print("ask buckets (entries):", {BUCKET_NAMES[k]: v for k, v in sorted(bk.items())})


# ---------------------------------------------------------------- statistics
def event_groups(rows, key="net"):
    """{event: [sum, n, t]} with t the earliest entry time of the event in these rows."""
    g = {}
    for r in rows:
        x = g.setdefault(r["event"], [0.0, 0, r["t"]])
        x[0] += r[key]; x[1] += 1; x[2] = min(x[2], r["t"])
    return g


def boot_ci(groups, rng, B=BOOT):
    """Event-cluster bootstrap 95% percentile interval of the mean per contract (sum over resampled events / contracts in them)."""
    ev = list(groups.values())
    k = len(ev)
    if k == 0:
        return None
    sums = np.array([e[0] for e in ev]); ns = np.array([e[1] for e in ev], dtype=float)
    out = np.empty(B)
    step = max(1, 4_000_000 // k)
    for i in range(0, B, step):
        j = rng.integers(0, k, size=(min(step, B - i), k))
        out[i:i + j.shape[0]] = sums[j].sum(axis=1) / ns[j].sum(axis=1)
    out.sort()
    return float(out[int(0.025 * B)]), float(out[int(0.975 * B) - 1])


def stats(rows, rng, B=BOOT):
    if not rows:
        return {"n": 0, "events": 0}
    g = event_groups(rows)
    n = len(rows)
    ci = boot_ci(g, rng, B)
    return {"n": n, "events": len(g), "dates": len({r["date"] for r in rows}), "win": sum(r["won"] for r in rows) / n, "price": sum(r["ask"] for r in rows) / n,
            "excess": sum(r["won"] - r["ask"] for r in rows) / n, "net": sum(r["net"] for r in rows) / n, "lo": ci[0], "hi": ci[1]}


def split_halves(rows):
    """First half / second half of the EVENTS by earliest close time within the cell (ties by event id)."""
    g = event_groups(rows)
    order = sorted(g, key=lambda e: (g[e][2], e))
    k = len(order) // 2
    first = set(order[:k])
    return [r for r in rows if r["event"] in first], [r for r in rows if r["event"] not in first]


def verdict(a, b):
    """The registered LEAD rule."""
    if a["events"] < MIN_EVENTS_HALF or b["events"] < MIN_EVENTS_HALF:
        return "NOT_ENOUGH_DATA"
    if a["net"] > 0 and b["net"] > 0 and a["lo"] > 0 and b["lo"] > 0:
        return "LEAD"
    return "NEGATIVE_OR_NO_EDGE"


def score(force=False):
    path = WORKERS / "CALIB1_RESULT.json"
    if path.exists() and not force:
        raise SystemExit("already run: workers/CALIB1_RESULT.json exists (run once)")
    ents = [json.loads(x) for x in open(OUT / "entries.jsonl")]
    assert all(e["ask"] <= ASK_HI + 1e-9 for e in ents)
    rng = np.random.default_rng(SEED)
    grid = []
    for cat in REGISTERED_CATEGORIES:
        for bi, name in enumerate(BUCKET_NAMES):
            rows = [e for e in ents if e["cat"] == cat and e["bk"] == bi]
            a_rows, b_rows = split_halves(rows)
            full, a, b = stats(rows, rng), stats(a_rows, rng), stats(b_rows, rng)
            grid.append({"cat": cat, "bucket": name, "all": full, "first": a, "second": b, "verdict": verdict(a, b) if a["n"] and b["n"] else "NOT_ENOUGH_DATA"})
    pooled = []
    for life in ("H", "D", "W", "ALL"):
        for bi, name in enumerate(BUCKET_NAMES):
            rows = [e for e in ents if e["bk"] == bi and (life == "ALL" or e["life"] == life)]
            pooled.append({"life": life, "bucket": name, **stats(rows, rng)})
    other = []
    for cat in sorted({e["cat"] for e in ents} - set(REGISTERED_CATEGORIES)):
        rows = [e for e in ents if e["cat"] == cat]
        other.append({"cat": cat, **stats(rows, rng, 500)})
    ttc = [{"ttc": t, **stats([e for e in ents if e["ttc"] == t], rng, 500)} for t in ("<=1h", "1-6h", "6-24h", "1-3d", ">3d")]
    out = {"entries": len(ents), "events": len({e["event"] for e in ents}), "markets": len({e["market"] for e in ents}), "grid": grid, "pooled": pooled, "other_categories": other, "by_time_to_close": ttc,
           "leads": [g for g in grid if g["verdict"] == "LEAD"]}
    path.write_text(json.dumps(out, indent=1))
    return out


def fmt(s):
    if not s.get("n"):
        return "n=0"
    return f"n={s['n']} ev={s['events']} win={100*s['win']:.1f}% px={100*s['price']:.1f}c net={100*s['net']:+.2f}c [{100*s['lo']:+.2f},{100*s['hi']:+.2f}]"


def report(out):
    print(f"{out['entries']} entries, {out['events']} events, {out['markets']} markets")
    print("POOLED (all categories), win rate minus price and net after fee, by life class and ask bucket")
    for p in out["pooled"]:
        if p.get("n"):
            print(f"  {p['life']:3s} {p['bucket']:7s} n={p['n']} ev={p['events']} win={100*p['win']:.1f}% px={100*p['price']:.1f}c excess={100*p['excess']:+.2f}c net={100*p['net']:+.2f}c [{100*p['lo']:+.2f},{100*p['hi']:+.2f}]")
    print("GRID (the only claims)")
    for g in out["grid"]:
        print(f"  {g['cat'][:22]:22s} {g['bucket']:7s} {g['verdict']:20s} all: {fmt(g['all'])} | H1: {fmt(g['first'])} | H2: {fmt(g['second'])}")
    print("LEADS:", [(g["cat"], g["bucket"]) for g in out["leads"]])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "extract":
        extract()
    elif cmd == "score":
        reg = WORKERS / "CALIB1_CATEGORIES.json"
        REGISTERED_CATEGORIES[:] = json.loads(reg.read_text())
        report(score())
    else:
        print(__doc__)
