"""RECORD1 (README, Pre-registration: RECORD1): does the spot-implied settlement probability beat the Kalshi quote in the last minute? Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
Reads the recorder's files from the git branch origin/quote-data (quotes/YYYY-MM-DD/HHMM/{quotes,spot,results,coverage,clock}.csv.gz).
Usage: python -m scalper.record1 look     an INFORMATION look at whatever has landed (decides nothing; may be repeated)
       python -m scalper.record1 read     the registered read; refused until 300 qualifying trades over 10 days exist, and refused a second time
"""
from __future__ import annotations

import csv
import gzip
import io
import math
import statistics as st
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone

from .calibration import cluster_mean_z
from .paths import DATA_DIR

# ---- fixed in the README before any real recorder file was read ----
SECONDS = (60, 45, 30, 15)
MARGIN, MIN_SIZE, STALE_S, SIGMA_WINDOW_S, MIN_CHANGES = 0.03, 5.0, 5, 300, 100
MEAN_C, Z_BAR, FALSIFY_C, FALSIFY_Z, MIN_N, MIN_DAYS, MIN_ASSETS, STRESS, MAX_OFFSET_MS = 0.020, 3.0, 0.005, 1.0, 300, 10, 3, 1.2, 100
ASSET = {"KXBTC15M": "BTC", "KXETH15M": "ETH", "KXSOL15M": "SOL", "KXXRP15M": "XRP", "KXDOGE15M": "DOGE"}
BRANCH, RESULT = "origin/quote-data", DATA_DIR / "record1_result.txt"


def phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def fee(p: float) -> float:
    return 0.07 * p * (1 - p)


def index_by_second(spot_rows: list[dict], asset: str) -> dict[int, float]:
    """second -> median over exchanges of the latest price seen no more than STALE_S seconds earlier; seconds with fewer than two exchanges are skipped."""
    ticks = sorted(((int(r["t_recv_ms"]), r["exchange"], float(r["price"])) for r in spot_rows if r["asset"] == asset), key=lambda x: x[0])
    if not ticks:
        return {}
    last: dict[str, tuple[int, float]] = {}
    out, i = {}, 0
    for sec in range(ticks[0][0] // 1000, ticks[-1][0] // 1000 + 1):
        while i < len(ticks) and ticks[i][0] < (sec + 1) * 1000:
            last[ticks[i][1]] = (ticks[i][0], ticks[i][2])
            i += 1
        live = [p for t, p in last.values() if (sec + 1) * 1000 - t <= STALE_S * 1000]
        if len(live) >= 2:
            out[sec] = st.median(live)
    return out


def p_yes(idx: dict[int, float], close_s: int, s: int, t_sec: int, strike: float):
    """P(60 s average of the index before the close is above the strike), or None when the data cannot support it."""
    if t_sec not in idx:
        return None
    window = [idx[x] for x in range(t_sec - SIGMA_WINDOW_S, t_sec) if x in idx and x + 1 in idx]
    changes = [idx[x + 1] - idx[x] for x in range(t_sec - SIGMA_WINDOW_S, t_sec) if x in idx and x + 1 in idx]
    if len(changes) < MIN_CHANGES:
        return None
    sigma = st.pstdev(changes)
    S = idx[t_sec]
    if s >= 60:
        mean, var = S, sigma ** 2 * ((s - 60) + 20)
    else:
        k, m = 60 - s, s
        known = [idx.get(x) for x in range(close_s - 60 + 1, close_s - 60 + 1 + k)]
        known = [v for v in known if v is not None]
        if len(known) < k * 0.8:
            return None
        mean = (sum(known) / len(known) * k + S * m) / 60
        var = sigma ** 2 * m / 3 * (m / 60) ** 2
    if var <= 0:
        return 1.0 if mean > strike else 0.0
    return 1 - phi((strike - mean) / math.sqrt(var))


def trade_for(polls: list[dict], idx: dict[int, float], close_ms: int, result: str, strike: float, stress: float = 1.0):
    """The registered rule on one market: earliest decision second that qualifies, one trade, 1 contract held to settlement. Returns a dict or None."""
    for s in SECONDS:
        poll = next((q for q in polls if q["t"] >= close_ms - s * 1000), None)
        if poll is None:
            continue
        p = p_yes(idx, close_ms // 1000, s, poll["t"] // 1000, strike)
        if p is None:
            continue
        ask, bid = poll["ask"], poll["bid"]
        if p - ask - fee(ask) >= MARGIN and poll["ask_size"] >= MIN_SIZE:
            side, price = "yes", ask
        elif (1 - p) - (1 - bid) - fee(1 - bid) >= MARGIN and poll["bid_size"] >= MIN_SIZE:
            side, price = "no", 1 - bid
        else:
            continue
        f = fee(price) * stress
        return {"s": s, "side": side, "price": price, "p": p, "net": ((1 - price - f) if side == result else -(price + f)), "gap": (p - poll["ask"]) if side == "yes" else ((1 - p) - (1 - poll["bid"]))}
    return None


def _git(*args: str) -> bytes:
    return subprocess.run(["git", *args], capture_output=True, check=True).stdout


def runs() -> dict[str, dict[str, list[dict]]]:
    """run folder -> file name -> rows, for every folder on the branch that has all five files."""
    names = _git("ls-tree", "-r", "--full-tree", "--name-only", BRANCH).decode().split("\n")
    folders = defaultdict(set)
    for n in names:
        parts = n.split("/")
        if len(parts) == 4 and parts[0] == "quotes":
            folders["/".join(parts[:3])].add(parts[3])
    out = {}
    for f, files in sorted(folders.items()):
        if {"quotes.csv.gz", "spot.csv.gz", "results.csv.gz", "coverage.csv.gz", "clock.csv.gz"} <= files:
            out[f] = {n[:-7]: list(csv.DictReader(io.StringIO(gzip.decompress(_git("show", f"{BRANCH}:{f}/{n}")).decode()))) for n in sorted(files)}
    return out


def trades_for_run(run: dict[str, list[dict]]) -> tuple[list[dict], dict]:
    by_t = defaultdict(list)
    for r in run["quotes"]:
        if r["status"] == "active" and r["yes_bid"] and r["yes_ask"]:
            by_t[r["ticker"]].append({"t": int(r["t_recv_ms"]), "bid": float(r["yes_bid"]), "ask": float(r["yes_ask"]), "bid_size": float(r["bid_size"] or 0), "ask_size": float(r["ask_size"] or 0), "strike": float(r["strike"])})
    spot_idx = {a: index_by_second(run["spot"], a) for a in set(ASSET.values())}
    offsets = [abs(float(c["offset_ms"])) for c in run["clock"] if c["offset_ms"] not in ("", None)]
    trades = []
    for res in run["results"]:
        tk, result = res["ticker"], res["result"]
        polls = sorted(by_t.get(tk, []), key=lambda q: q["t"])
        if result not in ("yes", "no") or not polls:
            continue
        close_ms = int(datetime.strptime(res["close_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() * 1000)
        asset = ASSET.get(tk.split("-")[0])
        if asset is None:
            continue
        strike = polls[0]["strike"]
        tr = trade_for(polls, spot_idx[asset], close_ms, result, strike)
        if tr:
            tr2 = trade_for(polls, spot_idx[asset], close_ms, result, strike, STRESS)
            tr.update({"date": res["close_time"][:10], "asset": asset, "ticker": tk, "stress": tr2["net"] if tr2 else tr["net"], "clock_ok": (max(offsets) <= MAX_OFFSET_MS) if offsets else None})
            trades.append(tr)
    cov = {"windows": len(run["results"]), "polls": sum(int(c["polls"]) for c in run["coverage"]), "n429": sum(int(c["n429"]) for c in run["coverage"])}
    return trades, cov


def judge(trades: list[dict]) -> dict:
    n, dates = len(trades), sorted({t["date"] for t in trades})
    if n < 2:
        return {"verdict": "NOT_ENOUGH_DATA", "n": n, "dates": len(dates)}
    m, _, z = cluster_mean_z([(t["date"], t["net"]) for t in trades])
    mid = dates[len(dates) // 2]
    h1 = [t["net"] for t in trades if t["date"] < mid]
    h2 = [t["net"] for t in trades if t["date"] >= mid]
    ms = st.mean(t["stress"] for t in trades)
    assets = defaultdict(list)
    for t in trades:
        assets[t["asset"]].append(t["net"])
    pos = sum(1 for v in assets.values() if st.mean(v) > 0)
    clock_bad = any(t["clock_ok"] is False for t in trades)
    if n < MIN_N or len(dates) < MIN_DAYS:
        verdict = "NOT_ENOUGH_DATA"
    elif m >= MEAN_C and z >= Z_BAR and h1 and h2 and st.mean(h1) > 0 and st.mean(h2) > 0 and ms > 0 and pos >= MIN_ASSETS and not clock_bad:
        verdict = "NOT_YET_FALSIFIED"
    elif m < FALSIFY_C or z < FALSIFY_Z:
        verdict = "FALSIFIED"
    else:
        verdict = "NOT_ENOUGH_DATA"
    return {"verdict": verdict, "n": n, "dates": len(dates), "mean_c": 100 * m, "z": z, "stress_c": 100 * ms, "assets_positive": pos, "assets": {a: (len(v), 100 * st.mean(v)) for a, v in assets.items()},
            "clock_ok": not clock_bad, "mean_model_gap_c": 100 * st.mean(t["gap"] for t in trades)}


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] not in ("look", "read"):
        print(__doc__)
        return
    subprocess.run(["git", "fetch", "-q", "origin", "quote-data"], check=False)
    allr = runs()
    trades, cov = [], {"windows": 0, "polls": 0, "n429": 0}
    for f, run in allr.items():
        t, c = trades_for_run(run)
        trades += t
        for k in cov:
            cov[k] += c[k]
    j = judge(trades)
    if argv[1] == "read":
        if j["n"] < MIN_N or j["dates"] < MIN_DAYS:
            print(f"Refusing the registered read: {j['n']} qualifying trades on {j['dates']} dates (needs {MIN_N} and {MIN_DAYS}).")
            return
        if RESULT.exists():
            print(f"Refusing to run again: {RESULT} exists. Delete it on purpose only for a crash fix, and log that in the README.")
            return
    out = [("REGISTERED READ" if argv[1] == "read" else "INFORMATION LOOK, NOT THE REGISTERED READ (decides nothing)") + f": {len(allr)} runs, coverage {cov}, 429 share {100 * cov['n429'] / max(1, cov['polls']):.1f}%", str(j)]
    if argv[1] == "read":
        RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
