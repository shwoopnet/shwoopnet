"""TAPE20 (README, Pre-registration: TAPE20): sixteen rules on who was trading in the two minutes before the 6 minute L1 decision (taker flow, trade counts and sizes from
Kalshi's public trade tape). Discovery on the first two thirds of the days, confirmation on the last third; each group is compared with the rest of the SAME
entries. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.tape20 run     (once; a second run is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import json
import statistics as st
import sys
import time

from . import feat1 as F
from .crowd1 import diff_z
from .fwd_reads import load_fresh
from .flat_r import load_rep
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before any outcome was split ----
SER = ("KXBTC15M", "KXETH15M", "KXXRP15M", "KXGOLD15M", "KXSOL15M")
DISC_FRAC = 2 / 3
MIN_N_DISC, MIN_N_CONF = 150, 60
DISC_C, DISC_Z, CONF_C, CONF_Z, FALSIFY_C, FALSIFY_Z = 0.020, 2.0, 0.010, 1.0, 0.005, 1.0
TAPE = DATA_DIR / "tape_flow.json"
RESULT = DATA_DIR / "tape20_result.txt"


def share(f: dict, side: str, tail: bool = False):
    """Favourite-side share of taker contracts over the window (or its last 60 seconds)."""
    a, b = (f["yes60"], f["no60"]) if tail else (f["yes"], f["no"])
    tot = a + b
    return None if tot <= 0 else (a if side == "yes" else b) / tot


def head_share(f: dict, side: str):
    """Share in the first minute (whole window minus the last 60 seconds)."""
    a, b = f["yes"] - f["yes60"], f["no"] - f["no60"]
    tot = a + b
    return None if tot <= 0 else (a if side == "yes" else b) / tot


def attach(rows: list[dict], tape: dict) -> list[dict]:
    out = []
    for r in rows:
        f = tape.get(r["ticker"])
        if f is None or f["n"] <= 0:
            continue
        side = r["side"]
        sh, st60, hd = share(f, side), share(f, side, True), head_share(f, side)
        tot = f["yes"] + f["no"]
        out.append({**r, "share": sh, "share60": st60, "head": hd, "n_tr": f["n"], "tot": tot, "avg": tot / f["n"], "maxr": f["max"] / (tot / f["n"]), "burst": f["n60"] / f["n"]})
    return out


def quantile_cuts(rows: list[dict], key: str) -> dict[str, tuple[float, float]]:
    cuts = {}
    for s in {r["series"] for r in rows}:
        v = sorted(r[key] for r in rows if r["series"] == s)
        cuts[s] = (v[len(v) // 4], v[(3 * len(v)) // 4])
    return cuts


def rules(rows: list[dict]):
    n_cut, t_cut = quantile_cuts(rows, "n_tr"), quantile_cuts(rows, "tot")
    ok = lambda *v: all(x is not None for x in v)
    return [
        ("BUY_PRESSURE", lambda r: ok(r["share"]) and r["share"] >= 0.60),
        ("SELL_PRESSURE", lambda r: ok(r["share"]) and r["share"] <= 0.40),
        ("LATE_BUY", lambda r: ok(r["share60"]) and r["share60"] >= 0.60),
        ("LATE_SELL", lambda r: ok(r["share60"]) and r["share60"] <= 0.40),
        ("ACCEL", lambda r: ok(r["share60"], r["head"]) and r["share60"] - r["head"] >= 0.20),
        ("DECEL", lambda r: ok(r["share60"], r["head"]) and r["share60"] - r["head"] <= -0.20),
        ("BIG_PRINT", lambda r: r["maxr"] >= 8),
        ("SMALL_TRADES", lambda r: r["avg"] <= 10),
        ("BUSY", lambda r: r["n_tr"] >= n_cut[r["series"]][1]),
        ("QUIET", lambda r: r["n_tr"] <= n_cut[r["series"]][0]),
        ("BURST", lambda r: r["burst"] >= 0.60),
        ("BALANCED", lambda r: ok(r["share"]) and 0.45 <= r["share"] <= 0.55),
        ("ONE_SIDED_BUY", lambda r: ok(r["share"]) and r["share"] >= 0.75),
        ("ONE_SIDED_SELL", lambda r: ok(r["share"]) and r["share"] <= 0.25),
        ("HEAVY", lambda r: r["tot"] >= t_cut[r["series"]][1]),
        ("LIGHT", lambda r: r["tot"] <= t_cut[r["series"]][0]),
    ]


def judge(rows: list[dict], f, cut_day: str) -> dict:
    g = [r for r in rows if f(r)]
    ids = {id(r) for r in g}
    rest = [r for r in rows if id(r) not in ids]
    d, dr = [r for r in g if r["day"] < cut_day], [r for r in rest if r["day"] < cut_day]
    c, cr = [r for r in g if r["day"] >= cut_day], [r for r in rest if r["day"] >= cut_day]
    if len(d) < MIN_N_DISC or len(c) < MIN_N_CONF or not dr or not cr:
        return {"verdict": "NOT_ENOUGH_DATA", "nd": len(d), "nc": len(c)}
    dm, dz, _ = diff_z(d, dr)
    cm, cz, _ = diff_z(c, cr)
    am, az, _ = diff_z(g, rest)
    sd, sc = diff_z(d, dr, "stress")[0], diff_z(c, cr, "stress")[0]
    ok = dm >= DISC_C and dz >= DISC_Z and cm >= CONF_C and cz >= CONF_Z and sd > 0 and sc > 0
    v = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (am < FALSIFY_C or az < FALSIFY_Z) else "NOT_ENOUGH_DATA")
    return {"verdict": v, "nd": len(d), "nc": len(c), "dm": dm, "dz": dz, "cm": cm, "cz": cz, "am": am, "az": az}


def cut_day(rows: list[dict]) -> str:
    days = sorted({r["day"] for r in rows})
    return days[int(len(days) * DISC_FRAC)]


def load_rows() -> list[dict]:
    tape = json.load(open(TAPE))
    mk = {}
    lo = time.time() - 30 * 86400
    for m in load() + load_fresh() + load_rep():
        if m[1] in SER and m[0] in tape and all(x[1] is not None and x[2] is not None for x in m[2]):
            mk[m[0]] = (m[0], m[1], [(e, b, a, b, a) for e, b, a, *_ in m[2]], m[3], m[4])
    rows, _, _ = F.build(list(mk.values()), 360)
    return attach(rows, tape)


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    rows = load_rows()
    cut = cut_day(rows)
    out = [f"TAPE20: {len(rows)} entries with a tape, {len({r['day'] for r in rows})} days, discovery before {cut}"]
    for name, f in rules(rows):
        j = judge(rows, f, cut)
        if "dm" in j:
            out.append(f"{name:15s} {j['verdict']:18s} disc n={j['nd']:4d} {100 * j['dm']:+6.2f}c z {j['dz']:+5.2f} | conf n={j['nc']:4d} {100 * j['cm']:+6.2f}c z {j['cz']:+5.2f} | all {100 * j['am']:+6.2f}c z {j['az']:+5.2f}")
        else:
            out.append(f"{name:15s} {j['verdict']:18s} disc n={j['nd']} conf n={j['nc']}")
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
