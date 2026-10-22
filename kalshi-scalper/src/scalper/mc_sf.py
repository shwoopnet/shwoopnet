"""MC1, SF1 and CAP1 (README, Pre-registration: MC1, SF1, FWD9 and CAP1): a walk-forward per-series entry-minute chooser, a flip-memory test, and a window co-occurrence table.
Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.mc_sf run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import statistics as st
import sys
from bisect import bisect_right
from collections import defaultdict

from . import lstrats as L
from .calibration import cluster_mean_z
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the first run ----
TIMES, DEFAULT_T, BURN_DAYS, REFIT_DAYS, MIN_TRAIN = (360, 480, 600), 360, 21, 7, 100
MC_Z, MC_DIFF_Z, MC_MIN_N, MIN_DAYS = 2.8, 2.0, 1000, 10
SF_Z, SF_MIN_GROUP, SF_PREV = 2.4, 500, 3
LIVE6 = ("KXBTC15M", "KXGOLD15M", "KXETH15M", "KXXRP15M", "KXDOGE15M", "KXNATGAS15M")
RESULT = DATA_DIR / "mc_sf_result.txt"


def choose(train: dict[int, list[float]]) -> int:
    """The entry time with the highest training mean among those with at least MIN_TRAIN earlier entries; else the default."""
    ok = {t: st.mean(v) for t, v in train.items() if len(v) >= MIN_TRAIN}
    return max(ok, key=lambda t: (ok[t], t == DEFAULT_T)) if ok else DEFAULT_T


def day_diff(a: list[dict], b: list[dict]):
    d = defaultdict(lambda: [[], []])
    for e in a:
        d[e["day"]][0].append(e["net"])
    for e in b:
        d[e["day"]][1].append(e["net"])
    rows = [(k, st.mean(v[0]) - st.mean(v[1])) for k, v in d.items() if v[0] and v[1]]
    return cluster_mean_z(rows) if len(rows) > 1 else (0.0, 0.0, 0.0)


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    by_t = {t: {e["ticker"]: e for e in L.hold_rule(full, t, L.L1["band"])} for t in TIMES}
    all_days = sorted({e["day"] for d in by_t.values() for e in d.values()})
    burn_end = all_days[BURN_DAYS]
    c = lambda x: f"{x * 100:+.2f}c"
    lines = []
    # ---------------- MC1
    series = sorted({e["series"] for e in by_t[DEFAULT_T].values()})
    oos_days = [d for d in all_days if d >= burn_end]
    chosen, rows = {}, []
    for s in series:
        for k, d in enumerate(oos_days):
            if k % REFIT_DAYS == 0:
                train = {t: [e["net"] for e in by_t[t].values() if e["series"] == s and e["day"] < d] for t in TIMES}
                cur = choose(train)
                chosen.setdefault(s, []).append(cur)
            for e in by_t[cur].values():
                if e["series"] == s and e["day"] == d:
                    rows.append(e)
    plain = [e for e in by_t[DEFAULT_T].values() if e["day"] >= burn_end]
    fixed10 = [e for e in by_t[600].values() if e["day"] >= burn_end]
    rows.sort(key=lambda e: e["close_ts"])
    n = len(rows)
    m, _, z = cluster_mean_z([(e["day"], e["net"]) for e in rows])
    h = n // 2
    h1, h2 = st.mean(e["net"] for e in rows[:h]), st.mean(e["net"] for e in rows[h:])
    stress = st.mean(e["stress"] for e in rows)
    dm, _, dz = day_diff(rows, plain)
    d10, _, z10 = day_diff(rows, fixed10)
    ok = n >= MC_MIN_N and len({e["day"] for e in rows}) >= MIN_DAYS and m > 0 and z >= MC_Z and h1 > 0 and h2 > 0 and stress > 0 and dm > 0 and dz >= MC_DIFF_Z
    lines += [f"MC1: {n} out-of-sample entries (days from {burn_end}); net {c(m)} (z {z:+.2f}) halves {c(h1)} / {c(h2)} fees x1.2 {c(stress)}",
              f"   plain 360 {len(plain)} entries {c(st.mean(e['net'] for e in plain))}; chooser minus plain {c(dm)} (z {dz:+.2f}); fixed 600 {len(fixed10)} entries {c(st.mean(e['net'] for e in fixed10))}; chooser minus fixed 600 {c(d10)} (z {z10:+.2f})",
              f"   VERDICT: {'NOT_YET_FALSIFIED' if ok else 'FALSIFIED'}", "   share of weeks each time was chosen (information): " + ", ".join(
                  f"{t}s {100 * sum(x.count(t) for x in chosen.values()) / sum(len(x) for x in chosen.values()):.0f}%" for t in TIMES)]
    # ---------------- SF1
    base = sorted(by_t[DEFAULT_T].values(), key=lambda e: e["close_ts"])
    per = defaultdict(list)
    for e in base:
        per[e["series"]].append(e)
    flip, calm = [], []
    for s, es in per.items():
        times = [e["close_ts"] for e in es]
        for i, e in enumerate(es):
            k = bisect_right(times, e["close_ts"] - L.L1["left_s"])
            if k < SF_PREV:
                continue
            (flip if any(x["gross"] < 0 for x in es[k - SF_PREV:k]) else calm).append(e)
    fm, _, fz = cluster_mean_z([(e["day"], e["net"]) for e in flip])
    cm, _, _ = cluster_mean_z([(e["day"], e["net"]) for e in calm])
    sd, _, sz = day_diff(flip, calm)
    if len(flip) < SF_MIN_GROUP or len(calm) < SF_MIN_GROUP:
        v = "NOT_ENOUGH_DATA"
    else:
        v = "NOT_YET_FALSIFIED" if abs(sz) >= SF_Z else "FALSIFIED"
    lines += [f"SF1: after a flip in the previous {SF_PREV} entries {len(flip)} at {c(fm)} (z {fz:+.2f}); calm {len(calm)} at {c(cm)}; after-flip minus calm {c(sd)} (day clustered z {sz:+.2f}); VERDICT: {v}"]
    # ---------------- CAP1 (information)
    win = defaultdict(list)
    for e in base:
        if e["series"] in LIVE6:
            win[e["close_ts"]].append(e)
    ks = defaultdict(int)
    alone, together = defaultdict(list), defaultdict(list)
    for ts, es in win.items():
        ks[len(es)] += 1
        for e in es:
            (alone if len(es) == 1 else together)[e["series"]].append(e["net"])
    lines.append("CAP1 (information): windows with k of the six live series having a favourite: " + ", ".join(f"{k}: {ks[k]}" for k in sorted(ks)))
    for s in LIVE6:
        a, t = alone[s], together[s]
        lines.append(f"   {s}: alone n {len(a)} at {c(st.mean(a)) if a else 'n/a'}; with others n {len(t)} at {c(st.mean(t)) if t else 'n/a'}")
    out = "\n".join(lines)
    RESULT.write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main(sys.argv)
