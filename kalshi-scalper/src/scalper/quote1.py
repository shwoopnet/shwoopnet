"""QUOTE1 (README, Pre-registration: QUOTE1): two-sided passive quoting on the Bitcoin and Ethereum 15 minute contracts, flat before the close. No-view lane, research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
    python -m scalper.quote1 fetch K N   (resumable shard K of N: the trade tape of the last 170 s of each recorded window)
    python -m scalper.quote1 run         (the one read; refused a second time)
"""
from __future__ import annotations

import csv
import gzip
import io
import json
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime

from . import api
from .paths import DATA_DIR

D = DATA_DIR / "quote1"
RESULT = DATA_DIR / "quote1_result.txt"
REPO = "/home/user/shwoopnet"
ASSETS = ("KXBTC15M", "KXETH15M")
FLAT_S, POST_END_S = 20, 150
LOT = 1


def fee(p, m=1.0):
    return m * 0.07 * p * (1 - p)


def git(*a):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True).stdout


def runs():
    subprocess.run(["git", "-C", REPO, "fetch", "-q", "origin", "quote-data"], capture_output=True)
    files = git("ls-tree", "-r", "--name-only", "origin/quote-data").decode().split()
    return sorted({f.rsplit("/", 1)[0] for f in files if f.endswith("quotes.csv.gz")})


def windows():
    """[(ticker, close_ts)] for Bitcoin and Ethereum windows with recorder coverage."""
    out = {}
    for r in runs():
        raw = git("show", f"origin/quote-data:{r}/coverage.csv.gz")
        if not raw:
            continue
        for row in csv.DictReader(io.TextIOWrapper(gzip.open(io.BytesIO(raw)))):
            t = row["ticker"]
            if t.split("-")[0] in ASSETS:
                out[t] = (int(datetime.fromisoformat(row["window_close_utc"].replace("Z", "+00:00")).timestamp()), r)
    return out


def fetch(shard, shards):
    D.mkdir(exist_ok=True)
    ws = sorted(windows().items())[shard::shards]
    fp = D / f"tape_{shard}.json"
    have = json.loads(fp.read_text()) if fp.exists() else {}
    for i, (tk, (close, run)) in enumerate(ws):
        if tk in have:
            continue
        cur, rows = None, []
        while True:
            p = {"ticker": tk, "limit": 1000, "min_ts": close - POST_END_S - 20, "max_ts": close}
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
        have[tk] = rows
        if i % 20 == 0:
            fp.write_text(json.dumps(have)); print(shard, i, len(ws), flush=True)
        time.sleep(0.05)
    fp.write_text(json.dumps(have)); print("done", flush=True)


def main(argv):
    if len(argv) < 2 or argv[1] not in ("fetch", "run"):
        print(__doc__); return
    if argv[1] == "fetch":
        fetch(int(argv[2]), int(argv[3])); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    ws = windows()
    tape = {}
    for f in sorted(D.glob("tape_*.json")):
        tape.update(json.loads(f.read_text()))
    byrun = defaultdict(list)
    for tk, (close, run) in ws.items():
        if tk in tape:
            byrun[run].append(tk)
    res = {True: [], False: []}   # fee on maker fills: True conservative, False zero
    stats = {"windows": 0, "buy_fill": 0, "sell_fill": 0, "cycles": 0, "flat": 0}
    for run, tks in byrun.items():
        raw = git("show", f"origin/quote-data:{run}/quotes.csv.gz")
        if not raw:
            continue
        rows = defaultdict(list)
        for r in csv.DictReader(io.TextIOWrapper(gzip.open(io.BytesIO(raw)))):
            if r["ticker"] in tks and r["yes_bid"] and r["yes_ask"]:
                rows[r["ticker"]].append((int(r["t_recv_ms"]) / 1000, float(r["yes_bid"]), float(r["yes_ask"]), float(r["bid_size"] or 0), float(r["ask_size"] or 0)))
        for tk in tks:
            q = sorted(rows.get(tk, []))
            close = ws[tk][0]
            q = [x for x in q if close - POST_END_S - 5 <= x[0] <= close]
            if len(q) < 20:
                continue
            t0, b0, a0, bs, as_ = q[0]
            if not (0 < b0 < a0 < 1):
                continue
            tr = sorted(x for x in tape[tk] if x[0] >= t0)
            flat_t = close - FLAT_S
            fq = [x for x in q if x[0] <= flat_t]
            if not fq:
                continue
            fb, fa = fq[-1][1], fq[-1][2]
            stats["windows"] += 1
            tb, ta = None, None
            cb = ca = 0.0
            for ts, price, size, side in tr:
                if ts > flat_t:
                    break
                p = price / 100
                if tb is None and side == -1:
                    if p < b0 - 1e-9:
                        tb = ts
                    elif abs(p - b0) < 1e-9:
                        cb += size
                        if cb > bs:
                            tb = ts
                if ta is None and side == 1:
                    if p > a0 + 1e-9:
                        ta = ts
                    elif abs(p - a0) < 1e-9:
                        ca += size
                        if ca > as_:
                            ta = ts
            stats["buy_fill"] += tb is not None; stats["sell_fill"] += ta is not None
            for conservative in (True, False):
                mf = (lambda p: fee(p)) if conservative else (lambda p: 0.0)
                pnl = 0.0
                if tb is not None and ta is not None:
                    pnl = (a0 - b0) - mf(b0) - mf(a0)
                    if conservative: stats["cycles"] += 1
                elif tb is not None:
                    pnl = (fb - b0) - mf(b0) - fee(fb)
                    if conservative: stats["flat"] += 1
                elif ta is not None:
                    pnl = (a0 - fa) - mf(a0) - fee(fa)
                    if conservative: stats["flat"] += 1
                res[conservative].append((tk, close, pnl))
    def pf(xs):
        w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0); return w / l if l else float("inf")
    closes = sorted({c for _, c, _ in res[True]})
    lines = []
    verdict = "NOT_ENOUGH_DATA" if len(closes) < 300 else "FALSIFIED"
    for conservative in (True, False):
        v = res[conservative]
        if not v:
            continue
        pn = [p for _, _, p in v]
        half = len(v) // 2
        order = sorted(v, key=lambda x: x[1])
        h1 = [p for _, _, p in order[:half]]; h2 = [p for _, _, p in order[half:]]
        cyc = [p for p in pn if p > 0]
        lines.append(f"{'maker fee = taker formula' if conservative else 'zero maker fee'}: windows {len(v)} on {len(closes)} independent closes, PF {pf(pn):.2f} (halves {pf(h1):.2f} / {pf(h2):.2f}), loss rate {100 * sum(1 for p in pn if p < 0) / len(pn):.0f}%, net per window {100 * sum(pn) / len(pn):+.3f}c, total {100 * sum(pn):+.1f}c")
    lines.append(f"fills: windows {stats['windows']}, buy fills {stats['buy_fill']}, sell fills {stats['sell_fill']}, completed cycles {stats['cycles']}, flattened one-sided {stats['flat']}")
    if res[True] and pf([p for _, _, p in res[True]]) < 1.5 and len(closes) >= 300:
        verdict = "FALSIFIED"
    lines.insert(0, f"QUOTE1 {verdict} (registered minimum 300 independent windows; {len(closes)} available)")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
