"""OVERROUND1 (workers/OVERROUND1_REGISTRATION.md): does the event overround (sum of YES asks over a mutually exclusive set of outcomes, minus 1)
condition the loss of the CHEAP side (ask 3c to 30c)? Cached USWEEP1 development candles only; no Kalshi fetch, no order, no model.
Cheap side only (owner rule): no entry above 0.30 is built, counted, scored or printed; no 15 minute crypto/gold trigger.

Usage: python3 -I -m scalper.overround1 census   structure only: events, overround quantiles, cheap entry counts per tercile (NO outcome is read)
       python3 -I -m scalper.overround1 score    ONE run -> workers/OVERROUND1_RESULT.json (refuses a second run)
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

from scalper import calib1 as c1

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORKERS = ROOT / "workers"
SWEEP = Path(os.environ.get("OVR1_SWEEP", "/tmp/usweep1_cache"))
OUT = Path(os.environ.get("OVR1_OUT", "/tmp/overround1"))

# ---- registered constants ----
FROZEN_FROM = 1791043200          # 2026-10-03T16:00Z: nothing at or after this is read
MIN_OUTCOMES = 4
MAX_PER_EVENT_LOOK = 2
MIN_TRADES = 150
MIN_LOOK_EVENTS = 30              # a look with fewer event-looks than this has no tercile and is dropped (counts reported)
CUT_FRACTION = 2 / 3              # terciles are cut on the first two thirds of event-looks by close time
PF_BAR = 1.5
BOOT, SEED = 2000, 20261104


def mtype(ticker: str) -> str:
    return ticker.rsplit("-", 1)[1][:1]


def structure_ok(tickers) -> bool:
    """Registered mutual exclusivity rule (structure only, no outcome): at least 4 outcomes, B (bracket) >= 3, exactly 2 T (the two open ends), nothing else."""
    ty = [mtype(t) for t in tickers]
    return len(ty) >= MIN_OUTCOMES and ty.count("B") >= 3 and ty.count("T") == 2 and len(ty) == ty.count("B") + 2


def yes_ask(q):
    """YES ask of a quote tuple (end, bid, ask, ...), or None if the outcome has no real ask (0 < ask < 1 required; a one sided quote is allowed)."""
    if q is None or q[2] is None or not (0 < q[2] < 1) or q[1] is None or not (0 <= q[1] < q[2]):
        return None
    return q[2]


def overround(asks) -> float | None:
    if len(asks) < MIN_OUTCOMES or any(a is None for a in asks):
        return None
    return round(sum(asks) - 1.0, 6)


def md5key(ticker: str) -> str:
    return hashlib.md5(ticker.encode()).hexdigest()


def pick(cands):
    """At most MAX_PER_EVENT_LOOK cheap-side candidates of one event-look: the smallest md5(ticker)."""
    return sorted(cands, key=lambda x: md5key(x["market"]))[:MAX_PER_EVENT_LOOK]


def tercile_cuts(vals):
    v = np.sort(np.array(vals, dtype=float))
    return float(v[int(len(v) / 3)]), float(v[int(2 * len(v) / 3)])


def tercile(x, cuts):
    return "LOW" if x < cuts[0] else ("MID" if x < cuts[1] else "HIGH")


def build(with_results: bool):
    """One record per (event, look): overround, the event's close, and its picked cheap-side candidates (with outcomes only if with_results)."""
    cen = {}
    for r in c1._jl(SWEEP / "census.jsonl"):
        if r.get("markets"):
            cen.setdefault(r["ticker"], r)
    res = {}
    if with_results:
        for x in c1._jl(SWEEP / "outcomes.jsonl"):
            res.update(x["r"])
    cls = {s: c1.profile_class(r) for s, r in cen.items()}
    ev = {}
    for s, r in cen.items():
        if r.get("capped"):
            continue
        for m in r["markets"]:
            ev.setdefault(c1.event_of(m[0]), []).append((s, m))
    wanted = {m[0] for v in ev.values() for _, m in v}
    cand = {}
    for x in c1._jl(SWEEP / "candles.jsonl"):
        if x["t"] in wanted and x["c"] and x["t"] not in cand:
            cand[x["t"]] = x
    recs = []
    for e, v in ev.items():
        tk = [m[0] for _, m in v]
        if not structure_ok(tk) or any(t not in cand for t in tk):
            continue
        anchors = {(m[3] or m[2]) for _, m in v}
        if len(anchors) != 1:
            continue
        anc = anchors.pop()
        open_ts = max(m[1] for _, m in v)
        if not anc or anc >= FROZEN_FROM or any((m[2] or 0) >= FROZEN_FROM for _, m in v):
            continue
        s = v[0][0]
        k = cls.get(s)
        if k is None:
            continue
        for T in c1.LOOKS[k]:
            target = anc - T * 60
            if target <= open_ts:
                continue
            qs = {t: c1.decision_quote(cand[t]["c"], target, cand[t]["iv"]) for t in tk}
            ov = overround([yes_ask(qs[t]) for t in tk])
            if ov is None:
                continue
            cs = []
            for t in tk:
                sd = c1.cheap_side(qs[t][1], qs[t][2])
                if sd:
                    d = {"market": t, "side": sd[0], "ask": sd[1], "fee": c1.fee_per_contract(sd[1])}
                    if with_results:
                        r_ = res.get(t)
                        if r_ not in ("yes", "no"):
                            continue
                        d["won"] = 1 if sd[0] == r_ else 0
                        d["net"] = c1.net_per_contract(d["won"] == 1, sd[1])
                    cs.append(d)
            assert all(d["ask"] <= c1.ASK_HI + 1e-9 for d in cs), "a favourite-side entry slipped in"
            recs.append({"event": e, "series": s, "look": f"T{T}", "anchor": anc, "ov": ov, "n_out": len(tk), "cands": pick(cs), "n_cands": len(cs)})
    return recs


def assign(recs):
    """Tercile per look tag, cut on the first two thirds of event-looks (by anchor, then event) of that look; every record gets a tercile and a half flag."""
    out = []
    for look in sorted({r["look"] for r in recs}):
        rs = sorted([r for r in recs if r["look"] == look], key=lambda r: (r["anchor"], r["event"]))
        if len(rs) < MIN_LOOK_EVENTS:
            continue
        k = int(len(rs) * CUT_FRACTION)
        cuts = tercile_cuts([r["ov"] for r in rs[:k]])
        for i, r in enumerate(rs):
            r["terc"], r["cuts"], r["dev"] = tercile(r["ov"], cuts), cuts, i < k
        out += rs
    return out


def census():
    recs = assign(build(False))
    print(f"event-looks {len(recs)}, events {len({r['event'] for r in recs})}, series {len({r['series'] for r in recs})}, looks {sorted({r['look'] for r in recs})} (STRUCTURE ONLY; no outcome read)")
    ovs = sorted(r["ov"] for r in recs)
    q = lambda p: ovs[int(p * (len(ovs) - 1))]
    print("overround quantiles 5/25/50/75/95:", [q(p) for p in (.05, .25, .5, .75, .95)], "negative:", sum(o < 0 for o in ovs))
    for look in sorted({r["look"] for r in recs}):
        rs = [r for r in recs if r["look"] == look]
        print(look, "cuts", rs[0]["cuts"], {t: (sum(1 for r in rs if r["terc"] == t), sum(len(r["cands"]) for r in rs if r["terc"] == t)) for t in ("LOW", "MID", "HIGH")})
    print("TOTAL event-looks and picked cheap entries per tercile (all / development third):",
          {t: (sum(1 for r in recs if r["terc"] == t), sum(len(r["cands"]) for r in recs if r["terc"] == t)) for t in ("LOW", "MID", "HIGH")})
    print("dates:", len({__import__('datetime').datetime.fromtimestamp(r['anchor'], __import__('datetime').timezone.utc).strftime('%Y-%m-%d') for r in recs}))


def _rows(recs, terc):
    rows = []
    for r in recs:
        if terc is None or r["terc"] == terc:
            for d in r["cands"]:
                rows.append({**d, "event": r["event"], "t": r["anchor"], "look": r["look"], "date": __import__('datetime').datetime.fromtimestamp(r["anchor"], __import__('datetime').timezone.utc).strftime("%Y-%m-%d")})
    return rows


def pf(rows):
    w = sum(r["net"] for r in rows if r["net"] > 0)
    l = -sum(r["net"] for r in rows if r["net"] < 0)
    return w / l if l > 0 else float("inf")


def summarize(rows, rng):
    if not rows:
        return {"n": 0}
    s = c1.stats(rows, rng)
    s["pf"] = pf(rows)
    return s


def verdict(low_rows, rng):
    """Registered kill rules. FALSIFIED if mean net after fees is not above 0 in both halves, or PF under 1.5; NOT_ENOUGH_DATA under 150 trades."""
    if len(low_rows) < MIN_TRADES:
        return "NOT_ENOUGH_DATA"
    a, b = c1.split_halves(low_rows)
    ma = sum(r["net"] for r in a) / len(a) if a else 0
    mb = sum(r["net"] for r in b) / len(b) if b else 0
    if not (ma > 0 and mb > 0) or pf(low_rows) < PF_BAR:
        return "FALSIFIED"
    return "LEAD_FOR_FORWARD_TEST"


def score(force=False):
    path = WORKERS / "OVERROUND1_RESULT.json"
    if path.exists() and not force:
        raise SystemExit("already run: workers/OVERROUND1_RESULT.json exists (run once)")
    recs = assign(build(True))
    rng = np.random.default_rng(SEED)
    out = {"event_looks": len(recs), "events": len({r["event"] for r in recs})}
    for t in ("LOW", "MID", "HIGH", None):
        rows = _rows(recs, t)
        a, b = c1.split_halves(rows)
        out[t or "ALL"] = {"all": summarize(rows, rng), "first": summarize(a, rng), "second": summarize(b, rng)}
    low = _rows(recs, "LOW")
    out["verdict"] = verdict(low, rng)
    a, b = c1.split_halves(low)
    out["low_half_means"] = [sum(r["net"] for r in a) / len(a) if a else None, sum(r["net"] for r in b) / len(b) if b else None]
    out["by_look_low"] = {lk: summarize([r for r in low if r["look"] == lk], rng) for lk in sorted({r["look"] for r in low})}
    # descriptive: the same terciles inside the development third only (cut was fitted there), and overround vs mean net by decile of ov
    dev = [r for r in recs if r["dev"]]
    out["dev_only"] = {t: summarize(_rows(dev, t), rng) for t in ("LOW", "MID", "HIGH")}
    # descriptive contrast LOW minus HIGH (event-cluster bootstrap over events)
    lo, hi = _rows(recs, "LOW"), _rows(recs, "HIGH")
    evs = sorted({r["event"] for r in lo + hi})
    gl, gh = c1.event_groups(lo), c1.event_groups(hi)
    diffs = []
    for _ in range(BOOT):
        pick_ = rng.integers(0, len(evs), len(evs))
        s_l = [gl[evs[i]] for i in pick_ if evs[i] in gl]; s_h = [gh[evs[i]] for i in pick_ if evs[i] in gh]
        if s_l and s_h:
            diffs.append(sum(x[0] for x in s_l) / sum(x[1] for x in s_l) - sum(x[0] for x in s_h) / sum(x[1] for x in s_h))
    diffs.sort()
    out["low_minus_high"] = {"mean": (sum(r["net"] for r in lo) / len(lo) - sum(r["net"] for r in hi) / len(hi)) if lo and hi else None,
                             "lo": diffs[int(.025 * len(diffs))] if diffs else None, "hi": diffs[int(.975 * len(diffs)) - 1] if diffs else None}
    path.write_text(json.dumps(out, indent=1, default=float))
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "census":
        census()
    elif cmd == "score":
        print(json.dumps(score(), indent=1, default=float))
    else:
        raise SystemExit(__doc__)
