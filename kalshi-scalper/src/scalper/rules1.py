"""RULES1B (README "RULES1B"; workers/RULES1_REGISTRATION.md): do cheap-side entries (ask 3c to 30c) win above their price in markets whose
OWN rules text carries a fixed fine-print feature?  Discovery only. Cheap side only (owner rule): no entry above 0.30 is built, counted or printed.
Name note: the id RULES1 was already used on 2026-10-29 for the lock rules review, so this study is stored as RULES1 files (registration/result) but
called RULES1B in prose.  Features are decided from the market's own text and strike_type fields; no outcome is read to pick them.

Usage: python3 -I -m scalper.rules1 census   COUNTS ONLY (reads no 'won'/'net'/'result')
       python3 -I -m scalper.rules1 score    ONE registered run -> workers/RULES1_RESULT.json (refuses a second run)
Inputs: RULES1_ENTRIES (CALIB1 entries.jsonl, development markets only), workers/RULES1_META.jsonl.gz (whitelisted market metadata, no result or price).
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORKERS = ROOT / "workers"
ENTRIES = Path(os.environ.get("RULES1_ENTRIES", "/tmp/calib1/entries.jsonl"))
META = Path(os.environ.get("RULES1_META", str(WORKERS / "RULES1_META.jsonl.gz")))
RESULT = WORKERS / "RULES1_RESULT.json"

ASK_LO, ASK_HI = 0.03, 0.30
FEE_RATE, C = 0.07, 10
MAX_PER_EVENT = 2
MIN_TRADES = 150
BOOT, SEED = 2000, 20261103

# ---- registered feature list (workers/RULES1_REGISTRATION.md); regexes run on lower-cased rules_primary + " " + rules_secondary ----
FEATURES = {
    "STRICT":     r"strictly (?:greater|more|less|above|below)",
    "INCLUSIVE":  r"at least|or higher|or more|or above|greater than or equal|\d\+ ",     # OR strike_type == greater_or_equal
    "ROUNDED":    r"rounded to",
    "PRINT":      r"candlestick|at the exact time|exact time|at exactly|opening candlestick",
    "FIRSTFINAL": r"first release|sooner of the first|first reported|preliminary|revis|official and final|final race results|provisional|most recently available",
    "EXACT":      r"is exactly|exactly \d",
    "VOID":       r"fair market price|does not occur|postponed|abandon|ends in a tie|no result|is cancel|cancelled|resolve to (?:the )?fair",
    "SOURCE":     r"according to|as published by|as reported by|reported by|based on the value reported",
}
ORDER = list(FEATURES)
_RX = {k: re.compile(v) for k, v in FEATURES.items()}


def text_of(m: dict) -> str:
    return ((m.get("rules_primary") or "") + " " + (m.get("rules_secondary") or "")).lower()


def flags_of(m: dict) -> dict:
    t = text_of(m)
    f = {k: bool(_RX[k].search(t)) for k in ORDER}
    if m.get("strike_type") == "greater_or_equal":
        f["INCLUSIVE"] = True
    return f


def series_flags(metas: list[dict]):
    """(flags per feature: True/False/None for unstable, any_flag). Two fetched markets per series must agree, else None for that feature."""
    fl = [flags_of(m) for m in metas]
    out = {}
    for k in ORDER:
        vals = {f[k] for f in fl}
        out[k] = vals.pop() if len(vals) == 1 else None
    return out


def md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


def fee_per_contract(p: float, c: int = C) -> float:
    return math.ceil(round(FEE_RATE * c * p * (1 - p) * 100, 6)) / 100.0 / c


def net_per_contract(won: int, p: float) -> float:
    return (1.0 if won else 0.0) - p - fee_per_contract(p)


def one_per_market(rows: list[dict]) -> list[dict]:
    """One entry per market: the md5-smallest of market|look (arbitrary, deterministic, outcome blind)."""
    best = {}
    for r in rows:
        k = md5(r["market"] + "|" + r["look"])
        if r["market"] not in best or k < best[r["market"]][0]:
            best[r["market"]] = (k, r)
    return [v[1] for v in best.values()]


def cap_per_event(rows: list[dict], cap: int = MAX_PER_EVENT) -> list[dict]:
    by = {}
    for r in rows:
        by.setdefault(r["event"], []).append(r)
    out = []
    for ev, rs in by.items():
        rs.sort(key=lambda r: md5(r["market"]))
        out += rs[:cap]
    return out


def load_meta():
    by = {}
    with gzip.open(META, "rt") as f:
        for line in f:
            m = json.loads(line)
            if m.get("ok"):
                by.setdefault(m["series"], []).append(m)
    return {s: series_flags(ms) for s, ms in by.items()}


def load_entries(outcomes: bool):
    keys = ["series", "ask", "event", "t", "market", "look", "cat"] + (["won"] if outcomes else [])
    rows = []
    with open(ENTRIES) as f:
        for line in f:
            x = json.loads(line)
            r = {k: x[k] for k in keys}
            assert ASK_LO - 1e-9 <= r["ask"] <= ASK_HI + 1e-9, "entry above 0.30"
            rows.append(r)
    return rows


def build(outcomes: bool):
    flags = load_meta()
    rows = cap_per_event(one_per_market(load_entries(outcomes)))
    for r in rows:
        r["fl"] = flags.get(r["series"])
    return rows


def groups(rows):
    """feature -> rows treated; CONTROL = no feature True and none unstable; UNSTABLE counted apart; ALL for reference."""
    g = {k: [] for k in ORDER}
    g["CONTROL"], g["UNSTABLE"], g["NOMETA"], g["ALL"] = [], [], [], []
    for r in rows:
        g["ALL"].append(r)
        fl = r["fl"]
        if fl is None:
            g["NOMETA"].append(r)
            continue
        for k in ORDER:
            if fl[k]:
                g[k].append(r)
        if any(v is None for v in fl.values()):
            g["UNSTABLE"].append(r)
        elif not any(fl.values()):
            g["CONTROL"].append(r)
    return g


def pf(nets):
    w = sum(x for x in nets if x > 0)
    l = -sum(x for x in nets if x < 0)
    return float("inf") if l == 0 and w > 0 else (w / l if l else float("nan"))


def cluster_ci(rows, nets, rng):
    """Event-cluster bootstrap 95% CI of the mean net."""
    by = {}
    for r, x in zip(rows, nets):
        by.setdefault(r["event"], []).append(x)
    ev = [np.array(v) for v in by.values()]
    sums = np.array([v.sum() for v in ev])
    cnt = np.array([len(v) for v in ev])
    n = len(ev)
    if n < 2:
        return (float("nan"), float("nan"))
    ms = []
    for _ in range(BOOT):
        i = rng.integers(0, n, n)
        ms.append(sums[i].sum() / cnt[i].sum())
    return tuple(np.percentile(ms, [2.5, 97.5]))


def stats(rows, rng):
    if not rows:
        return {"n": 0}
    nets = [net_per_contract(r["won"], r["ask"]) for r in rows]
    ci = cluster_ci(rows, nets, rng)
    return {"n": len(rows), "events": len({r["event"] for r in rows}), "series": len({r["series"] for r in rows}),
            "win": float(np.mean([r["won"] for r in rows])), "price": float(np.mean([r["ask"] for r in rows])),
            "net_c": float(np.mean(nets)) * 100, "pf": pf(nets), "ci_lo_c": ci[0] * 100, "ci_hi_c": ci[1] * 100}


def verdict(n, h1, h2, pfv):
    if n < MIN_TRADES:
        return "NOT_ENOUGH_DATA"
    if h1 is not None and h2 is not None and h1 > 0 and h2 > 0 and pfv >= 1.5:
        return "LEAD"
    return "FALSIFIED"


def split_halves(rows):
    ts = sorted(r["t"] for r in rows)
    mid = ts[len(ts) // 2]
    return mid


def census():
    rows = build(False)
    g = groups(rows)
    mid = split_halves(rows)
    print("entries after one-per-market and max 2 per event:", len(rows), "events:", len({r["event"] for r in rows}), "halves split at t =", mid)
    for k in ORDER + ["CONTROL", "UNSTABLE", "NOMETA", "ALL"]:
        rs = g[k]
        a = sum(1 for r in rs if r["t"] < mid)
        print(f"{k:11s} n={len(rs):5d} events={len({r['event'] for r in rs}):4d} series={len({r['series'] for r in rs}):3d} H1={a} H2={len(rs)-a}")


def score():
    if RESULT.exists():
        sys.exit("refusing a second run: " + str(RESULT))
    rows = build(True)
    g = groups(rows)
    mid = split_halves(rows)
    rng = np.random.default_rng(SEED)
    out = {"split_t": mid, "groups": {}}
    for k in ORDER + ["CONTROL", "ALL"]:
        rs = g[k]
        s = stats(rs, rng)
        h1, h2 = [r for r in rs if r["t"] < mid], [r for r in rs if r["t"] >= mid]
        s1, s2 = stats(h1, rng), stats(h2, rng)
        s["H1"], s["H2"] = s1, s2
        s["verdict"] = verdict(s["n"], s1.get("net_c"), s2.get("net_c"), s.get("pf", float("nan"))) if k in ORDER else "reference"
        out["groups"][k] = s
    RESULT.write_text(json.dumps(out, indent=1, default=str))
    for k, s in out["groups"].items():
        if s["n"]:
            print(f"{k:11s} n={s['n']:5d} ev={s['events']:4d} win={s['win']*100:5.1f}% price={s['price']*100:5.1f}c net={s['net_c']:+6.2f}c "
                  f"[{s['ci_lo_c']:+.2f},{s['ci_hi_c']:+.2f}] PF={s['pf']:.2f} H1={s['H1'].get('net_c', float('nan')):+.2f} H2={s['H2'].get('net_c', float('nan')):+.2f} {s['verdict']}")


if __name__ == "__main__":
    {"census": census, "score": score}[sys.argv[1]]()
