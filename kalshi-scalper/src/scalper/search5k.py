"""SEARCH5K (README, Pre-registration: SEARCH5K): 5,000 rules on Bitcoin and Ethereum L1 entries from outside information, judged against a
permutation null for the best-of-5,000. Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED,
NOT_ENOUGH_DATA. Nothing here means trade.

    python -m scalper.search5k build     (entries and features into data/search5k_rows.json)
    python -m scalper.search5k run       (the one read; a second is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import bisect
import json
import math
import random
import sqlite3
import statistics as st
import sys
from datetime import datetime, timezone

import numpy as np

from . import ideas20 as I
from . import lstrats as L
from .paths import DATA_DIR

DB = DATA_DIR / "search5k.sqlite"
ROWS = DATA_DIR / "search5k_rows.json"
RESULT = DATA_DIR / "search5k_result.txt"
SERIES = {"KXBTC15M": "BTC", "KXETH15M": "ETH"}
OTHER = {"BTC": "ETH", "ETH": "BTC"}
LEFT_S = 360
BAND = L.L1["band"]
BAR_S = 60                       # a Deribit bar stamped T closes at T + 60; the last usable bar starts at decision - 60
TAU = 5.0 + 1.0 / 3.0
N_RULES, SEED, N_PERM = 5000, 25102501, 300
MIN_DISC, MIN_CONF = 150, 60
DISC_C, CONF_C, CONF_Z, HOLD_Z = 0.020, 0.010, 1.64, 1.0
SPLIT = (0.60, 0.80)             # discovery, confirmation, holdout by day

NUMERIC = ["price", "spread", "rise1", "rise3", "rise5", "range5", "tib", "dip", "vol_last", "vol_ratio", "flips",
           "ret1", "ret5", "ret15", "ret60", "rv15", "rv60", "rv_ratio", "vol5_pct", "range15", "dist_sigma", "gap_fav", "gap_adv",
           "dvol", "dvol_chg", "vrp", "fund", "fund_chg", "oth_ret15", "oth_ret5"]
CATEGORICAL = {"hourb": [0, 1, 2, 3], "slot": [0, 1, 2, 3], "weekend": [0, 1], "usopen": [1]}


class Perp:
    """Minute arrays (NaN where a bar is missing), indexed by minute since t0; bars stamped by their start."""

    def __init__(self, con, cur):
        rows = con.execute("select ts, o, h, l, c, v from bar where cur=? order by ts", (cur,)).fetchall()
        self.t0 = rows[0][0] // 60000
        n = rows[-1][0] // 60000 - self.t0 + 1
        self.o, self.h, self.l, self.c, self.v = (np.full(n, np.nan) for _ in range(5))
        for ts, o, h, l, c, v in rows:
            i = ts // 60000 - self.t0
            self.o[i], self.h[i], self.l[i], self.c[i], self.v[i] = o, h, l, c, v
        d = con.execute("select ts, c from dv where cur=? order by ts", (cur,)).fetchall()
        self.d = np.full(n, np.nan)
        for ts, c in d:
            i = ts // 60000 - self.t0
            if 0 <= i < n:
                self.d[i] = c
        f = con.execute("select ts, i8 from fund where cur=? order by ts", (cur,)).fetchall()
        self.fts = [x[0] // 1000 for x in f]
        self.fv = [x[1] for x in f]
        self.n = n

    def idx(self, sec: int) -> int:
        return sec // 60 - self.t0

    def fund(self, sec: int, back: int = 0):
        """Funding rate from the last record stamped at least two hours before `sec`; `back` records earlier for the change."""
        k = bisect.bisect_right(self.fts, sec - 7200) - 1 - back
        return self.fv[k] if 0 <= k < len(self.fv) else None


def logret(a, b):
    return math.log(a / b) if a and b and a > 0 and b > 0 and not (math.isnan(a) or math.isnan(b)) else None


def perp_features(P: Perp, Q: Perp, t: int, open_t: int, sign: int) -> dict | None:
    """Features from bars that closed at or before `t` (the last one starts at t - 60). sign is +1 for a YES entry, -1 for NO."""
    j = P.idx(t - BAR_S)
    if j < 1500 or j >= P.n or P.idx(open_t - BAR_S) < 0:
        return None
    c = P.c
    S = c[j]
    K = c[P.idx(open_t - BAR_S)]
    if any(np.isnan(x) for x in (S, K)) or np.isnan(c[j - 60:j + 1]).any():
        return None
    r1 = np.diff(np.log(c[j - 60:j + 1]))
    rv60 = float(np.std(r1, ddof=1))
    rv15 = float(np.std(r1[-15:], ddof=1))
    if rv60 <= 0 or rv15 < 0:
        return None
    out = {"ret1": sign * math.log(S / c[j - 1]), "ret5": sign * math.log(S / c[j - 5]), "ret15": sign * math.log(S / c[j - 15]),
           "ret60": sign * math.log(S / c[j - 60]), "rv15": rv15, "rv60": rv60, "rv_ratio": rv15 / rv60}
    v5 = np.nansum(P.v[j - 4:j + 1])
    hist = [np.nansum(P.v[k - 4:k + 1]) for k in range(j - 1440, j, 5)]
    out["vol5_pct"] = float(np.mean([h <= v5 for h in hist]))
    out["range15"] = float((np.nanmax(P.h[j - 14:j + 1]) - np.nanmin(P.l[j - 14:j + 1])) / S)
    out["dist_sigma"] = sign * math.log(S / K) / (rv60 * math.sqrt(TAU))
    hi, lo = float(np.nanmax(P.h[j - 59:j + 1])), float(np.nanmin(P.l[j - 59:j + 1]))
    up, dn = (hi - S) / S, (S - lo) / S
    out["gap_fav"], out["gap_adv"] = (up, dn) if sign > 0 else (dn, up)
    d0, d60 = P.d[j], P.d[j - 60]
    if np.isnan(d0) or np.isnan(d60):
        return None
    out["dvol"], out["dvol_chg"] = float(d0), float(d0 - d60)
    out["vrp"] = float(d0 / 100.0 - rv60 * math.sqrt(525_600.0))
    f0, f1 = P.fund(t), P.fund(t, 1)
    if f0 is None or f1 is None:
        return None
    out["fund"], out["fund_chg"] = f0, f0 - f1
    jq = Q.idx(t - BAR_S)
    if jq < 20 or jq >= Q.n or np.isnan(Q.c[jq]) or np.isnan(Q.c[jq - 15]) or np.isnan(Q.c[jq - 5]):
        return None
    out["oth_ret15"] = sign * math.log(Q.c[jq] / Q.c[jq - 15])
    out["oth_ret5"] = sign * math.log(Q.c[jq] / Q.c[jq - 5])
    return out


def kalshi_features(m: dict, c: dict, earlier: list[dict], side: str, price: float) -> dict | None:
    by = {x["end"]: x for x in m["c"]}
    t = c["end"]
    mid = lambda x: (x["bid"] + x["ask"]) / 2 if side == "yes" else 1 - (x["bid"] + x["ask"]) / 2
    last5 = [by.get(t - 60 * k) for k in range(5)]
    p1, p3, p5 = by.get(t - 60), by.get(t - 180), by.get(t - 300)
    if p1 is None or p3 is None or p5 is None or any(x is None for x in last5) or not earlier:
        return None
    mids = [mid(x) for x in last5]
    tib, k = 0, t - 60
    while k in by and (by[k]["ask"] if side == "yes" else 1 - by[k]["bid"]) >= 0.88 and tib < 8:
        tib += 1
        k -= 60
    seq = [by.get(t - 60 * k) for k in range(7)]
    d = [mid(a) - mid(b) for a, b in zip(seq, seq[1:]) if a is not None and b is not None]
    signs = [1 if x > 0.0049 else (-1 if x < -0.0049 else 0) for x in d]
    nz = [s for s in signs if s != 0]
    flips = sum(1 for a, b in zip(nz, nz[1:]) if a != b)
    return {"price": price, "spread": c["ask"] - c["bid"], "rise1": mid(c) - mid(p1), "rise3": mid(c) - mid(p3), "rise5": mid(c) - mid(p5),
            "range5": max(mids) - min(mids), "tib": float(tib), "dip": min(mid(x) for x in earlier), "vol_last": float(c["vol"]),
            "vol_ratio": float(c["vol"]) / max(1.0, float(p1["vol"])), "flips": float(flips)}


def build() -> None:
    con = sqlite3.connect(DB)
    perp = {cur: Perp(con, cur) for cur in ("BTC", "ETH")}
    rows = []
    for series, cur in SERIES.items():
        for tk, m in I.load_btc(series).items():
            c, earlier = I.at(m, LEFT_S)
            if c is None:
                continue
            pick = L.favorite(c["bid"], c["ask"], BAND)
            if pick is None:
                continue
            side, price = pick
            t = m["close"] - LEFT_S
            sign = 1 if side == "yes" else -1
            kf = kalshi_features(m, c, earlier, side, price)
            pf = perp_features(perp[cur], perp[OTHER[cur]], t, m["close"] - 900, sign)
            if kf is None or pf is None:
                continue
            dt = datetime.fromtimestamp(m["close"], timezone.utc)
            yes = m["res"] == "yes"
            rows.append({"series": cur, "day": dt.strftime("%Y-%m-%d"), "close_ts": m["close"], "net": L.net(side, price, yes),
                         "stress": L.net(side, price, yes, L.STRESS), **kf, **pf, "hourb": dt.hour // 6, "slot": (dt.minute // 15) % 4,
                         "weekend": int(dt.weekday() >= 5), "usopen": int(13 * 60 + 30 <= dt.hour * 60 + dt.minute < 15 * 60)})
    rows.sort(key=lambda r: r["close_ts"])
    json.dump(rows, open(ROWS, "w"))
    print(len(rows), "entries,", len({r["day"] for r in rows}), "days")


def split_days(rows):
    days = sorted({r["day"] for r in rows})
    a, b = days[int(len(days) * SPLIT[0])], days[int(len(days) * SPLIT[1])]
    return a, b


def make_conditions(rows, disc):
    """Condition list: (name, feature, kind, arg). Quartile and median cuts per series from the discovery entries only."""
    conds = []
    cuts = {}
    for s in ("BTC", "ETH"):
        for f in NUMERIC:
            v = sorted(r[f] for r in disc if r["series"] == s)
            cuts[(s, f)] = (v[len(v) // 4], v[len(v) // 2], v[(3 * len(v)) // 4])
    for f in NUMERIC:
        for kind in ("q1", "q4", "lo", "hi"):
            conds.append((f"{f}:{kind}", f, kind, None))
    for f, vals in CATEGORICAL.items():
        for x in vals:
            conds.append((f"{f}={x}", f, "eq", x))
    return conds, cuts


def cond_mask(rows, cond, cuts):
    name, f, kind, arg = cond
    out = np.zeros(len(rows), dtype=bool)
    for i, r in enumerate(rows):
        if kind == "eq":
            out[i] = r[f] == arg
            continue
        q1, med, q3 = cuts[(r["series"], f)]
        v = r[f]
        out[i] = (v <= q1) if kind == "q1" else (v >= q3) if kind == "q4" else (v < med) if kind == "lo" else (v >= med)
    return out


def make_rules(conds, n=N_RULES, seed=SEED):
    """All single conditions, then pairs on two different features, drawn without replacement with a fixed seed."""
    singles = [(i,) for i in range(len(conds))]
    pairs = [(i, j) for i in range(len(conds)) for j in range(i + 1, len(conds)) if conds[i][1] != conds[j][1]]
    rng = random.Random(seed)
    take = rng.sample(pairs, n - len(singles))
    return singles + sorted(take)


def welch(x1, n1, s1, x2, n2, s2):
    """Group mean minus rest mean, and Welch z, from sums (x, count) and sums of squares."""
    m1, m2 = x1 / n1, x2 / n2
    v1 = np.maximum(1e-12, s1 / n1 - m1 * m1) * n1 / np.maximum(1, n1 - 1)
    v2 = np.maximum(1e-12, s2 / n2 - m2 * m2) * n2 / np.maximum(1, n2 - 1)
    return m1 - m2, (m1 - m2) / np.sqrt(v1 / n1 + v2 / n2)


def screen(M, x, min_n):
    """M: rules x entries (float32 0/1). Returns diff and z arrays for each rule (nan where the group is too small or too big)."""
    N = M.shape[1]
    n1 = M.sum(1)
    ok = (n1 >= min_n) & (n1 <= N - min_n)
    s1 = M @ x
    q1 = M @ (x * x)
    n1s = np.where(ok, n1, 1.0)
    n2 = np.where(ok, N - n1, 1.0)
    d, z = welch(s1, n1s, q1, x.sum() - s1, n2, (x * x).sum() - q1)
    return np.where(ok, d, np.nan), np.where(ok, z, np.nan)


def null_max(M, x, groups, n_perm, min_n, seed):
    """Largest z over all rules for each shuffle of x within (series, day) groups."""
    rng = np.random.default_rng(seed)
    mx = np.empty(n_perm)
    for k in range(n_perm):
        y = x.copy()
        for g in groups:
            y[g] = y[rng.permutation(g)]
        _, z = screen(M, y, min_n)
        mx[k] = np.nanmax(z)
    return mx


def run() -> None:
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    rows = json.load(open(ROWS))
    a, b = split_days(rows)
    disc = [r for r in rows if r["day"] < a]
    conf = [r for r in rows if a <= r["day"] < b]
    hold = [r for r in rows if r["day"] >= b]
    conds, cuts = make_conditions(rows, disc)
    rules = make_rules(conds)
    out = [f"SEARCH5K: {len(rows)} entries, discovery {len(disc)} (before {a}), confirmation {len(conf)} (before {b}), holdout {len(hold)}; {len(conds)} conditions, {len(rules)} rules"]
    mk = {i: cond_mask(rows, c, cuts) for i, c in enumerate(conds)}

    def matrix(sub_idx):
        M = np.zeros((len(rules), len(sub_idx)), dtype=np.float32)
        for k, r in enumerate(rules):
            m = mk[r[0]].copy()
            for i in r[1:]:
                m &= mk[i]
            M[k] = m[sub_idx]
        return M
    idx_d = np.array([i for i, r in enumerate(rows) if r["day"] < a])
    idx_c = np.array([i for i, r in enumerate(rows) if a <= r["day"] < b])
    idx_h = np.array([i for i, r in enumerate(rows) if r["day"] >= b])
    x_all = np.array([r["net"] for r in rows])
    st_all = np.array([r["stress"] for r in rows])
    Md, Mc, Mh = matrix(idx_d), matrix(idx_c), matrix(idx_h)
    d_d, z_d = screen(Md, x_all[idx_d], MIN_DISC)
    groups = {}
    for i, r in enumerate(rows[j] for j in idx_d):
        groups.setdefault((r["series"], r["day"]), []).append(i)
    mx = null_max(Md, x_all[idx_d], [np.array(g) for g in groups.values()], N_PERM, MIN_DISC, SEED)
    crit = float(np.percentile(mx, 95))
    out.append(f"null: best-of-{len(rules)} z over {N_PERM} shuffles: median {np.median(mx):.2f}, 95th pct {crit:.2f}, max {mx.max():.2f}")
    valid = np.where(~np.isnan(z_d))[0]
    out.append(f"rules with enough discovery entries: {len(valid)}; observed best z {np.nanmax(z_d):.2f}; rules above the null 95th pct: {int((z_d > crit).sum())}; above +{100*DISC_C:.0f}c and the null 95th pct: {int(((z_d > crit) & (d_d >= DISC_C)).sum())}")
    d_c, z_c = screen(Mc, x_all[idx_c], MIN_CONF)
    s_d, _ = screen(Md, st_all[idx_d], MIN_DISC)
    s_c, _ = screen(Mc, st_all[idx_c], MIN_CONF)
    surv = [k for k in valid if z_d[k] > crit and d_d[k] >= DISC_C]
    passed = [k for k in surv if not np.isnan(z_c[k]) and d_c[k] >= CONF_C and z_c[k] >= CONF_Z and s_d[k] > 0 and s_c[k] > 0]
    out.append(f"survivors of step 1: {len(surv)}; of steps 1 to 3: {len(passed)}")
    d_h, z_h = screen(Mh, x_all[idx_h], MIN_CONF)
    name = lambda k: " AND ".join(conds[i][0] for i in rules[k])
    for k in passed:
        ok = not np.isnan(z_h[k]) and d_h[k] > 0 and z_h[k] >= HOLD_Z
        out.append(f"SURVIVOR {'NOT_YET_FALSIFIED' if ok else 'NOT_ENOUGH_DATA'}: {name(k)} | disc {100*d_d[k]:+.2f}c z {z_d[k]:.2f} | conf {100*d_c[k]:+.2f}c z {z_c[k]:.2f} | holdout {100*d_h[k]:+.2f}c z {z_h[k]:.2f}")
    out.append("information only, top 10 by discovery z (confirmation shown, holdout not used for these):")
    for k in sorted(valid, key=lambda k: -z_d[k])[:10]:
        out.append(f"  {name(k):60s} disc {100*d_d[k]:+6.2f}c z {z_d[k]:5.2f} | conf {100*d_c[k]:+6.2f}c z {z_c[k]:5.2f}")
    verdict = "NOT_YET_FALSIFIED" if any("SURVIVOR NOT_YET" in line for line in out) else ("NOT_ENOUGH_DATA" if passed else "FALSIFIED")
    out.append(f"VERDICT for the family: {verdict}")
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "build":
        build()
    elif cmd == "run":
        run()
    else:
        print(__doc__)
