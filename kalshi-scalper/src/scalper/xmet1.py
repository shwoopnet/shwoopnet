"""XMET1 (workers/XMET1_REGISTRATION.md): gold's Kalshi 15 minute mid move (T-360 s to T-180 s, relative trigger) against the cheap side of
silver, copper, platinum and palladium 15 minute markets in the same direction, held to settlement. Research only; no promote verb.
    python -m scalper.xmet1 fetch   (resumable; settled markets and Kalshi 1 minute candles into $XMET1_CACHE)
    python -m scalper.xmet1 run     (the one scored read; refused a second time)
Never trades gold, Bitcoin, Ethereum or Dogecoin: gold is read as the signal only.
"""
from __future__ import annotations

import calendar
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from . import api, streaks
from .lag15 import fee, pnl as _pnl_unused, stats, line, thirds, pick  # noqa: F401  (shared cost model and statistics)

UTC = timezone.utc
CACHE = Path(os.environ.get("XMET1_CACHE", "/tmp/xmet1_cache"))
RESULT = CACHE / "xmet1_result.txt"
LEADER = "KXGOLD15M"
METALS = ["KXSILVER15M", "KXCOPPER15M", "KXPLATINUM15M", "KXPALLADIUM15M"]
NEVER = {"KXGOLD15M", "KXBTC15M", "KXETH15M", "KXDOGE15M"}
SIG_START, LOOK_S = 360, 180
REL = 1.0
SD_MIN, SD_BACK, SD_NEED = 0.005, 96, 48
BAND = (0.05, 0.50)
MAX_SPREAD, QUOTE_AGE_S, VOL_WINDOW_S, MIN_VOL = 0.10, 120, 300, 10.0
C = 10
BAR_PF, BAR_Z, MIN_MEAN_C, MIN_TRADES, MIN_GAP_C = 1.5, 5.27, 2.0, 150, 2.0
NRUN = 728722


def ts(s: str) -> int:
    return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))


def quote_at(candles, t):
    """candles: (end_ts, bid, ask, vol). Latest two sided quote ending at or before t, not older than QUOTE_AGE_S."""
    best = None
    for c in candles:
        if c[0] <= t and c[1] is not None and c[2] is not None and 0 < c[1] < c[2] < 1 and t - c[0] <= QUOTE_AGE_S:
            if best is None or c[0] > best[0]:
                best = c
    return best


def mid_at(candles, t):
    q = quote_at(candles, t)
    return None if q is None else (q[1] + q[2]) / 2


def chg(candles, close):
    a, b = mid_at(candles, close - SIG_START), mid_at(candles, close - LOOK_S)
    return None if a is None or b is None else b - a


def trailing_sd(gold_chg: dict, closes_sorted: list, i: int):
    """Population SD of chg over the previous SD_BACK gold windows (closes strictly before closes_sorted[i], within 24 hours)."""
    t = closes_sorted[i]
    xs = [gold_chg[c] for c in closes_sorted[max(0, i - SD_BACK):i] if gold_chg.get(c) is not None and t - c <= SD_BACK * 900]
    if len(xs) < SD_NEED:
        return None
    m = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))
    return sd if sd >= SD_MIN else None


def volume_ok(candles, look):
    return sum((c[3] or 0.0) for c in candles if look - VOL_WINDOW_S < c[0] <= look) >= MIN_VOL


def decide(series, direction, candles, close, against=False):
    """direction +1 gold up, -1 gold down. Returns None (not eligible) or dict(side, price) / dict(side None) when eligible but the
    chosen side is not the cheap side. Only candles at or before the look are used."""
    if series in NEVER:
        raise ValueError("never trade " + series)
    look = close - LOOK_S
    q = quote_at(candles, look)
    if q is None or q[2] - q[1] > MAX_SPREAD + 1e-9 or not volume_ok(candles, look):
        return None
    bid, ask = q[1], q[2]
    up = direction > 0
    if against:
        up = not up
    side, price = ("yes", ask) if up else ("no", 1 - bid)
    if not (BAND[0] - 1e-9 <= price <= BAND[1] + 1e-9):
        return {"side": None, "price": None}
    return {"side": side, "price": price}


def pnl(side, price, res, mult=1.0):
    win = (res == "yes") == (side == "yes")
    return ((1.0 if win else 0.0) - price - fee(price, mult)) * 100


def payoff(vals):
    w = [x for x in vals if x > 0]
    l = [-x for x in vals if x < 0]
    return (sum(w) / len(w)) / (sum(l) / len(l)) if w and l else float("nan")


# ---------------------------------------------------------------- fetch
def fetch() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    mp = CACHE / "markets.json"
    markets = json.loads(mp.read_text()) if mp.exists() else {}
    if not markets:
        for s in [LEADER] + METALS:
            for m in api.settled_markets(s, 0, 2**31 - 1):
                if m.get("result") in ("yes", "no"):
                    markets[m["ticker"]] = {"s": s, "close": ts(m["close_time"]), "res": m["result"], "vol": api.f(m.get("volume_fp") or m.get("volume"))}
        mp.write_text(json.dumps(markets)); print(len(markets), "markets", flush=True)
    cp = CACHE / "candles.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}
    by = defaultdict(list)
    for tk, m in markets.items():
        if tk not in have:
            by[m["close"]].append(tk)
    closes = sorted(by)
    groups = [closes[i:i + 4] for i in range(0, len(closes), 4)]
    pause = 0.3
    for i, g in enumerate(groups):
        tks = [t for c in g for t in by[c]]
        lo, hi = g[0] - 480, g[-1] - LOOK_S
        for attempt in range(12):
            try:
                req = urllib.request.Request(api.BASES[1] + "/markets/candlesticks?" + urllib.parse.urlencode({"market_tickers": ",".join(tks), "start_ts": lo, "end_ts": hi, "period_interval": 1}))
                d = json.load(urllib.request.urlopen(req, timeout=30))
                got = {x.get("market_ticker") or x.get("ticker"): x for x in d.get("markets", [])}
                for tk in tks:
                    close = markets[tk]["close"]
                    cs = (got.get(tk) or {}).get("candlesticks", [])
                    have[tk] = [(c["end_period_ts"], pick(c.get("yes_bid")), pick(c.get("yes_ask")), api.f(c.get("volume_fp") or c.get("volume"))) for c in cs if close - 900 < c["end_period_ts"] <= close - LOOK_S]
                pause = max(0.25, pause * 0.9)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    pause = min(pause * 1.3, 1.5); time.sleep(1 + attempt)
                else:
                    time.sleep(1 + attempt)
            except Exception:
                time.sleep(1 + attempt)
        else:
            print("skip", g[0], flush=True)
        if i % 50 == 0:
            cp.write_text(json.dumps(have)); print("candles", i, len(groups), "pause", round(pause, 2), flush=True)
        time.sleep(pause)
    cp.write_text(json.dumps(have)); print("done", flush=True)


# ---------------------------------------------------------------- run
def build(markets, cands):
    """Trade rows for H and M: (series, close, day, direction, side, price, res) per eligible triggered metal window."""
    gold = {m["close"]: tk for tk, m in markets.items() if m["s"] == LEADER}
    gc = {c: chg([tuple(x) for x in cands.get(tk, [])], c) for c, tk in gold.items()}
    cl = sorted(gold)
    trig = {}
    for i, c in enumerate(cl):
        if gc[c] is None:
            continue
        sd = trailing_sd(gc, cl, i)
        if sd is not None and abs(gc[c]) >= REL * sd and gc[c] != 0:
            trig[c] = 1 if gc[c] > 0 else -1
    rows = []
    for tk, m in markets.items():
        if m["s"] not in METALS or m["close"] not in trig:
            continue
        cs = [tuple(x) for x in cands.get(tk, [])]
        h, mm = decide(m["s"], trig[m["close"]], cs, m["close"]), decide(m["s"], trig[m["close"]], cs, m["close"], against=True)
        if h is None:
            continue
        day = datetime.fromtimestamp(m["close"], UTC).strftime("%Y-%m-%d")
        rows.append({"s": m["s"], "close": m["close"], "day": day, "H": h, "M": mm, "res": m["res"]})
    return rows, len(cl), len(trig)


def run_arm(rows, key, win, mult=1.0):
    tr = {w: [] for w in ("W1", "W2", "W3")}
    for r in rows:
        a = r[key]
        if a and a["side"]:
            tr[win[r["day"]]].append((r["day"], pnl(a["side"], a["price"], r["res"], mult), r))
    return tr


def main(argv):
    if argv and argv[0] == "fetch":
        return fetch()
    if RESULT.exists():
        print("refused: the one scored read has been run; see", RESULT); return
    markets = json.loads((CACHE / "markets.json").read_text())
    cands = json.loads((CACHE / "candles.json").read_text())
    rows, ngold, ntrig = build(markets, cands)
    out = [f"XMET1 run {datetime.now(UTC).isoformat()} N={NRUN} z bar {BAR_Z} cost: fee 7% x C x p x (1-p) rounded up, C={C}, taker at the ask"]
    out.append(f"gold windows {ngold}, triggered {ntrig}, eligible metal windows (quote rule passed) {len(rows)}")
    win = thirds([r["day"] for r in rows])
    out.append(f"eligible dates {len(set(win))}: W1 {sum(1 for w in set(win.values()) if w=='W1') and sum(1 for d,w in win.items() if w=='W1')}, W2 {sum(1 for d,w in win.items() if w=='W2')}, W3 {sum(1 for d,w in win.items() if w=='W3')}")
    res = {}
    for key, name in (("H", "H hypothesis (gold direction)"), ("M", "M control (against gold)")):
        t1, t12 = run_arm(rows, key, win), run_arm(rows, key, win, 1.2)
        S = {w: stats([(d, x) for d, x, _ in t1[w]]) for w in t1}
        S12 = {w: stats([(d, x) for d, x, _ in t12[w]]) for w in t12}
        for w in ("W1", "W2"):
            out.append(f"{name} " + line(w, S[w]) + f" | fees x1.2 mean {S12[w]['mean']:+.2f}c")
        ok = S["W1"]["pf"] >= BAR_PF and S["W2"]["pf"] >= BAR_PF
        w3 = ok and key == "H"
        read = ("W1", "W2", "W3") if w3 else ("W1", "W2")
        out.append(f"{name} W3 holdout: " + ("read because W1 and W2 passed " + line("W3", S["W3"]) if w3 else "not read"))
        pooled = [(d, x, r) for w in read for d, x, r in t1[w]]
        P = stats([(d, x) for d, x, _ in pooled])
        res[key] = (P, pooled, S, S12, w3)
        out.append(f"{name} " + line("pooled (windows read)", P))
        for s in METALS:
            sub = [x for d, x, r in pooled if r["s"] == s]
            out.append(f"   {s}: n {len(sub)} win rate {sum(1 for x in sub if x>0)/len(sub):.3f} PF {(sum(x for x in sub if x>0)/max(1e-9,-sum(x for x in sub if x<0))):.2f} mean {sum(sub)/len(sub):+.2f}c" if sub else f"   {s}: n 0")
    P, pooled, S, S12, w3 = res["H"]
    vals = [x for _, x, _ in sorted(pooled, key=lambda z: z[2]["close"])]
    wr = sum(1 for x in vals if x > 0) / len(vals) if vals else 0.0
    out.append(f"H pooled win rate {wr:.3f}, payoff ratio {payoff(vals):.2f}, PF {P['pf']:.2f}, mean {P['mean']:+.2f}c, n {P['n']}")
    if vals:
        es = streaks.empirical_streaks([x > 0 for x in vals])
        d = streaks.longest_losing_run_distribution(wr, 100)
        out.append(f"STREAKS (chronological, p=observed): longest losing run {es['longest_losing_run']} of n {es['n']}; in 100 trades p95 {d['p95']} p99 {d['p99']}; chance of >=1 ten-loss run in 100 trades {streaks.prob_run_at_least(10, wr, 100)*100:.0f}%")
    why = []
    if P["n"] < MIN_TRADES:
        word = "NOT_ENOUGH_DATA"; why.append(f"trades {P['n']} under {MIN_TRADES}")
    else:
        for w in (("W1", "W2", "W3") if w3 else ("W1", "W2")):
            if S[w]["pf"] < BAR_PF: why.append(f"{w} PF {S[w]['pf']:.2f} under {BAR_PF}")
            if S12[w]["mean"] <= 0: why.append(f"{w} not positive at fees x1.2")
        if P["mean"] < MIN_MEAN_C: why.append(f"pooled mean {P['mean']:+.2f}c under {MIN_MEAN_C}")
        Pm = res["M"][0]
        if P["mean"] - Pm["mean"] < MIN_GAP_C: why.append(f"H beats control by {P['mean']-Pm['mean']:+.2f}c, under {MIN_GAP_C}")
        word = "FALSIFIED" if why else ("NOT_YET_FALSIFIED" if P["z"] < BAR_Z else "NOT_YET_FALSIFIED")
        if not why and P["z"] < BAR_Z: why.append(f"z {P['z']:+.2f} under {BAR_Z}: not a pass")
    out.append(f"VERDICT {word}" + (" | " + "; ".join(why) if why else ""))
    txt = "\n".join(out)
    print(txt)
    CACHE.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(txt + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
