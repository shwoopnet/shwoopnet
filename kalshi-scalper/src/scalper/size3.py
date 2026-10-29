"""SIZE3 (README, Pre-registration: SIZE3): size L1 by price paid and expected win rate. Research only.
Usage: python -m scalper.size3 run   (once)
"""
from __future__ import annotations

import sys
from collections import defaultdict

from .calibration import cluster_mean_z
from .house1 import dstats
from .l1studies import fee, pf
from .paths import DATA_DIR
from .tstop1 import LEFT, LIVE5, day, load

BASE = 13
BANDS = [(88, 90), (91, 92), (93, 94), (95, 97)]
NAMES = {"KXGOLD15M": "gold", "KXBTC15M": "Bitcoin", "KXETH15M": "Ethereum", "KXDOGE15M": "Dogecoin", "KXXRP15M": "XRP"}
ZBAR = 5.17


def band(r):
    c = round(r["price"] * 100)
    return next((b for b in BANDS if b[0] <= c <= b[1]), None)


def won(r):
    return r["won"] > 0.5


def dollars(r, c, m=1.0):
    return 0.0 if c <= 0 else c * ((1.0 if won(r) else 0.0) - r["price"]) - m * c * fee(r["price"], c)


def edge(rs):
    return (sum(won(r) for r in rs) / len(rs) - sum(r["price"] for r in rs) / len(rs)) if rs else -9.0


def mult_band_rank(train, reverse=False):
    if reverse:
        return {(95, 97): 2.0, (93, 94): 1.5, (91, 92): 1.0, (88, 90): 0.5}
    ranked = sorted(BANDS, key=lambda b: -edge([r for r in train if band(r) == b]))
    return dict(zip(ranked, (2.0, 1.5, 1.0, 0.5)))


def kelly_table(train, k):
    def f_of(rs):
        if not rs:
            return 0.0
        n = len(rs); c = sum(r["price"] for r in rs) / n; p_hat = sum(won(r) for r in rs) / n
        p_s = c + (p_hat - c) * n / (n + k)
        return (p_s - c) / (1 - c)
    f_pool = f_of(train)
    tab = {}
    for s in NAMES:
        for b in BANDS:
            f = f_of([r for r in train if r["series"] == s and band(r) == b])
            tab[(s, b)] = 0.0 if f <= 0 or f_pool <= 0 else min(2.0, f / f_pool)
    return tab


def run_variant(rows, mult_fn, m=1.0):
    """rows sorted by entry; mult_fn(r, history) -> multiplier. Returns (entry_t, close_t, dollars, series, band)."""
    out = []
    for r in rows:
        mu = mult_fn(r)
        c = int(round(BASE * mu))
        out.append((r["close_ts"] - LEFT, r["close_ts"], dollars(r, c, m), r["series"], band(r)))
    return out


def rolling_fn(rows_all, train_wr, N):
    by_series = defaultdict(list)
    for r in sorted(rows_all, key=lambda r: r["close_ts"]):
        by_series[r["series"]].append(r)
    closes = {s: [(r["close_ts"], won(r)) for r in rs] for s, rs in by_series.items()}

    def fn(r):
        t = r["close_ts"] - LEFT
        hist = [w for c, w in closes[r["series"]] if c <= t][-N:]
        if len(hist) < N:
            return 1.0
        return 1.5 if sum(hist) / N >= train_wr[r["series"]] else 0.5
    return fn


def summarize(tr, flat):
    a = dstats([(x[0], x[1], x[2]) for x in tr]); b = dstats([(x[0], x[1], x[2]) for x in flat])
    byb = defaultdict(float); bym = defaultdict(float)
    for x in tr:
        byb[x[4]] += x[2]; bym[x[3]] += x[2]
    tot = sum(x[2] for x in tr)
    top_b = max(byb.values(), key=abs) / tot if tot else 0.0
    top_m = max(bym.values(), key=abs) / tot if tot else 0.0
    dd = defaultdict(float)
    for x, y in zip(tr, flat):
        dd[day(x[0])] += x[2] - y[2]
    _, _, z = cluster_mean_z([(k, v) for k, v in dd.items()]) if len(dd) > 1 else (0, 0, 0.0)
    return a, b, top_b, top_m, z


def main():
    if sys.argv[1:] != ["run"]:
        print(__doc__); return
    out = DATA_DIR / "size3_result.txt"
    if out.exists():
        print("Refusing to run again"); return
    rows = sorted([r for r in load() if r["series"] in LIVE5 and band(r) is not None], key=lambda r: r["close_ts"])
    train = [r for r in rows if r["win"] == 0]
    train_wr = {s: (sum(won(r) for r in train if r["series"] == s) / max(1, sum(1 for r in train if r["series"] == s))) for s in NAMES}
    variants = []
    for g, ser in list({nm: {s} for s, nm in NAMES.items()}.items()) + [("live five", set(NAMES))]:
        tr_g = [r for r in train if r["series"] in ser]
        ma = mult_band_rank(tr_g); mb = mult_band_rank(tr_g, reverse=True)
        variants.append((f"(a) band by train edge, {g}", ser, lambda r, ma=ma: ma[band(r)]))
        variants.append((f"(b) owner's hint 95-97c heavy, {g}", ser, lambda r, mb=mb: mb[band(r)]))
    for k in (50, 200):
        tab = kelly_table(train, k)
        variants.append((f"(c) shrunk Kelly k={k}", set(NAMES), lambda r, tab=tab: tab[(r["series"], band(r))]))
    for N in (20, 50):
        variants.append((f"(d) rolling last {N}", set(NAMES), rolling_fn(rows, train_wr, N)))
    def spread_fn(r):
        q = r.get("entry_q")
        if not q:
            return 1.0
        sp = q[1] - q[0]
        return 1.5 if sp <= 0.01 + 1e-9 else (0.5 if sp >= 0.02 - 1e-9 else 1.0)
    variants.append(("(e) spread at entry", set(NAMES), spread_fn))
    lines, passes = [f"SIZE3: {len(rows)} entries, live five, base {BASE} contracts; t1 is the train window (in-sample)"], []
    for name, ser, fn in variants:
        ok, parts = True, []
        for w in range(3):
            rs = [r for r in rows if r["series"] in ser and r["win"] == w]
            tr = run_variant(rs, fn); flat = run_variant(rs, lambda r: 1.0)
            a, b, tb, tm, z = summarize(tr, flat)
            s12 = dstats([(x[0], x[1], x[2]) for x in run_variant(rs, fn, 1.2)])
            net_ok = a["net"] >= 1.10 * b["net"] if b["net"] > 0 else a["net"] >= b["net"] + 0.10 * abs(b["net"])
            worst_ok = a["worst"] >= b["worst"]
            ok = ok and net_ok and worst_ok and z >= ZBAR
            parts.append(f"t{w + 1}: net ${a['net']:+.2f} vs flat ${b['net']:+.2f} ({100 * (a['net'] / b['net'] - 1) if b['net'] else 0:+.0f}%) PF {a['pf']:.3f} vs {b['pf']:.3f} worst ${a['worst']:+.2f} vs ${b['worst']:+.2f} DD ${a['dd']:.2f} vs ${b['dd']:.2f} top band {100 * tb:.0f}% top market {100 * tm:.0f}% z {z:+.2f} fees1.2 ${s12['net']:+.2f} [{'net' if net_ok else '-'} {'worst' if worst_ok else '-'}]")
        if ok:
            passes.append(name)
        lines.append(f"{name}: {'PASSES' if ok else 'fails'}")
        lines += ["    " + p for p in parts]
    lines.insert(0, "SIZE3 VERDICT: " + (("passes: " + "; ".join(passes)) if passes else "FALSIFIED (no variant beats flat by 10% with a worst day no worse in all three thirds at the deflated z)"))
    out.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main()
