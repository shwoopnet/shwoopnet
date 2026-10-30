"""GEN10 (workers/GEN10_REGISTRATION.md): a generator on GOLD'S public trade tape (KXGOLD15M, 10 second bars from
data/gen9/bars.sqlite): ENTER mid-window on a tape signal and HOLD TO SETTLEMENT. The signal bar ends 840 to 420 s before the
close (minutes 1 to 8 of the window); nothing in the last 6 minutes. The side is chosen by the tape (every rule has at least one
SIGNED tape condition), priced 15c to 85c at the signal bar. Fill: the NEXT 10 s bar's last trade price + half the candle spread
+ 1c (GEN9's model: derived from trades, NOT a book). One fee, 7% x C x p x (1 - p) rounded up per order, C = 10 (C = 1 and
fees x1.2 reported); settlement is free. Research only; nothing here places an order, reads a key or decides anything live.
    python -m scalper.gen10 discovery      (build discovery rows, generate, dedupe, screen, freeze)
    python -m scalper.gen10 validate       (once, after the frozen files are committed and pushed)
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import sqlite3
import sys
from datetime import datetime, timezone

import numpy as np

from .gen7 import DISC, FILES, VAL, pf
from .gen9 import BAR, FETCH_LO, NBARS, STALE, Tape, _fee, day_of, half_spread, load_candles, side_feats, FEATS as F9
from .paths import DATA_DIR

G = DATA_DIR / "gen10"
SERIES = "KXGOLD15M"
SEED = 10
ENTRY_LS = tuple(range(840, 419, -10))        # 43 signal bar ends (seconds left); fill at the next bar (L - 10)
LOOKS = tuple(range(840, 419, -60))           # range bounds: 840, 780, ..., 420
RANGES = [(a, b) for a in LOOKS for b in LOOKS if b <= a]
ZONE = (15.0, 85.0)                           # side price in cents by the last trade at the signal bar
C = 10
TARGET, MAX_DRAWS, MIN_TRADES = 5000, 300_000, 30
N_PRIOR = 678_929
NEW = ["fw", "iw", "dpw", "tbig"]
FEATS = F9 + NEW                              # 20 features
SIGNED = {"f10", "f30", "f60", "i10", "i30", "i60", "dp10", "dp30", "dp60", "bigdir30", "fw", "iw", "dpw"}
BIG_MULT, BIG_MIN = 5.0, 50.0                 # a big print: at least 5x the window's mean print so far and at least 50 contracts
NSHUF = 200


def load_results(tickers):
    out = {}
    for name in FILES:
        p = DATA_DIR / f"{name}.sqlite"
        if not p.exists():
            continue
        db = sqlite3.connect(p)
        for tk in tickers:
            if tk in out:
                continue
            r = db.execute("select result from market where ticker=?", (tk,)).fetchone()
            if r and r[0] in ("yes", "no"):
                out[tk] = r[0]
    return out


def new_feats(T, L, yes):
    """fw: s x (YES-taker minus NO-taker contracts) since the window open (bar 0 to the signal bar); iw: fw over all contracts;
    dpw: s x (last price at L minus the first traded price of the window), cents; tbig: seconds from the end of the latest bar
    at or before L holding a big print to L (missing if none yet)."""
    s = 1 if yes else -1
    j = T.j(L)
    bs = T.b[: j + 1]
    vy = sum(x[1] for x in bs); vn = sum(x[2] for x in bs)
    fw = s * (vy - vn)
    iw = fw / (vy + vn) if vy + vn > 0 else np.nan
    p, _ = T.px(L)
    first = next((x[5] for x in bs if x[5] is not None), None)
    dpw = np.nan if (p is None or first is None) else s * (p - first)
    cnt = vol = 0.0
    tb = None
    for k, x in enumerate(bs):
        cnt += x[0]; vol += x[1] + x[2]
        if x[0] > 0 and x[3] >= BIG_MIN and x[3] >= BIG_MULT * (vol / cnt):
            tb = k
    tbig = np.nan if tb is None else float((j - tb) * BAR)
    return [fw, iw, dpw, tbig]


def window_rows(bars, close, cs, result):
    """Every (signal bar, side) row with the side's last-trade price in [15, 85] at the signal bar (trade at most 60 s old), a
    trade at most 60 s old at the fill bar and a candle spread at the fill time. Net per contract in cents held to settlement."""
    T = Tape(bars, close)
    rows = []
    for L in ENTRY_LS:
        p, pts = T.px(L)
        if p is None or (close - L) - pts > STALE:
            continue
        Lf = L - BAR
        q, qts = T.px(Lf)
        if q is None or (close - Lf) - qts > STALE:
            continue
        hs = half_spread(cs, close - Lf)
        if hs is None:
            continue
        for yes in (1, 0):
            sp = p if yes else 100 - p
            if not (ZONE[0] - 1e-9 <= sp <= ZONE[1] + 1e-9):
                continue
            e_c = (q if yes else 100 - q) + hs + 1.0
            if not (1.0 <= e_c <= 99.0):
                continue
            win = (result == "yes") == bool(yes)
            nets = []
            for c, m in ((C, 1.0), (C, 1.2), (1, 1.0)):
                fee = 100 * _fee(e_c / 100, c, m)
                nets.append((100 - e_c - fee) if win else (-e_c - fee))
            rows.append({"L": L, "yes": yes, "feats": side_feats(T, L, yes) + new_feats(T, L, yes), "fill": e_c, "nets": nets, "win": win})
    return rows


def build(lo, hi):
    db = sqlite3.connect(DATA_DIR / "gen9" / "bars.sqlite")
    W = db.execute("select ticker, close, data from bars where series=? and close >= ? and close < ? order by close", (SERIES, lo, hi)).fetchall()
    CS = load_candles([w[0] for w in W])
    RS = load_results([w[0] for w in W])
    X, meta, N10, NS, N1, WIN = [], [], [], [], [], []
    wl = []
    for tk, close, data in W:
        if tk not in CS or tk not in RS:
            continue
        wid = len(wl); wl.append((tk, close))
        day = day_of(close)
        for r in window_rows(json.loads(data), close, CS[tk], RS[tk]):
            X.append(r["feats"]); meta.append((wid, day, r["L"], r["yes"], r["fill"]))
            N10.append(r["nets"][0]); NS.append(r["nets"][1]); N1.append(r["nets"][2]); WIN.append(r["win"])
    days = sorted({m[1] for m in meta})
    di = {d: i for i, d in enumerate(days)}
    D = {"X": np.array(X, dtype=np.float64).reshape(-1, len(FEATS)),
         "wid": np.array([m[0] for m in meta], dtype=np.int64), "day": np.array([di[m[1]] for m in meta], dtype=np.int64),
         "L": np.array([m[2] for m in meta], dtype=np.int64), "yes": np.array([m[3] for m in meta], dtype=np.int64),
         "fill": np.array([m[4] for m in meta]), "n10": np.array(N10), "ns": np.array(NS), "n1": np.array(N1),
         "win": np.array(WIN, dtype=bool), "days": days, "nwin": len(wl), "windows": wl}
    D["opp"] = {(int(w), int(L), int(y)): i for i, (w, L, y) in enumerate(zip(D["wid"], D["L"], D["yes"]))}
    return D


# ---------------------------------------------------------------- generator

def draw(rng, Q):
    L_hi, L_lo = rng.choice(RANGES)
    s = {"side": rng.choice(("yes", "no", "both")), "L_hi": L_hi, "L_lo": L_lo, "conds": []}
    for f in rng.sample(FEATS, rng.randint(1, 3)):
        s["conds"].append((f, rng.choice(("le", "gt")), float(Q[f][rng.choice(range(10, 91, 10))])))
    return s


def has_signed(s):
    return any(f in SIGNED for f, _, _ in s["conds"])


def trades(D, s):
    m = (D["L"] <= s["L_hi"]) & (D["L"] >= s["L_lo"])
    if s["side"] != "both":
        m &= D["yes"] == (1 if s["side"] == "yes" else 0)
    for f, op, q in s["conds"]:
        x = D["X"][:, FEATS.index(f)]
        with np.errstate(invalid="ignore"):
            m &= (x <= q) if op == "le" else (x > q)       # NaN fails both
    idx = np.nonzero(m)[0]
    if not len(idx):
        return idx
    _, first = np.unique(D["wid"][idx], return_index=True)
    return idx[first]


def dayz(v, d):
    if len(v) < 2:
        return 0.0
    mu = v.mean()
    s = np.bincount(d, weights=v - mu)
    den = math.sqrt(float((s ** 2).sum()))
    return float(v.sum() / den) if den > 0 else 0.0


def score(D, idx):
    v = D["n10"][idx]; vs = D["ns"][idx]; v1 = D["n1"][idx]
    return {"n": int(len(idx)), "days": int(len(set(D["day"][idx].tolist()))), "pf": pf(v), "mean": float(v.mean()) if len(v) else 0.0,
            "pfs": pf(vs), "pf1": pf(v1), "z": dayz(v, D["day"][idx]),
            "winrate": float(D["win"][idx].mean()) if len(idx) else 0.0, "fill": float(D["fill"][idx].mean()) if len(idx) else 0.0}


def shuffled(D, idx, nshuf=NSHUF, seed=1010):
    """Side-shuffled control: each trade keeps its window and signal bar and takes the OPPOSITE side's row with probability 1/2
    (kept as is when the opposite row does not exist). Returns the PFs of nshuf shuffles."""
    rng = random.Random(seed)
    opp = np.array([D["opp"].get((int(D["wid"][i]), int(D["L"][i]), 1 - int(D["yes"][i])), i) for i in idx])
    out = []
    for _ in range(nshuf):
        flip = np.array([rng.random() < 0.5 for _ in idx])
        sel = np.where(flip, opp, idx)
        out.append(pf(D["n10"][sel]))
    return out


def desc(s):
    c = " & ".join(f"{f} {'<=' if op == 'le' else '>'} {q:.4g}" for f, op, q in s["conds"])
    return f"{s['side']} {s['L_hi']}..{s['L_lo']}s, {c}, held"


def base_info(D):
    out = {}
    for side in ("yes", "no", "both"):
        s = {"side": side, "L_hi": 840, "L_lo": 420, "conds": []}
        out[side] = score(D, trades(D, s))
    return out


def bonferroni_z(n):
    a = 0.05 / n
    lo, hi = 0.0, 10.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if 0.5 * math.erfc(mid / math.sqrt(2)) > a:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def discovery():
    D = build(*DISC)
    print(SERIES, "discovery windows", D["nwin"], "rows", len(D["wid"]), "days", len(D["days"]), flush=True)
    G.mkdir(parents=True, exist_ok=True)
    if D["nwin"] < 300 or len(D["days"]) < 15:
        print("NOT_ENOUGH_DATA"); (G / "disc_info.json").write_text(json.dumps({"nwin": D["nwin"], "days": len(D["days"]), "verdict": "NOT_ENOUGH_DATA"})); return
    Q = {f: np.nanpercentile(D["X"][:, i], list(range(101))) for i, f in enumerate(FEATS)}
    rng = random.Random(SEED * 1000 + 2)
    kept, kbits, ksz = [], [], []
    gen = rej_unsigned = rej_small = rej_dup = 0
    while len(kept) < TARGET and gen < MAX_DRAWS:
        s = draw(rng, Q); gen += 1
        if not has_signed(s):
            rej_unsigned += 1; continue
        idx = trades(D, s)
        if len(idx) < MIN_TRADES:
            rej_small += 1; continue
        bits = 0
        for w, y in zip(D["wid"][idx].tolist(), D["yes"][idx].tolist()):
            bits |= 1 << (2 * w + y)
        n = len(idx); dup = False
        for kb, kn in zip(kbits, ksz):
            inter = (kb & bits).bit_count()
            if inter / (kn + n - inter) > 0.5:
                dup = True; break
        if dup:
            rej_dup += 1; continue
        kbits.append(bits); ksz.append(n)
        kept.append((s, score(D, idx)))
        if len(kept) % 500 == 0:
            print("distinct", len(kept), "generated", gen, flush=True)
    size = lambda sc: sc["n"] >= 100 and sc["days"] >= 15
    ok = lambda sc: sc["pf"] >= 1.5
    surv = [{"strategy": s, "disc": sc} for s, sc in kept if size(sc) and ok(sc)]
    ctrl = [{"strategy": s, "disc": sc} for s, sc in kept if size(sc) and not ok(sc)]
    best = [{"strategy": s, "disc": sc} for s, sc in sorted(kept, key=lambda r: -(r[1]["pf"] if size(r[1]) else 0))[:10]]
    pfs = np.array([sc["pf"] for _, sc in kept]) if kept else np.array([0.0])
    big = np.array([sc["pf"] for _, sc in kept if size(sc)])
    info = {"series": SERIES, "generated": gen, "distinct": len(kept),
            "rejected": {"no_signed_condition": rej_unsigned, "under_30_trades": rej_small, "duplicate": rej_dup},
            "disc_windows": D["nwin"], "disc_rows": int(len(D["wid"])), "disc_days": len(D["days"]),
            "pf_median": float(np.median(pfs)), "pf_p95": float(np.percentile(pfs, 95)),
            "mean_median": float(np.median([sc["mean"] for _, sc in kept])) if kept else 0.0,
            "at_size": int(len(big)), "at_size_pf_ge_1": int((big >= 1.0).sum()), "at_size_pf_ge_1_3": int((big >= 1.3).sum()),
            "best_at_size": float(big.max()) if len(big) else 0.0, "survivors_n": len(surv), "controls_n": len(ctrl),
            "base_info": base_info(D), "frozen_at": datetime.now(timezone.utc).isoformat()}
    (G / "distinct.json").write_text(json.dumps({"info": info, "distinct": [{"strategy": s, "disc": sc} for s, sc in kept]}))
    (G / "controls.json").write_text(json.dumps({"info": info, "controls": ctrl}))
    (G / "frozen.json").write_text(json.dumps({"info": info, "survivors": surv, "best10": best}, indent=1))
    print(json.dumps(info, indent=1))
    for r in best:
        print(desc(r["strategy"]), {k: round(v, 3) for k, v in r["disc"].items()})
    for name in ("frozen", "controls", "distinct"):
        print(name, hashlib.sha256((G / f"{name}.json").read_bytes()).hexdigest())


def _vpass(vs):
    return vs["pf"] >= 1.3 and vs["n"] >= 50 and vs["pfs"] > 1.0


def _tup(s):
    s["conds"] = [tuple(c) for c in s["conds"]]
    return s


def validate():
    out = G / "validation.json"
    if out.exists():
        print("Refusing to run again: validation already read"); return
    fz = json.loads((G / "frozen.json").read_text())
    ct = json.loads((G / "controls.json").read_text())
    D = build(*VAL)
    print(SERIES, "validation windows", D["nwin"], "rows", len(D["wid"]), "days", len(D["days"]), flush=True)
    res = {"windows": D["nwin"], "days": len(D["days"]), "survivors": [], "controls_n": len(ct["controls"]), "controls_pass": 0,
           "base_info": base_info(D)}
    looks = 0
    for r in fz["survivors"]:
        s = _tup(r["strategy"]); idx = trades(D, s); vs = score(D, idx)
        sh = shuffled(D, idx) if len(idx) else []
        unc = score(D, trades(D, {"side": s["side"], "L_hi": s["L_hi"], "L_lo": s["L_lo"], "conds": []})); looks += 1
        p95 = float(np.percentile(sh, 95)) if sh else None
        res["survivors"].append({"desc": desc(s), "disc": r["disc"], "val": vs, "pass": _vpass(vs),
                                 "shuffle_p95": p95, "shuffle_median": float(np.median(sh)) if sh else None,
                                 "beats_shuffle": bool(p95 is not None and vs["pf"] > p95), "unconditioned_val": unc})
    cp = []
    for r in ct["controls"]:
        s = _tup(r["strategy"]); vs = score(D, trades(D, s))
        cp.append(vs["pf"])
        if _vpass(vs):
            res["controls_pass"] += 1
    res["controls_val_pf_median"] = float(np.median(cp)) if cp else None
    res["controls_val_pf_p95"] = float(np.percentile(cp, 95)) if cp else None
    res["best10"] = []
    for r in fz["best10"]:
        s = _tup(r["strategy"]); idx = trades(D, s); vs = score(D, idx)
        sh = shuffled(D, idx) if len(idx) else []
        res["best10"].append({"desc": desc(s), "disc": r["disc"], "val": vs, "shuffle_p95": float(np.percentile(sh, 95)) if sh else None,
                              "shuffle_median": float(np.median(sh)) if sh else None})
    ns = len(res["survivors"])
    res["survivor_pass_rate"] = sum(x["pass"] for x in res["survivors"]) / ns if ns else None
    res["control_pass_rate"] = res["controls_pass"] / res["controls_n"] if res["controls_n"] else None
    res["information_looks"] = looks + 3
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "discovery":
        discovery()
    elif cmd == "validate":
        validate()
    elif cmd == "zbar":
        print(bonferroni_z(int(sys.argv[2])))
