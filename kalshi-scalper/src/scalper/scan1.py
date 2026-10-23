"""SCAN1 (README, Pre-registration: SCAN1): mine conjunctions of simple conditions on the first 46 days of L1 entries, test the top 10 once on the last 23 days. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.scan1 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import itertools
import statistics as st
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

from . import feat1 as F
from .crowd1 import diff_z
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before the first run ----
TRAIN_DAYS, MIN_SUPPORT, TOP_K, MIN_UNION = 46, 400, 10, 600
DIFF_C, DIFF_Z_BAR, FALSIFY_C, FALSIFY_Z, STRESS_MIN_RULES = 0.010, 2.0, 0.003, 1.0, 6
CLASS = {"KXBTC15M": "btceth", "KXETH15M": "btceth", "KXSOL15M": "altcrypto", "KXXRP15M": "altcrypto", "KXDOGE15M": "altcrypto", "KXBNB15M": "altcrypto", "KXHYPE15M": "altcrypto",
         "KXNEAR15M": "altcrypto", "KXZEC15M": "altcrypto", "KXGOLD15M": "metals", "KXSILVER15M": "metals", "KXPLATINUM15M": "metals", "KXPALLADIUM15M": "metals",
         "KXCOPPER15M": "metals", "KXWTI15M": "energy", "KXNATGAS15M": "energy", "KXEURUSD15M": "fx", "KXGBPUSD15M": "fx", "KXUSDJPY15M": "fx"}
RESULT = DATA_DIR / "scan1_result.txt"


def conds(r: dict) -> dict[str, str]:
    """The condition each feature takes for one entry (feat1 layout: price, spread, rise3, d1, tib, dip, rng5, ...)."""
    x = r["x"]
    price, spread, rise3, tib, dip, rng5 = x[0], x[1], x[2], x[4], x[5], x[6]
    hour = datetime.fromtimestamp(r["close_ts"], timezone.utc).hour // 4
    wd = datetime.strptime(r["day"], "%Y-%m-%d").weekday()
    return {"price": "p<.92" if price < 0.92 else "p.92-.95" if price < 0.95 else "p>=.95",
            "spread": "spread<=1c" if spread <= 0.0105 else "spread>1c",
            "rise3": "rise3<-.02" if rise3 < -0.02 else "rise3 flat" if rise3 <= 0.02 else "rise3 .02-.10" if rise3 <= 0.10 else "rise3>.10",
            "rng5": "rng5<.10" if rng5 < 0.10 else "rng5 .10-.25" if rng5 < 0.25 else "rng5 .25-.45" if rng5 <= 0.45 else "rng5>.45",
            "tib": "tib0-1" if tib <= 1 else "tib2-4" if tib <= 4 else "tib5+",
            "dip": "dip<.50" if dip < 0.50 else "dip .50-.75" if dip < 0.75 else "dip>=.75",
            "class": "class " + CLASS.get(r["series"], "other"), "side": "side " + r["side"], "hour": f"hour {hour * 4:02d}-{hour * 4 + 3:02d}Z", "weekend": "weekend" if wd >= 5 else "weekday"}


def rules(depth: int = 3):
    feats = ["price", "spread", "rise3", "rng5", "tib", "dip", "class", "side", "hour", "weekend"]
    for d in range(1, depth + 1):
        yield from itertools.combinations(feats, d)


def mine(train: list[dict]) -> list[tuple[float, tuple[str, ...], int, float]]:
    """(score, rule, support, mean net) for every conjunction with at least MIN_SUPPORT train entries; score = mean - standard error. Also returns the number enumerated through `mine.count`."""
    cache = [conds(r) for r in train]
    nets = [r["net"] for r in train]
    stats: dict[tuple[str, ...], list[float]] = defaultdict(lambda: [0, 0.0, 0.0])
    for feats in rules():
        for c, nt in zip(cache, nets):
            key = tuple(c[f] for f in feats)
            s = stats[key]
            s[0] += 1; s[1] += nt; s[2] += nt * nt
    mine.count = len(stats)
    out = []
    for key, (n, sm, sq) in stats.items():
        if n >= MIN_SUPPORT:
            mean = sm / n
            var = max(sq / n - mean * mean, 0.0)
            out.append((mean - (var / n) ** 0.5, key, n, mean))
    return sorted(out, reverse=True)


mine.count = 0


def matches(r: dict, key: tuple[str, ...]) -> bool:
    c = set(conds(r).values())
    return all(k in c for k in key)


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    mk = [m for m in load() if all(x[1] is not None and x[2] is not None for x in m[2])]
    full = [(t, s, [(e, b, a, b, a) for e, b, a in c], cl, r) for t, s, c, cl, r in mk]
    rows, _, _ = F.build(full, 360)
    days = sorted({r["day"] for r in rows})
    cut = days[TRAIN_DAYS]
    train, test = [r for r in rows if r["day"] < cut], [r for r in rows if r["day"] >= cut]
    mined = mine(train)
    top = mined[:TOP_K]
    out = [f"SCAN1: {len(rows)} entries, train {len(train)} (to {days[TRAIN_DAYS - 1]}), test {len(test)}; {mine.count} distinct rule instances seen, {len(mined)} with support >= {MIN_SUPPORT}"]
    hit = [any(matches(r, key) for _, key, _, _ in top) for r in test]
    union = [r for r, h in zip(test, hit) if h]
    rest = [r for r, h in zip(test, hit) if not h]
    m, z, nd = diff_z(union, rest) if union and rest else (0.0, 0.0, 0)
    ms, _, _ = diff_z(union, rest, "stress") if union and rest else (0.0, 0.0, 0)
    tdays = sorted({r["day"] for r in test})
    mid = tdays[len(tdays) // 2]
    h1 = diff_z([r for r in union if r["day"] < mid], [r for r in rest if r["day"] < mid])[0]
    h2 = diff_z([r for r in union if r["day"] >= mid], [r for r in rest if r["day"] >= mid])[0]
    per_rule = []
    for sc, key, n, mean in top:
        sel = [r for r in test if matches(r, key)]
        oth = [r for r in test if not matches(r, key)]
        per_rule.append((key, n, mean, len(sel), st.mean(r["net"] for r in sel) if sel else 0.0, st.mean(r["net"] for r in oth)))
    good = sum(1 for _, _, _, ns, mt, mo in per_rule if ns and mt > mo)
    ok = len(union) >= MIN_UNION and m >= DIFF_C and z >= DIFF_Z_BAR and h1 > 0 and h2 > 0 and ms > 0 and good >= STRESS_MIN_RULES
    verdict = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (m < FALSIFY_C or z < FALSIFY_Z) else "NOT_ENOUGH_DATA")
    out += [f"verdict: {verdict}", f"union of top {TOP_K} rules on test: n={len(union)} vs rest n={len(rest)}: diff {100 * m:+.2f}c, z {z:+.2f}, days {nd}, halves {100 * h1:+.2f}c / {100 * h2:+.2f}c, stress {100 * ms:+.2f}c, rules above rest {good} of {TOP_K}",
            "top rules: conjunction | train n, train net | test n, test net | test rest net"]
    for key, n, mean, ns, mt, mo in per_rule:
        out.append(" AND ".join(key) + f" | {n}, {100 * mean:+.2f}c | {ns}, {100 * mt:+.2f}c | {100 * mo:+.2f}c")
    cnt = Counter(c for _, key, _, _ in mined[:100] for c in key)
    out.append("info: conditions most often in the top 100 train rules: " + ", ".join(f"{c} ({k})" for c, k in cnt.most_common(14)))
    big = sorted([x for x in mined if x[3] >= 0.01], key=lambda x: -x[2])[:12]
    out.append("info: largest-support rules with train net >= +1c: rule | train n, train net | test n, test net")
    for sc, key, n, mean in big:
        sel = [r for r in test if matches(r, key)]
        out.append(" AND ".join(key) + f" | {n}, {100 * mean:+.2f}c | {len(sel)}, {100 * st.mean(r['net'] for r in sel):+.2f}c" if sel else " AND ".join(key) + f" | {n}, {100 * mean:+.2f}c | 0")
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
