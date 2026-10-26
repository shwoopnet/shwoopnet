"""CRYPTO1 (README, Pre-registration: CRYPTO1): slow Bitcoin and Ethereum strategies on spot and perpetual costs, 2019 to 2026. Research only: nothing here places an
order. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

    python -m scalper.crypto1 fetch    (Deribit hourly bars and funding, resumable, into data/crypto1.sqlite)
    python -m scalper.crypto1 run      (the one read; refused a second time)
"""
from __future__ import annotations

import math
import sqlite3
import sys
import time
from datetime import datetime, timezone

import numpy as np

from .iv1 import _get
from .paths import DATA_DIR

DB = DATA_DIR / "crypto1.sqlite"
RESULT = DATA_DIR / "crypto1_result.txt"
INST = {"BTC": ("BTC-PERPETUAL", "2019-01-01"), "ETH": ("ETH-PERPETUAL", "2019-03-15")}
LS = (6, 12, 24, 48, 96, 168)
HS = (4, 12, 24, 48)
RULES = ("MOM", "REV", "BRK", "VMOM")
COST = {"perp": 0.0014, "spot": 0.0060}
DISC_END, CONF_END = "2024-01-01", "2025-01-01"
B, BLOCK, MIN_DISC = 1000, 7, 150
HOUR = 3600


def fetch() -> None:
    con = sqlite3.connect(DB)
    con.execute("create table if not exists bar(cur text, ts integer, o real, h real, l real, c real, primary key(cur, ts))")
    con.execute("create table if not exists fund(cur text, ts integer, f1 real, primary key(cur, ts))")
    end = int(time.time()) * 1000
    for cur, (inst, start) in INST.items():
        s0 = int(datetime.fromisoformat(start).replace(tzinfo=timezone.utc).timestamp()) * 1000
        have = con.execute("select max(ts) from bar where cur=?", (cur,)).fetchone()[0]
        t = (have + 3_600_000) if have else s0
        while t < end:
            t2 = min(end, t + 4000 * 3_600_000)
            d = _get(f"https://www.deribit.com/api/v2/public/get_tradingview_chart_data?instrument_name={inst}&start_timestamp={t}&end_timestamp={t2}&resolution=60")["result"]
            con.executemany("insert or ignore into bar values (?,?,?,?,?,?)", [(cur, int(a), o, h, l, c) for a, o, h, l, c in zip(d["ticks"], d["open"], d["high"], d["low"], d["close"])])
            con.commit()
            t = t2 + 3_600_000
        have = con.execute("select max(ts) from fund where cur=?", (cur,)).fetchone()[0]
        t = (have + 3_600_000) if have else s0
        while t < end:
            t2 = min(end, t + 30 * 86_400_000)
            d = _get(f"https://www.deribit.com/api/v2/public/get_funding_rate_history?instrument_name={inst}&start_timestamp={t}&end_timestamp={t2}")["result"]
            con.executemany("insert or ignore into fund values (?,?,?)", [(cur, int(x["timestamp"]), x["interest_1h"]) for x in d])
            con.commit()
            t = t2 + 1000
        for tb in ("bar", "fund"):
            print(cur, tb, con.execute(f"select count(*) from {tb} where cur=?", (cur,)).fetchone()[0], flush=True)


def load(cur: str):
    con = sqlite3.connect(DB)
    rows = con.execute("select ts, o, h, l, c from bar where cur=? order by ts", (cur,)).fetchall()
    ts = np.array([r[0] // 1000 for r in rows])
    f = {r[0] // 1000: r[1] for r in con.execute("select ts, f1 from fund where cur=?", (cur,))}
    return ts, np.array([r[1] for r in rows]), np.array([r[2] for r in rows]), np.array([r[3] for r in rows]), np.array([r[4] for r in rows]), f


def signals(rule: str, L: int, o, h, l, c, rv24, rvmed):
    """Position (+1, -1, 0) decided at the close of hour i, for every i; uses bars up to and including i only."""
    n = len(c)
    sig = np.zeros(n, dtype=int)
    for i in range(L, n):
        if rule in ("MOM", "REV", "VMOM"):
            r = c[i] / c[i - L] - 1.0
            s = 1 if r > 0 else (-1 if r < 0 else 0)
            if rule == "REV":
                s = -s
            if rule == "VMOM" and not (rv24[i] == rv24[i] and rvmed[i] == rvmed[i] and rv24[i] < rvmed[i]):
                s = 0
        else:
            hi, lo = h[i - L:i].max(), l[i - L:i].min()
            s = 1 if c[i] > hi else (-1 if c[i] < lo else 0)
        sig[i] = s
    return sig


def run_strategy(sig, ts, o, f, H: int, mode: str, mu: float, cost: float):
    """Non-overlapping trades: enter at the open of hour i+1, exit at the open of hour i+1+H. Returns [(exit_ts, net_excess)]."""
    n = len(o)
    out = []
    i = 0
    while i < n - H - 2:
        s = sig[i]
        if mode == "spot" and s < 0:
            s = 0
        if s == 0:
            i += 1
            continue
        e, x = i + 1, i + 1 + H
        ret = o[x] / o[e] - 1.0
        fund = sum(f.get(int(ts[j]), 0.0) for j in range(e, x)) if mode == "perp" else 0.0
        net = s * (ret - mu) - cost - s * fund
        out.append((int(ts[x]), net))
        i = x
    return out


def day_of(t: int) -> str:
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d")


def tstat(v: np.ndarray) -> float:
    return float(v.mean() / (v.std(ddof=1) / math.sqrt(len(v)))) if len(v) > 2 and v.std(ddof=1) > 0 else 0.0


def run() -> None:
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists.")
        return
    out = []
    for cur in INST:
        ts, o, h, l, c, f = load(cur)
        days = [day_of(int(t)) for t in ts]
        disc_mask = np.array([d < DISC_END for d in days])
        # realised 24h volatility of hourly returns and its trailing 90 day median (known at the decision)
        r1 = np.r_[np.nan, np.diff(np.log(c))]
        rv24 = np.full(len(c), np.nan)
        for i in range(24, len(c)):
            rv24[i] = np.nanstd(r1[i - 23:i + 1], ddof=1)
        rvmed = np.full(len(c), np.nan)
        W = 90 * 24
        for i in range(W, len(c), 1):
            rvmed[i] = np.nanmedian(rv24[i - W:i:6]) if i % 6 == 0 or True else rvmed[i - 1]
        alld = sorted(set(days))
        dix = {d: k for k, d in enumerate(alld)}
        nd = len(alld)
        for mode in ("perp", "spot"):
            names, P, N, S = [], [], [], []
            for rule in RULES:
                for L in LS:
                    sig = signals(rule, L, o, h, l, c, rv24, rvmed)
                    for H in HS:
                        d_idx = np.where(disc_mask)[0]
                        mu = float(np.mean(o[d_idx[d_idx + H < len(o)] + H] / o[d_idx[d_idx + H < len(o)]] - 1.0))
                        tr = run_strategy(sig, ts, o, f, H, mode, mu, COST[mode])
                        tr15 = run_strategy(sig, ts, o, f, H, mode, mu, COST[mode] * 1.5)
                        p = np.zeros(nd); n = np.zeros(nd); s15 = np.zeros(nd)
                        for (t, a), (_, a15) in zip(tr, tr15):
                            k = dix.get(day_of(t))
                            if k is None:
                                continue
                            p[k] += a; n[k] += 1; s15[k] += a15
                        names.append((rule, L, H)); P.append(p); N.append(n); S.append(s15)
            P, N, S = np.array(P), np.array(N), np.array(S)
            di = np.array([k for k, d in enumerate(alld) if d < DISC_END])
            ci = np.array([k for k, d in enumerate(alld) if DISC_END <= d < CONF_END])
            hi_ = np.array([k for k, d in enumerate(alld) if d >= CONF_END])
            Pd = P[:, di]
            t_d = np.array([tstat(Pd[k]) for k in range(len(P))])
            ok = N[:, di].sum(1) >= MIN_DISC
            rng = np.random.default_rng(26102601)
            nb = len(di)
            mx = np.empty(B)
            m_d = Pd.mean(1); sd = Pd.std(1, ddof=1)
            for b in range(B):
                starts = rng.integers(0, nb, size=nb // BLOCK + 1)
                idx = np.concatenate([(np.arange(BLOCK) + s) % nb for s in starts])[:nb]
                tb = math.sqrt(nb) * (Pd[:, idx].mean(1) - m_d) / np.where(sd > 0, sd, np.nan)
                mx[b] = np.nanmax(tb[ok])
            crit = float(np.percentile(mx, 95))
            out.append(f"{cur} {mode}: {len(P)} strategies, {int(ok.sum())} with {MIN_DISC}+ discovery trades; best discovery t {np.nanmax(t_d[ok]):.2f}; Reality Check 95th pct {crit:.2f} (median {np.median(mx):.2f}); above it: {int((ok & (t_d > crit)).sum())}")
            surv = []
            for k in np.where(ok & (t_d > crit))[0]:
                nc, nh = N[k, ci].sum(), N[k, hi_].sum()
                mc = P[k, ci].sum() / max(1, nc); mh = P[k, hi_].sum() / max(1, nh)
                tc, th = tstat(P[k, ci]), tstat(P[k, hi_])
                if mc > 0 and tc >= 1.64 and S[k, di].sum() > 0 and S[k, ci].sum() > 0:
                    surv.append((k, mc, tc, nc, mh, th, nh))
            out.append(f"  survivors of discovery plus confirmation: {len(surv)}")
            for k, mc, tc, nc, mh, th, nh in surv:
                good = mh > 0 and th >= 1.0
                out.append(f"  SURVIVOR {'NOT_YET_FALSIFIED' if good else 'NOT_ENOUGH_DATA'}: {cur} {mode} {names[k]} | disc t {t_d[k]:.2f} | conf {100*mc:+.3f}% per trade t {tc:.2f} n {int(nc)} | holdout {100*mh:+.3f}% t {th:.2f} n {int(nh)}")
            out.append("  information, top 5 by discovery t (confirmation and holdout shown):")
            for k in np.argsort(-np.where(ok, t_d, -9))[:5]:
                nc, nh = N[k, ci].sum(), N[k, hi_].sum()
                out.append(f"    {names[k]} disc t {t_d[k]:5.2f} ({100*P[k, di].sum()/max(1, N[k, di].sum()):+.3f}% per trade, n {int(N[k, di].sum())}) | conf {100*P[k, ci].sum()/max(1, nc):+.3f}% t {tstat(P[k, ci]):5.2f} | hold {100*P[k, hi_].sum()/max(1, nh):+.3f}% t {tstat(P[k, hi_]):5.2f}")
            print("\n".join(out[-9:]), flush=True)
    verdict = "NOT_YET_FALSIFIED" if any("SURVIVOR NOT_YET" in x for x in out) else ("NOT_ENOUGH_DATA" if any("SURVIVOR" in x for x in out) else "FALSIFIED")
    out.append(f"VERDICT for the family: {verdict}")
    RESULT.write_text("\n".join(out) + "\n")
    print(out[-1])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "fetch":
        fetch()
    elif cmd == "run":
        run()
    else:
        print(__doc__)
