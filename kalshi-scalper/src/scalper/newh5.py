"""NEWH5: four skip filters on live L1's gold entry (research only).

Registration: workers/NEWH5_REGISTRATION.md (pushed before any scoring).
F1 GLADF (hourly ladder disagrees), F2 GTHIN (thin window), F3 GOIDROP (open interest fell before the look),
F4 GPRIOR (previous 15 minutes moved hard against the favourite).
Parent: L1 on KXGOLD15M, signal at -360 s, fill at the -300 s candle's ask, live 25c exit at minute closes (hold reported).

    PYTHONPATH=src python -m scalper.newh5 run
"""
from __future__ import annotations

import math
import sys
from collections import defaultdict

from .exitoig import load
from .newh2 import DISC_END, day, fee, ladder, pf, side_ask
from .newh3 import side_bid

GOLD = "KXGOLD15M"
FILES = ("l1b", "book", "fresh", "five")
SIZES = (10, 16)
MIN_SKIP = 20


def money(fill, won, exit_bid, c, m):
    if exit_bid is not None:
        return c * (exit_bid - fill) - fee(fill, c, m) - fee(exit_bid, c, m)
    return c * ((1.0 if won else 0.0) - fill) - fee(fill, c, m)


def entries(W):
    E, gaps = [], defaultdict(int)
    for close, w in sorted(W.items()):
        c = w["c"]
        s = c.get(-360)
        if s is None:
            continue
        side = None
        for sd in ("yes", "no"):
            a = side_ask(s, sd)
            if a is not None and 0.88 <= a <= 0.97:
                side = sd
                break
        if side is None:
            continue
        fr = c.get(-300)
        a = side_ask(fr, side)
        if a is None or a > 0.99:
            gaps["no fill"] += 1
            continue
        won = w["result"] == side
        xb = None
        for off in (-240, -180, -120, -60):
            b = side_bid(c.get(off), side)
            if b is not None and b <= 0.25 + 1e-9:
                xb = b
                break
        e = {"close": close, "day": day(close), "side": side, "sig": side_ask(s, side), "fill": a, "won": won,
             "vol0": fr[2] == 0, "xb": xb, "w": w}
        for cc in SIZES:
            for m, tag in ((1.0, ""), (1.2, "x")):
                e[f"x{cc}{tag}"] = money(a, won, xb, cc, m)
                e[f"h{cc}{tag}"] = money(a, won, None, cc, m)
        E.append(e)
    return E, dict(gaps)


# ---------- features (no outcome used) ----------

def f_ladder(E, L):
    for e in E:
        e["lad"] = None
        if e["close"] % 3600 or e["close"] not in L:
            continue
        rows = L[e["close"]].get(-360) or []
        k15 = e["w"]["strike"]
        lo = [(k, b, a) for k, b, a in rows if k <= k15]
        hi = [(k, b, a) for k, b, a in rows if k > k15]
        if not lo or not hi or k15 is None:
            continue
        kl, bl, al = max(lo)
        kh, bh, ah = min(hi)
        if kh - kl > 6.0 + 1e-9:
            continue
        ml, mh = (bl + al) / 2, (bh + ah) / 2
        p = ml + (mh - ml) * (k15 - kl) / (kh - kl)
        e["lad"] = p if e["side"] == "yes" else 1 - p


def f_volume(E):
    for e in E:
        e["V"] = sum(v[2] for off, v in e["w"]["c"].items() if off <= -360)


def f_oi(E):
    for e in E:
        a, b = e["w"]["c"].get(-540), e["w"]["c"].get(-360)
        e["oi"] = (b[3] / a[3]) if (a and b and a[3] and b[3] is not None) else None


def f_prior(E, W):
    for e in E:
        p = W.get(e["close"] - 900)
        k, kp = e["w"]["strike"], (p or {}).get("strike")
        e["M"] = None if (k is None or kp is None) else (k - kp) * (1 if e["side"] == "yes" else -1)


def quantile(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    i = q * (len(xs) - 1)
    lo = int(math.floor(i))
    return xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (i - lo)


# ---------- statistics ----------

def worst_day(xs):
    d = defaultdict(float)
    for e, v in xs:
        d[e["day"]] += v
    return min(d.values()) if d else 0.0


def diff_z(K, S, key):
    if len(K) < 2 or len(S) < 2:
        return float("nan"), float("nan")
    mk = sum(e[key] for e in K) / len(K)
    ms = sum(e[key] for e in S) / len(S)
    u = defaultdict(float)
    for e in K:
        u[e["day"]] += (e[key] - mk) / len(K)
    for e in S:
        u[e["day"]] -= (e[key] - ms) / len(S)
    g = len(u)
    var = sum(x * x for x in u.values()) * g / (g - 1)
    return mk - ms, ((mk - ms) / math.sqrt(var) if var > 0 else float("nan"))


def assess(E, flag, name, prefix="x"):
    """Return (lines, ok, n_skipped) for one window."""
    K = [e for e in E if not flag(e)]
    S = [e for e in E if flag(e)]
    ok, lines = True, []
    for cc in SIZES:
        key, kx = f"{prefix}{cc}", f"{prefix}{cc}x"
        base, kept, skip = sum(e[key] for e in E), sum(e[key] for e in K), sum(e[key] for e in S)
        skx = sum(e[kx] for e in S)
        wb = worst_day([(e, e[key]) for e in E])
        wk = worst_day([(e, e[key]) for e in K])
        d, z = diff_z(K, S, key)
        c1 = skip < 0 and skx < 0
        c2 = wk >= wb - 1e-9
        c3 = z >= 2.0
        ok = ok and c1 and c2 and c3
        lr = lambda xs: (1 - sum(e["won"] for e in xs) / len(xs)) if xs else float("nan")
        lines.append(
            f"    C={cc}: base n {len(E)} net ${base:+.2f} PF {pf([e[key] for e in E]):.3f} | kept n {len(K)} PF {pf([e[key] for e in K]):.3f}"
            f" | SKIPPED n {len(S)} net ${skip:+.2f} (x1.2 ${skx:+.2f}) PF {pf([e[key] for e in S]):.3f} loss rate {lr(S):.3f} vs kept {lr(K):.3f}\n"
            f"           net/opportunity base {base / len(E) * 100 / cc:+.3f}c/ct kept {kept / len(E) * 100 / cc:+.3f}c/ct | worst day base ${wb:+.2f}"
            f" kept ${wk:+.2f} | kept-minus-skipped ${d:+.3f}/entry day z {z:+.2f} | [{'net' if c1 else '-'} {'day' if c2 else '-'} {'z' if c3 else '-'}]")
    return lines, ok, len(S)


def run():
    W = load(GOLD, FILES)
    E, gaps = entries(W)
    f_ladder(E, ladder())
    f_volume(E)
    f_oi(E)
    f_prior(E, W)
    disc = [e for e in E if e["close"] < DISC_END]
    val = [e for e in E if e["close"] >= DISC_END]
    v20 = quantile([e["V"] for e in disc], 0.20)
    m80 = quantile([abs(e["M"]) for e in disc if e["M"] is not None], 0.80)
    print(f"NEWH5 run. Gold windows {len(W)} (disc {sum(c < DISC_END for c in W)}, val {sum(c >= DISC_END for c in W)}); "
          f"L1 entries {len(E)} (disc {len(disc)}, val {len(val)}); gaps {gaps}; 25c exits {sum(e['xb'] is not None for e in E)}")
    print(f"Thresholds from discovery features only: V 20th pct {v20:.1f} contracts; |M| 80th pct ${m80:.2f}")
    miss = {"F1 ladder defined (top-of-hour)": sum(e['lad'] is not None for e in E),
            "F3 oi missing": sum(e['oi'] is None for e in E), "F4 prior missing": sum(e['M'] is None for e in E)}
    print("Coverage:", miss, "\n")
    F = {
        "F1 GLADF": lambda e: e["lad"] is not None and e["lad"] <= e["sig"] - 0.05 + 1e-9,
        "F2 GTHIN": lambda e: e["V"] < v20,
        "F3 GOIDROP": lambda e: e["oi"] is not None and e["oi"] <= 0.95 + 1e-9,
        "F4 GPRIOR": lambda e: e["M"] is not None and e["M"] < 0 and abs(e["M"]) >= m80 - 1e-9,
    }
    verdicts = {}
    for name, flag in F.items():
        print(f"== {name}")
        oks, ns = [], []
        for wn, X in (("DISC", disc), ("VAL", val)):
            for label, xs, pre in (("25c exit (headline)", X, "x"), ("hold", X, "h"),
                                   ("25c exit, zero-volume fills removed", [e for e in X if not e["vol0"]], "x")):
                lines, ok, n = assess(xs, flag, name, pre)
                print(f"  {wn} {label}:")
                print("\n".join(lines))
                if label.startswith("25c exit (headline)"):
                    oks.append(ok)
                    ns.append(n)
        if min(ns) < MIN_SKIP:
            v = "NOT_ENOUGH_DATA"
        elif all(oks):
            v = "NOT_YET_FALSIFIED"
        else:
            v = "FALSIFIED"
        verdicts[name] = (v, ns)
        print(f"  -> {v} (skipped disc {ns[0]}, val {ns[1]})\n")
    print("Verdicts (N = 4):")
    for k, (v, ns) in verdicts.items():
        print(f"  {k}: {v} (skipped {ns[0]} / {ns[1]})")


if __name__ == "__main__":
    if sys.argv[1:] == ["run"]:
        run()
    else:
        print(__doc__)
