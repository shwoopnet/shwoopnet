"""SWEEP1 (README, Pre-registration: SWEEP1): big prints and sweeps on Bitcoin 15 minute markets, followed or faded, with scale-out exits. Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
    python -m scalper.sweep1 fetch K N   (resumable shard K of N; tape of the 13 minutes before each close, last 30 days)
    python -m scalper.sweep1 run         (the one read; refused a second time)
"""
from __future__ import annotations

import json
import sqlite3
import statistics as st
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

from . import api
from .paths import DATA_DIR

RESULT = DATA_DIR / "sweep1_result.txt"
SOURCES = ["book", "l1b", "fresh"]
DAYS, TAPE_S = 7, 780
BIG_MIN, BIG_X, BIG_HIST, SW_LEVELS, SW_MIN = 100.0, 10.0, 50, 3, 100.0
ASK_LO, ASK_HI, MAX_SPREAD = 0.20, 0.80, 0.03
SELL_BEFORE, REPS, SEED = 120, 300, 27102707
MIN_N, MIN_DAYS, BAR_C, CTRL_C, FALSIFY_C = 200, 12, 0.010, 0.010, 0.003


def fee(p: float, mult: float = 1.0) -> float:
    return mult * 0.07 * p * (1 - p)


def mlist() -> list[tuple]:
    out, lo = {}, time.time() - DAYS * 86400
    for name in SOURCES:
        db = sqlite3.connect(DATA_DIR / f"{name}.sqlite")
        for tk, close_ts, res in db.execute("select ticker, close_ts, result from market where series='KXBTC15M'"):
            if close_ts >= lo and res in ("yes", "no") and tk not in out:
                out[tk] = (tk, close_ts, res, name)
    return sorted(out.values(), key=lambda x: x[1])


def fetch(shard: int, shards: int) -> None:
    ms = mlist()[shard::shards]
    db = sqlite3.connect(DATA_DIR / f"sweep1_{shard}.sqlite", timeout=120)
    db.execute("CREATE TABLE IF NOT EXISTS done(ticker TEXT PRIMARY KEY, n INTEGER, trig TEXT, dm TEXT)")
    done = {r[0] for r in db.execute("SELECT ticker FROM done")}
    print(len(ms), "markets,", len(done), "done", flush=True)
    for k, (tk, close_ts, res, _) in enumerate(ms):
        if tk in done:
            continue
        cur, n, rows = None, 0, []
        while True:
            p = {"ticker": tk, "limit": 1000, "min_ts": close_ts - TAPE_S, "max_ts": close_ts}
            if cur:
                p["cursor"] = cur
            try:
                d = api._get("/markets/trades", p)
            except Exception:
                time.sleep(5); continue
            tr = d.get("trades", [])
            rows += [(datetime.fromisoformat(t["created_time"].replace("Z", "+00:00")).timestamp(), round(float(t["yes_price_dollars"]) * 100), float(t["count_fp"]), 1 if t["taker_outcome_side"] == "yes" else -1) for t in tr]
            n += len(tr)
            cur = d.get("cursor")
            if not cur or not tr:
                break
        rows.sort()
        dm = defaultdict(float)
        for ts, price, size, side in rows:
            dm[int(ts // 60) + 1] += side * size
        db.execute("INSERT OR REPLACE INTO done VALUES(?,?,?,?)", (tk, n, json.dumps(triggers(rows, close_ts)), json.dumps({str(k): v for k, v in dm.items()}))); db.commit()
        if k % 25 == 0:
            print(k, "of", len(ms), tk, n, flush=True)
    print("done", flush=True)


def triggers(tr: list[tuple], close_ts: int) -> list[tuple]:
    """(minute-end index m, kind, sign) for big prints and sweeps; trades are (ts, price, size, side), sorted. A trigger counts at the end of its minute."""
    out, sizes = [], []
    by_sec = defaultdict(list)
    for ts, price, size, side in tr:
        m = int(ts // 60) + 1
        left = close_ts - m * 60
        if len(sizes) >= BIG_HIST and size >= BIG_MIN and size >= BIG_X * st.median(sizes) and 180 <= left <= 720:
            out.append((m, "BIG", side))
        sizes.append(size)
        by_sec[(int(ts), side)].append((price, size, m))
    for (sec, side), v in by_sec.items():
        m = v[0][2]
        left = close_ts - m * 60
        if len({p for p, _, _ in v}) >= SW_LEVELS and sum(s for _, s, _ in v) >= SW_MIN and 180 <= left <= 720:
            out.append((m, "SWEEP", side))
    return out


def simulate(by, close_ts, m, side_yes: bool, combo, mult: float = 1.0):
    """Entry at minute m+1's closing ask; scale-out exits per the README; returns net per contract or None."""
    q = by.get(m + 1)
    if q is None or q[1] - q[0] > MAX_SPREAD + 1e-9:
        return None
    e = q[1] if side_yes else round(1 - q[0], 4)
    if not ASK_LO <= e <= ASK_HI:
        return None
    frac, tgt, trail, stop = combo
    res = None
    # settlement outcome is attached by the caller via by["res"]
    payoff = 1.0 if by["res"] == ("yes" if side_yes else "no") else 0.0
    pos, cash, hi, tg_hit = 1.0, -e - fee(e, mult), e, False
    for k in range(m + 2, close_ts // 60 - SELL_BEFORE // 60 + 1):
        x = by.get(k)
        if x is None:
            continue
        b = x[0] if side_yes else round(1 - x[1], 4)
        hi = max(hi, b)
        if stop is not None and b <= e - stop + 1e-9:
            return cash + pos * (b - fee(b, mult))
        if not tg_hit and b >= e * (1 + tgt) - 1e-9:
            cash += frac * (b - fee(b, mult)); pos -= frac; tg_hit = True
            if pos <= 1e-9:
                return cash
        if tg_hit and trail is not None and b <= hi - trail + 1e-9:
            return cash + pos * (b - fee(b, mult))
    if tg_hit and trail is not None:
        x = by.get(close_ts // 60 - SELL_BEFORE // 60)
        if x is not None:
            b = x[0] if side_yes else round(1 - x[1], 4)
            return cash + pos * (b - fee(b, mult))
    return cash + pos * payoff


COMBOS = [(0.30, 0.30, None, None), (0.30, 0.30, 0.05, None), (0.50, 0.20, None, None), (0.30, 0.30, None, 0.08), (0.30, 0.30, 0.05, 0.08), (0.50, 0.20, None, 0.08)]


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
        fetch(int(argv[2]), int(argv[3])); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    meta = {m[0]: m for m in mlist()}
    cands = {}
    for name in SOURCES:
        db = sqlite3.connect(DATA_DIR / f"{name}.sqlite")
        for tk in meta:
            if meta[tk][3] == name:
                cands[tk] = {r[0] // 60: (r[1], r[2]) for r in db.execute("select end_ts, bid_c, ask_c from candle where ticker=? and bid_c is not null and ask_c is not null", (tk,))}
    seen_tk = set()
    recs = []  # (day, kind, sign, [outcomes follow], [outcomes fade], [stress follow], [stress fade], delta_sign_flag)
    ctrl_recs = []
    for f in sorted(DATA_DIR.glob("sweep1_*.sqlite")):
        d = sqlite3.connect(f)
        for (tk, n_tr, trig_s, dm_s) in d.execute("select ticker, n, trig, dm from done"):
            if tk not in meta or tk in seen_tk:
                continue
            seen_tk.add(tk)
            close_ts, res = meta[tk][1], meta[tk][2]
            by = dict(cands.get(tk, {})); by["res"] = res
            if n_tr < 100 or len(by) < 20:
                continue
            day = datetime.fromtimestamp(close_ts, timezone.utc).strftime("%Y-%m-%d")
            dm = {int(k): v for k, v in json.loads(dm_s).items()}
            for m, sg in list(dm.items()):
                left = close_ts - m * 60
                if sg != 0 and 180 <= left <= 720 and (m + 1) in by:
                    o = [[simulate(by, close_ts, m, (sg > 0) == fol, c) for c in COMBOS] for fol in (True, False)]
                    ctrl_recs.append((day, o))
            seen = set()
            for m, kind, sg in json.loads(trig_s):
                if (m, kind) in seen:
                    continue
                seen.add((m, kind))
                o = [[simulate(by, close_ts, m, (sg > 0) == fol, c) for c in COMBOS] for fol in (True, False)]
                o2 = [[simulate(by, close_ts, m, (sg > 0) == fol, c, 1.2) for c in COMBOS] for fol in (True, False)]
                recs.append((day, kind, o, o2))
    days = sorted({r[0] for r in recs + ctrl_recs})
    if not recs:
        RESULT.write_text("SWEEP1 NOT_ENOUGH_DATA: no triggers\n"); print("no triggers"); return
    cut = days[len(days) // 2]; didx = {d: i for i, d in enumerate(days)}
    lines = [f"SWEEP1: {len(recs)} triggers, {len(ctrl_recs)} control minutes, {len(days)} days"]
    rules = [(k, fol, ci) for k in ("BIG", "SWEEP") for fol in (0, 1) for ci in range(len(COMBOS))]
    def arr(kind, fol, ci, which=2):
        xs = [(didx[r[0]], r[0] >= cut, r[which][fol][ci]) for r in recs if r[1] == kind and r[which][fol][ci] is not None]
        return xs
    def carr(fol, ci):
        return [(didx[r[0]], r[0] >= cut, r[1][fol][ci]) for r in ctrl_recs if r[1][fol][ci] is not None]
    stats = {}
    for (k, fol, ci) in rules:
        xs = arr(k, fol, ci)
        if len(xs) < 5:
            continue
        x = np.array([a[2] for a in xs]); dd = np.array([a[0] for a in xs]); h2 = np.array([a[1] for a in xs])
        xs2 = arr(k, fol, ci, 3)
        cx = np.array([a[2] for a in carr(fol, ci)])
        stats[(k, fol, ci)] = {"n": len(x), "days": len(set(dd)), "mean": float(x.mean()), "z": zday(x, dd), "h1": float(x[~h2].mean()) if (~h2).any() else 0.0, "h2": float(x[h2].mean()) if h2.any() else 0.0,
                               "stress": float(np.mean([a[2] for a in xs2])), "ctrl": float(cx.mean()) if len(cx) else 0.0}
    rng = np.random.default_rng(SEED)
    cpool = {(fol, ci): np.array([(a[0], a[2]) for a in carr(fol, ci)]) for fol in (0, 1) for ci in range(len(COMBOS))}
    maxz = []
    for _ in range(REPS):
        best = -9.0
        for key, s in stats.items():
            p = cpool[(key[1], key[2])]
            if len(p) < s["n"]:
                continue
            idx = rng.integers(0, len(p), s["n"])
            best = max(best, zday(p[idx, 1], p[idx, 0].astype(int)))
        maxz.append(best)
    crit = float(np.quantile(maxz, 0.95))
    passed = []
    lines.append(f"null 95th percentile of best z over the rules: {crit:.2f}")
    for key, s in sorted(stats.items(), key=lambda kv: -kv[1]["mean"]):
        ok = s["n"] >= MIN_N and s["days"] >= MIN_DAYS and s["mean"] >= BAR_C and s["z"] >= crit and s["h1"] > 0 and s["h2"] > 0 and s["stress"] > 0 and s["mean"] - s["ctrl"] >= CTRL_C
        if ok: passed.append(key)
        lines.append(f"{key[0]:5s} {'follow' if key[1] == 0 else 'fade  '} exit{key[2]} n={s['n']:4d} days={s['days']:2d} net {100 * s['mean']:+.2f}c z {s['z']:+.2f} halves {100 * s['h1']:+.2f}/{100 * s['h2']:+.2f} stress {100 * s['stress']:+.2f} control {100 * s['ctrl']:+.2f} {'PASS' if ok else ''}")
    best = max(stats.values(), key=lambda s: s["mean"])
    verdict = "NOT_YET_FALSIFIED" if passed else ("NOT_ENOUGH_DATA" if best["n"] < MIN_N else ("FALSIFIED" if best["mean"] < FALSIFY_C else "NOT_ENOUGH_DATA"))
    lines.insert(1, f"VERDICT {verdict}; passing: {passed}")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
