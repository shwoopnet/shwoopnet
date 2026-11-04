"""NHLROUND1: cheap-side pool of KXNHLGOAL 1+ rungs, only in games whose ladder sum of YES asks is at most E - M. Research only.
Registration: workers/NHLROUND1_REGISTRATION.md (E and M fixed there, before any outcome). Fetches NOTHING: reads the NHLALL1 cache
through nhlall1.entries(). Refuses to score until workers/NHLALL1_RESULT.md exists.
  python -m scalper.nhlround1 score
"""
from __future__ import annotations
import json, sys, statistics as st
from pathlib import Path
from .nhlall1 import conn, entries, pick_two, clustered, verdict, fmt

ROOT = Path(__file__).resolve().parents[2]
E_SCORERS = 3.9085   # ESPN FIT games: mean listed players (volume-positive 1+ rung) who scored
MARGIN = 0.3
THRESH = E_SCORERS - MARGIN


def is_round(lsum: float, nl: int) -> bool:
    """Treated game: at least 8 valid rungs and ladder sum at or below E - M."""
    return nl >= 8 and lsum <= THRESH + 1e-12


def score():
    if not (ROOT / "workers" / "NHLALL1_RESULT.md").exists():
        print("NHLALL1_RESULT.md not written yet: refusing to score")
        return
    G = entries(conn())
    med = st.median([g["start"] for g in G if is_round(g["lsum"], g["nl"])] or [0])
    T, U = [], []
    for g in G:
        for t in pick_two(g["cheap"]):
            t["half"] = "H1" if g["start"] < med else "H2"
            (T if is_round(g["lsum"], g["nl"]) else U).append(t)
    out = dict(games=len(G), treated_games=sum(1 for g in G if is_round(g["lsum"], g["nl"])), thresh=THRESH)
    d = dict(game=clustered(T, "game"), date=clustered(T, "date"), x12=clustered(T, "game", 1.2))
    for h in ("H1", "H2"):
        d[h] = clustered([t for t in T if t["half"] == h], "game")
    d["verdict"] = verdict(d["game"]["n"], [d["H1"]["mean_c"], d["H2"]["mean_c"]], d["game"]["lo95_c"], d["game"]["pf"])
    out["treated"] = d
    out["untreated_information"] = clustered(U, "game")
    json.dump(out, open(ROOT / "workers" / "NHLROUND1_RESULT.json", "w"), indent=1, default=str)
    for k, v in out.items():
        print(k, v if not isinstance(v, dict) else {a: (fmt(b) if isinstance(b, dict) else b) for a, b in v.items()})


if __name__ == "__main__":
    if sys.argv[1] == "score":
        score()
