"""FACT1 (README, Pre-registration: FACT1): 4,230 complete strategies (entry time, side rule, exit, time-of-day gate) for Bitcoin and Ethereum,
judged by a Reality Check over days. Research only: nothing here places an order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
Nothing here means trade.

    python -m scalper.fact1 run      (the one read; a second is refused unless the result file is deleted on purpose, a crash fix only)
"""
from __future__ import annotations

import math
import sqlite3
import sys
from datetime import datetime, timezone

import numpy as np

from . import ideas20 as I
from . import lstrats as L
from . import search5k as S5
from .paths import DATA_DIR

RESULT = DATA_DIR / "fact1_result.txt"
ASSETS = {"KXBTC15M": "BTC", "KXETH15M": "ETH"}
ENTRY_LEFT = (780, 660, 540, 420, 300, 240, 180)
SIDES = ("FAV50", "FAV70", "FAV88", "UND5", "UND20", "UP_lo", "UP_hi", "FADE_lo", "FADE_hi")
EXITS = ("hold", "tp10", "tp20", "sl10", "sl20", "time4", "time2")
GATES = ("all", "00-06", "06-12", "12-18", "18-24")
DISC_FRAC, CONF_FRAC = 0.60, 0.80
B = 1000
MIN_DISC = 150
SPOT_MIN = 0.0003
STRESS = 1.2


def fee(p: float, mult: float = 1.0) -> float:
    return mult * 0.07 * p * (1 - p)


def valid(left: int, exit_: str) -> bool:
    if exit_ == "time4":
        return left >= 300
    if exit_ == "time2":
        return left >= 180
    return True


def side_price(rule: str, c: dict, spot_sign: int):
    """(side, ask) for the rule at decision candle c, or None. spot_sign is +1 / -1 / 0 (the perpetual's last 5 minutes)."""
    bid, ask = c["bid"], c["ask"]
    if bid is None or ask is None or not (0 < bid < ask < 1):
        return None
    ya, na = ask, round(1 - bid, 4)
    fav = "yes" if (bid + ask) / 2 >= 0.5 else "no"
    und = "no" if fav == "yes" else "yes"
    px = {"yes": ya, "no": na}
    if rule in ("FAV50", "FAV70", "FAV88"):
        lo, hi = {"FAV50": (0.50, 0.70), "FAV70": (0.70, 0.88), "FAV88": (0.88, 0.97)}[rule]
        return (fav, px[fav]) if lo <= px[fav] < hi else None
    if rule in ("UND5", "UND20"):
        lo, hi = {"UND5": (0.03, 0.12), "UND20": (0.12, 0.30)}[rule]
        return (und, px[und]) if lo <= px[und] < hi else None
    if spot_sign == 0:
        return None
    up = "yes" if spot_sign > 0 else "no"
    side = up if rule.startswith("UP") else ("no" if up == "yes" else "yes")
    lo, hi = (0.30, 0.60) if rule.endswith("lo") else (0.60, 0.88)
    return (side, px[side]) if lo <= px[side] < hi else None


def side_bid(side: str, x: dict):
    if x["bid"] is None or x["ask"] is None:
        return None
    return x["bid"] if side == "yes" else round(1 - x["ask"], 4)


def simulate(exit_: str, side: str, p0: float, t0: int, close: int, later: list[dict], yes_won: bool, mult: float = 1.0):
    """Net per contract. Exits read only candles ending strictly after t0 and use closing bids; anything not triggered holds to settlement."""
    hold = (1.0 if (yes_won == (side == "yes")) else 0.0) - p0 - fee(p0, mult)
    if exit_ == "hold":
        return hold
    if exit_ in ("time4", "time2"):
        te = close - (240 if exit_ == "time4" else 120)
        if t0 >= te:
            return None
        x = next((c for c in later if c["end"] == te), None)
        b = side_bid(side, x) if x else None
        return hold if b is None else b - p0 - fee(p0, mult) - fee(b, mult)
    d = 0.10 if exit_.endswith("10") else 0.20
    for x in later:
        b = side_bid(side, x)
        if b is None:
            continue
        if (exit_.startswith("tp") and b >= p0 + d) or (exit_.startswith("sl") and b <= p0 - d):
            return b - p0 - fee(p0, mult) - fee(b, mult)
    return hold


def daily(vec: np.ndarray, day_idx: np.ndarray, mask: np.ndarray, ndays: int):
    """Daily sum and count of entries of one strategy (NaN = no entry) under a gate mask."""
    ok = mask & ~np.isnan(vec)
    s = np.zeros(ndays)
    n = np.zeros(ndays)
    np.add.at(s, day_idx[ok], vec[ok])
    np.add.at(n, day_idx[ok], 1)
    return s, n


def tstat(P: np.ndarray):
    n = P.shape[1]
    m = P.mean(1)
    sd = P.std(1, ddof=1)
    return m, sd, np.where(sd > 0, m / (sd / math.sqrt(n)), np.nan)


def run_asset(series: str, perp, out: list[str]) -> list[str]:
    markets = sorted(I.load_btc(series).values(), key=lambda m: m["close"])
    days = sorted({datetime.fromtimestamp(m["close"], timezone.utc).strftime("%Y-%m-%d") for m in markets})
    dix = {d: i for i, d in enumerate(days)}
    nd = len(days)
    day_idx = np.array([dix[datetime.fromtimestamp(m["close"], timezone.utc).strftime("%Y-%m-%d")] for m in markets])
    hour = np.array([datetime.fromtimestamp(m["close"], timezone.utc).hour for m in markets])
    gates = {"all": np.ones(len(markets), bool), "00-06": hour < 6, "06-12": (hour >= 6) & (hour < 12), "12-18": (hour >= 12) & (hour < 18), "18-24": hour >= 18}
    d_end, c_end = int(nd * DISC_FRAC), int(nd * CONF_FRAC)
    names, nets, stress = [], [], []
    for left in ENTRY_LEFT:
        picks = {r: [None] * len(markets) for r in SIDES}
        for i, m in enumerate(markets):
            c = next((x for x in m["c"] if x["end"] == m["close"] - left), None)
            if c is None:
                continue
            j = perp.idx(m["close"] - left - 60)
            sgn = 0
            if 5 <= j < perp.n and not np.isnan(perp.c[j]) and not np.isnan(perp.c[j - 5]):
                r5 = math.log(perp.c[j] / perp.c[j - 5])
                sgn = 0 if abs(r5) < SPOT_MIN else (1 if r5 > 0 else -1)
            for rule in SIDES:
                picks[rule][i] = side_price(rule, c, sgn)
        for rule in SIDES:
            for ex in EXITS:
                if not valid(left, ex):
                    continue
                v = np.full(len(markets), np.nan)
                vs = np.full(len(markets), np.nan)
                for i, m in enumerate(markets):
                    pk = picks[rule][i]
                    if pk is None:
                        continue
                    t0 = m["close"] - left
                    later = [x for x in m["c"] if x["end"] > t0]
                    yw = m["res"] == "yes"
                    a = simulate(ex, pk[0], pk[1], t0, m["close"], later, yw)
                    if a is None:
                        continue
                    v[i] = a
                    vs[i] = simulate(ex, pk[0], pk[1], t0, m["close"], later, yw, STRESS)
                for g in GATES:
                    names.append((left // 60, rule, ex, g))
                    nets.append((v, gates[g]))
                    stress.append((vs, gates[g]))
    K = len(names)
    P = np.zeros((K, nd)); N = np.zeros((K, nd)); PS = np.zeros((K, nd))
    for k in range(K):
        P[k], N[k] = daily(nets[k][0], day_idx, nets[k][1], nd)
        PS[k], _ = daily(stress[k][0], day_idx, stress[k][1], nd)
    out.append(f"{ASSETS[series]}: {len(markets)} markets, {nd} days, {K} strategies; discovery days {d_end}, confirmation {c_end - d_end}, holdout {nd - c_end}")
    Pd, Nd = P[:, :d_end], N[:, :d_end]
    m_d, sd_d, t_d = tstat(Pd)
    valid_k = np.where((Nd.sum(1) >= MIN_DISC) & ~np.isnan(t_d))[0]
    rng = np.random.default_rng(25102502)
    mx = np.empty(B)
    root = math.sqrt(d_end)
    for b in range(B):
        idx = rng.integers(0, d_end, d_end)
        mb = Pd[:, idx].mean(1)
        tb = root * (mb - m_d) / np.where(sd_d > 0, sd_d, np.nan)
        mx[b] = np.nanmax(tb[valid_k])
    crit = float(np.percentile(mx, 95))
    best = valid_k[np.argsort(-t_d[valid_k])[:10]]
    out.append(f"  strategies with at least {MIN_DISC} discovery entries: {len(valid_k)}; best discovery t {t_d[valid_k].max():.2f}; Reality Check 95th percentile of the best-of-{len(valid_k)} t: {crit:.2f} (median {np.median(mx):.2f}); above it: {int((t_d[valid_k] > crit).sum())}")
    def seg(k, a, b2):
        p, n = P[k, a:b2], N[k, a:b2]
        _, _, t = tstat(P[k:k + 1, a:b2])
        return (p.sum() / max(1, n.sum())), float(t[0]), int(n.sum())
    surv = []
    for k in valid_k:
        if t_d[k] <= crit:
            continue
        mc, tc, nc = seg(k, d_end, c_end)
        mh, th, nh = seg(k, c_end, nd)
        sd_ = PS[k, :d_end].sum() / max(1, Nd[k].sum()); sc_ = PS[k, d_end:c_end].sum() / max(1, N[k, d_end:c_end].sum())
        if mc > 0 and tc >= 1.64 and sd_ > 0 and sc_ > 0:
            surv.append((k, mc, tc, nc, mh, th, nh))
    out.append(f"  survivors of discovery plus confirmation: {len(surv)}")
    for k, mc, tc, nc, mh, th, nh in surv:
        ok = mh > 0 and th >= 1.0
        left, rule, ex, g = names[k]
        out.append(f"  SURVIVOR {'NOT_YET_FALSIFIED' if ok else 'NOT_ENOUGH_DATA'}: left {left}m {rule} exit {ex} gate {g} | disc t {t_d[k]:.2f} | conf {100*mc:+.2f}c t {tc:.2f} n {nc} | holdout {100*mh:+.2f}c t {th:.2f} n {nh}")
    out.append("  information only, top 10 by discovery t (confirmation shown):")
    for k in best:
        mc, tc, nc = seg(k, d_end, c_end)
        left, rule, ex, g = names[k]
        out.append(f"    left {left:2d}m {rule:8s} {ex:5s} {g:6s} disc t {t_d[k]:5.2f} ({100*Pd[k].sum()/max(1,Nd[k].sum()):+6.2f}c, n {int(Nd[k].sum())}) | conf {100*mc:+6.2f}c t {tc:5.2f} n {nc}")
    return out


def main(argv):
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__)
        return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
        return
    con = sqlite3.connect(S5.DB)
    out = []
    for series, cur in ASSETS.items():
        perp = S5.Perp(con, cur)
        run_asset(series, perp, out)
        print("\n".join(out[-14:]), flush=True)
    verdict = "NOT_YET_FALSIFIED" if any("SURVIVOR NOT_YET" in l for l in out) else ("NOT_ENOUGH_DATA" if any("SURVIVOR" in l for l in out) else "FALSIFIED")
    out.append(f"VERDICT for the family: {verdict}")
    RESULT.write_text("\n".join(out) + "\n")
    print(out[-1])


if __name__ == "__main__":
    main(sys.argv)
