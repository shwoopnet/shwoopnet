"""FP2 (README, Pre-registration: FP2): gold footprint as a loss warning. Is opposing taker flow in the 3 minutes before the 6 minute decision a mark of the losers?
Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Usage: python -m scalper.fp2 fetch   (resumable)    python -m scalper.fp2 run   (once; a second run is refused)
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys
import time

from . import api
from . import feat1 as F
from .crowd1 import diff_z
from .flat_r import load_rep
from .fwd_reads import load_fresh
from .hs1 import load
from .paths import DATA_DIR

# ---- fixed in the README before any gold tape was fetched ----
SERIES = "KXGOLD15M"
WIN_FAR, WIN_NEAR = 540, 360  # seconds before the close
OPP_MIN, OPP_SHARE = 100.0, 0.40
DISC_FRAC = 0.60
MIN_N_DISC, MIN_N_CONF = 40, 20
DISC_C, DISC_Z, CONF_C, CONF_Z, FALSIFY_C, FALSIFY_Z, LOSS_RATIO = 0.030, 2.0, 0.015, 1.0, 0.010, 1.0, 1.5
TAPE = DATA_DIR / "fp2_tape.json"
RESULT = DATA_DIR / "fp2_result.txt"


def flow(trades: list[dict]) -> dict:
    """Taker contracts per side over the window."""
    agg = {"yes": 0.0, "no": 0.0, "n": 0}
    for t in trades:
        side = t.get("taker_outcome_side")
        if side not in ("yes", "no"):
            continue
        agg[side] += float(t["count_fp"])
        agg["n"] += 1
    return agg


def opposed(f: dict, side: str) -> bool:
    """Taker contracts against the favourite are at least OPP_MIN and at least OPP_SHARE of all."""
    against = f["no"] if side == "yes" else f["yes"]
    tot = f["yes"] + f["no"]
    return tot > 0 and against >= OPP_MIN and against / tot >= OPP_SHARE


def toward_share(f: dict, side: str):
    tot = f["yes"] + f["no"]
    return None if tot <= 0 else (f["yes"] if side == "yes" else f["no"]) / tot


def gold_rows() -> list[dict]:
    mk = {}
    for m in load() + load_fresh() + load_rep():
        if m[1] == SERIES and all(x[1] is not None and x[2] is not None for x in m[2]):
            mk[m[0]] = (m[0], m[1], [(e, b, a, b, a) for e, b, a, *_ in m[2]], m[3], m[4])
    rows, _, _ = F.build(list(mk.values()), 360)
    return rows


def fetch() -> None:
    rows = gold_rows()
    done = json.load(open(TAPE)) if TAPE.exists() else {}
    print(len(rows), "gold L1 entries;", len(done), "already fetched", flush=True)
    for r in sorted(rows, key=lambda r: r["close_ts"], reverse=True):
        tk = r["ticker"]
        if tk in done:
            continue
        c, trades, cur = r["close_ts"], [], None
        while True:
            p = {"ticker": tk, "limit": 1000, "min_ts": c - WIN_FAR, "max_ts": c - WIN_NEAR}
            if cur:
                p["cursor"] = cur
            try:
                d = api._get("/markets/trades", p)
            except Exception:
                time.sleep(5)
                continue
            tr = d.get("trades", [])
            trades += tr
            cur = d.get("cursor")
            if not cur or not tr:
                break
        done[tk] = flow(trades)
        if len(done) % 20 == 0:
            json.dump(done, open(TAPE, "w"))
            print(len(done), "of", len(rows), flush=True)
        time.sleep(0.1)
    json.dump(done, open(TAPE, "w"))
    print("done", len(done), flush=True)


def judge(rows: list[dict], cut: str) -> dict:
    g = [r for r in rows if r["opp"]]
    rest = [r for r in rows if not r["opp"]]
    d, dr = [r for r in g if r["day"] < cut], [r for r in rest if r["day"] < cut]
    c, cr = [r for r in g if r["day"] >= cut], [r for r in rest if r["day"] >= cut]
    if len(d) < MIN_N_DISC or len(c) < MIN_N_CONF or not dr or not cr:
        return {"verdict": "NOT_ENOUGH_DATA", "nd": len(d), "nc": len(c), "n": len(g)}
    # gap = rest minus opposed, so a positive number means the warning works
    dm, dz, _ = diff_z(dr, d)
    cm, cz, _ = diff_z(cr, c)
    am, az, _ = diff_z(rest, g)
    loss = lambda xs: st.mean(r["lost"] for r in xs)
    ratio_d = loss(d) / max(loss(dr), 1e-9)
    ratio_c = loss(c) / max(loss(cr), 1e-9)
    ok = dm >= DISC_C and dz >= DISC_Z and cm >= CONF_C and cz >= CONF_Z and ratio_d >= LOSS_RATIO and ratio_c >= LOSS_RATIO
    v = "NOT_YET_FALSIFIED" if ok else ("FALSIFIED" if (am < FALSIFY_C or az < FALSIFY_Z) else "NOT_ENOUGH_DATA")
    return {"verdict": v, "nd": len(d), "nc": len(c), "n": len(g), "dm": dm, "dz": dz, "cm": cm, "cz": cz, "am": am, "az": az,
            "ratio_d": ratio_d, "ratio_c": ratio_c, "loss_opp": loss(g), "loss_rest": loss(rest)}


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] not in ("fetch", "run"):
        print(__doc__)
        return
    if argv[1] == "fetch":
        fetch()
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    tape = json.load(open(TAPE))
    rows = []
    for r in gold_rows():
        f = tape.get(r["ticker"])
        if f is None:
            continue
        sh = toward_share(f, r["side"])
        rows.append({**r, "opp": opposed(f, r["side"]), "toward": sh is not None and sh >= 0.70})
    days = sorted({r["day"] for r in rows})
    cut = days[int(len(days) * DISC_FRAC)]
    out = [f"FP2: {len(rows)} gold entries with a tape, {len(days)} days, discovery before {cut}"]
    j = judge(rows, cut)
    out.append(f"OPPOSED {j['verdict']}: " + ", ".join(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" for k, v in j.items() if k != "verdict"))
    ctl = [r for r in rows if r["toward"]]
    rest = [r for r in rows if not r["toward"]]
    if ctl and rest:
        m, z, _ = diff_z(ctl, rest)
        out.append(f"FLOW_TOWARD (information only) n={len(ctl)} net minus rest {100 * m:+.2f}c z {z:+.2f}")
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
