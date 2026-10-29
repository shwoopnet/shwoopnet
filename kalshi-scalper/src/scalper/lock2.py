"""LOCK2 (README, Pre-registration: LOCK2): coincident-close locks between the 15 minute contract and the hourly ladder, on the
recorder's simultaneous quotes with sizes (branch quote-data: quotes/*/quotes.csv and ladder.csv). Research only.
    python -m scalper.lock2 count   (closes per asset with both books recorded; scores nothing)
    python -m scalper.lock2 run     (once, refused until 25 closes per asset)
"""
from __future__ import annotations

import csv
import gzip
import io
import subprocess
import sys
from collections import defaultdict
from datetime import datetime

from .fees import taker_fee
from .paths import DATA_DIR

ASSETS = {"BTC": ("KXBTC15M", "KXBTCD"), "ETH": ("KXETH15M", "KXETHD")}
RESULT = DATA_DIR / "lock2_result.txt"
PAIR_MS = 1000      # a ladder poll is paired with the 15 minute quote nearest in send time, at most 1 s apart
MIN_C = 10


def _git(*a):
    return subprocess.run(["git", *a], capture_output=True, check=True, cwd=DATA_DIR.parent).stdout


def files(name):
    _git("fetch", "-q", "origin", "quote-data")
    return [p for p in _git("ls-tree", "-r", "--full-tree", "--name-only", "origin/quote-data").decode().split() if p.startswith("quotes/") and p.endswith(name)]


def rows(path):
    return list(csv.DictReader(io.StringIO(gzip.decompress(_git("show", f"origin/quote-data:{path}")).decode())))


def close_of_15(tk):
    # KXBTC15M-26OCT290630-30: date and time are the close in US Eastern; read the close from the ladder instead (exact UTC)
    return tk.split("-")[1]


def load():
    lad = defaultdict(list)    # (asset, close_iso) -> [(t_ms, strike, bid, ask, bid_size, ask_size)]
    for p in files("ladder.csv.gz"):
        for r in rows(p):
            for a, (s15, sl) in ASSETS.items():
                if r["ticker"].startswith(sl + "-") and r["yes_bid"] and r["yes_ask"]:
                    lad[(a, r["close_time"])].append((int(r["t_send_ms"]), float(r["strike"]), float(r["yes_bid"]), float(r["yes_ask"]), float(r["bid_size"] or 0), float(r["ask_size"] or 0)))
    q15 = defaultdict(list)    # (asset, close code) -> [(t_ms, strike, bid, ask, bid_size, ask_size)]
    for p in files("quotes.csv.gz"):
        for r in rows(p):
            for a, (s15, sl) in ASSETS.items():
                if r["ticker"].startswith(s15 + "-") and r["yes_bid"] and r["yes_ask"]:
                    q15[(a, close_of_15(r["ticker"]))].append((int(r["t_send_ms"]), float(r["strike"]), float(r["yes_bid"]), float(r["yes_ask"]), float(r["bid_size"] or 0), float(r["ask_size"] or 0)))
    pairs = {}
    for (a, ciso), lq in lad.items():
        c = datetime.fromisoformat(ciso.replace("Z", "+00:00"))
        if c.minute != 0:
            continue
        # match the 15 minute market closing at the same instant: its ticker code is the close in US Eastern
        from zoneinfo import ZoneInfo
        code = c.astimezone(ZoneInfo("America/New_York")).strftime("%y%b%d%H%M").upper()
        q = q15.get((a, code))
        if q:
            pairs[(a, ciso)] = (sorted(q), sorted(lq))
    return pairs


def count():
    P = load()
    per = defaultdict(int)
    for a, _ in P:
        per[a] += 1
    print("LOCK2 closes with both books recorded:", dict(per), "(25 per asset needed)")
    return P, per


def run():
    if RESULT.exists():
        print("Refusing to run again"); return
    P, per = count()
    if min(per.get(a, 0) for a in ASSETS) < 25:
        print("Refused: fewer than 25 closes for an asset (NOT_ENOUGH_DATA if this stays so)"); return
    import bisect
    lines = []
    for a in ASSETS:
        closes = [k for k in P if k[0] == a]
        with_lock, durs, sizes, best = 0, [], [], -9.0
        for k in closes:
            q, lq = P[k]
            qt = [x[0] for x in q]
            locked_polls = defaultdict(list)   # poll time -> best lock value at >= MIN_C contracts
            for t, K, lb, la, lbs, las in lq:
                i = bisect.bisect_left(qt, t)
                cand = [j for j in (i - 1, i) if 0 <= j < len(q) and abs(q[j][0] - t) <= PAIR_MS]
                if not cand:
                    continue
                _, K0, b15, a15, bs15, as15 = q[min(cand, key=lambda j: abs(q[j][0] - t))]
                for p1, s1, p2, s2, ok in ((a15, as15, 1 - lb, lbs, K >= K0), (1 - b15, bs15, la, las, K < K0)):
                    if not ok or not (0 < p1 < 1 and 0 < p2 < 1):
                        continue
                    size = int(min(s1, s2))
                    if size < MIN_C:
                        continue
                    v = 1 - p1 - p2 - (taker_fee(p1, MIN_C) + taker_fee(p2, MIN_C)) / MIN_C
                    best = max(best, v)
                    if v >= 0.01:
                        locked_polls[t].append((v, size))
            if locked_polls:
                with_lock += 1
                ts = sorted(locked_polls)
                run_s, start = 0.0, ts[0]
                for x, y in zip(ts, ts[1:] + [None]):
                    if y is None or y - x > 4000:
                        run_s = max(run_s, (x - start) / 1000); start = y
                durs.append(run_s); sizes.append(max(s for v in locked_polls.values() for _, s in v))
        lines.append(f"{a}: closes {len(closes)}, closes with a lock >= 1.0c at >= {MIN_C} contracts {with_lock}; "
                     f"median duration {sorted(durs)[len(durs) // 2] if durs else 0:.1f}s, max {max(durs) if durs else 0:.1f}s; max size {max(sizes) if sizes else 0}; best pair value {100 * best:.2f}c")
    v = "FALSIFIED" if all(" with a lock >= 1.0c at >= 10 contracts 0;" in l for l in lines) else "see the registered NOT_YET_FALSIFIED rule (5 of 25 closes, 5 s, 10 contracts)"
    lines.insert(0, f"LOCK2 VERDICT: {v}")
    RESULT.write_text("\n".join(lines) + "\n"); print("\n".join(lines))


if __name__ == "__main__":
    {"count": count, "run": run}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
