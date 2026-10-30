"""GEN8 (workers/GEN8_REGISTRATION.md): a generator of MID-PRICE ROUND TRIPS on KXBTC15M and KXGOLD15M.
Entry at the candle ending 840 to 300 s before the close (every minute), the side whose ask is 30c to 70c (the coin-flip zone),
1 to 3 conditions from GEN1's Kalshi-side features and GEN7's open interest features, and an exit that is ALWAYS before
settlement: sell at the bid H seconds after the fill (H 60 to 300, never later than 120 s before the close), or a take profit /
stop with the same time fallback. Research only; nothing here places an order, reads a key or decides anything live.
    python -m scalper.gen8 discovery <btc|gold>    (build discovery rows, generate, dedupe, screen, write the frozen survivor file)
    python -m scalper.gen8 validate <btc|gold>     (once, after the frozen files are committed)
    python -m scalper.gen8 parity <btc|gold>       (forward_eval against the history scorer on validation windows)
forward_eval(window, params) is the forward-ledger evaluator (workers/candidates/README.md).
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from datetime import datetime, timezone

import numpy as np

from .gen7 import DISC, FEATS, MARKETS, PEERS, VAL, _jac, _oi_feats, _sq, load_windows, pf, ref_sets, vfee

LOOKS = tuple(range(840, 299, -60))                      # 840, 780, ..., 300
RANGES = [(a, b) for a in LOOKS for b in LOOKS if b <= a]
ZONE = (0.30, 0.70)
HOLDS = (60, 120, 180, 240, 300)                         # seconds after the fill candle
TPS = (0.03, 0.05, 0.08, 0.12, 0.15)
STOPS = (0.05, 0.10, 0.15, 0.20)
EXITS = [("time", h) for h in HOLDS] + [("tp", i, j, h) for i in range(len(TPS)) for j in range(len(STOPS)) for h in HOLDS]
LAST_EXIT = 120                                          # no exit later than this many seconds before the close
SEED = 8
TARGET, MAX_DRAWS, MIN_TRADES = 5000, 300_000, 30
N_PRIOR = 592_100
# exit flags: 0 sold at a positive bid at or before the fallback; 1 fallback bid was 0, booked at 0;
#             2 no candle at or after the fallback, booked at 0; 3 fallback candle missing, the next candle's bid was used
FLAG_NAMES = ("sold", "zero bid booked 0", "no candle booked 0", "late candle")


def hold_of(e):
    k = EXITS[e]
    return k[1] if k[0] == "time" else k[3]


def exit_allowed(e, L_lo):
    """Fill candle ends at close - L + 60; the fallback at fill + H must be at least 120 s before the close at every look."""
    return hold_of(e) <= L_lo - 60 - LAST_EXIT


def exit_near(a, b):
    x, y = EXITS[a], EXITS[b]
    if x[0] != y[0]:
        return False
    if x[0] == "time":
        return abs(HOLDS.index(x[1]) - HOLDS.index(y[1])) <= 1
    return abs(x[1] - y[1]) <= 1 and abs(x[2] - y[2]) <= 1 and abs(HOLDS.index(x[3]) - HOLDS.index(y[3])) <= 1


def _exit(e, scan, fill, fill_t):
    """(exit bid, zero-volume flag, exit end_ts or None, flag). scan = [(end_ts, side bid, zero volume)] after the fill candle.
    A bid of 0 is never a sale before the fallback; at the fallback a bid of 0 is booked at 0."""
    k = EXITS[e]
    T = fill_t + hold_of(e)
    if k[0] == "tp":
        tp, st = TPS[k[1]], STOPS[k[2]]
        for t, b, z in scan:
            if t > T:
                break
            if b <= 0:
                continue
            if b >= fill + tp - 1e-9 or b <= fill - st + 1e-9:
                return (b, z, t, 0)
    for t, b, z in scan:
        if t >= T:
            if b > 0:
                return (b, z, t, 0 if t == T else 3)
            return (0.0, z, t, 1)
    return (0.0, False, None, 2)


def window_rows(series, close_ts, cs, peers):
    """Every (look, side) row of one window with the side's ask in [0.30, 0.70] at the signal candle, in entry order (840 s first,
    YES before NO). Shared by history and forward. 'gaps' lists looks whose signal or fill candle was missing."""
    rows, gaps = [], []
    pa = peers.get(PEERS[series][0]); pb = peers.get(PEERS[series][1])
    start = close_ts - 900
    wkeys = sorted(k for k in cs if start < k <= close_ts - 60)
    first = wkeys[0] if wkeys else None
    for L in LOOKS:
        t = close_ts - L
        q = cs.get(t)
        if q is None:
            gaps.append(L); continue
        nq = cs.get(t + 60)
        fill_t = t + 60
        scan_keys = [k for k in wkeys if k > fill_t]
        hour = datetime.fromtimestamp(t, timezone.utc).hour
        oif = None
        for yes in (1, 0):
            bid, ask, mid = _sq(q, yes)
            if not (ZONE[0] - 1e-9 <= ask <= ZONE[1] + 1e-9):
                continue
            if nq is None:
                gaps.append(L); continue
            fill = _sq(nq, yes)[1]
            if not (0 < fill < 1):
                continue
            if oif is None:
                oif = _oi_feats(cs, t, q, first)
            sgn = 1 if yes else -1

            def dlag(lag):
                p = cs.get(t - lag)
                return (bid - _sq(p, yes)[0]) if p is not None else np.nan

            marks = [cs.get(t - 60 * j) for j in range(6)]
            rng5 = (max(_sq(m, yes)[0] for m in marks) - min(_sq(m, yes)[0] for m in marks)) if all(m is not None for m in marks) else np.nan
            px = []
            for P in (pa, pb):
                a = P.get(t) if P else None
                b = P.get(t - 120) if P else None
                if a is None:
                    px += [np.nan, np.nan]; continue
                ma = (a[0] + a[1]) / 2
                px += [sgn * (ma - (b[0] + b[1]) / 2) if b is not None else np.nan, ma]
            f = np.array(oif + [ask, bid, q[1] - q[0], dlag(60), dlag(120), dlag(180), dlag(300), rng5, q[2], hour,
                                px[0], px[1], px[2], px[3]], dtype=np.float64)
            scan = [(k, _sq(cs[k], yes)[0], cs[k][2] <= 0) for k in scan_keys]
            ex = [_exit(e, scan, fill, fill_t) for e in range(len(EXITS))]
            rows.append({"L": L, "yes": yes, "t": t, "feats": f, "fill": fill, "sig_ask": ask,
                         "zv_entry": q[2] <= 0 or nq[2] <= 0, "exits": ex})
    return rows, gaps


# ---------------------------------------------------------------- history

def build(series, lo, hi):
    W = load_windows(series, lo, hi)
    X, meta, EB, EZ, EF = [], [], [], [], []
    for wid, (tk, ct, res, cs, peers) in enumerate(W):
        rows, _ = window_rows(series, ct, cs, peers)
        day = datetime.fromtimestamp(ct, timezone.utc).strftime("%Y-%m-%d")
        for r in rows:
            win = 1.0 if (res == "yes") == bool(r["yes"]) else 0.0
            X.append(r["feats"]); meta.append((wid, day, r["L"], r["yes"], r["fill"], r["sig_ask"], r["zv_entry"], win, ct))
            EB.append([b for b, z, k, fl in r["exits"]]); EZ.append([z for b, z, k, fl in r["exits"]])
            EF.append([fl for b, z, k, fl in r["exits"]])
    days = sorted({m[1] for m in meta})
    di = {d: i for i, d in enumerate(days)}
    col = lambda i: np.array([m[i] for m in meta])
    D = {"X": np.array(X).reshape(-1, len(FEATS)), "wid": col(0), "day": np.array([di[m[1]] for m in meta]), "L": col(2), "yes": col(3),
         "fill": col(4), "sig": col(5), "zve": col(6), "win": col(7), "close": col(8), "EB": np.array(EB), "EZ": np.array(EZ),
         "EF": np.array(EF, dtype=np.int8), "days": days, "nwin": len(W), "tickers": [w[0] for w in W]}
    o = np.lexsort((-D["yes"], -D["L"], D["wid"]))
    for k in ("X", "wid", "day", "L", "yes", "fill", "sig", "zve", "win", "close", "EB", "EZ", "EF"):
        D[k] = D[k][o]
    return D, W


def nets(D, idx, e, c=10, m=1.0, sig=False):
    a = (D["sig"] if sig else D["fill"])[idx]
    b = D["EB"][idx, e]
    return b - a - vfee(a, c, m) - vfee(b, c, m)


def trades(D, s):
    m = (D["L"] <= s["L_hi"]) & (D["L"] >= s["L_lo"])
    if s["side"] != "both":
        m &= D["yes"] == (1 if s["side"] == "yes" else 0)
    for f, op, th in s["conds"]:
        col = D["X"][:, FEATS.index(f)]
        with np.errstate(invalid="ignore"):
            m &= (col <= th) if op == "le" else (col > th)   # NaN compares False: a missing feature fails its condition
    idx = np.flatnonzero(m)
    if len(idx) == 0:
        return idx
    w = D["wid"][idx]
    return idx[np.r_[True, w[1:] != w[:-1]]]


def score(D, idx, e):
    v = nets(D, idx, e)
    zv = (D["zve"][idx] | D["EZ"][idx, e]) if len(idx) else np.array([], bool)
    fl = D["EF"][idx, e] if len(idx) else np.array([], np.int8)
    days = D["day"][idx]
    out = {"n": int(len(idx)), "days": int(len(set(days.tolist()))), "pf": pf(v), "pf1": pf(nets(D, idx, e, c=1)),
           "pfs": pf(nets(D, idx, e, m=1.2)), "pf_sig": pf(nets(D, idx, e, sig=True)), "zv": float(zv.mean()) if len(idx) else 1.0,
           "mean": float(v.mean()) if len(v) else 0.0, "win_rate": float((v > 0).mean()) if len(v) else 0.0,
           "ask": float(D["fill"][idx].mean()) if len(idx) else 0.0,
           "pf_nozv": pf(v[~zv]) if len(idx) and zv.any() else pf(v),
           "booked0": int(((fl == 1) | (fl == 2)).sum()), "late": int((fl == 3).sum())}
    if len(idx) > 1:
        from .calibration import cluster_mean_z
        out["z"] = cluster_mean_z(list(zip(days.tolist(), v.tolist())))[2]
    else:
        out["z"] = 0.0
    return out


def draw(rng, Q):
    L_hi, L_lo = rng.choice(RANGES)
    s = {"L_hi": L_hi, "L_lo": L_lo, "side": rng.choice(["yes", "no", "both"]), "conds": [], "e": rng.randrange(len(EXITS))}
    used = set()
    for _ in range(rng.randint(1, 3)):
        f = rng.choice([g for g in FEATS if g not in used]); used.add(f)
        s["conds"].append((f, rng.choice(["le", "gt"]), float(Q[f][rng.choice(range(10, 91, 10))])))
    return s


def desc(s):
    e = EXITS[s["e"]]
    ex = (f"sell {e[1]}s after fill" if e[0] == "time" else
          f"TP +{int(round(TPS[e[1]] * 100))}c stop -{int(round(STOPS[e[2]] * 100))}c else sell {e[3]}s after fill")
    cond = " & ".join(f"{f}{'<=' if op == 'le' else '>'}{th:.3g}" for f, op, th in s["conds"])
    return f"[{s['side']} {s['L_hi']}..{s['L_lo']}s | {cond} | {ex}]"


def base_info(D):
    """Information only (not a strategy, not counted): every first in-zone row per window, YES before NO, each pure time exit."""
    idx = trades(D, {"L_hi": 840, "L_lo": 300, "side": "both", "conds": [], "e": 0})
    return {f"sell {h}s": round(pf(nets(D, idx, e)), 3) for e, h in enumerate(HOLDS)} | {"n": int(len(idx))}


def discovery(key):
    series = MARKETS[key]
    D, W = build(series, *DISC)
    print(series, "discovery windows", D["nwin"], "rows", len(D["wid"]), "days", len(D["days"]), flush=True)
    if D["nwin"] < 1000:
        print("NOT_ENOUGH_DATA"); return
    Q = {f: np.nanpercentile(D["X"][:, i], list(range(101))) for i, f in enumerate(FEATS)}
    nw = D["nwin"]
    rng = random.Random(SEED * 1000 + (1 if key == "btc" else 2))
    K = np.zeros((TARGET, nw), dtype=np.float32); ksz = np.zeros(TARGET); kexit = []
    kept = []
    gen = rej_exit = rej_small = rej_dup = 0
    while len(kept) < TARGET and gen < MAX_DRAWS:
        s = draw(rng, Q); gen += 1
        if not exit_allowed(s["e"], s["L_lo"]):
            rej_exit += 1; continue
        idx = trades(D, s)
        if len(idx) < MIN_TRADES:
            rej_small += 1; continue
        ws = D["wid"][idx]
        v = np.zeros(nw, dtype=np.float32); v[ws] = 1
        k = len(kept)
        if k:
            near = np.array([exit_near(s["e"], x) for x in kexit])
            if near.any():
                inter = K[:k][near] @ v
                jac = inter / (ksz[:k][near] + len(ws) - inter)
                if (jac > 0.5).any():
                    rej_dup += 1; continue
        K[k] = v; ksz[k] = len(ws); kexit.append(s["e"])
        kept.append((s, score(D, idx, s["e"])))
        if len(kept) % 500 == 0:
            print("distinct", len(kept), "generated", gen, flush=True)
    size = lambda sc: sc["n"] >= 100 and sc["days"] >= 15
    surv = [{"strategy": s, "disc": sc} for s, sc in kept if size(sc) and sc["pf"] >= 1.5 and sc["zv"] <= 0.2]
    ctrl = [{"strategy": s, "disc": sc} for s, sc in kept if size(sc) and not (sc["pf"] >= 1.5 and sc["zv"] <= 0.2)]
    pfs = np.array([sc["pf"] for _, sc in kept])
    big = np.array([sc["pf"] for _, sc in kept if size(sc)])
    b0 = sum(sc["booked0"] for _, sc in kept); late = sum(sc["late"] for _, sc in kept); nt = sum(sc["n"] for _, sc in kept)
    info = {"series": series, "generated": gen, "distinct": len(kept),
            "rejected": {"exit_not_allowed": rej_exit, "under_30_trades": rej_small, "duplicate": rej_dup},
            "disc_windows": nw, "disc_rows": int(len(D["wid"])), "disc_days": len(D["days"]),
            "pf_median": float(np.median(pfs)), "pf_p95": float(np.percentile(pfs, 95)), "at_size": int(len(big)),
            "best_at_size": float(big.max()) if len(big) else 0.0, "survivors_n": len(surv), "controls_n": len(ctrl),
            "booked0_share_all_distinct_trades": b0 / nt if nt else 0.0, "late_share": late / nt if nt else 0.0,
            "base_info": base_info(D), "frozen_at": datetime.now(timezone.utc).isoformat()}
    (DATA_DIR() / f"gen8_{key}_distinct.json").write_text(json.dumps({"info": info, "distinct": [{"strategy": s, "disc": sc} for s, sc in kept]}))
    (DATA_DIR() / f"gen8_{key}_controls.json").write_text(json.dumps({"info": info, "controls": ctrl}))
    (DATA_DIR() / f"gen8_{key}_frozen.json").write_text(json.dumps({"info": info, "survivors": surv}, indent=1))
    print(json.dumps(info, indent=1))
    for r in sorted(surv, key=lambda r: -r["disc"]["pf"])[:15]:
        print(desc(r["strategy"]), {k: round(v, 3) for k, v in r["disc"].items()})
    for name in ("frozen", "controls", "distinct"):
        print(name, hashlib.sha256((DATA_DIR() / f"gen8_{key}_{name}.json").read_bytes()).hexdigest())


def DATA_DIR():
    from .paths import DATA_DIR as d
    return d


def _vpass(vs):
    return vs["pf"] >= 1.3 and vs["n"] >= 50 and vs["pfs"] > 1.0 and vs["zv"] <= 0.2


def _tup(s):
    s["conds"] = [tuple(c) for c in s["conds"]]
    return s


def validate(key):
    series = MARKETS[key]
    out = DATA_DIR() / f"gen8_{key}_validation.json"
    if out.exists():
        print("Refusing to run again: validation already read"); return
    fz = json.loads((DATA_DIR() / f"gen8_{key}_frozen.json").read_text())
    ct = json.loads((DATA_DIR() / f"gen8_{key}_controls.json").read_text())
    D, W = build(series, *VAL)
    print(series, "validation windows", D["nwin"], "rows", len(D["wid"]), "days", len(D["days"]), flush=True)
    R = ref_sets(W, series)
    res = {"windows": D["nwin"], "days": len(D["days"]), "survivors": [], "controls_pass": 0, "controls_n": len(ct["controls"]),
           "ref_sets": {k: len(v) for k, v in R.items()}, "base_info": base_info(D)}
    for r in fz["survivors"]:
        s = _tup(r["strategy"])
        idx = trades(D, s); vs = score(D, idx, s["e"])
        ws = set(D["wid"][idx].tolist())
        vs["jac_oicore"] = _jac(ws, R["oicore"]) if R["oicore"] else None
        vs["in_oicore"] = len(ws & R["oicore"])
        if R["oicore"] and len(idx):
            v = nets(D, idx, s["e"]); ino = np.array([w in R["oicore"] for w in D["wid"][idx].tolist()])
            vs["pf_in_oicore"] = pf(v[ino]); vs["pf_out_oicore"] = pf(v[~ino])
        res["survivors"].append({"strategy": s, "disc": r["disc"], "valid": vs, "pass": _vpass(vs),
                                 "entries": [D["tickers"][w] for w in D["wid"][idx].tolist()]})
    cpass = []
    for r in ct["controls"]:
        s = _tup(r["strategy"])
        vs = score(D, trades(D, s), s["e"])
        res["controls_pass"] += int(_vpass(vs))
        cpass.append({"strategy": s, "disc": r["disc"], "valid": vs})
    out.write_text(json.dumps(res))
    (DATA_DIR() / f"gen8_{key}_controls_validation.json").write_text(json.dumps(cpass))
    sp = sum(r["pass"] for r in res["survivors"])
    print("survivors", len(res["survivors"]), "pass", sp, "controls", res["controls_n"], "pass", res["controls_pass"])
    print("base", res["base_info"], "control median PF", float(np.median([c["valid"]["pf"] for c in cpass])) if cpass else None)
    for r in sorted(res["survivors"], key=lambda r: -r["valid"]["pf"]):
        print("PASS" if r["pass"] else "fail", desc(r["strategy"]), "disc", round(r["disc"]["pf"], 2), r["disc"]["n"],
              {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r["valid"].items()})


# ---------------------------------------------------------------- forward

def forward_eval(window, params):
    """One frozen GEN8 strategy (params["strategy"]) on one window (source "candles"). Same rows and selection as the history.
    Always returns an exit (a bid, or 0.0 when the fallback bid was 0 or no later candle existed): GEN8 never holds."""
    from .fwdeval import NoData
    s = params.get("strategy", params)
    series = window["series"]
    if series not in PEERS or series != params.get("series", series):
        return None
    conds = [tuple(c) for c in s["conds"]]
    rows, gaps = window_rows(series, window["close_ts"], window["candles"], window.get("peers", {}))
    missing = False
    for r in rows:
        if not (s["L_lo"] <= r["L"] <= s["L_hi"]):
            continue
        if s["side"] != "both" and r["yes"] != (1 if s["side"] == "yes" else 0):
            continue
        ok = True
        for f, op, th in conds:
            v = r["feats"][FEATS.index(f)]
            if np.isnan(v):
                missing = True; ok = False; break
            if not ((v <= th) if op == "le" else (v > th)):
                ok = False; break
        if not ok:
            continue
        b, z, k, fl = r["exits"][s["e"]]
        return {"side": "yes" if r["yes"] else "no", "entry": float(r["fill"]), "exit": float(b),
                "t": int(r["t"] + 60), "zero_volume": bool(r["zv_entry"] or z),
                "note": f"look {r['L']}s, signal ask {r['sig_ask']:.2f}, exit {FLAG_NAMES[fl]}" +
                        ("" if k is None else f" at {window['close_ts'] - k}s left")}
    if missing or any(s["L_lo"] <= L <= s["L_hi"] for L in gaps):
        raise NoData("a candle or feature input the rule needs is missing")
    return None


def parity(key):
    """forward_eval against trades()/nets() on the validation windows for every validation pass."""
    series = MARKETS[key]
    D, W = build(series, *VAL)
    res = json.loads((DATA_DIR() / f"gen8_{key}_validation.json").read_text())
    from .fwdeval import NoData
    from .fwdledger import net_per_contract
    bad = checked = 0
    for r in res["survivors"]:
        if not r["pass"]:
            continue
        s = _tup(r["strategy"])
        idx = trades(D, s); hv = nets(D, idx, s["e"])
        hist = {int(D["wid"][i]): float(v) for i, v in zip(idx, hv)}
        for wid, (tk, ct, rs, cs, peers) in enumerate(W):
            try:
                tr = forward_eval({"series": series, "close_ts": ct, "candles": cs, "peers": peers}, {"strategy": s})
            except NoData:
                tr = "nodata"
            checked += 1
            if tr == "nodata" or tr is None:
                bad += wid in hist; continue
            fv = net_per_contract(tr, rs, 10)
            if wid not in hist or abs(fv - hist[wid]) > 1e-6:
                bad += 1
    print("parity windows checked", checked, "mismatches", bad)


if __name__ == "__main__":
    cmd, key = sys.argv[1], sys.argv[2]
    {"discovery": discovery, "validate": validate, "parity": parity}[cmd](key)
