"""WTIW1 (workers/WTIW1_REGISTRATION.md): Kalshi WTI weekly, 10 year yield weekly and USD/JPY daily range ladders against a trailing 20 observation volatility model.
Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE. Nothing here means trade; no promote verb.
    python -m scalper.wtiw1 fetch   (resumable: listings, FRED csv via curl, hourly candles for the registered universe, into data/wtiw1/)
    python -m scalper.wtiw1 run     (the one scored read; refused a second time)
"""
from __future__ import annotations

import json
import math
import re
import subprocess
import sys
import time
from bisect import bisect_right
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from statistics import NormalDist, stdev

from . import api
from .econnew1 import fee, line, pick, pnl, stats
from .paths import DATA_DIR

D = DATA_DIR / "wtiw1"
RESULT = DATA_DIR / "wtiw1_result.txt"
UTC = timezone.utc
# series key -> (kalshi series tickers, fred id, kind)
FAM = {"WTI": (("KXWTIW", "WTIW"), "DCOILWTICO", "log"), "TNOTE": (("KXTNOTEW", "TNOTEW"), "DGS10", "level"), "JPY": (("KXUSDJPY", "USDJPY"), "DEXJPUS", "log")}
GAP, MAX_SPREAD, MAX_AGE_S, NVOL, LOOK_H = 0.08, 0.10, 6 * 3600, 20, 4
UNIV = (0.10, 0.90)
BAR_PF, BAR_Z, MIN_MEAN_C, MIN_TRADES = 1.5, 5.27, 2.0, 150
N_ND = NormalDist()


def fam_of(ticker):
    p = ticker.split("-")[0]
    for k, (ss, _, _) in FAM.items():
        if p in ss:
            return k


def parse_strike(title):
    """('range', lo, hi, tick) | ('above', a, None, tick) | ('below', a, None, tick) | None, from yes_sub_title."""
    t = (title or "").replace(",", "").replace("$", "").replace("%", "")
    nums = re.findall(r"-?\d+(?:\.\d+)?", t)
    if not nums:
        return None
    dec = max((len(n.split(".")[1]) if "." in n else 0) for n in nums)
    tick = 10 ** -dec
    if " to " in t and len(nums) >= 2:
        return ("range", float(nums[0]), float(nums[1]), tick)
    if "or above" in t:
        return ("above", float(nums[0]), None, tick)
    if "or below" in t:
        return ("below", float(nums[0]), None, tick)
    return None


def load_fred(path):
    """{date: value} skipping '.' rows."""
    out = {}
    for ln in open(path).read().splitlines()[1:]:
        d, _, v = ln.partition(",")
        try:
            out[date.fromisoformat(d)] = float(v)
        except ValueError:
            pass
    return out


def vol_and_level(series, look_date, kind):
    """(level date, level, sigma) from the last NVOL+1 observations dated <= look_date; None if fewer than NVOL changes."""
    ds = sorted(d for d in series if d <= look_date)[-(NVOL + 1):]
    if len(ds) < NVOL + 1:
        return None
    xs = [series[d] for d in ds]
    if kind == "log":
        if min(xs) <= 0:
            return None
        ch = [math.log(b / a) for a, b in zip(xs, xs[1:])]
    else:
        ch = [b - a for a, b in zip(xs, xs[1:])]
    return ds[-1], xs[-1], stdev(ch)


def weekdays_between(d0, d1):
    """Weekdays in (d0, d1]."""
    n, d = 0, d0
    while d < d1:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


def fair(kind, x0, sigma, h, strike):
    """Probability of the parsed strike interval (bounds widened by half a tick)."""
    if h <= 0 or sigma <= 0:
        return None
    kindk, a, b, tick = strike
    lo, hi = (a - tick / 2, b + tick / 2) if kindk == "range" else ((a - tick / 2, math.inf) if kindk == "above" else (-math.inf, a + tick / 2))
    sd = sigma * math.sqrt(h)

    def cdf(v):
        if v == math.inf:
            return 1.0
        if v == -math.inf:
            return 0.0
        if kind == "log":
            if v <= 0:
                return 0.0
            return N_ND.cdf((math.log(v) - math.log(x0)) / sd)
        return N_ND.cdf((v - x0) / sd)

    return cdf(hi) - cdf(lo)


def entry(f, bid, ask, gap=GAP):
    if ask - bid > MAX_SPREAD + 1e-9:
        return None
    if f - ask - 0.07 * ask * (1 - ask) >= gap:
        return "yes", ask
    if bid - f - 0.07 * bid * (1 - bid) >= gap:
        return "no", 1 - bid
    return None


def quote(cs, look, opened):
    q = [c for c in cs if opened <= c[0] <= look and c[1] is not None and c[2] is not None and 0 < c[1] < c[2] < 1 and look - c[0] <= MAX_AGE_S]
    return (q[-1][1], q[-1][2]) if q else None


def ts(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def thirds(events):
    ev = sorted(events)
    n = len(ev)
    cut1, cut2 = ev[n // 3], ev[(2 * n) // 3]
    return lambda s: "W1" if s < cut1 else ("W2" if s < cut2 else "W3")


def universe(markets, fred):
    """Strikes with a model fair 0.10..0.90 for events with 20 earlier changes. No price is read."""
    uni, events = {}, {}
    for m in markets:
        fk = fam_of(m["ticker"])
        st = parse_strike(m.get("yes_sub_title"))
        if fk is None or st is None or m.get("result") not in ("yes", "no"):
            continue
        opened, closed = ts(m["open_time"]), ts(m["close_time"])
        look = opened + LOOK_H * 3600
        ldate = datetime.fromtimestamp(look, UTC).date()
        vl = vol_and_level(fred[fk], ldate, FAM[fk][2])
        if vl is None:
            continue
        d0, x0, sig = vl
        h = weekdays_between(d0, datetime.fromtimestamp(closed, UTC).date())
        f = fair(FAM[fk][2], x0, sig, h, st)
        ev = m["event_ticker"].split("-", 1)[1]
        events[(fk, ev)] = datetime.fromtimestamp(opened, UTC).date()
        if f is not None and UNIV[0] <= f <= UNIV[1]:
            uni[m["ticker"]] = dict(fam=fk, event=m["event_ticker"], ev=ev, fair=f, res=m["result"], look=look, opened=opened, src=m.get("src", "hist"), series=m["event_ticker"].split("-")[0], h=h, d0=d0.isoformat())
    return uni, events


# ---------------------------------------------------------------- data
def fetch_fred():
    D.mkdir(parents=True, exist_ok=True)
    for fk, (_, fid, _) in FAM.items():
        p = D / f"{fid}.csv"
        if not p.exists() or p.stat().st_size < 1000:
            subprocess.run(["curl", "-sS", "-m", "60", "-o", str(p), f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={fid}&cosd=2022-01-01"], check=True)


def load_all_fred():
    return {fk: load_fred(D / f"{fid}.csv") for fk, (_, fid, _) in FAM.items()}


def fetch():
    fetch_fred()
    fred = load_all_fred()
    markets = json.loads((D / "markets.json").read_text())
    uni, _ = universe(markets, fred)
    (D / "universe.json").write_text(json.dumps(uni))
    print("universe strikes", len(uni), {k: sum(1 for m in uni.values() if m["fam"] == k) for k in FAM}, flush=True)
    cp = D / "candles.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}
    for i, (tk, m) in enumerate(uni.items()):
        if tk in have:
            continue
        try:
            path = f"/historical/markets/{tk}/candlesticks" if m["src"] == "hist" else f"/series/{m['series']}/markets/{tk}/candlesticks"
            d = api._get(path, {"start_ts": m["look"] - 6 * 3600, "end_ts": m["look"], "period_interval": 60})
            have[tk] = [(c["end_period_ts"], pick(c.get("yes_bid")), pick(c.get("yes_ask"))) for c in d.get("candlesticks", [])]
        except Exception as e:
            print("skip", tk, e)
            continue
        if i % 50 == 0:
            cp.write_text(json.dumps(have))
            print(i, len(uni), flush=True)
        time.sleep(0.35)
    cp.write_text(json.dumps(have))
    print("done", len(have), flush=True)


# ---------------------------------------------------------------- run
def collect(uni, cands, win, mult=1.0, gap=GAP):
    rows = defaultdict(list)
    for tk, m in uni.items():
        q = quote(cands.get(tk, []), m["look"], m["opened"])
        if not q:
            continue
        e = entry(m["fair"], q[0], q[1], gap)
        if e:
            rows[win(m["ev"])].append((m["event"], pnl(e[0], e[1], m["res"], mult)))
    return rows


def brier(uni, cands):
    mod = mkt = n = 0
    for tk, m in uni.items():
        q = quote(cands.get(tk, []), m["look"], m["opened"])
        if not q or q[1] - q[0] > MAX_SPREAD + 1e-9:
            continue
        y = 1.0 if m["res"] == "yes" else 0.0
        mod += (m["fair"] - y) ** 2
        mkt += ((q[0] + q[1]) / 2 - y) ** 2
        n += 1
    return (mod / n, mkt / n, n) if n else (None, None, 0)


def run_one(fk, uni, cands, events):
    u = {t: m for t, m in uni.items() if m["fam"] == fk}
    out = [f"== {fk} == predicted events {sum(1 for k in events if k[0] == fk)}, universe strikes {len(u)}, with candles {sum(1 for t in u if t in cands)}"]
    evs = sorted((d, ev) for (f, ev), d in events.items() if f == fk)
    if len(evs) < 3:
        return "NOT_RUNNABLE", out + ["too few events"], None
    cut1, cut2 = evs[len(evs) // 3][0], evs[(2 * len(evs)) // 3][0]
    dmap = {ev: d for d, ev in evs}
    win = lambda ev: "W1" if dmap[ev] < cut1 else ("W2" if dmap[ev] < cut2 else "W3")
    mb, kb, nb = brier(u, cands)
    if nb:
        out.append(f"Brier model {mb:.4f} market mid {kb:.4f} (strikes {nb})")
    r1, r12 = collect(u, cands, win), collect(u, cands, win, 1.2)
    S, S12, ok = {}, {}, True
    for w in ("W1", "W2"):
        S[w], S12[w] = stats(r1[w]), stats(r12[w])
        out.append(line(w, S[w]) + f" | fees x1.2 PF {S12[w]['pf']:.2f}")
        ok = ok and S[w]["pf"] >= BAR_PF
    ntr = sum(S[w]["n"] for w in S)
    pooled = [x for w in ("W1", "W2") for x in r1[w]]
    if ok and nb and mb < kb:
        S["W3"], S12["W3"] = stats(r1["W3"]), stats(r12["W3"])
        out.append(line("W3 (holdout, read because W1 and W2 passed)", S["W3"]) + f" | fees x1.2 PF {S12['W3']['pf']:.2f}")
        pooled += r1["W3"]
        ntr += S["W3"]["n"]
    else:
        out.append("W3 holdout NOT read")
    ps = stats(pooled)
    out.append(line("pooled read windows", ps))
    for g in (0.05, 0.12):
        rr = collect(u, cands, win, 1.0, g)
        out.append(f"info gap {g}: " + " ".join(f"{w} n {len(rr[w])} PF {stats(rr[w])['pf']:.2f}" for w in ("W1", "W2")))
    why = []
    if not nb:
        return "NOT_RUNNABLE", out + ["no candles with a quote"], ps
    if ntr < MIN_TRADES:
        verdict, why = "NOT_ENOUGH_DATA", [f"{ntr} trades under {MIN_TRADES}"]
        if not (mb < kb):
            why.append("model Brier not better than the market (reported, not a verdict under the count rule)")
    else:
        if any(S[w]["pf"] < BAR_PF for w in S):
            why.append("PF under 1.5 in a window")
        if any(S12[w]["pf"] < 1.0 for w in S12):
            why.append("not positive at fees x1.2")
        if not (mb < kb):
            why.append("model Brier not better than the market")
        if ps["z"] < BAR_Z:
            why.append(f"pooled z {ps['z']:.2f} under {BAR_Z}")
        if ps["mean"] < MIN_MEAN_C:
            why.append("pooled mean under 2c")
        verdict = "FALSIFIED" if why else "NOT_YET_FALSIFIED"
    out.append(f"VERDICT {fk}: {verdict}: " + "; ".join(why))
    return verdict, out, ps


def main(argv):
    if argv and argv[0] == "fetch":
        return fetch()
    if RESULT.exists():
        print("refused: the one scored read has been run; see", RESULT)
        return
    markets = json.loads((D / "markets.json").read_text())
    fred = load_all_fred()
    uni, events = universe(markets, fred)
    cands = json.loads((D / "candles.json").read_text())
    out = [f"WTIW1 run {datetime.now(UTC).isoformat()} N=728706 z bar {BAR_Z} cost 7% x C x p x (1-p) rounded up, C=10, taker at the ask"]
    for fk in FAM:
        v, o, _ = run_one(fk, uni, cands, events)
        out += o
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1:])
