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
    print("run is added after the tape is downloaded (the rules are in the README)")


if __name__ == "__main__":
    main(sys.argv)
