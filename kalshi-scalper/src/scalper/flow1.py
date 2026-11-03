"""FLOW1 (workers/FLOW1_REGISTRATION.md): cheap-side taker flow at 180 s before the close, 15 minute markets, on the public trade tape.
Research only; keyless; nothing here places an order. Cheap side only (ask 0.05 to 0.50); no favourite-side result is computed.
    python -m scalper.flow1 list  <SERIES>                 (windows to fetch, from candles only; no outcome)
    python -m scalper.flow1 fetch <SERIES> <shard> <shards> [hours]
    python -m scalper.flow1 status <SERIES>
    python -m scalper.flow1 score  <SERIES>                (BTC: D1/D2 kill rules, holdout only if they do not fire; others: replication)
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from . import api
from .gen6 import fee as g6fee

CACHE = Path.home() / ".cache" / "flow1"
THRESH = -0.036            # FITTED by the refinement chat on 146 R6 windows; fixed here, never tuned
LO_ASK, HI_ASK, LIMIT = 0.05, 0.50, 0.50
START, END = 1785974400, 1793664000          # 2026-08-06 00:00Z, 2026-11-03 00:00Z
CUT1 = START + (END - START) // 3            # D1 | D2
CUT2 = START + 2 * (END - START) // 3        # D2 | HOLDOUT
R6_FROM = 1793145600                         # 2026-10-29 00:00Z
HIST_CUTOFF = 1788480000                     # 2026-09-04 00:00Z (/historical/cutoff trades_created_ts)
FIXED_DOI = 86299.56000000001
SEED = 36


# ---------------------------------------------------------------- candle side (no outcome)

def cheap_entry(cs: dict, ct: int):
    """(side, signal ask, fill ask) for the window, or (None, reason). Cheap side = lower ask at the candle ending ct-180 (ties: none);
    signal ask in [0.05, 0.50]; fill = that side's ask at the NEXT candle (ending ct-120), hard limit 0.50."""
    q, nq = cs.get(ct - 180), cs.get(ct - 120)
    if q is None:
        return None, "no_signal_candle"
    ay, an = q[1], round(1 - q[0], 4)
    if abs(ay - an) < 1e-9:
        return None, "tie"
    side = "yes" if ay < an else "no"
    a = min(ay, an)
    if not (LO_ASK - 1e-9 <= a <= HI_ASK + 1e-9):
        return None, "out_of_band"
    if nq is None:
        return None, "no_fill_candle"
    f = nq[1] if side == "yes" else round(1 - nq[0], 4)
    if f > LIMIT + 1e-9:
        return None, "over_limit"
    return (side, a, f), "ok"


def windows(series: str, lo: int = START, hi: int = END) -> list[tuple]:
    from . import oicorex1
    M = oicorex1.load_series(series, lo, hi)
    return [(tk, ct, res, cs) for tk, (ct, res, cs, _) in sorted(M.items(), key=lambda x: x[1][0]) if res in ("yes", "no")]


def fetch_list(series: str) -> list[tuple]:
    """(ticker, close) of the windows that can trade on candles alone, in a seeded random order (any prefix is a random sample)."""
    out = [(tk, ct) for tk, ct, _, cs in windows(series) if cheap_entry(cs, ct)[0] is not None]
    random.Random(SEED).shuffle(out)
    return out


# ---------------------------------------------------------------- flow (tape side)

def flow_of(rows, cheap: str):
    """rows: (taker_outcome_side, count). flow = (bought - sold) / total of the CHEAP side; None if no contracts.
    A taker long the cheap side BOUGHT it; a taker long the other side sold it (same exposure). Unknown side: in total only."""
    bought = sold = total = 0.0
    for s, n in rows:
        total += n
        if s == cheap:
            bought += n
        elif s in ("yes", "no"):
            sold += n
    return None if total <= 0 else (bought - sold) / total


# ---------------------------------------------------------------- tape fetch (outside the repo)

def _db(series: str):
    CACHE.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(CACHE / f"tape_{series}.sqlite", timeout=120)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("CREATE TABLE IF NOT EXISTS trades(ticker TEXT, ts REAL, size REAL, taker TEXT, tid TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS done(ticker TEXT PRIMARY KEY, n INTEGER, pages INTEGER, src TEXT, at REAL)")
    db.execute("CREATE INDEX IF NOT EXISTS ix_tr ON trades(ticker)")
    return db


def _get(path: str, params: dict):
    url = api.BASES[0] + path + "?" + urllib.parse.urlencode(params)
    for i in range(60):
        try:
            with urllib.request.urlopen(url, timeout=25) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            time.sleep(3.0 if e.code == 429 else 6.0)
        except Exception:
            time.sleep(6.0)
    raise RuntimeError("GET failed " + path)


def _pages(path: str, tk: str, lo: int, hi: int):
    cur, rows, pages = None, [], 0
    while True:
        p = {"ticker": tk, "limit": 1000, "min_ts": lo, "max_ts": hi}
        if cur:
            p["cursor"] = cur
        d = _get(path, p)
        pages += 1
        for t in d.get("trades", []):
            ts = datetime.fromisoformat(t["created_time"].replace("Z", "+00:00")).timestamp()
            side = t.get("taker_outcome_side") or t.get("taker_side") or "?"
            rows.append((ts, float(t["count_fp"]), side, t.get("trade_id", "")))
        cur = d.get("cursor")
        time.sleep(0.4)
        if not cur or not d.get("trades"):
            return rows, pages


def fetch_window(tk: str, ct: int):
    lo, hi = ct - 360, ct - 180
    first = "/historical/trades" if ct < HIST_CUTOFF else "/markets/trades"
    second = "/markets/trades" if first == "/historical/trades" else "/historical/trades"
    rows, pages = _pages(first, tk, lo, hi)
    src = first
    if not rows:
        rows, p2 = _pages(second, tk, lo, hi)
        pages += p2
        src = second if rows else "empty"
    return [r for r in rows if lo < r[0] <= hi], pages, src


def fetch(series: str, shard: int, shards: int, hours: float = 99.0):
    db = _db(series)
    jobs = fetch_list(series)[shard::shards]
    done = {r[0] for r in db.execute("select ticker from done")}
    t0 = time.time()
    print(series, len(jobs), "jobs this shard,", len(done), "done (all shards)", flush=True)
    for i, (tk, ct) in enumerate(jobs):
        if tk in done:
            continue
        if time.time() - t0 > hours * 3600:
            print("time box reached", flush=True)
            break
        rows, pages, src = fetch_window(tk, ct)
        db.executemany("insert into trades values(?,?,?,?,?)", [(tk, r[0], r[1], r[2], r[3]) for r in rows])
        db.execute("insert or replace into done values(?,?,?,?,?)", (tk, len(rows), pages, src, time.time()))
        db.commit()
        if i % 25 == 0:
            print(shard, i, len(jobs), tk, len(rows), pages, src, round(time.time() - t0), flush=True)
    print("shard", shard, "finished", flush=True)


# ---------------------------------------------------------------- scoring

def entries(series: str) -> tuple[list[dict], dict]:
    """One dict per fetched, flow-defined, fillable window (outcome joined here, not before). Counters for skipped windows."""
    db = _db(series)
    done = {r[0]: r for r in db.execute("select ticker, n, pages, src from done")}
    by = defaultdict(list)
    for tk, ts, n, s in db.execute("select ticker, ts, size, taker from trades"):
        by[tk].append((s, n))
    wins = windows(series)
    thr90 = _trailing(wins)
    out, cnt = [], defaultdict(int)
    for tk, ct, res, cs in wins:
        e, why = cheap_entry(cs, ct)
        if e is None:
            cnt["no_trade_" + why] += 1
            continue
        if tk not in done:
            cnt["not_fetched"] += 1
            continue
        if done[tk][1] == 0:
            cnt["empty_tape"] += 1
            continue
        side, a, f = e
        fl = flow_of(by[tk], side)
        if fl is None:
            cnt["empty_tape"] += 1
            continue
        win = 1.0 if res == side else 0.0
        doi = _doi(cs, ct)
        day = datetime.fromtimestamp(ct, timezone.utc).strftime("%Y-%m-%d")
        out.append({"tk": tk, "ct": ct, "day": day, "month": day[:7], "side": side, "ask": a, "fill": f, "win": win, "flow": fl,
                    "low": fl <= THRESH, "r6": ct >= R6_FROM,
                    "net": win - f - g6fee(f, 10), "net1": win - f - g6fee(f, 1), "net12": win - f - g6fee(f, 10, 1.2),
                    "oi_fixed": None if doi is None else doi > FIXED_DOI,
                    "oi_trail": None if (doi is None or thr90.get(ct) is None) else doi > thr90[ct]})
    cnt["scored"] = len(out)
    return out, dict(cnt)


def _doi(cs, ct):
    a, b = cs.get(ct - 360), cs.get(ct - 180)
    if a is None or b is None or a[3] is None or b[3] is None:
        return None
    return float(b[3] - a[3])


def _trailing(wins):
    from .rev1 import trailing_p90
    return trailing_p90([(ct, _doi(cs, ct)) for _, ct, _, cs in wins])


def pf(nets):
    g = sum(x for x in nets if x > 0)
    l = -sum(x for x in nets if x < 0)
    return float("inf") if l == 0 and g > 0 else (g / l if l else 0.0)


def stat(rows, key="net"):
    if not rows:
        return {"n": 0}
    n = [r[key] for r in rows]
    return {"n": len(n), "win": sum(r["win"] for r in rows) / len(n), "paid": sum(r["fill"] for r in rows) / len(n),
            "net_c": 100 * sum(n) / len(n), "pf": pf(n), "days": len({r["day"] for r in rows})}


def fmt(name, s):
    if not s["n"]:
        return f"  {name}: n 0"
    return f"  {name}: n {s['n']}  win {100*s['win']:.1f}% vs paid {100*s['paid']:.1f}c  net {s['net_c']:+.2f}c  PF {s['pf']:.2f}  days {s['days']}"


def perm_p(rows, n_perm=10000, seed=SEED):
    """One sided: share of within-day shuffles of the low/high label whose (mean net low - mean net high) >= observed."""
    import numpy as np
    days = defaultdict(list)
    for r in rows:
        days[r["day"]].append((r["net"], r["low"]))
    arrs = [(np.array([x for x, _ in v]), np.array([l for _, l in v])) for v in days.values()]
    allnet = np.concatenate([a for a, _ in arrs]); alllow = np.concatenate([l for _, l in arrs])
    nl, nh = alllow.sum(), (~alllow).sum()
    if nl == 0 or nh == 0:
        return None, None
    obs = allnet[alllow].mean() - allnet[~alllow].mean()
    rng = np.random.default_rng(seed)
    ge = 0
    for _ in range(n_perm):
        s = 0.0
        for a, l in arrs:
            s += a[rng.permutation(len(a))[: int(l.sum())]].sum()
        low_sum = s
        diff = low_sum / nl - (allnet.sum() - low_sum) / nh
        ge += diff >= obs - 1e-12
    return float(obs), (ge + 1) / (n_perm + 1)


def block(rows, label):
    lo = [r for r in rows if r["low"]]; hi = [r for r in rows if not r["low"]]
    print(label)
    print(fmt("LOW ", stat(lo)))
    print(fmt("HIGH", stat(hi)))
    sl, sh = stat(lo), stat(hi)
    if sl["n"] and sh["n"]:
        print(f"  low minus high net {sl['net_c'] - sh['net_c']:+.2f}c   low share {100*sl['n']/len(rows):.1f}%")
    return sl, sh


def _by_month(rows):
    for m in sorted({r["month"] for r in rows}):
        print(fmt("month " + m + " LOW", stat([r for r in rows if r["month"] == m and r["low"]])))


def _guard(name):
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / name
    if p.exists():
        sys.exit(f"{name} already exists: this read runs once ({p.read_text()[:80]})")
    p.write_text(datetime.now(timezone.utc).isoformat())


def score(series: str):
    from .calibration import cluster_mean_z
    rows, cnt = entries(series)
    print("counters", cnt)
    if series != "KXBTC15M":
        return replication(series, rows)
    _guard("scored_KXBTC15M_D.txt")
    d1 = [r for r in rows if r["ct"] < CUT1]; d2 = [r for r in rows if CUT1 <= r["ct"] < CUT2]
    print("== D1, D2 (kill rules)")
    s1l, s1h = block(d1, "D1"); s2l, s2h = block(d2, "D2")
    dd = d1 + d2
    lo = [r for r in dd if r["low"]]
    print(f"pooled D low at C=1: net {100*sum(r['net1'] for r in lo)/max(1,len(lo)):+.2f}c; fees x1.2 PF {pf([r['net12'] for r in lo]):.2f}")
    obs, p = perm_p(dd)
    m, se, z = cluster_mean_z([(r["day"], r["net"]) for r in lo]) if len(lo) > 1 else (0, 0, 0)
    print(f"permutation (within-day, one sided) observed diff {None if obs is None else round(100*obs,2)}c p {p}; low-half date clustered z {z:.2f}")
    print("by month (D1+D2 low):"); _by_month(dd)
    pre = [r for r in dd if not r["r6"]]
    print(fmt("D1+D2 LOW, no R6 windows (none expected: R6 sits in the holdout)", stat([r for r in pre if r["low"]])))
    ov(lo)
    nlow = len(lo)
    killed = []
    for nm, sl, sh in (("D1", s1l, s1h), ("D2", s2l, s2h)):
        if sl["n"] < 20:
            killed.append(nm + " too few")
        elif sl["pf"] < 1.5:
            killed.append(f"{nm} low PF {sl['pf']:.2f} < 1.5")
        if sl["n"] and sh["n"] and sl["net_c"] - sh["net_c"] <= 0:
            killed.append(f"{nm} low minus high not positive")
    if lo and sum(r["net1"] for r in lo) <= 0:
        killed.append("pooled low net at C=1 not positive")
    if lo and pf([r["net12"] for r in lo]) < 1.0:
        killed.append("fees x1.2 PF < 1")
    if nlow < 150:
        verdict = f"NOT_ENOUGH_DATA ({nlow} low-half trades of 150)"
    elif killed:
        verdict = "FALSIFIED: " + "; ".join(killed)
    else:
        verdict = "NOT_YET_FALSIFIED on D1/D2 (holdout to be read)"
    print("VERDICT (D):", verdict)
    if verdict.startswith("NOT_YET"):
        _guard("scored_KXBTC15M_HOLDOUT.txt")
        ho = [r for r in rows if r["ct"] >= CUT2]
        print("== HOLDOUT (read once)")
        block(ho, "HOLDOUT all")
        block([r for r in ho if not r["r6"]], "HOLDOUT without R6 windows")
        block([r for r in ho if r["r6"]], "HOLDOUT R6 windows only")
        obs, p = perm_p(ho)
        print("holdout permutation", obs, p)
        ov([r for r in ho if r["low"]])


def ov(lo):
    if not lo:
        return
    for key, nm in (("oi_fixed", "fixed 86,299.56"), ("oi_trail", "trailing 24 h p90")):
        inn = [r for r in lo if r[key] is True]; out = [r for r in lo if r[key] is False]
        print(f"  OICORE overlap ({nm}): {len(inn)} of {len(lo)} low-half trades ({100*len(inn)/len(lo):.1f}%)")
        print(fmt("   inside ", stat(inn))); print(fmt("   outside", stat(out)))


def replication(series, rows):
    print("== replication", series, "(not pooled; fixed threshold", THRESH, ")")
    block(rows, "all fetched")
    mid = (START + END) // 2
    block([r for r in rows if r["ct"] < mid], "first half of range"); block([r for r in rows if r["ct"] >= mid], "second half of range")
    block([r for r in rows if not r["r6"]], "without R6 windows")
    obs, p = perm_p(rows); print("permutation", obs, p)
    ov([r for r in rows if r["low"]])
    lo, hi = stat([r for r in rows if r["low"]]), stat([r for r in rows if not r["low"]])
    ok = lo["n"] and hi["n"] and lo["pf"] > 1.0 and lo["pf"] > hi["pf"]
    for part in ([r for r in rows if r["ct"] < mid], [r for r in rows if r["ct"] >= mid]):
        a, b = stat([r for r in part if r["low"]]), stat([r for r in part if not r["low"]])
        ok = ok and a["n"] and b["n"] and a["pf"] > 1.0 and a["pf"] > b["pf"]
    print("REPLICATION:", "SUPPORTS" if ok else "DOES_NOT_SUPPORT")


if __name__ == "__main__":
    cmd, series = sys.argv[1], sys.argv[2]
    if cmd == "list":
        fl = fetch_list(series); print(len(fl), "windows to fetch", fl[:2])
    elif cmd == "fetch":
        fetch(series, int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]) if len(sys.argv) > 5 else 99.0)
    elif cmd == "status":
        db = _db(series); n = len(fetch_list(series))
        r = db.execute("select count(*), sum(n), sum(pages), sum(n=0) from done").fetchone()
        print(series, "done", r[0], "of", n, "trades", r[1], "pages", r[2], "empty", r[3])
    elif cmd == "score":
        score(series)
