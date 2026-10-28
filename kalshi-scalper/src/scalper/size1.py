"""SIZE1 (README, Pre-registration: SIZE1): size and fee audit. Analysis only."""
from __future__ import annotations
import csv, json, math, statistics, sys
from collections import defaultdict
from . import maker4 as M4
from .daycut1 import history, LIVE
from .paths import DATA_DIR

RESULT = DATA_DIR / "size1_result.txt"


def fee_exact(p, k=0.07):
    return k * p * (1 - p)


def fee_order(p, c, k=0.07):
    return math.ceil(k * c * p * (1 - p) * 100 - 1e-9) / 100 / c


def pf(xs):
    w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0); return w / l if l else 99.0


def main():
    lines = []
    # L1 history: rows are (entry_ts, close_ts, 11 * net) with net = payoff - p - exact fee
    from . import feat1 as F
    from .flat_r import load_rep
    from .fwd_reads import load_fresh
    from .hs1 import load
    mk = {}
    for m in load() + load_fresh() + load_rep():
        if m[1].endswith("15M") and all(x[1] is not None and x[2] is not None for x in m[2]):
            mk[m[0]] = (m[0], m[1], [(e, b, a, b, a) for e, b, a, *_ in m[2]], m[3], m[4])
    rows, _, _ = F.build(list(mk.values()), 360)
    pays = [r["net"] + r["price"] + fee_exact(r["price"]) for r in rows]
    bad = sum(1 for x in pays if min(abs(x), abs(x - 1)) > 1e-6)
    lines.append(f"L1 history: {len(rows)} entries; payoff check (net + price + exact fee is 0 or 1): {len(rows) - bad} ok, {bad} not")
    for label, f in (("exact per contract (as reported)", lambda p: fee_exact(p)), ("1 contract, rounded per order", lambda p: fee_order(p, 1)), ("10 contracts, rounded per order", lambda p: fee_order(p, 10))):
        v = [round(py) - r["price"] - f(r["price"]) for r, py in zip(rows, pays)]
        lines.append(f"  {label:34s} PF {pf(v):.3f}, net {100 * sum(v) / len(v):+.3f}c per contract, avg fee {100 * sum(f(r['price']) for r in rows) / len(rows):.3f}c")
    # MAKER4 bounds with rounded fees: patch the module fee
    tape = {}
    for f in sorted((DATA_DIR / "maker4").glob("tape_*.json")):
        tape.update(json.loads(f.read_text()))
    Mk = M4.sampled(M4.markets())
    for qlabel, strict in (("Q1", True), ("Q0", False)):
        for flabel, fn in (("exact", lambda p, k: fee_exact(p, k)), ("1 contract rounded", lambda p, k: fee_order(p, 1, k)), ("10 contracts rounded", lambda p, k: fee_order(p, 10, k))):
            M4.fee = fn
            for k in (0.0175, 0.0):
                byc = defaultdict(float)
                for tk, (series, close, cs) in Mk.items():
                    if tk in tape:
                        r = M4.simulate(close, cs, tape[tk], strict, k)
                        if r[5]: byc[close] += r[0]
                v = list(byc.values())
                lines.append(f"MAKER4 {qlabel} maker fee {100 * k:.2f}%, {flabel:20s}: PF {pf(v):.3f}, net {100 * sum(v) / len(v):+.2f}c per close, closes {len(v)}")
    # depth from the live export
    d = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(LIVE)):
        for fld in ("bidSize", "askSize", "depthAtLimit", "count"):
            try:
                if r[fld] not in ("", None): d[r["series"]][fld].append(float(r[fld]))
            except (ValueError, KeyError):
                pass
    for s, f in sorted(d.items()):
        parts = [f"{k} median {statistics.median(v):.0f} (n={len(v)})" for k, v in f.items() if v]
        lines.append(f"live {s}: " + "; ".join(parts))
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main()
