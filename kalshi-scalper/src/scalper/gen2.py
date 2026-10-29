"""GEN2 (README, Pre-registration: GEN2): 7,500 more distinct full strategies from new building blocks, all 18 fifteen-minute series.
Research only; nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
    python -m scalper.gen2 build     (rows and exits, discovery and validation days only; the holdout is not on disk)
    python -m scalper.gen2 search    (generate, dedupe, gates, freeze survivors)
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from multiprocessing import Pool

import numpy as np

from . import auto3
from .calibration import cluster_mean_z
from .gen1 import HOLD_FROM, DISC_DAYS, TP, ST, TE, BK, boot_pf5, pf, _norm_ppf
from .paths import DATA_DIR
from .scalp12 import sigma1

FILES = ("book", "l1b", "fresh", "alts2", "alts3", "alts4", "e3b")
SERIES = ["KXBTC15M", "KXETH15M", "KXGOLD15M", "KXDOGE15M", "KXXRP15M", "KXBNB15M", "KXNEAR15M", "KXHYPE15M", "KXZEC15M", "KXWTI15M",
          "KXSILVER15M", "KXNATGAS15M", "KXCOPPER15M", "KXPALLADIUM15M", "KXPLATINUM15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M"]
FAMILY = {s: (0 if i in (0, 1, 3, 4, 5, 6, 7, 8) else 1 if s in ("KXGOLD15M", "KXSILVER15M", "KXCOPPER15M", "KXPALLADIUM15M", "KXPLATINUM15M") else 2 if s in ("KXWTI15M", "KXNATGAS15M") else 3) for i, s in enumerate(SERIES)}
PARTNER = {0: "KXBTC15M", 1: "KXGOLD15M", 2: "KXWTI15M", 3: "KXEURUSD15M"}
CUR = {"KXBTC15M": "BTC", "KXETH15M": "ETH"}
LEFTS = list(range(840, 179, -60))
FEATS = ["asset", "family", "yes", "left", "ask", "bid", "spread", "d1", "d2", "d3", "d5", "rng5", "vol", "volz", "doi", "hour", "dow", "winidx",
         "mkt_d2", "part_d2", "part_mid", "prev_won", "prev_last", "z", "r3", "tb1", "tb5"]
NEW_FEATS = {"volz", "dow", "winidx", "mkt_d2", "prev_won", "prev_last"}
GRAMMAR = [f for f in FEATS if f not in ("asset", "family", "yes", "left")]
SINGLE = [("fixed", a, b, c, d) for a in TP for b in ST for c in TE for d in BK] + [("trail", t, None, c, None) for t in (0.05, 0.10, 0.15) for c in TE]
SCALEOUT = [(t1, te) for t1 in (0.05, 0.10) for te in (120, 240)]
NPZ = DATA_DIR / "gen2_rows.npz"
CHUNKS = DATA_DIR / "gen2_chunks"
RESULT = DATA_DIR / "gen2_result.txt"
FROZEN = DATA_DIR / "gen2_survivors.json"
N_PRIOR = 411_000
TARGET, MIN_DISC = 7500, 30
G = {}


def vfee(p, c, m=1.0):
    p = np.asarray(p, dtype=np.float64)
    return np.ceil(m * 0.07 * c * p * (1 - p) * 100 - 1e-9) / 100 / c


def load_all():
    M = {}
    for name in FILES:
        db = sqlite3.connect(DATA_DIR / f"{name}.sqlite")
        try:
            rows = db.execute("select ticker, series, strike, close_ts, result from market where series in (%s)" % ",".join("?" * len(SERIES)), SERIES).fetchall()
        except sqlite3.OperationalError:
            continue
        for tk, series, strike, close_ts, res in rows:
            if tk in M or close_ts >= HOLD_FROM:
                continue
            cs = {r[0]: (r[1], r[2], r[3] or 0.0, r[4] or 0.0) for r in db.execute(
                "select end_ts, bid_c, ask_c, volume, oi from candle where ticker=? and bid_c is not null and ask_c is not null", (tk,))}
            if cs:
                M[tk] = (series, strike, close_ts, cs, res)
    return M


def exits(bids, mids, spreads, ks, e, yes, close_ts, entry_mid):
    tp = np.array([np.inf if (c[0] == "trail" or c[1] is None) else c[1] for c in SINGLE])[:, None]
    st = np.array([np.inf if (c[0] == "trail" or c[2] is None) else c[2] for c in SINGLE])[:, None]
    tr = np.array([c[1] if c[0] == "trail" else np.inf for c in SINGLE])[:, None]
    te = np.array([c[3] for c in SINGLE])[:, None]
    bk = np.array([BK.index(c[4]) if c[0] == "fixed" else 0 for c in SINGLE])[:, None]
    B, S, Mi, K = bids[None, :], spreads[None, :], mids[None, :], ks[None, :]
    peak = np.maximum.accumulate(np.r_[e, bids])[1:][None, :]
    against = (Mi < 0.5) if (yes and entry_mid >= 0.5) else ((Mi > 0.5) if ((not yes) and entry_mid <= 0.5) else np.zeros_like(Mi, bool))
    hit = (B >= e + tp - 1e-9) | (B <= e - st + 1e-9) | (B <= peak - tr + 1e-9) | (K >= close_ts - te) | ((bk == 1) & (S >= 0.03 - 1e-9)) | ((bk == 2) & against)
    hit[:, -1] = True
    i1 = hit.argmax(axis=1)
    so1, so2 = [], []
    for t1, tte in SCALEOUT:
        h2 = (K[0] >= close_ts - tte); h2[-1] = True; j2 = int(h2.argmax())
        h1 = (bids >= e + t1 - 1e-9); h1 = h1 & (np.arange(len(bids)) <= j2)
        j1 = int(h1.argmax()) if h1.any() else j2
        so1.append(j1); so2.append(j2)
    return i1, np.array(so1), np.array(so2)


def chunk(items):
    M, spot, byclose, prev, volmed, mkt = G["M"], G["spot"], G["byclose"], G["prev"], G["volmed"], G["mkt"]
    X, W, D, XB, ZV, SO1, SO2, SZ = [], [], [], [], [], [], [], []
    for wid, tk in items:
        series, strike, close_ts, cs, res = M[tk]
        fam = FAMILY[series]; part = byclose.get((PARTNER[fam], close_ts)) if PARTNER[fam] != series else None
        day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
        keys = sorted(k for k in cs if k <= close_ts - 60)
        pv = prev.get((series, close_ts - 900))
        for L in LEFTS:
            t = close_ts - L; q = cs.get(t)
            if q is None:
                continue
            later = [k for k in keys if k > t]
            if not later:
                continue
            z0 = r30 = 0.0
            if series in CUR:
                cur = CUR[series]; s = spot.get((cur, t - 60)); sg = sigma1(spot, cur, t); s3 = spot.get((cur, t - 240))
                if s and sg and strike and s3:
                    z0 = math.log(s / strike) / (sg * math.sqrt(L / 60)); r30 = math.log(s / s3)
            mid = (q[0] + q[1]) / 2; p2 = cs.get(t - 120); own_d2 = mid - ((p2[0] + p2[1]) / 2 if p2 else mid)
            ms = mkt.get((close_ts, t), (0.0, 0))
            mkt_d2 = (ms[0] - own_d2) / (ms[1] - 1) if ms[1] > 1 else 0.0
            if part:
                a, b = part.get(t), part.get(t - 120)
                pm = (a[0] + a[1]) / 2 if a else 0.5; pd2 = pm - ((b[0] + b[1]) / 2 if b else pm)
            else:
                pm, pd2 = 0.5, 0.0
            ka = np.array(later); yb = np.array([cs[k][0] for k in later]); ya = np.array([cs[k][1] for k in later]); vz = np.array([cs[k][2] <= 0 for k in later])
            dt_ = datetime.fromtimestamp(t, timezone.utc)
            for yes in (1, 0):
                bid, ask = (q[0], q[1]) if yes else (1 - q[1], 1 - q[0])
                if not 0.03 <= ask <= 0.85:
                    continue
                sg_ = 1 if yes else -1
                ds = []
                for lag in (60, 120, 180, 300):
                    p = cs.get(t - lag); ds.append(bid - ((p[0] if yes else 1 - p[1]) if p else bid))
                path = [(cs[t - 60 * j][0] if yes else 1 - cs[t - 60 * j][1]) for j in range(6) if (t - 60 * j) in cs]
                fl = auto3.flow(CUR[series], t, sg_) if series in CUR else (0.0,) * 5
                pw = 0.0; pl = 0.5
                if pv:
                    pw = (1.0 if (pv[0] == "yes") == bool(yes) else -1.0) if pv[0] in ("yes", "no") else 0.0
                    pl = pv[1] if yes else 1 - pv[1]
                bids = yb if yes else 1 - ya
                i1, j1, j2 = exits(bids, (ya + yb) / 2, ya - yb, ka, ask, yes, close_ts, mid)
                X.append([SERIES.index(series), fam, yes, L, ask, bid, ask - bid, ds[0], ds[1], ds[2], ds[3], max(path) - min(path) if path else 0.0,
                          q[2], q[2] / volmed.get(series, 1.0), (q[3] - cs[t - 180][3]) if (t - 180) in cs else 0.0, dt_.hour, dt_.weekday(),
                          (close_ts // 900) % 4, sg_ * mkt_d2, sg_ * pd2, pm if yes else 1 - pm, pw, pl, sg_ * z0, sg_ * r30, fl[0], fl[1]])
                W.append(wid); D.append(day)
                XB.append(bids[i1].astype(np.float32)); ZV.append(vz[i1] | (q[2] <= 0))
                SO1.append(bids[j1].astype(np.float32)); SO2.append(bids[j2].astype(np.float32)); SZ.append(vz[j2] | (q[2] <= 0))
    out = CHUNKS / f"{items[0][0]}.npz"
    np.savez(out, X=np.array(X, dtype=np.float32).reshape(-1, len(FEATS)), W=np.array(W, dtype=np.int64), D=np.array(D),
             XB=np.array(XB, dtype=np.float32).reshape(-1, len(SINGLE)), ZV=np.array(ZV, dtype=bool).reshape(-1, len(SINGLE)),
             SO1=np.array(SO1, dtype=np.float32).reshape(-1, len(SCALEOUT)), SO2=np.array(SO2, dtype=np.float32).reshape(-1, len(SCALEOUT)),
             SZ=np.array(SZ, dtype=bool).reshape(-1, len(SCALEOUT)))
    return str(out)


def build():
    M = load_all()
    spot = {(c, ts // 1000): v for c, ts, v in sqlite3.connect(DATA_DIR / "search5k.sqlite").execute("select cur, ts, c from bar")}
    auto3.FUT = auto3.fut_load()
    byclose = {(m[0], m[2]): m[3] for m in M.values()}
    prev = {}
    for m in M.values():
        cs = m[3]; last = cs.get(m[2] - 60) or cs[max(cs)]
        prev[(m[0], m[2])] = (m[4], (last[0] + last[1]) / 2)
    closes = sorted({m[2] for m in M.values()})
    days = sorted({datetime.fromtimestamp(c, timezone.utc).strftime("%Y-%m-%d") for c in closes}); cut = days[DISC_DAYS] if len(days) > DISC_DAYS else days[-1]
    vols = defaultdict(list)
    for m in M.values():
        if datetime.fromtimestamp(m[2], timezone.utc).strftime("%Y-%m-%d") < cut:
            vols[m[0]] += [v[2] for v in m[3].values()]
    volmed = {s: max(statistics.median(v), 1.0) for s, v in vols.items() if v}
    mkt = defaultdict(lambda: [0.0, 0])
    for m in M.values():
        cs = m[3]
        for L in LEFTS:
            t = m[2] - L; a, b = cs.get(t), cs.get(t - 120)
            if a:
                d2 = (a[0] + a[1]) / 2 - (((b[0] + b[1]) / 2) if b else (a[0] + a[1]) / 2)
                x = mkt[(m[2], t)]; x[0] += d2; x[1] += 1
    G.update(M=M, spot=spot, byclose=byclose, prev=prev, volmed=volmed, mkt={k: tuple(v) for k, v in mkt.items()})
    CHUNKS.mkdir(exist_ok=True)
    for f in CHUNKS.glob("*.npz"):
        f.unlink()
    items = list(enumerate(sorted(M)))
    with Pool(4) as p:
        files = p.map(chunk, [items[i::96] for i in range(96)])
    P = [dict(np.load(f)) for f in files]
    cat = lambda k: np.concatenate([q[k] for q in P])
    X, Wd, Ds = cat("X"), cat("W"), cat("D")
    days = sorted(set(Ds.tolist())); didx = {d: i for i, d in enumerate(days)}
    day = np.array([didx[d] for d in Ds.tolist()])
    close = np.array([M[sorted(M)[w]][2] for w in Wd.tolist()])
    order = np.lexsort((-X[:, 2], -X[:, 3], Wd))
    np.savez(NPZ, X=X[order], W=Wd[order], day=day[order], close=close[order], XB=cat("XB")[order], ZV=cat("ZV")[order], SO1=cat("SO1")[order],
             SO2=cat("SO2")[order], SZ=cat("SZ")[order], days=np.array(days))
    print("rows", len(X), "days", len(days), "windows", len(M), flush=True)


# ---------------------------------------------------------------- search

def load():
    z = np.load(NPZ)
    return {k: z[k] for k in z.files}


def leg_net(D, idx, ex, c=10, m=1.0):
    """Per-trade net for exit `ex` (an index into SINGLE, or ("so", k) for scale-out) at C contracts."""
    e = D["X"][idx, FEATS.index("ask")].astype(np.float64)
    if isinstance(ex, tuple):
        k = ex[1]; x1 = D["SO1"][idx, k].astype(np.float64); x2 = D["SO2"][idx, k].astype(np.float64)
        h = max(c // 2, 1)
        return 0.5 * (x1 - vfee(x1, h, m)) + 0.5 * (x2 - vfee(x2, h, m)) - e - vfee(e, c, m), D["SZ"][idx, k]
    xb = D["XB"][idx, ex].astype(np.float64)
    return xb - e - vfee(e, c, m) - vfee(xb, c, m), D["ZV"][idx, ex]


def mask(D, s, split):
    X = D["X"]
    m = split & (X[:, 3] <= s["L_hi"]) & (X[:, 3] >= s["L_lo"])
    if s["scope"][0] == "series":
        m &= np.isin(X[:, 0], s["scope"][1])
    elif s["scope"][0] == "family":
        m &= X[:, 1] == s["scope"][1]
    if s["side"] != "both":
        m &= X[:, 2] == (1 if s["side"] == "yes" else 0)
    for f, op, th in s["conds"]:
        col = X[:, FEATS.index(f)]
        m &= (col <= th) if op == "le" else (col > th)
    return m


def first_per_window(D, idx):
    if len(idx) == 0:
        return idx
    w = D["W"][idx]
    return idx[np.r_[True, w[1:] != w[:-1]]]


def evaluate(D, s, split, c=10, m=1.0):
    """Returns (per-window net array, day array, window ids, zero-volume share)."""
    if s["kind"] == "pair":
        A = first_per_window(D, np.flatnonzero(mask(D, s, split)))
        X = D["X"]; out, days, ws, zv = [], [], [], []
        partner = SERIES.index(s["partner"])
        for i in A:
            key = (D["close"][i], int(X[i, 3]), partner, 0 if X[i, 2] == 1 else 1)
            j = G["pairidx"].get(key)
            if j is None:
                continue
            diff = X[i, FEATS.index("d2")] - X[j, FEATS.index("d2")]
            if not ((diff <= s["div"]) if s["div_op"] == "le" else (diff > s["div"])):
                continue
            n1, z1 = leg_net(D, np.array([i]), s["exit"], c, m); n2, z2 = leg_net(D, np.array([j]), s["exit"], c, m)
            out.append(n1[0] + n2[0]); days.append(D["day"][i]); ws.append(D["W"][i]); zv.append(bool(z1[0] or z2[0]))
        return np.array(out), np.array(days), np.array(ws), (float(np.mean(zv)) if zv else 1.0)
    idx = first_per_window(D, np.flatnonzero(mask(D, s, split)))
    net, zv = leg_net(D, idx, s["exit"], c, m)
    if s["kind"] == "scalein" and len(idx):
        X = D["X"]; add = np.zeros(len(idx)); zz = zv.copy()
        for n, i in enumerate(idx):
            j = G["legidx"].get((int(D["W"][i]), int(X[i, 3]) - 60, int(X[i, 2])))
            if j is not None and X[j, FEATS.index("bid")] <= X[i, FEATS.index("bid")] - 0.05:
                a2, z2 = leg_net(D, np.array([j]), s["exit"], c, m); add[n] = a2[0]; zz[n] = zz[n] or z2[0]
        net = net + add; zv = zz
    return net, D["day"][idx], D["W"][idx], (float(zv.mean()) if len(idx) else 1.0)


def stats(net, days):
    if len(net) == 0:
        return {"n": 0, "days": 0, "pf": 0.0, "z": 0.0, "mean_c": 0.0}
    _, _, z = cluster_mean_z(list(zip(days.tolist(), net.tolist()))) if len(net) > 1 else (0, 0, 0.0)
    return {"n": int(len(net)), "days": int(len(set(days.tolist()))), "pf": pf(net), "z": float(z), "mean_c": float(100 * net.mean())}


def has_new_block(s):
    if s["kind"] in ("pair", "scalein") or isinstance(s["exit"], tuple) or SINGLE[s["exit"]][0] == "trail":
        return True
    if s["scope"][0] == "family" or (s["scope"][0] == "series" and any(a > 2 for a in s["scope"][1])) or s["scope"][0] == "all":
        return True
    return any(f in NEW_FEATS for f, _, _ in s["conds"])


def draw(rng, Q):
    kind = rng.choices(["single", "scalein", "pair"], [0.7, 0.1, 0.2])[0]
    width = rng.choice(range(60, 601, 60)); L_hi = rng.choice([L for L in LEFTS if L - width >= 180])
    if kind == "pair":
        a = rng.choice([i for i in range(len(SERIES)) if PARTNER[FAMILY[SERIES[i]]] != SERIES[i]])
        scope = ("series", (a,))
    else:
        r = rng.random()
        scope = ("series", tuple(sorted(rng.sample(range(len(SERIES)), rng.choice([1, 1, 1, 2, 3]))))) if r < 0.6 else (("family", rng.randrange(4)) if r < 0.9 else ("all", None))
    s = {"kind": kind, "scope": scope, "L_hi": L_hi, "L_lo": L_hi - width, "side": rng.choice(["yes", "no", "both"]) if kind != "pair" else rng.choice(["yes", "no"]), "conds": []}
    used = set()
    for _ in range(rng.randint(0 if kind == "pair" else 1, 3 if kind == "pair" else 4)):
        f = rng.choice([g for g in GRAMMAR if g not in used]); used.add(f)
        s["conds"].append((f, rng.choice(["le", "gt"]), float(Q[f][rng.choice(range(10, 91, 10))])))
    s["exit"] = ("so", rng.randrange(len(SCALEOUT))) if rng.random() < 0.08 else rng.randrange(len(SINGLE))
    if kind == "pair":
        s["partner"] = PARTNER[FAMILY[SERIES[scope[1][0]]]]
        s["div_op"] = rng.choice(["le", "gt"]); s["div"] = float(Q["_pairdiff"][rng.choice(range(10, 91, 10))])
    return s


def exit_key(ex):
    if isinstance(ex, tuple):
        return ("so",) + SCALEOUT[ex[1]]
    return SINGLE[ex]


def near(a, b):
    ka, kb = exit_key(a["exit"]), exit_key(b["exit"])
    if ka[0] != kb[0] or a["kind"] != b["kind"]:
        return False
    if ka[0] == "fixed":
        return all(abs(seq.index(x) - seq.index(y)) <= 1 for seq, x, y in ((TP, ka[1], kb[1]), (ST, ka[2], kb[2]), (TE, ka[3], kb[3]))) and ka[4] == kb[4]
    if ka[0] == "trail":
        return abs(ka[1] - kb[1]) <= 0.051 and abs(TE.index(ka[3]) - TE.index(kb[3])) <= 1
    return True


def desc(s):
    sc = s["scope"]
    who = {"series": "+".join(SERIES[i].replace("KX", "").replace("15M", "") for i in sc[1]) if sc[0] == "series" else "", "family": ["crypto", "metals", "energy", "fx"][sc[1]] if sc[0] == "family" else "", "all": "all"}[sc[0]]
    ex = exit_key(s["exit"])
    ext = (f"TP {ex[1]} stop {ex[2]} time {ex[3]}s book {ex[4]}" if ex[0] == "fixed" else f"trail {ex[1]} time {ex[3]}s") if ex[0] != "so" else f"scale-out half at +{ex[1]} rest at {ex[2]}s"
    cond = " & ".join(f"{f}{'<=' if op == 'le' else '>'}{th:.3g}" for f, op, th in s["conds"])
    extra = f" | pair vs {s['partner']} opposite side, d2 diff {s['div_op']} {s['div']:.3g}" if s["kind"] == "pair" else (" | scale-in +1 min if bid -5c" if s["kind"] == "scalein" else "")
    return f"[{s['kind']} {who} {s['side']} {s['L_hi']}..{s['L_lo']}s | {cond or 'no conditions'}{extra} | {ext}]"


def search():
    D = load(); X = D["X"]
    disc = D["day"] < DISC_DAYS; val = ~disc
    G["legidx"] = {(int(w), int(L), int(y)): i for i, (w, L, y) in enumerate(zip(D["W"].tolist(), X[:, 3].tolist(), X[:, 2].tolist()))}
    G["pairidx"] = {(int(c), int(L), int(a), int(y)): i for i, (c, L, a, y) in enumerate(zip(D["close"].tolist(), X[:, 3].tolist(), X[:, 0].tolist(), X[:, 2].tolist()))}
    Q = {f: np.percentile(X[disc][:, FEATS.index(f)], list(range(0, 101))) for f in GRAMMAR}
    Q["_pairdiff"] = np.percentile(X[disc][:, FEATS.index("d2")] - X[disc][:, FEATS.index("part_d2")], list(range(0, 101)))
    rng = random.Random(20261030)
    distinct, generated, rejected_old = [], 0, 0
    while len(distinct) < TARGET and generated < 600_000:
        s = draw(rng, Q); generated += 1
        if not has_new_block(s):
            rejected_old += 1; continue
        net, days, ws, zv = evaluate(D, s, disc)
        if len(net) < MIN_DISC:
            continue
        wset = set(ws.tolist())
        if any(near(s, s2) and len(wset & w2) / len(wset | w2) > 0.5 for s2, w2, _ in distinct):
            continue
        st = stats(net, days); st["zv"] = zv
        distinct.append((s, wset, st))
        if len(distinct) % 500 == 0:
            print("distinct", len(distinct), "generated", generated, flush=True)
    N_total = N_PRIOR + generated
    zbar = _norm_ppf(1 - 0.05 / N_total)
    rows = []
    for s, w, d in distinct:
        fail = None
        if d["pf"] < 1.5: fail = "DISCOVERY_PF"
        elif d["n"] < 150 or d["days"] < 25: fail = "DISCOVERY_N"
        elif d["zv"] > 0.2: fail = "FILL_OPTIMISM"
        v = b5 = None
        if fail is None:
            net, days, _, zv = evaluate(D, s, val); v = stats(net, days)
            v["pfs"] = pf(evaluate(D, s, val, m=1.2)[0]); v["pf1"] = pf(evaluate(D, s, val, c=1)[0]); v["zv"] = zv
            if v["n"] < 60 or v["days"] < 15: fail = "VALIDATION_N"
            elif v["pf"] < 1.5: fail = "VALIDATION_PF"
            elif v["pfs"] < 1.2: fail = "VALIDATION_STRESS"
            elif zv > 0.2: fail = "FILL_OPTIMISM"
            else:
                b5 = boot_pf5(net, days)
                if b5 <= 1.0: fail = "VALIDATION_BOOTSTRAP"
                elif v["z"] < zbar: fail = "DEFLATION"
        rows.append({"s": s, "disc": d, "valid": v, "boot5": b5, "fail": fail})
    dp = [r for r in rows if r["valid"] is not None]
    full = [r for r in rows if r["fail"] is None]
    pfs = np.array([r["disc"]["pf"] for r in rows]); big = [r for r in rows if r["disc"]["n"] >= 150]
    lines = [f"GEN2: generated {generated} (rejected for using no new block {rejected_old}), distinct {len(distinct)}; overlap with GEN1/GEN1S by canonical form: 0 (every strategy uses a new block); N tried {N_total}, Bonferroni z bar {zbar:.2f}",
             f"discovery PF over distinct: median {np.median(pfs):.2f}, 95th pct {np.percentile(pfs, 95):.2f}; best with 150+ trades {max((r['disc']['pf'] for r in big), default=0):.2f}",
             f"passed discovery {len(dp)}; failed in validation: " + ", ".join(f"{k} {sum(1 for r in dp if r['fail'] == k)}" for k in ("VALIDATION_N", "VALIDATION_PF", "VALIDATION_STRESS", "FILL_OPTIMISM", "VALIDATION_BOOTSTRAP", "DEFLATION")) + f"; survivors (all validation gates incl. deflation) {len(full)}"]
    order = {None: 9, "DEFLATION": 8, "VALIDATION_BOOTSTRAP": 7, "VALIDATION_STRESS": 6, "VALIDATION_PF": 5, "FILL_OPTIMISM": 4, "VALIDATION_N": 3}
    best = sorted(dp, key=lambda r: (order.get(r["fail"], 0), r["valid"]["pf"]), reverse=True)
    best += sorted([r for r in big if r["valid"] is None], key=lambda r: -r["disc"]["pf"])[:max(0, 5 - len(best))]
    top = []
    for r in best[:5]:
        s = r["s"]
        if r["valid"] is None:
            net, days, _, zv = evaluate(D, s, val); v = stats(net, days); v["pfs"] = pf(evaluate(D, s, val, m=1.2)[0]); v["pf1"] = pf(evaluate(D, s, val, c=1)[0]); info = True
        else:
            v = r["valid"]; info = False
        label = "PASSED_ALL_GATES_TO_VALIDATION (holdout from 2026-10-28 not yet read)" if r["fail"] is None else "FAILED_GATE_" + r["fail"]
        top.append({"rule": desc(s), "label": label, "discovery": r["disc"], "validation": v, "validation_is_information_only": info, "bootstrap5": r["boot5"], "zBar": round(zbar, 2)})
        lines.append(f"  {label}: {desc(s)} | disc PF {r['disc']['pf']:.2f} n={r['disc']['n']} days {r['disc']['days']} | valid PF {v['pf']:.2f} (1c {v.get('pf1', 0):.2f}, stress {v.get('pfs', 0):.2f}) n={v['n']} days {v['days']} z {v['z']:+.2f}{' (information only)' if info else ''}")
    FROZEN.write_text(json.dumps({"frozen_at": datetime.now(timezone.utc).isoformat(), "survivors": [r["s"] for r in full]}, default=list))
    (DATA_DIR / "gen2_top5.json").write_text(json.dumps(top, indent=1, default=list))
    lines.insert(0, "GEN2 VERDICT so far: " + ("NO_WINNER (FALSIFIED before the holdout)" if not full else f"{len(full)} survivors frozen for the holdout"))
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    {"build": build, "search": search}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
