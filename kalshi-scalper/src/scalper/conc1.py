"""CONC1 (README, Pre-registration: CONC1): are L1 favourites that the other crypto series back better than ones they contradict? Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.conc1 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import random
import statistics as st
import sys
from collections import defaultdict

from . import lstrats as L
from .crowd1 import diff_z
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the first run ----
CRYPTO = ["KXBTC15M", "KXETH15M", "KXXRP15M", "KXDOGE15M"]
LEAN_HI, LEAN_LO = 0.60, 0.40
DIFF_C, DIFF_Z_BAR, FALSIFY_C, FALSIFY_Z, MIN_N, MIN_DAYS, MONTH_MIN, PLACEBO_REPS, SEED = 0.010, 2.0, 0.003, 1.0, 300, 10, 30, 100, 59
RESULT = DATA_DIR / "conc1_result.txt"


def lean(bid: float, ask: float):
    """'yes', 'no' or None (neutral) from a YES candle's quote."""
    mid = (bid + ask) / 2
    return "yes" if mid >= LEAN_HI else "no" if mid <= LEAN_LO else None


def classify(ents: list[dict], quotes: dict) -> tuple[list[dict], list[dict]]:
    """(agree, disagree). quotes[(close_ts, series)] = (bid, ask) of the YES candle ending 360 s before the close."""
    agree, dis = [], []
    for e in ents:
        if e["series"] not in CRYPTO:
            continue
        leans = [lean(*quotes[(e["close_ts"], s)]) for s in CRYPTO if s != e["series"] and (e["close_ts"], s) in quotes]
        leans = [x for x in leans if x]
        if not leans:
            continue
        (dis if any(x != e["side"] for x in leans) else agree).append(e)
    return agree, dis


def judge(agree: list[dict], dis: list[dict]) -> dict:
    n, days = len(dis), len({r["day"] for r in dis})
    m, z, _ = diff_z(agree, dis)
    a, d = sorted(agree, key=lambda r: r["close_ts"]), sorted(dis, key=lambda r: r["close_ts"])
    ha, hd = len(a) // 2, len(d) // 2
    h1 = st.mean(r["net"] for r in a[:ha]) - st.mean(r["net"] for r in d[:hd]) if ha and hd else 0.0
    h2 = st.mean(r["net"] for r in a[ha:]) - st.mean(r["net"] for r in d[hd:]) if ha and hd else 0.0
    ms, _, _ = diff_z(agree, dis, "stress")
    months = defaultdict(lambda: [[], []])
    for r in agree:
        months[r["day"][:7]][0].append(r["net"])
    for r in dis:
        months[r["day"][:7]][1].append(r["net"])
    mdiff = {k: st.mean(v[0]) - st.mean(v[1]) for k, v in months.items() if len(v[1]) >= MONTH_MIN and v[0]}
    rng = random.Random(SEED)
    pool = agree + dis
    pz = []
    for _ in range(PLACEBO_REPS):
        rng.shuffle(pool)
        pz.append(diff_z(pool[:len(agree)], pool[len(agree):])[1])
    p95 = sorted(pz)[int(0.95 * len(pz)) - 1]
    ok = (n >= MIN_N and days >= MIN_DAYS and m >= DIFF_C and z >= DIFF_Z_BAR and h1 > 0 and h2 > 0 and ms > 0
          and sum(1 for v in mdiff.values() if v > 0) >= min(2, len(mdiff)) and z > p95)
    if n < MIN_N or days < MIN_DAYS:
        verdict = "NOT_ENOUGH_DATA"
    elif ok:
        verdict = "NOT_YET_FALSIFIED"
    elif m < FALSIFY_C or z < FALSIFY_Z:
        verdict = "FALSIFIED"
    else:
        verdict = "NOT_ENOUGH_DATA"
    loss = lambda xs: 100 * sum(1 for r in xs if r["gross"] < 0) / max(1, len(xs))
    return {"verdict": verdict, "n_agree": len(agree), "n_disagree": n, "days": days, "diff_c": 100 * m, "z": z,
            "halves_c": (100 * h1, 100 * h2), "stress_diff_c": 100 * ms, "months_c": {k: 100 * v for k, v in sorted(mdiff.items())},
            "placebo_tail": p95, "agree_c": 100 * st.mean(r["net"] for r in agree) if agree else 0.0,
            "disagree_c": 100 * st.mean(r["net"] for r in dis) if dis else 0.0,
            "loss_pct_agree": loss(agree), "loss_pct_disagree": loss(dis)}


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    quotes = {}
    for _, s, candles, close_ts, _ in mk:
        if s in CRYPTO:
            c = next((x for x in candles if x[0] == close_ts - L.L1["left_s"]), None)
            if c:
                quotes[(close_ts, s)] = (c[1], c[2])
    ents = L.hold_rule(mk, L.L1["left_s"], L.L1["band"])
    r = judge(*classify(ents, quotes))
    out = ["CONC1"] + [f"{k}: {v}" for k, v in r.items()]
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)


FRESH_FROM = "2026-10-14"                       # CONC1's history ends 2026-10-13 22:15; the forward claim uses later days only
F_DIFF_C, F_Z, F_MIN_N = 0.010, 2.0, 300


def conc2f(markets: list[tuple]) -> str:
    """CONC2-F (README): DISAGREE minus AGREE on fresh days from FRESH_FROM; the reverse of CONC1's registered claim."""
    quotes = {}
    for _, s, candles, close_ts, _ in markets:
        if s in CRYPTO:
            c = next((x for x in candles if x[0] == close_ts - L.L1["left_s"]), None)
            if c:
                quotes[(close_ts, s)] = (c[1], c[2])
    ents = [e for e in L.hold_rule(markets, L.L1["left_s"], L.L1["band"]) if e["day"] >= FRESH_FROM]
    agree, dis = classify(ents, quotes)
    days = len({r["day"] for r in dis})
    if len(dis) < 2 or not agree:
        return f"CONC2-F: DISAGREE n={len(dis)}, AGREE n={len(agree)}; VERDICT: NOT_ENOUGH_DATA"
    m, z, _ = diff_z(dis, agree)
    ms, _, _ = diff_z(dis, agree, "stress")
    d, a = sorted(dis, key=lambda r: r["close_ts"]), sorted(agree, key=lambda r: r["close_ts"])
    hd, ha = len(d) // 2, len(a) // 2
    h1 = st.mean(r["net"] for r in d[:hd]) - st.mean(r["net"] for r in a[:ha])
    h2 = st.mean(r["net"] for r in d[hd:]) - st.mean(r["net"] for r in a[ha:])
    ok = len(dis) >= F_MIN_N and m >= F_DIFF_C and z >= F_Z and ms > 0 and h1 > 0 and h2 > 0
    v = "NOT_YET_FALSIFIED" if ok else ("NOT_ENOUGH_DATA" if len(dis) < F_MIN_N else "FALSIFIED")
    c = lambda x: f"{x * 100:+.2f}c"
    return (f"CONC2-F: DISAGREE n={len(dis)} on {days} days at {c(st.mean(r['net'] for r in dis))}, AGREE n={len(agree)} at {c(st.mean(r['net'] for r in agree))}; "
            f"difference {c(m)} (day clustered z {z:+.2f}); halves {c(h1)} / {c(h2)}; stress {c(ms)}; VERDICT: {v}")
