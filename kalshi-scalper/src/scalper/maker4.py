"""MAKER4 (README, Pre-registration: MAKER4): mid-window two-sided maker scalp on KXBTC15M, KXETH15M, KXGOLD15M.
Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
    python -m scalper.maker4 fetch K N   (resumable shard K of N: trade tape from 12.5 to 2 minutes left of each window)
    python -m scalper.maker4 run         (the one read; refused a second time)
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from datetime import datetime, timezone

from . import api
from .calibration import cluster_mean_z
from .paths import DATA_DIR

D = DATA_DIR / "maker4"
RESULT = DATA_DIR / "maker4_result.txt"
SERIES = ("KXBTC15M", "KXETH15M", "KXGOLD15M")
FIRST, LAST_POST, FLAT = 720, 240, 120
LO, HI, STOP = 0.20, 0.80, 0.05
MIN_N, BAR = 300, 1.5


def fee(p, k):
    return k * p * (1 - p)


def markets():
    db = sqlite3.connect(DATA_DIR / "fresh.sqlite")
    out = {}
    for tk, series, close_ts in db.execute("select ticker, series, close_ts from market where series in (?,?,?)", SERIES):
        cs = {r[0]: (r[1], r[2]) for r in db.execute("select end_ts, bid_c, ask_c from candle where ticker=? and bid_c is not null and ask_c is not null", (tk,))}
        if cs:
            out[tk] = (series, close_ts, cs)
    return out


def sampled(M):
    """Amendment (before any fill was computed): the tape runs to about 30,000 trades a window, too slow to fetch for all
    1,544 closes, so every close time whose index (in time order) is a multiple of 4 is kept, with all its assets."""
    closes = sorted({v[1] for v in M.values()})
    keep = set(closes[::4])
    return {k: v for k, v in M.items() if v[1] in keep}


def fetch(shard, shards):
    D.mkdir(exist_ok=True)
    ms = sorted(sampled(markets()).items())[shard::shards]
    fp = D / f"tape_{shard}.json"
    have = json.loads(fp.read_text()) if fp.exists() else {}
    for i, (tk, (series, close, cs)) in enumerate(ms):
        if tk in have:
            continue
        cur, rows = None, []
        while True:
            p = {"ticker": tk, "limit": 1000, "min_ts": close - FIRST - 30, "max_ts": close - FLAT + 5}
            if cur:
                p["cursor"] = cur
            try:
                d = api._get("/markets/trades", p)
            except Exception:
                time.sleep(5); continue
            for t in d.get("trades", []):
                rows.append((datetime.fromisoformat(t["created_time"].replace("Z", "+00:00")).timestamp(), round(float(t["yes_price_dollars"]) * 100), float(t["count_fp"]), 1 if t["taker_outcome_side"] == "yes" else -1))
            cur = d.get("cursor")
            if not cur or not d.get("trades"):
                break
        have[tk] = sorted(rows)
        if i % 25 == 0:
            fp.write_text(json.dumps(have)); print(shard, i, len(ms), flush=True)
        time.sleep(0.05)
    fp.write_text(json.dumps(have)); print("done", shard, flush=True)


def simulate(close, cs, tape, strict, kmaker):
    """One window. Returns (pnl, cycles, one_sided_exits, spread_gain, exit_loss, posted)."""
    pnl = spread = exit_loss = 0.0; cycles = exits = posted = 0
    t = close - FIRST
    pos = 0; entry = None  # pos +1 long YES from a filled buy, -1 short from a filled sell
    bid = ask = None
    ti = 0
    def mid(k):
        b, a = cs[k]; return (b + a) / 2
    while t <= close - FLAT:
        q = cs.get(t)
        if pos == 0:
            if t > close - LAST_POST or q is None:
                t += 60; continue
            b, a = q
            if not (LO <= b and a <= HI and a > b):
                t += 60; continue
            bid, ask = round(b * 100), round(a * 100); posted += 1
        else:
            if q is not None:
                m = mid(t)
                if (pos == 1 and m <= entry / 100 - STOP) or (pos == -1 and m >= entry / 100 + STOP):
                    px = q[0] if pos == 1 else q[1]
                    g = (px - entry / 100) * pos - fee(px, 0.07)
                    pnl += g; exit_loss += g; exits += 1; pos = 0; t += 60; continue
        # walk the tape over (t, t+60]
        end = t + 60
        while ti < len(tape) and tape[ti][0] <= t:
            ti += 1
        j = ti
        buy_open = pos in (0, -1) and bid is not None
        sell_open = pos in (0, 1) and ask is not None
        while j < len(tape) and tape[j][0] <= min(end, close - FLAT):
            ts, px, sz, side = tape[j]
            if buy_open and side == -1 and (px < bid if strict else px <= bid) and (pos == 0 or pos == -1):
                if pos == 0:
                    pos, entry = 1, bid; pnl -= fee(bid / 100, kmaker); sell_open = True; buy_open = False
                else:
                    g = (entry - bid) / 100 - fee(bid / 100, kmaker); pnl += g; spread += (entry - bid) / 100; cycles += 1; pos = 0; buy_open = sell_open = False
            elif sell_open and side == 1 and (px > ask if strict else px >= ask) and (pos == 0 or pos == 1):
                if pos == 0:
                    pos, entry = -1, ask; pnl -= fee(ask / 100, kmaker); buy_open = True; sell_open = False
                else:
                    g = (ask - entry) / 100 - fee(ask / 100, kmaker); pnl += g; spread += (ask - entry) / 100; cycles += 1; pos = 0; buy_open = sell_open = False
            j += 1
            if pos == 0 and not buy_open and not sell_open:
                break
        ti = j
        t = end
        if pos == 0:
            bid = ask = None  # cancel; re-post next minute
    if pos != 0:
        q = cs.get(close - FLAT)
        if q is None:
            ks = [k for k in cs if k <= close - FLAT]
            q = cs[max(ks)] if ks else (entry / 100, entry / 100)
        px = q[0] if pos == 1 else q[1]
        g = (px - entry / 100) * pos - fee(px, 0.07); pnl += g; exit_loss += g; exits += 1
    return pnl, cycles, exits, spread, exit_loss, posted


def run():
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    tape = {}
    for f in sorted(D.glob("tape_*.json")):
        tape.update(json.loads(f.read_text()))
    M = sampled(markets())
    lines = []
    verdict = None
    for label, strict, k in (("Q1 maker fee 1.75% (VERDICT)", True, 0.0175), ("Q1 stress: maker fee 7%", True, 0.07), ("Q1 zero maker fee (info)", True, 0.0), ("Q0 optimistic, maker fee 1.75% (info)", False, 0.0175), ("Q0 optimistic, zero maker fee (info)", False, 0.0)):
        rows = []
        for tk, (series, close, cs) in M.items():
            if tk not in tape:
                continue
            r = simulate(close, cs, tape[tk], strict, k)
            if r[5] == 0:
                continue
            rows.append((close, series) + r)
        by_close = {}
        for close, series, pnl, *_ in rows:
            by_close[close] = by_close.get(close, 0.0) + pnl
        days = sorted({datetime.fromtimestamp(c, timezone.utc).strftime("%Y-%m-%d") for c in by_close}); cut = days[len(days) // 2]
        dayof = lambda c: datetime.fromtimestamp(c, timezone.utc).strftime("%Y-%m-%d")
        def pf(xs):
            w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0); return w / l if l else (99.0 if w else 0.0)
        allv = list(by_close.values())
        h1 = [v for c, v in by_close.items() if dayof(c) < cut]; h2 = [v for c, v in by_close.items() if dayof(c) >= cut]
        mean, _, z = cluster_mean_z([(dayof(c), v) for c, v in by_close.items()])
        cyc = sum(r[3] for r in rows); ex = sum(r[4] for r in rows); sg = sum(r[5] for r in rows); el = sum(r[6] for r in rows)
        res = {"pf": pf(allv), "h1": pf(h1), "h2": pf(h2), "n": len(allv), "z": z}
        if verdict is None:
            base = res
        if label.startswith("Q1 stress"):
            stress = res["pf"]
        lines.append(f"{label}: PF {res['pf']:.2f} (halves {res['h1']:.2f}/{res['h2']:.2f}), independent closes {res['n']} over {len(days)} days, loss rate {100 * sum(1 for v in allv if v < 0) / max(len(allv), 1):.0f}%, net {100 * mean:+.2f}c per close, z {z:+.2f}; windows {len(rows)}, completed cycles {cyc} (spread earned {100 * sg:+.1f}c total), one-sided exits {ex} (total {100 * el:+.1f}c)")
        for s in SERIES:
            v = [r[2] for r in rows if r[1] == s]
            if v:
                lines.append(f"    {s}: PF {pf(v):.2f}, windows {len(v)}, net {100 * sum(v) / len(v):+.2f}c")
        verdict = verdict or "set"
    b = base
    if b["n"] < MIN_N:
        v = "NOT_ENOUGH_DATA"
    elif b["pf"] >= BAR and b["h1"] >= 1 and b["h2"] >= 1 and stress >= 1.2:
        v = "NOT_YET_FALSIFIED"
    else:
        v = "FALSIFIED"
    lines.insert(0, f"MAKER4 VERDICT {v} (decided on Q1, maker fee 1.75%)")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "fetch":
        fetch(int(sys.argv[2]), int(sys.argv[3]))
    elif len(sys.argv) >= 2 and sys.argv[1] == "run":
        run()
    else:
        print(__doc__)
