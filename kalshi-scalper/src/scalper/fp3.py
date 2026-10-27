"""FP3 (README, Pre-registration: FP3): footprint micro-scalps on deep tennis markets, scored as price moves, never to settlement. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

    python -m scalper.fp3 fetch   (resumable; the trade tape of the most liquid tennis matches already in sc1.sqlite)
    python -m scalper.fp3 run     (the one read; refused a second time)
SPREAD_CAPTURE (posting at the bid) is NOT run: its fill needs queue position, which no candle or tape gives; the README says it cannot pass.
"""
from __future__ import annotations

import sqlite3
import statistics as st
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

from . import api
from .paths import DATA_DIR

SC1, DB, RESULT = DATA_DIR / "sc1.sqlite", DATA_DIR / "fp3.sqlite", DATA_DIR / "fp3_result.txt"
N_MATCHES = 250
MAX_SPREAD, MID_LO, MID_HI, MIN_VOL = 0.03, 0.15, 0.85, 100.0
TARGETS, HOLD_MIN = (0.03, 0.05, 0.10, 0.20), 5
STACK_RATIO, STACK_MIN, STACK_LEVELS = 3.0, 20.0, 3
DELTA_Q, ABSORB_X, ABSORB_MOVE, BIG_X = 0.95, 3.0, 0.01, 10.0
REPS, SEED = 300, 27102704
MIN_TRADES, MIN_DAYS, BAR_C, CTRL_C, FALSIFY_C = 200, 12, 0.010, 0.010, 0.003


def fee(p: float, mult: float = 1.0) -> float:
    return mult * 0.07 * p * (1 - p)


def fetch(shard: int = 0, shards: int = 1) -> None:
    src = sqlite3.connect(SC1)
    db = sqlite3.connect(DB, timeout=120)
    db.execute("CREATE TABLE IF NOT EXISTS trade(ticker TEXT, ts REAL, price INTEGER, size REAL, side INTEGER)")
    db.execute("CREATE TABLE IF NOT EXISTS done(ticker TEXT PRIMARY KEY, n INTEGER)")
    rows = src.execute("SELECT m.ticker, m.series, m.close_ts, SUM(c.volume), MIN(c.end_ts) FROM market m JOIN candle c ON c.ticker=m.ticker "
                       "WHERE m.series IN ('KXATPMATCH','KXWTAMATCH','KXATPCHALLENGERMATCH','KXWTACHALLENGERMATCH') GROUP BY m.ticker ORDER BY 4 DESC").fetchall()
    seen, pick = set(), []
    for tk, s, close_ts, vol, first in rows:
        ev = tk.rsplit("-", 1)[0]
        if ev in seen:
            continue
        seen.add(ev); pick.append((tk, close_ts, first))
        if len(pick) >= N_MATCHES:
            break
    pick = pick[shard::shards]
    done = {r[0] for r in db.execute("SELECT ticker FROM done")}
    print(len(pick), "matches;", len(done), "done", flush=True)
    for k, (tk, close_ts, first) in enumerate(pick):
        if tk in done:
            continue
        cur, n = None, 0
        while True:
            p = {"ticker": tk, "limit": 1000, "min_ts": first - 120, "max_ts": close_ts + 60}
            if cur:
                p["cursor"] = cur
            try:
                d = api._get("/markets/trades", p)
            except Exception:
                time.sleep(5); continue
            tr = d.get("trades", [])
            db.executemany("INSERT INTO trade VALUES(?,?,?,?,?)", [(tk, datetime.fromisoformat(t["created_time"].replace("Z", "+00:00")).timestamp(),
                           round(float(t["yes_price_dollars"]) * 100), float(t["count_fp"]), 1 if t["taker_outcome_side"] == "yes" else -1) for t in tr])
            n += len(tr)
            cur = d.get("cursor")
            if not cur or not tr:
                break
        db.execute("INSERT OR REPLACE INTO done VALUES(?,?)", (tk, n)); db.commit()
        if k % 10 == 0:
            print(k, "of", len(pick), tk, n, "trades", flush=True)
    print("done", flush=True)


def stack_sign(levels: dict) -> int:
    """+1 / -1 if STACK_LEVELS adjacent price levels are all one-sided STACK_RATIO to 1 with at least STACK_MIN contracts on the winning side, else 0."""
    best, run, last_p, last_s = 0, 0, None, 0
    for p in sorted(levels):
        s, b = levels[p]
        sg = 1 if (b >= STACK_RATIO * max(s, 1e-9) and b >= STACK_MIN) else (-1 if (s >= STACK_RATIO * max(b, 1e-9) and s >= STACK_MIN) else 0)
        if sg != 0 and sg == last_s and last_p is not None and p - last_p == 1:
            run += 1
        else:
            run = 1 if sg != 0 else 0
        if run >= STACK_LEVELS:
            best = sg
        last_p, last_s = p, sg
    return best


def sim(q, i, sign_yes: bool, T: float, S: float, mult: float = 1.0):
    """Enter at the closing quote of minute i+1, scan minutes i+2 .. i+1+HOLD_MIN for target or stop on the exit side's closing quote; None if a minute is missing."""
    e = q.get(i + 1)
    if e is None:
        return None
    buy = e[1] if sign_yes else round(1 - e[0], 4)
    if not 0.02 < buy < 0.98:
        return None
    val = None
    for j in range(i + 2, i + 2 + HOLD_MIN):
        x = q.get(j)
        if x is None:
            return None
        val = x[0] if sign_yes else round(1 - x[1], 4)
        if val >= buy + T - 1e-9 or val <= buy - S + 1e-9:
            break
    return val - buy - fee(buy, mult) - fee(val, mult)


def build_events():
    db = sqlite3.connect(DB); src = sqlite3.connect(SC1)
    tickers = [r[0] for r in db.execute("SELECT ticker FROM done")]
    out = []
    for tk in tickers:
        cd = src.execute("SELECT end_ts, bid_c, ask_c, volume FROM candle WHERE ticker=? ORDER BY end_ts", (tk,)).fetchall()
        tr = db.execute("SELECT ts, price, size, side FROM trade WHERE ticker=? ORDER BY ts", (tk,)).fetchall()
        if len(cd) < 60 or len(tr) < 200:
            continue
        q = {c[0] // 60: (c[1], c[2]) for c in cd if c[1] is not None and c[2] is not None and 0 < c[1] < c[2] < 1}
        vol = {c[0] // 60: (c[3] or 0.0) for c in cd}
        bars = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))
        prints = []
        for ts, price, size, side in tr:
            m = int(ts // 60) + 1  # candle end index of the minute containing the trade
            bars[m][price][1 if side > 0 else 0] += size
            prints.append((m, size, side))
        mins = sorted(q)
        deltas_hist, vols_hist, print_hist = [], [], []
        pi = 0
        for idx, m in enumerate(mins):
            if (m - 1) not in q:
                continue
            q0, q1 = q[m - 1], q[m]
            mid0, mid1 = (q0[0] + q0[1]) / 2, (q1[0] + q1[1]) / 2
            spread = q1[1] - q1[0]
            lv = bars.get(m)
            vm = sum(v[0] + v[1] for v in lv.values()) if lv else 0.0
            dm = sum(v[1] - v[0] for v in lv.values()) if lv else 0.0
            eligible = vm >= MIN_VOL and spread <= MAX_SPREAD and MID_LO <= mid1 <= MID_HI and (m + 1) in q
            mprints = []
            while pi < len(prints) and prints[pi][0] <= m:
                if prints[pi][0] == m:
                    mprints.append(prints[pi])
                pi += 1
            trig = {}
            if eligible and lv:
                s = stack_sign(lv)
                if s: trig["STACK"] = s
                if len(deltas_hist) >= 30 and dm != 0:
                    thr = float(np.quantile(np.abs(deltas_hist), DELTA_Q))
                    if abs(dm) >= thr and (dm > 0) == (mid1 > mid0):
                        trig["DELTA_BREAK"] = 1 if dm > 0 else -1
                if len(vols_hist) >= 30 and vm >= ABSORB_X * max(st.median(vols_hist[-30:]), 1.0) and abs(mid1 - mid0) < ABSORB_MOVE and dm != 0:
                    trig["ABSORB"] = 1 if dm > 0 else -1
                if len(print_hist) >= 50 and mprints:
                    med = st.median(print_hist[-200:])
                    big = max(mprints, key=lambda x: x[1])
                    if big[1] >= BIG_X * max(med, 1.0):
                        trig["BIG_PRINT"] = big[2]
            out.append({"tk": tk, "m": m, "day": datetime.fromtimestamp(m * 60, timezone.utc).strftime("%Y-%m-%d"), "elig": eligible, "dm": dm, "trig": trig, "q": q})
            if vm > 0:
                deltas_hist.append(dm); vols_hist.append(vm)
            print_hist.extend(p[1] for p in mprints)
    return out


def zday(x: np.ndarray, d: np.ndarray) -> float:
    n = len(x)
    if n < 20:
        return 0.0
    r = x - x.mean()
    s = np.bincount(d, weights=r)
    se = np.sqrt((s * s).sum()) / n
    return float(x.mean() / se) if se > 0 else 0.0


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] not in ("fetch", "run"):
        print(__doc__); return
    if argv[1] == "fetch":
        fetch(int(argv[2]) if len(argv) > 2 else 0, int(argv[3]) if len(argv) > 3 else 1); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    ev = build_events()
    elig = [e for e in ev if e["elig"] and e["dm"] != 0]
    days = sorted({e["day"] for e in elig}); didx = {d: k for k, d in enumerate(days)}; cut = days[len(days) // 2]
    combos = [(T, S) for T in TARGETS for S in (T / 2, T)]
    # outcome table for every eligible minute: [yes-long, no-long] x combos, plus stressed
    out_tab = np.full((len(elig), 2, len(combos)), np.nan); out_str = np.full_like(out_tab, np.nan)
    for a, e in enumerate(elig):
        for side in (0, 1):
            for c, (T, S) in enumerate(combos):
                out_tab[a, side, c] = sim_val if (sim_val := sim(e["q"], e["m"], side == 0, T, S)) is not None else np.nan
                v2 = sim(e["q"], e["m"], side == 0, T, S, 1.2)
                out_str[a, side, c] = v2 if v2 is not None else np.nan
    dix = np.array([didx[e["day"]] for e in elig]); half2 = np.array([e["day"] >= cut for e in elig])
    rules = [(t, d, c) for t in ("STACK", "DELTA_BREAK", "ABSORB", "BIG_PRINT") for d in ("follow", "fade") for c in range(len(combos))]

    def pick(trig_idx_sign, d):
        # sign +1 flow: follow buys YES (side 0); fade buys NO (side 1)
        return np.where((trig_idx_sign > 0) == (d == "follow"), 0, 1)

    trig_sign = {t: np.array([e["trig"].get(t, 0) for e in elig]) for t in ("STACK", "DELTA_BREAK", "ABSORB", "BIG_PRINT")}
    dsign = np.sign([e["dm"] for e in elig]).astype(int)
    res = {}
    for (t, d, c) in rules:
        ids = np.where(trig_sign[t] != 0)[0]
        sd = pick(trig_sign[t][ids], d)
        x = out_tab[ids, sd, c]; xs = out_str[ids, sd, c]; ok = ~np.isnan(x)
        ids, x, xs = ids[ok], x[ok], xs[ok]
        if len(x) == 0:
            res[(t, d, c)] = None; continue
        h2 = half2[ids]
        # control: every eligible minute, direction by that minute's delta sign, same exits
        sdc = pick(dsign, d); xc = out_tab[np.arange(len(elig)), sdc, c]; xc = xc[~np.isnan(xc)]
        res[(t, d, c)] = {"n": len(x), "days": len({elig[i]["day"] for i in ids}), "mean": float(x.mean()), "z": zday(x, dix[ids]), "h1": float(x[~h2].mean()) if (~h2).any() else 0.0,
                          "h2": float(x[h2].mean()) if h2.any() else 0.0, "stress": float(xs[~np.isnan(xs)].mean()), "ctrl": float(xc.mean())}
    # family-wise null: random eligible minutes, same count per rule, direction by the minute's delta sign
    rng = np.random.default_rng(SEED); maxz = []
    for _ in range(REPS):
        best = -9.0
        for (t, d, c) in rules:
            r = res[(t, d, c)]
            if r is None: continue
            ids = rng.integers(0, len(elig), r["n"])
            sd = pick(dsign[ids], d); x = out_tab[ids, sd, c]; ok = ~np.isnan(x)
            if ok.sum() > 20:
                best = max(best, zday(x[ok], dix[ids][ok]))
        maxz.append(best)
    crit = float(np.quantile(maxz, 0.95))
    lines = [f"FP3: {len(ev)} minutes, {len(elig)} eligible with flow, {len(days)} days, null 95th percentile of best z over rules {crit:.2f}"]
    passed = []
    for (t, d, c), r in sorted(((k, v) for k, v in res.items() if v), key=lambda kv: -kv[1]["mean"])[:20]:
        T, S = combos[c]
        ok = r["n"] >= MIN_TRADES and r["days"] >= MIN_DAYS and r["mean"] >= BAR_C and r["z"] >= crit and r["h1"] > 0 and r["h2"] > 0 and r["stress"] > 0 and r["mean"] - r["ctrl"] >= CTRL_C
        if ok: passed.append((t, d, T, S))
        lines.append(f"{t:11s} {d:6s} T{100 * T:.0f}c S{100 * S:.1f}c n={r['n']:5d} days={r['days']:3d} net {100 * r['mean']:+.2f}c z {r['z']:+.2f} halves {100 * r['h1']:+.2f}/{100 * r['h2']:+.2f} stress {100 * r['stress']:+.2f} control {100 * r['ctrl']:+.2f}  {'PASS' if ok else ''}")
    best = max((v for v in res.values() if v), key=lambda v: v["mean"])
    verdict = "NOT_YET_FALSIFIED" if passed else ("NOT_ENOUGH_DATA" if best["n"] < MIN_TRADES else ("FALSIFIED" if best["mean"] < FALSIFY_C else "NOT_ENOUGH_DATA"))
    lines.insert(1, f"VERDICT {verdict}; passing rules: {passed}")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
