"""FALS4: falsifier for GEN6's open interest core (research only).

Written from the raw candles, without reading gen6.py. Rule under test:
Bitcoin 15 minute market, signal candle ending 180 s before the close, cheap
side (ask 5c to 50c, YES first), open interest up more than 86,300 contracts
from the candle ending 360 s before the close to the signal candle, fill at
the next candle's closing ask, held to settlement.

Run: PYTHONPATH=src python -m scalper.fals4  (prints every check)
"""
import math
import random
import sqlite3
import statistics
from collections import defaultdict
from datetime import datetime, timezone

from scalper.paths import DATA_DIR

FILES = ["l1b.sqlite", "book.sqlite", "fresh.sqlite"]
SERIES = "KXBTC15M"
FORWARD_TS = int(datetime(2026, 10, 28, tzinfo=timezone.utc).timestamp())
DISC_END = int(datetime(2026, 9, 21, tzinfo=timezone.utc).timestamp())
START = int(datetime(2026, 8, 6, tzinfo=timezone.utc).timestamp())
THRESH = 86299.56000000001
LO, HI = 0.05, 0.50


def day(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def load():
    """{ticker: dict(close, result, c={offset: row})}, close before forward."""
    win = {}
    for f in FILES:
        con = sqlite3.connect(DATA_DIR / f)
        for t, close, res in con.execute(
                "select ticker, close_ts, result from market where series=? "
                "and close_ts>=? and close_ts<? and result in ('yes','no')",
                (SERIES, START, FORWARD_TS)):
            if t in win:
                continue
            win[t] = {"close": close, "result": res, "c": {}, "file": f}
        for (t, end, bid, ask, vol, oi) in con.execute(
                "select ticker, end_ts, bid_c, ask_c, volume, oi from candle "
                "where series=?", (SERIES,)):
            w = win.get(t)
            if w is None or w["file"] != f:
                continue
            w["c"][end - w["close"]] = (bid, ask, vol, oi)
    return win


def fee(p, c=10, mult=1.0):
    return math.ceil(round(0.07 * c * p * (1 - p) * mult * 100, 9)) / 100


def side_ask(row, side):
    bid, ask = row[0], row[1]
    if side == "yes":
        return ask
    return None if bid is None else round(1 - bid, 6)


def side_bid(row, side):
    bid, ask = row[0], row[1]
    if side == "yes":
        return bid
    return None if ask is None else round(1 - ask, 6)


def cheap_side(row):
    for s in ("yes", "no"):
        a = side_ask(row, s)
        if a is not None and LO <= a <= HI:
            return s
    return None


def net(fill, won, c=10, mult=1.0):
    """Net dollars per order of c contracts."""
    return c * ((1.0 if won else 0.0) - fill) - fee(fill, c, mult)


def pf(nets):
    g = sum(x for x in nets if x > 0)
    l = -sum(x for x in nets if x < 0)
    return float("inf") if l == 0 else g / l


def dayz(trades):
    """Day-clustered z of mean net: per-day sums, t on days."""
    d = defaultdict(float)
    for t in trades:
        d[t["day"]] += t["net"]
    v = list(d.values())
    if len(v) < 3:
        return float("nan")
    sd = statistics.stdev(v)
    return statistics.mean(v) / (sd / math.sqrt(len(v))) if sd else float("nan")


def stage(close):
    return "disc" if close < DISC_END else "val"


def signal(w, L=180, back=180):
    """Features at the signal candle, or None when a needed candle is missing."""
    c = w["c"]
    s, p = c.get(-L), c.get(-L - back)
    if s is None or p is None or s[3] is None or p[3] is None:
        return None
    return {"doi": s[3] - p[3], "row": s}


def trades(win, *, thresh=THRESH, thr_fn=None, side_mode="cheap",
           fill_mode="next", fill_add=0.0, c=10, mult=1.0, fill_band=False,
           cond=None):
    out = []
    for t, w in win.items():
        sg = signal(w)
        if sg is None:
            continue
        th = thr_fn(w) if thr_fn else thresh
        if th is None:
            continue
        if cond is None:
            if not sg["doi"] > th:
                continue
        elif not cond(w, sg):
            continue
        cs = cheap_side(sg["row"])
        if cs is None:
            continue
        side = cs if side_mode == "cheap" else ("no" if cs == "yes" else "yes")
        if fill_mode == "next":
            fr = w["c"].get(-120)
        elif fill_mode == "later":
            fr = w["c"].get(-60)
        else:
            fr = sg["row"]
        if fr is None:
            continue
        fill = side_ask(fr, side)
        if fill is None or fill >= 1 or fill <= 0:
            continue
        if fill_band and not (LO <= fill <= HI):
            continue
        fill = min(0.99, round(fill + fill_add, 6))
        won = w["result"] == side
        out.append({"t": t, "close": w["close"], "day": day(w["close"]),
                    "side": side, "fill": fill, "won": won,
                    "net": net(fill, won, c, mult),
                    "fvol": fr[2], "svol": sg["row"][2], "doi": sg["doi"],
                    "stage": stage(w["close"])})
    out.sort(key=lambda x: x["close"])
    return out


def summ(tr, label):
    parts = []
    for st in ("disc", "val"):
        x = [t for t in tr if t["stage"] == st]
        n = [t["net"] for t in x]
        if not x:
            parts.append(f"{st} n 0")
            continue
        parts.append(f"{st} n {len(x)} PF {pf(n):.2f} win {sum(t['won'] for t in x)/len(x):.1%} "
                     f"fill {statistics.mean(t['fill'] for t in x):.3f} z {dayz(x):.2f}")
    print(f"{label:38s} | " + " | ".join(parts))
    return tr


def main():
    win = load()
    print("windows", len(win), "disc", sum(stage(w["close"]) == "disc" for w in win.values()),
          "val", sum(stage(w["close"]) == "val" for w in win.values()))
    # ---- Check 1
    print("\n## Check 1")
    core = summ(trades(win), "core C=10 next fill")
    yes = [t for t in core if t["side"] == "yes"]
    summ(yes, "  YES only")
    summ([t for t in core if t["side"] == "no"], "  NO only")
    # ---- Check 2
    print("\n## Check 2")
    # (a) oi meaning: post-close candle oi vs close candle oi; oi vs cumulative volume
    same = diff = 0
    incr = []
    for w in win.values():
        c = w["c"]
        if 0 in c and 60 in c and c[0][3] is not None and c[60][3] is not None:
            if abs(c[0][3] - c[60][3]) < 1e-6:
                same += 1
            else:
                diff += 1
        for off in range(-780, 1, 60):
            a, b = c.get(off - 60), c.get(off)
            if a and b and a[3] is not None and b[3] is not None and b[2] is not None:
                incr.append((b[3] - a[3], b[2]))
    print(f"post-close (+60) oi equals close-candle oi: {same} of {same+diff}")
    viol = sum(1 for d, v in incr if abs(d) > v + 1e-6)
    print(f"|oi change| over one candle greater than that candle's volume: {viol} of {len(incr)}")
    fc = [w["c"][-840] for w in win.values() if -840 in w["c"] and w["c"][-840][3] is not None]
    print(f"first candle (-840): oi <= volume in {sum(1 for r in fc if r[3] <= r[2] + 1e-6)} of {len(fc)}")
    # (b) latency stress
    summ(trades(win, fill_mode="later"), "latency: fill at candle -60")
    # (c) missing candles
    miss = defaultdict(lambda: [0, 0])
    for w in win.values():
        ok = all(o in w["c"] and w["c"][o][3] is not None for o in (-360, -180)) and -120 in w["c"]
        k = "complete" if ok else "gap"
        miss[k][0] += 1
        miss[k][1] += w["result"] == "yes"
    for k, (n, y) in miss.items():
        print(f"{k}: {n} windows, YES {y/n:.1%}")
    bad = 0
    for t, w in win.items():
        dt = datetime.fromtimestamp(w["close"], timezone.utc)
        from zoneinfo import ZoneInfo
        et = dt.astimezone(ZoneInfo("America/New_York"))
        code = et.strftime("%y%b%d%H%M").upper()
        if t.split("-")[1] != code:
            bad += 1
    print(f"ticker time part != close_ts (ET): {bad} of {len(win)}")
    # (d) fill band
    summ(trades(win, fill_band=True), "also fill ask in 5c-50c")
    # ---- Check 3
    print("\n## Check 3")
    summ(trades(win, c=1), "C=1")
    summ(trades(win, mult=1.2), "C=10 fees x1.2")
    summ(trades(win, fill_mode="signal", fill_add=0.01), "signal ask +1c")
    summ(trades(win, fill_mode="signal", fill_add=0.02), "signal ask +2c")
    summ(trades(win, fill_mode="signal"), "(info) signal ask +0")
    # ---- Check 4
    print("\n## Check 4")
    summ([t for t in core if t["fill"] >= 0.05], "fills >= 5c only")
    for st in ("disc", "val"):
        x = [t for t in core if t["stage"] == st]
        lo = sum(1 for t in x if t["fill"] < 0.05)
        lv = sum(1 for t in x if (t["fvol"] or 0) < 10)
        z0 = sum(1 for t in x if (t["fvol"] or 0) == 0 or (t["svol"] or 0) == 0)
        print(f"{st}: fills < 5c {lo} of {len(x)}; fill candle volume < 10: {lv}; zero-volume signal or fill: {z0}")
    # ---- Check 5
    print("\n## Check 5")
    doi_by_day = defaultdict(list)
    for w in win.values():
        sg = signal(w)
        if sg:
            doi_by_day[day(w["close"])].append(sg["doi"])
    days = sorted(doi_by_day)
    cache = {}

    def thr_fn(w):
        d = day(w["close"])
        if d in cache:
            return cache[d]
        d0 = datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()
        prev = [x for x in days if d0 - 30 * 86400 <= datetime.strptime(x, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() < d0]
        if len(prev) < 10:
            cache[d] = None
        else:
            v = sorted(sum((doi_by_day[x] for x in prev), []))
            cache[d] = v[int(0.9 * (len(v) - 1))]
        return cache[d]
    drift = summ(trades(win, thr_fn=thr_fn), "trailing 30d p90 threshold")
    th = [cache[d] for d in sorted(cache) if cache[d] is not None]
    print(f"threshold first {th[0]:.0f}, median {statistics.median(th):.0f}, last {th[-1]:.0f}")
    print(f"first day with a threshold: {min(d for d in cache if cache[d] is not None)}")
    # ---- Check 6
    print("\n## Check 6")
    b0 = START
    k = 0
    while b0 < FORWARD_TS:
        b1 = min(b0 + 8 * 86400, FORWARD_TS)
        x = [t for t in core if b0 <= t["close"] < b1]
        n = [t["net"] for t in x]
        print(f"block {k} {day(b0)}..{day(b1-1)}: n {len(x)} PF {pf(n):.2f} net ${sum(n):.2f}")
        b0, k = b1, k + 1
    run = best = 0
    for t in core:
        run = run + 1 if t["net"] < 0 else 0
        best = max(best, run)
    eq = peak = 0.0
    peak_day = core[0]["day"]
    longest = 0
    for t in core:
        eq += t["net"]
        if eq > peak:
            peak, peak_day = eq, t["day"]
        else:
            gap = (datetime.strptime(t["day"], "%Y-%m-%d") - datetime.strptime(peak_day, "%Y-%m-%d")).days
            longest = max(longest, gap)
    print(f"longest losing run {best} trades; longest days without a new equity high {longest}; total net ${eq:.2f}")
    # ---- Check 7
    print("\n## Check 7")
    summ(trades(win, side_mode="fav"), "favourite, same windows")
    # ---- Check 8
    print("\n## Check 8")
    nd = sum(1 for t in core if t["stage"] == "disc")

    def vol3(w):
        c = w["c"]
        v = [c.get(o) for o in (-300, -240, -180)]
        if any(r is None or r[2] is None for r in v):
            return None
        return sum(r[2] for r in v)

    def move(w):
        c = w["c"]
        a, b = c.get(-360), c.get(-180)
        if a is None or b is None or None in (a[0], a[1], b[0], b[1]):
            return None
        return abs((b[0] + b[1]) / 2 - (a[0] + a[1]) / 2)

    base = trades(win, cond=lambda w, sg: True)
    summ(base, "base: cheap side, no condition")
    for name, fn in (("vol3", vol3), ("move", move)):
        vals = sorted((fn(win[t["t"]]) for t in base if t["stage"] == "disc" and fn(win[t["t"]]) is not None), reverse=True)
        q = vals[nd - 1]
        summ(trades(win, cond=lambda w, sg, fn=fn, q=q: (fn(w) or -1) >= q), f"{name} >= {q:.3f} (disc matched)")
        x = trades(win, cond=lambda w, sg, fn=fn, q=q: (fn(w) or -1) >= q)
        cs = set(t["t"] for t in core)
        for st in ("disc", "val"):
            a = [t for t in x if t["stage"] == st]
            print(f"   {st}: overlap with core {sum(t['t'] in cs for t in a)} of {len(a)}")
    # hour mix resampling
    rng = random.Random(4)
    for st in ("disc", "val"):
        cx = [t for t in core if t["stage"] == st]
        hours = [datetime.fromtimestamp(t["close"] - 180, timezone.utc).hour for t in cx]
        pool = defaultdict(list)
        for t in base:
            if t["stage"] == st:
                pool[datetime.fromtimestamp(t["close"] - 180, timezone.utc).hour].append(t["net"])
        pfs = []
        for _ in range(2000):
            pfs.append(pf([rng.choice(pool[h]) for h in hours]))
        pfs.sort()
        print(f"hour-mix resample {st}: median PF {pfs[1000]:.2f}, 95th {pfs[1900]:.2f} (core {pf([t['net'] for t in cx]):.2f})")
    # doi given volume
    v_all = sorted(vol3(win[t["t"]]) for t in base if t["stage"] == "disc" and vol3(win[t["t"]]) is not None)
    med = v_all[len(v_all) // 2]
    summ([t for t in core if (vol3(win[t["t"]]) or 0) < med], f"core, vol3 below disc median {med:.0f}")
    summ([t for t in core if (vol3(win[t["t"]]) or 0) >= med], "core, vol3 at or above median")
    vq = sorted((vol3(win[t["t"]]) for t in base if t["stage"] == "disc" and vol3(win[t["t"]]) is not None), reverse=True)[nd - 1]
    summ([t for t in base if (vol3(win[t["t"]]) or -1) >= vq and not t["doi"] > THRESH],
         "info: high vol3, doi NOT above")
    # corr doi vs vol3
    pairs = [(t["doi"], vol3(win[t["t"]])) for t in base if vol3(win[t["t"]]) is not None]
    xs, ys = zip(*pairs)
    print(f"corr(doi, vol3) over base: {statistics.correlation(xs, ys):.2f}")


if __name__ == "__main__":
    main()
