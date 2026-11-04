"""LIQ1 (README "LIQ1 liquidity"; workers/LIQ1_REGISTRATION.md): is the CHEAP side (ask 3c to 30c) near fair when the quote is tight or the candle
is busy? Pooled development caches of CALIB1 (USWEEP1/2/3, NEWLIST1), no Kalshi fetch, no order, no threshold search.
Cheap side only (owner rule): no entry above 0.30 is ever built, counted, scored or printed.
(Named liq1_spread.py because src/scalper/liq1.py already belongs to the earlier LIQ1-INFO liquidation check.)

Usage: python3 -I -m scalper.liq1_spread extract   features -> LIQ1_OUT/features.jsonl and settled results -> LIQ1_OUT/res.json; prints COUNTS ONLY
       python3 -I -m scalper.liq1_spread score     ONE run -> workers/LIQ1_RESULT.json (refuses a second run)
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path

import numpy as np

from scalper import calib1 as C

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORKERS, DATA = ROOT / "workers", ROOT / "data"
OUT = Path(os.environ.get("LIQ1_OUT", "/tmp/liq1"))
SEED, BOOT = 20261104, 2000
MIN_TRADES = 150
PF_BAR = 1.5
MAX_PER_EVENT = 2


# ---------------------------------------------------------------- features (no outcome)
def quote_features(bid, ask, vol):
    """Cheap side with the spread (ask - bid of the YES book, the same width for the NO side) in cents and the candle volume."""
    cs = C.cheap_side(bid, ask)
    if not cs:
        return None
    return {"side": cs[0], "ask": cs[1], "spread_c": round((ask - bid) * 100, 4), "vol": float(vol or 0.0)}


def feature_row(src, series, cat, ticker, life_s, anchor, look_ts, q, look_tag):
    return {"src": src, "series": series, "cat": C.norm_cat(cat), "life": C.life_class(life_s), "bk": C.ask_bucket(q["ask"]), "ask": q["ask"],
            "side": q["side"], "spread_c": q["spread_c"], "vol": q["vol"], "event": C.event_of(ticker), "t": anchor, "market": ticker, "look": look_tag}


def candle_source(src, cdir):
    """As calib1.entries_candle_source, but keeps the look candle's volume and spread and does not read the result's value, only that it settled."""
    cen = {}
    for r in C._jl(cdir / "census.jsonl"):
        if r.get("markets"):
            cen.setdefault(r["ticker"], r)
    res = {}
    for x in C._jl(cdir / ("outcomes.jsonl" if src == "sweep" else "census_results.jsonl")):
        res.update(x["r"])
    meta = {}
    for s, r in cen.items():
        for m in r["markets"]:
            meta.setdefault(m[0], (s, m))
    cls = {s: C.profile_class(r) for s, r in cen.items()}
    seen, out, results = set(), [], {}
    for x in C._jl(cdir / "candles.jsonl"):
        t = x["t"]
        if t in seen or t not in meta or not x["c"]:
            continue
        seen.add(t)
        s, m = meta[t]
        k = cls.get(s)
        if k is None or res.get(t) not in ("yes", "no"):
            continue
        open_ts, close_ts, anc = m[1], m[2], (m[3] or m[2])
        if not open_ts or not close_ts or not anc or anc <= open_ts:
            continue
        for T in C.LOOKS[k]:
            target = anc - T * 60
            if target <= open_ts or target >= close_ts:
                continue
            q = C.decision_quote(x["c"], target, x["iv"])
            if not q:
                continue
            f = quote_features(q[1], q[2], q[3] if len(q) > 3 else 0.0)
            if f:
                out.append(feature_row(src, s, cen[s].get("cat"), t, anc - open_ts, anc, target, f, f"T{T}"))
                results[t] = res[t]
    return out, results


def newlist_source():
    cuts = json.loads((DATA / "newlist1_cuts.json").read_text())
    c = sqlite3.connect(str(DATA / "newlist1.sqlite"))
    res = dict(c.execute("select ticker, result from res"))
    mk = {r[0]: r for r in c.execute("select ticker, series, category, open_ts, close_ts from mk")}
    cds = {}
    for t, e, b, a, v in c.execute("select ticker, end_ts, bid, ask, vol from cd order by ticker, end_ts"):
        cds.setdefault(t, []).append((e, b, a, v))
    out, results = [], {}
    for t, cs in cds.items():
        if t not in mk or res.get(t) not in ("yes", "no"):
            continue
        _, s, cat, o, cl = mk[t]
        if not o or not cl or cl >= cuts["t2"]:
            continue
        looks = {}
        for h in C.AGE_LOOK_H:
            looks[f"A{h}h"] = next((q for q in cs if o + h * 3600 <= q[0] < o + (h + 1) * 3600), None)
        late = None
        for q in cs:
            if q[0] > cl - C.LATE_LEAD_H * 3600:
                break
            late = q
        looks["late"] = late
        for tag, q in looks.items():
            if q is None:
                continue
            f = quote_features(q[1], q[2], q[3])
            if f:
                out.append(feature_row("newlist1", s, cat, t, cl - o, cl, q[0], f, tag))
                results[t] = res[t]
    return out, results


def build():
    rows, results = [], {}
    for src in ("sweep", "us2", "us3"):
        part, r = candle_source(src, C.SRC[src])
        print(f"  {src}: {len(part)} cheap-side entries", file=sys.stderr)
        rows += part
        results.update(r)
    part, r = newlist_source()
    print(f"  newlist1: {len(part)} cheap-side entries", file=sys.stderr)
    rows += part
    results.update(r)
    out, seen = [], set()
    for e in rows:                                   # one entry per (market, look), first source wins (as CALIB1)
        k = (e["market"], e["look"])
        if k not in seen:
            seen.add(k)
            out.append(e)
    return out, results


# ---------------------------------------------------------------- registered rules
def quantile(xs, q):
    """Lower empirical quantile (no interpolation), so a cut is always an observed value."""
    s = sorted(xs)
    return s[min(len(s) - 1, int(q * len(s)))]


def fit_split(rows):
    """Events ordered by earliest close time (ties by event id); the first two thirds are the fit set."""
    g = C.event_groups(rows, key="ask")
    order = sorted(g, key=lambda e: (g[e][2], e))
    k = (2 * len(order)) // 3
    return set(order[:k]), set(order[k:])


def fit_cuts(rows, fit_events):
    sp = [r["spread_c"] for r in rows if r["event"] in fit_events]
    vo = [r["vol"] for r in rows if r["event"] in fit_events]
    return {"spread_lo": quantile(sp, 1 / 3), "spread_hi": quantile(sp, 2 / 3), "vol_lo": quantile(vo, 1 / 3), "vol_hi": quantile(vo, 2 / 3)}


def groups_for(r, cuts):
    """Group labels for one entry. TIGHT spread <= spread_lo; WIDE spread >= spread_hi (placebo; equal cuts make both tails, reported);
    HIGH vol > vol_hi when vol_hi > 0 else vol > 0; LOWV vol <= vol_lo (placebo)."""
    g = []
    if r["spread_c"] <= cuts["spread_lo"] + 1e-9:
        g.append("TIGHT")
    if r["spread_c"] >= cuts["spread_hi"] - 1e-9:
        g.append("WIDE")
    if r["vol"] > max(cuts["vol_hi"], 0.0) + 1e-9:
        g.append("HIGHV")
    if r["vol"] <= cuts["vol_lo"] + 1e-9:
        g.append("LOWV")
    return g


def cap_per_event(rows, k=MAX_PER_EVENT):
    by = {}
    for r in rows:
        by.setdefault(r["event"], []).append(r)
    out = []
    for e, rs in by.items():
        rs = sorted(rs, key=lambda r: hashlib.md5(f"{r['market']}|{r['look']}".encode()).hexdigest())
        out += rs[:k]
    return out


def pf(rows):
    w = sum(r["net"] for r in rows if r["net"] > 0)
    l = -sum(r["net"] for r in rows if r["net"] < 0)
    return w / l if l > 0 else float("inf")


def cell(rows, rng, B=BOOT):
    s = C.stats(rows, rng, B)
    if s["n"]:
        s["pf"] = pf(rows)
        s["ask_mix"] = {C.BUCKET_NAMES[b]: sum(1 for r in rows if r["bk"] == b) for b in range(len(C.BUCKET_NAMES))}
    return s


def verdict(name, h1, h2, whole):
    if whole["n"] < MIN_TRADES:
        return "NOT_ENOUGH_DATA"
    if h1["n"] and h2["n"] and h1["net"] > 0 and h2["net"] > 0 and whole["pf"] >= PF_BAR:
        return "LEAD"
    return "FALSIFIED"


def score(force=False):
    path = WORKERS / "LIQ1_RESULT.json"
    if path.exists() and not force:
        raise SystemExit("already run: workers/LIQ1_RESULT.json exists (run once)")
    feats = [json.loads(x) for x in open(OUT / "features.jsonl")]
    res = json.load(open(OUT / "res.json"))
    assert all(f["ask"] <= C.ASK_HI + 1e-9 for f in feats)
    ents = []
    for f in feats:
        won = f["side"] == res[f["market"]]
        ents.append({**f, "won": 1 if won else 0, "net": C.net_per_contract(won, f["ask"]), "fee": C.fee_per_contract(f["ask"]),
                     "date": C.datetime.fromtimestamp(f["t"], C.timezone.utc).strftime("%Y-%m-%d")})
    fit_ev, oos_ev = fit_split(ents)
    cuts = fit_cuts(ents, fit_ev)
    rng = np.random.default_rng(SEED)
    sel = {"CONTROL": ents, "TIGHT": [], "WIDE": [], "HIGHV": [], "LOWV": []}
    for r in ents:
        for g in groups_for(r, cuts):
            sel[g].append(r)
    out = {"entries": len(ents), "events": len({e["event"] for e in ents}), "cuts": cuts, "fit_events": len(fit_ev), "oos_events": len(oos_ev), "groups": {}}
    for name, rows in sel.items():
        rows = cap_per_event(rows)
        a, b = C.split_halves(rows)
        whole, h1, h2 = cell(rows, rng), cell(a, rng), cell(b, rng)
        oos = cell([r for r in rows if r["event"] in oos_ev], rng)
        fit = cell([r for r in rows if r["event"] in fit_ev], rng)
        out["groups"][name] = {"all": whole, "D1": h1, "D2": h2, "fit": fit, "oos": oos,
                               "verdict": verdict(name, h1, h2, whole) if name in ("TIGHT", "HIGHV") else "PLACEBO_OR_CONTROL"}
    # observation only: spread tercile means over all cheap entries by ask bucket (no claim)
    path.write_text(json.dumps(out, indent=1))
    return out


def fmt(s):
    if not s.get("n"):
        return "n=0"
    return (f"n={s['n']} ev={s['events']} win={100*s['win']:.2f}% px={100*s['price']:.2f}c w-p={100*s['excess']:+.2f}c "
            f"net={100*s['net']:+.2f}c [{100*s['lo']:+.2f},{100*s['hi']:+.2f}] PF={s['pf']:.2f}")


def report(out):
    print(f"{out['entries']} entries, {out['events']} events; fit events {out['fit_events']}, out-of-fit {out['oos_events']}; cuts {out['cuts']}")
    for name, g in out["groups"].items():
        print(f"{name:8s} {g['verdict']}\n   all: {fmt(g['all'])}\n   D1: {fmt(g['D1'])}\n   D2: {fmt(g['D2'])}\n   fit: {fmt(g['fit'])}\n   oos: {fmt(g['oos'])}")


def census():
    ents, res = build()
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "features.jsonl", "w") as f:
        for e in ents:
            f.write(json.dumps(e) + "\n")
    json.dump(res, open(OUT / "res.json", "w"))
    assert all(e["ask"] <= C.ASK_HI + 1e-9 for e in ents)
    fit_ev, oos_ev = fit_split([{**e, "ask": e["ask"]} for e in ents])
    cuts = fit_cuts(ents, fit_ev)
    print(f"{len(ents)} entries, {len({e['event'] for e in ents})} events; fit events {len(fit_ev)}, out-of-fit {len(oos_ev)} (COUNTS ONLY; no outcome aggregated)")
    print("cuts:", cuts)
    sp = {}
    for e in ents:
        sp[e["spread_c"]] = sp.get(e["spread_c"], 0) + 1
    print("spread_c histogram (top):", sorted(sp.items(), key=lambda kv: -kv[1])[:12])
    print("vol zero share:", sum(1 for e in ents if e["vol"] <= 0) / len(ents))
    for name, fn in (("TIGHT", lambda e: "TIGHT" in groups_for(e, cuts)), ("WIDE", lambda e: "WIDE" in groups_for(e, cuts)),
                     ("HIGHV", lambda e: "HIGHV" in groups_for(e, cuts)), ("LOWV", lambda e: "LOWV" in groups_for(e, cuts)), ("CONTROL", lambda e: True)):
        rows = [e for e in ents if fn(e)]
        cap = cap_per_event(rows)
        print(f"  {name}: {len(rows)} entries, {len({e['event'] for e in rows})} events, {len(cap)} after max {MAX_PER_EVENT} per event")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "extract":
        census()
    elif cmd == "score":
        report(score())
    else:
        print(__doc__)
