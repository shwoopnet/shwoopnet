"""GEN4 (workers/GEN4_REGISTRATION.md, pushed as 0c613bc before this file existed): a strategy generator on the
recorder's second-resolution books in the last 150 seconds of KXBTC15M (gold registered, not runnable on this split).
Research only; nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE.

    PYTHONPATH=src python3 -m scalper.gen4 discovery     # generate, score discovery, freeze the survivors
    PYTHONPATH=src python3 -m scalper.gen4 validation    # once, after the frozen list is committed
    evaluate(spec, since=..., commit=...)                # forward ledger hook: trades of one frozen rule on later windows
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import random
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
SCR = Path("/tmp/claude-0/-home-user-shwoopnet/026f6e8f-6dc4-5e3b-8c3b-e0089b12fb94/scratchpad/gen4")
DISC_COMMIT = "b7dc9cbe823b2b9f734dc085ea03452a1aec3c1b"
FROZEN = ROOT / "kalshi-scalper/studies/gen4_survivors_FROZEN_2026-10-29.json"
PREFIX = {"bitcoin": "KXBTC15M", "gold": "KXGOLD15M"}
DISC_END = datetime(2026, 10, 27, tzinfo=timezone.utc).timestamp()
VAL_END = datetime(2026, 10, 30, tzinfo=timezone.utc).timestamp()
GRID = (150, 120, 90, 60, 45, 30, 20, 10)
EXITS = (0, 90, 60, 30, 15, 5)          # 0 = hold to settlement
SIDES = ("YES", "NO", "FAV", "DOG")
BASE_FEATS = ["ask", "bid", "spread", "lsz_ask", "lsz_bid", "imb", "dm5", "dm15", "dm30"]
SPOT_FEATS = ["sp5", "sp15", "sp30", "zd", "edge", "vol"]
ASK_LO, ASK_HI = 0.03, 0.85
SEED, TARGET, MAX_GEN, MIN_DISTINCT_TRADES, JACC = 4, 5000, 300_000, 20, 0.9
N_PRIOR = 439_160


def feats_for(market):
    return BASE_FEATS + (SPOT_FEATS if market == "bitcoin" else [])


def git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, check=True).stdout


def rows(commit, f, nm):
    return list(csv.DictReader(io.StringIO(gzip.decompress(git("show", f"{commit}:{f}/{nm}.csv.gz")).decode())))


def fee(p, c, m=1.0):
    return math.ceil(round(100 * 0.07 * c * p * (1 - p) * m, 9)) / 100 if c > 0 else 0.0


def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def proxy(spot):
    ticks = sorted((int(r["t_recv_ms"]), r["exchange"], float(r["price"])) for r in spot if r["asset"] == "BTC" and r["price"])
    out = {}
    if not ticks:
        return out
    last, i = {}, 0
    for sec in range(ticks[0][0] // 1000, ticks[-1][0] // 1000 + 1):
        while i < len(ticks) and ticks[i][0] < (sec + 1) * 1000:
            last[ticks[i][1]] = (ticks[i][0], ticks[i][2]); i += 1
        live = sorted(p for t, p in last.values() if (sec + 1) * 1000 - t <= 5000)
        if len(live) >= 2:
            out[sec] = float(np.median(live))
    return out


def load_windows(market, commit, t_from, t_to):
    """Windows (close time in [t_from, t_to)) with polls, strike, result; first folder holding a window wins."""
    pre = PREFIX[market]
    names = git("ls-tree", "-r", "--name-only", commit, "quotes/").decode().split()
    folders = sorted({"/".join(n.split("/")[:3]) for n in names if n.count("/") == 3 and n.endswith("quotes.csv.gz")})
    W, X = {}, {}
    for f in folders:
        try:
            res = rows(commit, f, "results")
        except subprocess.CalledProcessError:
            continue
        resd = {}
        for r in res:
            if r["ticker"].startswith(pre + "-") and r["result"] in ("yes", "no") and r["ticker"] not in W:
                C = datetime.strptime(r["close_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
                if t_from <= C < t_to:
                    resd[r["ticker"]] = (C, r["result"])
        if not resd:
            continue
        q = rows(commit, f, "quotes")
        if market == "bitcoin":
            try:
                X.update(proxy(rows(commit, f, "spot")))
            except subprocess.CalledProcessError:
                pass
        polls = defaultdict(list)
        for r in q:
            if r["ticker"] in resd:
                polls[r["ticker"]].append(r)
        for tk, (C, result) in resd.items():
            ps = sorted(polls[tk], key=lambda p: int(p["t_recv_ms"]))
            if not ps:
                continue
            arr = []
            for p in ps:
                ok = p["status"] == "active" and p["yes_bid"] not in ("", None) and p["yes_ask"] not in ("", None)
                yb = float(p["yes_bid"]) if ok else np.nan
                ya = float(p["yes_ask"]) if ok else np.nan
                arr.append((int(p["t_recv_ms"]) / 1000.0, yb, ya, float(p["bid_size"] or 0), float(p["ask_size"] or 0)))
            a = np.array(arr, dtype=float)
            W[tk] = {"C": C, "K": float(ps[0]["strike"]), "result": result, "date": datetime.fromtimestamp(C, timezone.utc).strftime("%Y-%m-%d"),
                     "t": a[:, 0], "yb": a[:, 1], "ya": a[:, 2], "bs": a[:, 3], "as": a[:, 4]}
    return W, X


def side_q(w, i, s):
    """Side ask, ask size, bid, bid size at poll i (s 0 YES, 1 NO); nan when not two-sided."""
    yb, ya, bs, as_ = w["yb"][i], w["ya"][i], w["bs"][i], w["as"][i]
    if not (yb > 0 and ya < 1 and yb <= ya):
        # one-sided books still give a bid of 0 (or an ask of 1) to the exit leg
        if s == 0:
            return (ya if ya < 1 else np.nan), as_, (yb if yb > 0 else 0.0), (bs if yb > 0 else 0.0)
        return ((1 - yb) if yb > 0 else np.nan), bs, ((1 - ya) if ya < 1 else 0.0), (as_ if ya < 1 else 0.0)
    if s == 0:
        return ya, as_, yb, bs
    return 1 - yb, bs, 1 - ya, as_


def pnl_trade(side_win, p, asz, exit_bid, exit_bsz, c_max, m):
    c = min(c_max, math.floor(asz + 1e-9))
    if c <= 0:
        return np.nan
    settle = 1.0 if side_win else 0.0
    sold = 0 if exit_bid is None or exit_bid <= 0 else min(c, math.floor(exit_bsz + 1e-9))
    return sold * exit_bid - fee(exit_bid, sold, m) + (c - sold) * settle - c * p - fee(p, c, m) if sold else c * settle - c * p - fee(p, c, m)


def build(market, W, X):
    """One row per (window, poll, side) in the last 150 s. Returns feature matrix and per-exit pnl arrays."""
    F = feats_for(market)
    keys = sorted(W, key=lambda k: W[k]["C"])
    R = defaultdict(list)
    for wi, tk in enumerate(keys):
        w = W[tk]
        t, C = w["t"], w["C"]
        n = len(t)
        two = (w["yb"] > 0) & (w["ya"] < 1) & (w["yb"] <= w["ya"])
        mid = np.where(two, (w["yb"] + w["ya"]) / 2, np.nan)
        # exit polls: first poll at or after C - X, within 5 s
        exit_idx = {}
        for X_ in EXITS[1:]:
            j = int(np.searchsorted(t, C - X_, side="left"))
            exit_idx[X_] = j if j < n and t[j] <= C - X_ + 5 else None
        for i in range(n):
            left = C - t[i]
            if left > 150 or left <= 0 or not two[i]:
                continue
            sec = int(t[i]) - 1
            spot = {}
            if market == "bitcoin":
                S = X.get(sec)
                sp = {d: (math.log(S / X[sec - d]) * 1e4 if S and X.get(sec - d) else np.nan) for d in (5, 15, 30)}
                lr = [math.log(X[u + 1] / X[u]) for u in range(sec - 120, sec) if u in X and u + 1 in X]
                sig = float(np.std(lr)) if len(lr) >= 60 else np.nan
                zd = (S - w["K"]) / (sig * S * math.sqrt(left)) if S and sig and sig > 0 else np.nan
                spot = {"sp": sp, "sig": sig, "zd": zd}
            dmid = {}
            for d in (5, 15, 30):
                j = int(np.searchsorted(t, t[i] - d, side="right")) - 1
                dmid[d] = mid[i] - mid[j] if j >= 0 and not np.isnan(mid[j]) else np.nan
            for s in (0, 1):
                ask, asz, bid, bsz = side_q(w, i, s)
                if not (ASK_LO <= ask <= ASK_HI) or asz < 1:
                    continue
                sgn = 1 if s == 0 else -1
                smid = mid[i] if s == 0 else 1 - mid[i]
                f = {"ask": ask, "bid": bid, "spread": w["ya"][i] - w["yb"][i], "lsz_ask": math.log1p(asz), "lsz_bid": math.log1p(bsz),
                     "imb": (bsz - asz) / (bsz + asz) if bsz + asz > 0 else np.nan,
                     "dm5": sgn * dmid[5], "dm15": sgn * dmid[15], "dm30": sgn * dmid[30]}
                if market == "bitcoin":
                    f.update({"sp5": sgn * spot["sp"][5], "sp15": sgn * spot["sp"][15], "sp30": sgn * spot["sp"][30],
                              "zd": sgn * spot["zd"], "vol": spot["sig"] * 1e4 if spot["sig"] == spot["sig"] else np.nan})
                    f["edge"] = phi(f["zd"]) - ask if f["zd"] == f["zd"] else np.nan
                win = (w["result"] == "yes") == (s == 0)
                # same-poll fill, then the latency fill at the next poll
                outs = {}
                for tag in ("s", "l"):
                    fi, fp, fsz = i, ask, asz
                    if tag == "l":
                        if i + 1 >= n or t[i + 1] >= C or t[i + 1] <= t[i]:
                            fi = None
                        else:
                            fp, fsz, _, _ = side_q(w, i + 1, s)
                            fi = i + 1 if fp == fp and 0 < fp < 1 and fsz >= 1 else None
                    for e in EXITS:
                        for c, m in ((1, 1.0), (10, 1.0), (1, 1.2)):
                            key = f"{tag}{e}_{c}_{m}"
                            if fi is None:
                                outs[key] = np.nan; continue
                            ej = exit_idx.get(e) if e else None
                            if e and ej is not None and t[ej] > t[fi]:
                                _, _, eb, ebs = side_q(w, ej, s)
                                outs[key] = pnl_trade(win, fp, fsz, eb if ebs >= 1 else None, ebs, c, m)
                            else:
                                outs[key] = pnl_trade(win, fp, fsz, None, 0, c, m)
                            if e and c == 1 and m == 1.0 and tag == "s":
                                outs[f"held{e}"] = 0 if (ej is not None and t[ej] > t[fi] and side_q(w, ej, s)[3] >= 1 and side_q(w, ej, s)[2] > 0) else 1
                R["w"].append(wi); R["t"].append(t[i]); R["left"].append(left); R["side"].append(s); R["fav"].append(1 if smid > 0.5 else (-1 if smid < 0.5 else 0))
                for k in F:
                    R[k].append(f[k])
                for k, v in outs.items():
                    R[k].append(v)
    A = {k: np.array(v, dtype=float) for k, v in R.items()}
    dates = np.array([W[k]["date"] for k in keys])
    return A, keys, dates


def deciles(A, F):
    return {k: [float(x) for x in np.nanquantile(A[k], [i / 10 for i in range(1, 10)])] for k in F}


def random_spec(rng, F, Q):
    hi, lo = sorted(rng.sample(GRID, 2), reverse=True)
    conds = []
    for f in rng.sample(F, rng.randint(1, 3)):
        conds.append([f, rng.choice([">=", "<="]), Q[f][rng.randrange(9)]])
    ex = rng.choice([e for e in EXITS if e == 0 or e < lo])
    return {"side": rng.choice(SIDES), "hi": hi, "lo": lo, "conds": sorted(conds), "exit": ex}


def canon(sp):
    return json.dumps([sp["side"], sp["hi"], sp["lo"], sp["conds"], sp["exit"]])


def entries(A, sp):
    m = (A["left"] <= sp["hi"]) & (A["left"] >= sp["lo"])
    if sp["side"] == "YES":
        m &= A["side"] == 0
    elif sp["side"] == "NO":
        m &= A["side"] == 1
    elif sp["side"] == "FAV":
        m &= A["fav"] == 1
    else:
        m &= A["fav"] == -1
    for f, op, q in sp["conds"]:
        v = A[f]
        with np.errstate(invalid="ignore"):
            m &= (v >= q) if op == ">=" else (v <= q)
    idx = np.nonzero(m)[0]
    if not len(idx):
        return idx
    # rows are in (window, time) order; first matching poll per window (one side per poll for every side rule)
    _, first = np.unique(A["w"][idx], return_index=True)
    return idx[first]


def stats(A, dates, idx, sp, tag="s"):
    e = sp["exit"]
    out = {}
    for c, m in ((1, 1.0), (10, 1.0), (1, 1.2)):
        v = A[f"{tag}{e}_{c}_{m}"][idx]
        v = v[~np.isnan(v)]
        g, l = v[v > 0].sum(), -v[v < 0].sum()
        out[f"pf{c}_{m}"] = float(g / l) if l > 0 else (float("inf") if g > 0 else 0.0)
        out[f"net{c}_{m}"] = float(v.sum())
        if c == 1 and m == 1.0:
            out["n"] = int(len(v))
            out["mean1"] = float(v.mean()) if len(v) else 0.0
            out["z"] = float(v.mean() / (v.std(ddof=1) / math.sqrt(len(v)))) if len(v) > 1 and v.std(ddof=1) > 0 else 0.0
            out["wins"] = int((v > 0).sum())
    out["dates"] = int(len(set(dates[A["w"][idx].astype(int)]))) if len(idx) else 0
    out["mean_ask"] = float(A["ask"][idx].mean()) if len(idx) else 0.0
    return out


def jfin(x):
    return x if x == x and abs(x) != float("inf") else (999.0 if x == float("inf") else None)


def discovery():
    SCR.mkdir(parents=True, exist_ok=True)
    W, X = load_windows("bitcoin", DISC_COMMIT, 0, DISC_END)
    A, keys, dates = build("bitcoin", W, X)
    F = feats_for("bitcoin")
    Q = deciles(A, F)
    lines = [f"GEN4 discovery, data {DISC_COMMIT[:9]}, Bitcoin windows {len(keys)} on {len(set(dates))} dates, rows {len(A['w'])}"]
    gw, _ = load_windows("gold", DISC_COMMIT, 0, DISC_END)
    lines.append(f"Gold discovery windows: {len(gw)} -> NOT_RUNNABLE on this split")
    if len(keys) < 100:
        lines.append("NOT_ENOUGH_DATA: fewer than 100 discovery windows"); print("\n".join(lines)); return
    rng = random.Random(SEED)
    seen, kept, bits = set(), [], defaultdict(list)
    generated = 0
    while len(kept) < TARGET and generated < MAX_GEN:
        sp = random_spec(rng, F, Q)
        generated += 1
        c = canon(sp)
        if c in seen:
            continue
        seen.add(c)
        idx = entries(A, sp)
        if len(idx) < MIN_DISTINCT_TRADES:
            continue
        b = 0
        for wi, s in zip(A["w"][idx].astype(int), A["side"][idx].astype(int)):
            b |= 1 << (2 * int(wi) + int(s))
        pc = b.bit_count()
        if any((b & o).bit_count() / (pc + po - (b & o).bit_count()) > JACC for o, po in bits[sp["exit"]]):
            continue
        bits[sp["exit"]].append((b, pc))
        st = stats(A, dates, idx, sp)
        stl = stats(A, dates, idx, sp, "l")
        held = int(np.nansum(A[f"held{sp['exit']}"][idx])) if sp["exit"] else 0
        kept.append({"spec": sp, "disc": st, "disc_lat": {"pf1": stl["pf1_1.0"], "n": stl["n"]}, "held_fallback": held})
    surv = [k for k in kept if k["disc"]["pf1_1.0"] >= 1.5 and k["disc"]["n"] >= 40 and k["disc"]["dates"] >= 4 and k["disc"]["net1_1.2"] > 0]
    ctrl = [k for k in kept if k["disc"]["n"] >= 40 and k not in surv]
    pfs = np.array([min(k["disc"]["pf1_1.0"], 99) for k in kept])
    lines += [f"generated {generated}, distinct canonical {len(seen)}, distinct kept {len(kept)}, N added {2 * generated}",
              f"discovery PF1 over distinct: median {np.median(pfs):.2f}, p95 {np.quantile(pfs, 0.95):.2f}",
              f"passed discovery {len(surv)}; control pool (n>=40, failed) {len(ctrl)}"]
    for k in sorted(surv, key=lambda k: -k["disc"]["pf1_1.0"])[:15]:
        d = k["disc"]
        lines.append(f"  {canon(k['spec'])}  PF1 {d['pf1_1.0']:.2f} PF10 {d['pf10_1.0']:.2f} x1.2 {d['pf1_1.2']:.2f} n {d['n']} dates {d['dates']} ask {d['mean_ask']:.2f} lat {k['disc_lat']['pf1']:.2f}")
    frozen = {"worker": "GEN4", "data_commit": DISC_COMMIT, "generated": generated, "distinct": len(kept), "N_added": 2 * generated,
              "deciles": Q, "survivors": [{"spec": k["spec"], "disc": {a: jfin(b) for a, b in k["disc"].items()}} for k in surv],
              "control": [{"spec": k["spec"], "disc": {a: jfin(b) for a, b in k["disc"].items()}} for k in ctrl]}
    FROZEN.write_text(json.dumps(frozen, indent=1, sort_keys=True))
    lines.append(f"frozen {FROZEN.name} sha256 {hashlib.sha256(FROZEN.read_bytes()).hexdigest()}")
    txt = "\n".join(lines)
    (SCR / "disc_result.txt").write_text(txt)
    print(txt)


def validation(commit):
    fz = json.loads(FROZEN.read_text())
    W, X = load_windows("bitcoin", commit, DISC_END, VAL_END)
    A, keys, dates = build("bitcoin", W, X)
    lines = [f"GEN4 validation, data {commit[:9]}, frozen sha256 {hashlib.sha256(FROZEN.read_bytes()).hexdigest()}",
             f"Bitcoin validation windows {len(keys)} on {len(set(dates))} dates"]

    def judge(k):
        sp = k["spec"]
        idx = entries(A, sp)
        st, stl = stats(A, dates, idx, sp), stats(A, dates, idx, sp, "l")
        ok = st["pf1_1.0"] >= 1.3 and st["n"] >= 20 and st["dates"] >= 2 and st["net1_1.2"] > 0 and stl["pf1_1.0"] >= 1.0
        return ok, st, stl
    res = []
    for k in fz["survivors"]:
        ok, st, stl = judge(k)
        res.append((ok, k, st, stl))
    cres = [judge(k)[0] for k in fz["control"]]
    ps = sum(r[0] for r in res) / max(len(res), 1)
    pc = sum(cres) / max(len(cres), 1)
    lines += [f"survivors {len(res)}, passed validation {sum(r[0] for r in res)} ({100 * ps:.1f}%)",
              f"control {len(cres)}, passed {sum(cres)} ({100 * pc:.1f}%)",
              f"family control rule (survivor rate >= control + 5 pt): {'met' if ps >= pc + 0.05 else 'NOT met -> FALSIFIED as a family'}"]
    for ok, k, st, stl in sorted(res, key=lambda r: (-r[0], -min(r[2]['pf1_1.0'], 99))):
        d = k["disc"]
        lines.append(f"  {'PASS' if ok else 'fail'} {canon(k['spec'])} | disc PF1 {d['pf1_1.0']} n {d['n']} | val PF1 {st['pf1_1.0']:.2f} PF10 {st['pf10_1.0']:.2f} "
                     f"x1.2 {st['pf1_1.2']:.2f} n {st['n']} dates {st['dates']} mean {100 * st['mean1']:+.2f}c z {st['z']:.2f} lat {stl['pf1_1.0']:.2f} (n {stl['n']}) ask {st['mean_ask']:.2f}")
    out = {"commit": commit, "results": [{"pass": ok, "spec": k["spec"], "disc": k["disc"], "val": {a: jfin(b) for a, b in st.items()},
                                          "val_lat": {a: jfin(b) for a, b in stl.items()}} for ok, k, st, stl in res],
           "control_pass": sum(cres), "control_n": len(cres)}
    (SCR / "val_result.json").write_text(json.dumps(out, indent=1))
    txt = "\n".join(lines)
    (SCR / "val_result.txt").write_text(txt)
    print(txt)


def evaluate(spec, since="2026-10-30", commit="origin/quote-data", until=None):
    """Forward ledger hook. Trades of one frozen GEN4 rule on Bitcoin windows closing at or after `since` (UTC date).
    Returns a list of dicts: ticker, close, side, price, pnl1, pnl10, pnl1_x12, latency pnl1. Reads only `commit`."""
    commit = git("rev-parse", commit).decode().strip()
    t0 = datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()
    t1 = datetime.strptime(until, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() if until else 4e9
    W, X = load_windows(spec.get("market", "bitcoin"), commit, t0, t1)
    if not W:
        return []
    A, keys, dates = build(spec.get("market", "bitcoin"), W, X)
    idx = entries(A, spec)
    e = spec["exit"]
    out = []
    for i in idx:
        tk = keys[int(A["w"][i])]
        out.append({"ticker": tk, "close": W[tk]["C"], "date": W[tk]["date"], "side": "yes" if A["side"][i] == 0 else "no",
                    "price": float(A["ask"][i]), "left": float(A["left"][i]), "pnl1": float(A[f"s{e}_1_1.0"][i]),
                    "pnl10": float(A[f"s{e}_10_1.0"][i]), "pnl1_x12": float(A[f"s{e}_1_1.2"][i]), "lat_pnl1": float(A[f"l{e}_1_1.0"][i]),
                    "data_commit": commit})
    return out


if __name__ == "__main__":
    if sys.argv[1] == "discovery":
        discovery()
    elif sys.argv[1] == "validation":
        validation(git("rev-parse", sys.argv[2] if len(sys.argv) > 2 else "origin/quote-data").decode().strip())
