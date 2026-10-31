"""WXNEW1 (workers/WXNEW1_REGISTRATION.md): hourly temperature ladders against a persistence-plus-trend nowcast from public ASOS data.
Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA.
Usage: python -m scalper.wxnew1 fetch ; python -m scalper.wxnew1 run   (run is refused a second time)
"""
from __future__ import annotations

import bisect
import calendar
import csv
import io
import json
import math
import sys
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from . import api
from .paths import DATA_DIR

CACHE = DATA_DIR / "wxnew1_cache.json"
RESULT = DATA_DIR / "wxnew1_result.txt"
CUT = calendar.timegm((2026, 10, 31, 0, 0, 0))
SYN_B = [("discovery", 0, calendar.timegm((2026, 10, 4, 0, 0, 0)), 100),
         ("validation", calendar.timegm((2026, 10, 4, 0, 0, 0)), calendar.timegm((2026, 10, 19, 0, 0, 0)), 50),
         ("holdout", calendar.timegm((2026, 10, 19, 0, 0, 0)), CUT, 30)]
TWC_B = [("discovery", 0, calendar.timegm((2026, 9, 1, 0, 0, 0)), 100),
         ("validation", calendar.timegm((2026, 9, 1, 0, 0, 0)), calendar.timegm((2026, 9, 6, 0, 0, 0)), 50),
         ("holdout", calendar.timegm((2026, 9, 6, 0, 0, 0)), CUT, 30)]
TRIES = {
    "WXH-SYN": dict(series=["KXTEMPCHIHS", "KXTEMPMIAH", "KXTEMPNYCHS", "KXTEMPLAXHS"], twc=False, bounds=SYN_B,
                    stations={"KXTEMPCHIHS": ["ORD", "MDW"], "KXTEMPMIAH": ["MIA", "OPF"], "KXTEMPNYCHS": ["NYC", "LGA"], "KXTEMPLAXHS": ["LAX", "SMO"]}),
    "WXH-TWC": dict(series=["KXTEMPNYCH", "KXTEMPLAXH", "KXTEMPCHIH", "KXTEMPAUSH", "KXTEMPDCH"], twc=True, bounds=TWC_B,
                    stations={"KXTEMPNYCH": ["NYC"], "KXTEMPLAXH": ["LAX"], "KXTEMPCHIH": ["ORD"], "KXTEMPAUSH": ["AUS"], "KXTEMPDCH": ["DCA"]}),
}
STATIONS = ["ORD", "MDW", "MIA", "OPF", "NYC", "LGA", "LAX", "SMO", "AUS", "DCA"]
EDGE, PLO, PHI, SFLOOR, OBS_MAX_AGE = 0.06, 0.10, 0.90, 0.7, 600
Z_BAR = 5.27


def ts(s: str) -> int:
    return calendar.timegm(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S"))


def fetch_obs(cache) -> None:
    lo = min(ts(m["close_time"]) for ms in cache["markets"].values() for m in ms) - 7200
    for st in STATIONS:
        rows = []
        t0 = lo
        while t0 < CUT:
            t1 = min(t0 + 8 * 86400, CUT)
            fmt = lambda t: time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(t))
            url = f"https://mesonet.agron.iastate.edu/cgi-bin/request/asos1min.py?station={st}&vars=tmpf&sts={fmt(t0)}&ets={fmt(t1)}&sample=1min&what=download&tz=UTC"
            txt = urllib.request.urlopen(url, timeout=120).read().decode()
            for r in csv.DictReader(io.StringIO(txt)):
                v = r.get("tmpf", "")
                try:
                    rows.append([ts(r["valid(UTC)"].replace(" ", "T") + ":00"), float(v)])
                except (ValueError, KeyError):
                    pass
            t0 = t1
        cache["obs"][st] = rows
        print(st, len(rows), "obs", flush=True)


def fetch() -> None:
    cache = {"markets": {}, "candles": {}, "obs": {}}
    mk = DATA_DIR / "wxnew1_markets.json"
    if mk.exists():
        cache["markets"] = json.loads(mk.read_text())
    else:
        for s in sorted({x for t in TRIES.values() for x in t["series"]}):
            ms = [m for m in api.settled_markets(s, 0, CUT) if ts(m["close_time"]) < CUT]
            cache["markets"][s] = [{k: m.get(k) for k in ("ticker", "event_ticker", "close_time", "floor_strike", "strike_type", "expiration_value", "result", "open_time")} for m in ms]
            print(s, len(ms), "markets", flush=True)
        mk.write_text(json.dumps(cache["markets"]))
    evs = {}
    for s, ms in cache["markets"].items():
        for m in ms:
            evs.setdefault(m["event_ticker"], []).append(m["ticker"])
    evclose = {}
    for s, ms in cache["markets"].items():
        for m in ms:
            evclose[m["event_ticker"]] = ts(m["close_time"])
    evs = {e: t for e, t in evs.items() if (evclose[e] // 3600) % 24 % 3 == 1}   # AMENDMENT 2: hour mod 3 = 1, clock only
    print("events after thinning", len(evs), flush=True)

    def one(ev):
        c = evclose[ev]
        time.sleep(0.3)
        try:
            d = api._get("/markets/candlesticks", {"market_tickers": ",".join(evs[ev]), "start_ts": c - 3600, "end_ts": c - 1740, "period_interval": 1})
        except Exception as e:  # noqa: BLE001
            return ev, None, str(e)
        out = {}
        for m in d.get("markets", []):
            out[m["market_ticker"]] = [[x["end_period_ts"], api.f((x.get("yes_bid") or {}).get("close_dollars")), api.f((x.get("yes_ask") or {}).get("close_dollars"))] for x in m.get("candlesticks", [])]
        return ev, out, None
    DEADLINE = calendar.timegm((2026, 10, 31, 3, 25, 0))   # AMENDMENT 3
    order = sorted(evs, key=lambda e: ((evclose[e] // 3600) * 7919 % 1009, evclose[e], e))
    cache["fetched"] = []
    # observations first (fast), so a stopped candle download still has them
    fetch_obs(cache)
    for i, ev in enumerate(order):
        if time.time() > DEADLINE:
            print("deadline reached at", i, "of", len(order), flush=True)
            break
        ev_, out, err = one(ev)
        if out is None:
            print("skip", ev, err, flush=True)
            continue
        cache["candles"].update(out)
        cache["fetched"].append(ev)
        if i % 100 == 0:
            print("candles", i, len(order), flush=True)
            CACHE.write_text(json.dumps(cache))
    CACHE.write_text(json.dumps(cache))


def Phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def fee(q: float, mult: float = 1.0) -> float:
    return mult * math.ceil(round(0.07 * 10 * q * (1 - q) * 100, 9)) / 100 / 10


class Obs:
    def __init__(self, rows):
        rows = sorted(rows)
        self.t = [r[0] for r in rows]
        self.v = [r[1] for r in rows]

    def at(self, t):
        i = bisect.bisect_right(self.t, t) - 1
        if i < 0 or t - self.t[i] > OBS_MAX_AGE:
            return None
        return self.v[i]


def P(obsl, t):
    xs = [o.at(t) for o in obsl]
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def quote(cand, t):
    best = None
    for c in cand or []:
        if c[0] <= t:
            best = c
    return best


def build_events(cache, spec):
    obs = {k: Obs(v) for k, v in cache["obs"].items()}
    evs = defaultdict(list)
    for s in spec["series"]:
        for m in cache["markets"][s]:
            m = dict(m); m["series"] = s
            evs[m["event_ticker"]].append(m)
    out = []
    fetched = set(cache.get("fetched", []))
    for ev, ms in evs.items():
        if ev not in fetched:
            continue
        if len(ms) < 8 or (ts(ms[0]["close_time"]) // 3600) % 24 % 3 != 1:
            continue
        c = ts(ms[0]["close_time"]); L = c - 1800
        s = ms[0]["series"]
        ol = [obs[x] for x in spec["stations"][s]]
        x0, xm = P(ol, L), P(ol, L - 1800)
        try:
            y = float(ms[0]["expiration_value"])
        except (TypeError, ValueError):
            y = None
        out.append(dict(ev=ev, close=c, L=L, x0=x0, x1=None if x0 is None or xm is None else x0 - xm, y=y, ms=ms, series=s))
    return out


def window_of(spec, c):
    for name, lo, hi, need in spec["bounds"]:
        if lo <= c < hi:
            return name
    return None


def fit(rows):
    rows = [r for r in rows if r["x0"] is not None and r["x1"] is not None and r["y"] is not None]
    n = len(rows)
    sx = sum(r["x1"] for r in rows); sy = sum(r["y"] - r["x0"] for r in rows)
    sxx = sum(r["x1"] ** 2 for r in rows); sxy = sum(r["x1"] * (r["y"] - r["x0"]) for r in rows)
    den = n * sxx - sx * sx
    k = (n * sxy - sx * sy) / den if den else 0.0
    b = (sy - k * sx) / n
    res = [(r["y"] - r["x0"]) - b - k * r["x1"] for r in rows]
    s = max(math.sqrt(sum(e * e for e in res) / max(n - 2, 1)), SFLOOR)
    return b, k, s, n


def trades(events, cache, spec, b, k, s):
    tr, brier_m, brier_k = [], [], []
    for e in events:
        if e["x0"] is None or e["x1"] is None or e["y"] is None:
            continue
        mu = e["x0"] + b + k * e["x1"]
        for m in e["ms"]:
            F = m["floor_strike"]
            if F is None or m["strike_type"] != "greater":
                continue
            t = F - 0.49 if spec["twc"] else F
            p = 1 - Phi((t - mu) / s)
            q = quote(cache["candles"].get(m["ticker"]), e["L"] + 60)
            yes = 1.0 if e["y"] > F else 0.0
            if q is None or q[1] is None or q[2] is None:
                continue
            bid, ask = q[1], q[2]
            if not (0.01 <= bid <= ask <= 0.99 + 1e-9) or ask > 0.99:
                continue
            brier_m.append(((bid + ask) / 2 - yes) ** 2); brier_k.append((p - yes) ** 2)
            ey = p - ask - fee(ask); en = (1 - p) - (1 - bid) - fee(1 - bid)
            if max(ey, en) < EDGE:
                continue
            if ey >= en:
                price, side, win = ask, "Y", yes
            else:
                price, side, win = 1 - bid, "N", 1 - yes
            if not (PLO <= price <= PHI):
                continue
            tr.append(dict(ev=e["ev"], day=e["close"] // 86400, price=price, side=side, win=win, net=win - price - fee(price), net12=win - price - fee(price, 1.2)))
    return tr, brier_m, brier_k


def trades_all(events, cache, spec, params):
    tr, bm, bk = [], [], []
    for sr in spec["series"]:
        b, k, s, nfit = params[sr]
        if nfit < 100:
            continue
        a, c, d = trades([e for e in events if e["series"] == sr], cache, spec, b, k, s)
        tr += a; bm += c; bk += d
    return tr, bm, bk


def stats(tr, key="net"):
    n = len(tr)
    if not n:
        return dict(n=0, mean=float("nan"), pf=float("nan"), z=float("nan"), zday=float("nan"))
    xs = [t[key] for t in tr]
    mean = sum(xs) / n
    gw = sum(x for x in xs if x > 0); gl = -sum(x for x in xs if x < 0)
    def clz(kf):
        g = defaultdict(float)
        for t in tr:
            g[t[kf]] += t[key] - mean
        G = len(g)
        if G < 2:
            return float("nan")
        se = math.sqrt(G / (G - 1) * sum(v * v for v in g.values())) / n
        return mean / se if se else float("nan")
    return dict(n=n, mean=mean, pf=gw / gl if gl else float("inf"), z=clz("ev"), zday=clz("day"))


def run() -> None:
    if RESULT.exists():
        print("refused: result exists"); return
    cache = json.loads(CACHE.read_text())
    out = []
    P_ = out.append
    for name, spec in TRIES.items():
        evs = build_events(cache, spec)
        wins = defaultdict(list)
        for e in evs:
            w = window_of(spec, e["close"])
            if w:
                wins[w].append(e)
        P_(f"== {name}: events {len(evs)}; usable (obs and index) " + str({w: sum(1 for e in v if e['x0'] is not None and e['x1'] is not None and e['y'] is not None) for w, v in wins.items()}))
        params = {}
        for sr in spec["series"]:
            d_ = [e for e in wins["discovery"] if e["series"] == sr]
            b, k, s, nfit = fit(d_) if d_ else (0, 0, 1, 0)
            params[sr] = (b, k, s, nfit)
            eq = sum(1 for e in d_ if e["x0"] is not None and e["y"] is not None and round(e["x0"]) == round(e["y"]))
            P_(f"fit {sr} on discovery: n {nfit} b {b:.3f} k {k:.3f} s {s:.3f}; info: rounded ASOS at L equals the settled value in {eq} of {len(d_)} discovery events (at L, 30 min before the close)")
        res = {}
        for w, _, _, need in spec["bounds"]:
            if w == "holdout":
                continue
            tr, bm, bk = trades_all(wins[w], cache, spec, params)
            st, st12 = stats(tr), stats(tr, "net12")
            res[w] = (tr, st, st12, need)
            P_(f"{w}: trades {st['n']} (need {need}) days {len(set(t['day'] for t in tr))} mean {st['mean']*100:.2f}c PF {st['pf']:.2f} z_event {st['z']:.2f} z_day {st['zday']:.2f} | fees x1.2 mean {st12['mean']*100:.2f}c PF {st12['pf']:.2f} | mean price {sum(t['price'] for t in tr)/max(len(tr),1):.3f} YES share {sum(1 for t in tr if t['side']=='Y')/max(len(tr),1):.2f} | Brier model {sum(bk)/max(len(bk),1):.4f} market {sum(bm)/max(len(bm),1):.4f} over {len(bk)} quotes")
        both = res["discovery"][0] + res["validation"][0]
        sp = stats(both)
        P_(f"pooled discovery+validation: n {sp['n']} mean {sp['mean']*100:.2f}c PF {sp['pf']:.2f} z_event {sp['z']:.2f} z_day {sp['zday']:.2f} (deflated bar {Z_BAR})")
        enough = all(res[w][1]["n"] >= res[w][3] for w in res)
        passed = all(res[w][1]["n"] >= res[w][3] and res[w][1]["pf"] >= 1.5 and res[w][2]["mean"] > 0 for w in res)
        if not enough:
            perday = res["discovery"][1]["n"] / max(len({t['day'] for t in res['discovery'][0]}), 1)
            verdict = "NOT_ENOUGH_DATA (a window is below its trade count; trades per day in discovery %.1f)" % perday
        elif not passed or not sp["z"] >= Z_BAR:
            verdict = "FALSIFIED (holdout not read)"
        else:
            tr, bm, bk = trades_all(wins["holdout"], cache, spec, params)
            st, st12 = stats(tr), stats(tr, "net12")
            P_(f"holdout: trades {st['n']} mean {st['mean']*100:.2f}c PF {st['pf']:.2f} z {st['z']:.2f}")
            verdict = "NOT_YET_FALSIFIED" if st["n"] >= 30 and st["pf"] >= 1.5 and st12["mean"] > 0 else "FALSIFIED"
        P_(f"VERDICT {name}: {verdict}")
        if "NOT_ENOUGH_DATA" in verdict or "FALSIFIED (holdout" in verdict:
            P_("(the verdict is stated from discovery and validation; when the counts are short the PF and z above are information only)")
    txt = "\n".join(out)
    print(txt)
    RESULT.write_text(txt + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "fetch":
        fetch()
    elif len(sys.argv) > 1 and sys.argv[1] == "run":
        run()
    else:
        print(__doc__)
