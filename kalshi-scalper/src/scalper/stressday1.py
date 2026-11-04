"""STRESSDAY1 (README "STRESSDAY1"; workers/STRESSDAY1_REGISTRATION.md): census of cheap-side (ask 3c to 30c) entries on market-stress days
vs calm days. Cheap side only (owner rule). CENSUS ONLY: this module reads entries.jsonl rows, keeps ONLY (cat, series, look, t, event, ask)
and never touches 'won' or 'net'; no outcome is joined, aggregated or printed. No Kalshi fetch. Discovery only.

Usage: python3 -I -m scalper.stressday1 census ENTRIES_JSONL VIX_CHART_JSON
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATS = ("Financials", "Commodities", "Crypto")
FROZEN_FROM = 1791043200          # 2026-10-03T16:00Z, never fetched or joined
RELEASES = ("FOMC", "CPI", "JOBS")
ASK_HI = 0.30
MIN_STRESS_DAYS, MIN_TREATED = 25, 150
KEEP = ("cat", "series", "look", "t", "event", "ask")


def day_of(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def load_vix(path):
    j = json.load(open(path))["chart"]["result"][0]
    return sorted((day_of(t), c) for t, c in zip(j["timestamp"], j["indicators"]["quote"][0]["close"]) if c)


def vix_change(vix, d):
    """Close-to-close change of the last two sessions strictly BEFORE date d (known before d opens)."""
    prev = [x for x in vix if x[0] < d]
    return prev[-1][1] / prev[-2][1] - 1 if len(prev) >= 2 else None


def releases(path=ROOT / "workers" / "EVENT1_CALENDAR.csv"):
    out = set()
    for line in open(path):
        p = line.split(",")
        if len(p) > 2 and p[2] in RELEASES:
            out.add(p[0])
    return out


def entry_rows(rows):
    """T-look entries (entry time = close - minutes) of the registered categories, before the frozen date. Outcome fields are dropped."""
    out = []
    for r in rows:
        r = {k: r[k] for k in KEEP}
        assert r["ask"] <= ASK_HI + 1e-9, "favourite side"
        if r["cat"] not in CATS or not r["look"].startswith("T") or r["t"] >= FROZEN_FROM:
            continue
        te = r["t"] - int(r["look"][1:]) * 60
        if te >= FROZEN_FROM:
            continue
        r["d"] = day_of(te)
        out.append(r)
    return out


def cut_point(vix, days):
    """67th percentile of the signed prior-day VIX change over the FIRST TWO THIRDS of the development days."""
    ch = sorted(x for x in (vix_change(vix, d) for d in days[: len(days) * 2 // 3]) if x is not None)
    return ch[int(len(ch) * 2 / 3)]


def census(rows, vix, rel):
    ents = entry_rows(rows)
    days = sorted({e["d"] for e in ents})
    cut = cut_point(vix, days)
    stress = lambda d: ((vix_change(vix, d) or -9) >= cut) or d in rel
    sd = [d for d in days if stress(d)]
    n_st = sum(1 for e in ents if stress(e["d"]))
    res = {"entries": len(ents), "days": len(days), "cut": cut, "stress_days": len(sd), "stress_entries": n_st,
           "calm_entries": len(ents) - n_st, "stress_events": len({e["event"] for e in ents if stress(e["d"])}),
           "by_cat": {c: sum(1 for e in ents if e["cat"] == c) for c in CATS}}
    res["verdict"] = "RUNNABLE" if res["stress_days"] >= MIN_STRESS_DAYS and res["stress_entries"] >= MIN_TREATED else "NOT_ENOUGH_DATA"
    return res


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "census":
        rows = [json.loads(l) for l in open(sys.argv[2]) if l.strip()]
        print(json.dumps(census(rows, load_vix(sys.argv[3]), releases()), indent=1))
