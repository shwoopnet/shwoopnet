"""ECONNEW1 angle (a) (workers/ECONNEW1_REGISTRATION.md): weekly initial jobless claims strikes (KXJOBLESSCLAIMS) against a fixed persistence
model of the previous prints. Research only (discovery lane). Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE.
Nothing here means trade.
    python -m scalper.econnew1 fetch   (resumable; FRED ICSA csv, markets, hourly candles for the registered universe, into data/econnew1/)
    python -m scalper.econnew1 run     (the one scored read; refused a second time)
The universe (strikes with model probability 0.10 to 0.90) is built from the FRED series and the strike alone; no outcome is read to build it.
"""
from __future__ import annotations

import csv
import json
import math
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone

from . import api
from .calibration import cluster_mean_z
from .paths import DATA_DIR

D = DATA_DIR / "econnew1"
RESULT = DATA_DIR / "econnew1_result.txt"
SERIES = "KXJOBLESSCLAIMS"
EDGE, HALF, LEAD_S, MAX_AGE_TRADE_S, MAX_AGE_QUOTE_S = 0.05, 0.03, 86400, 48 * 3600, 6 * 3600
UNIV_LO = 0.10
ERR_WEEKS = 104
DISC_END, VAL_END = datetime(2026, 4, 1, tzinfo=timezone.utc), datetime(2026, 10, 17, tzinfo=timezone.utc)
BAR_PF, BAR_Z, MIN_EVENTS, MIN_TRADES, MIN_MEAN_C, FEE_STRESS_PF = 1.5, 5.27, 25, 100, 2.0, 1.3


def pick(o):
    """Live candles name the field close_dollars, historical candles name it close (run 1 read only close_dollars and so saw no quote in the historical era)."""
    o = o or {}
    return api.f(o.get("close_dollars") if o.get("close_dollars") is not None else o.get("close"))


def get_text(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode()


def load_icsa():
    out = {}
    for r in list(csv.reader(open(D / "ICSA.csv")))[1:]:
        try:
            out[date.fromisoformat(r[0])] = float(r[1])
        except ValueError:
            pass
    return out


def fc(icsa, s):
    """Forecast for the week ending s from weeks ending s-7 .. s-28 only: half the last print, half the 4 week mean."""
    a = [icsa.get(s - timedelta(days=7 * k)) for k in range(1, 5)]
    if any(x is None for x in a):
        return None
    return 0.5 * a[0] + 0.5 * sum(a) / 4


def target_week(close_dt):
    d = close_dt.date()
    t = d
    while t.weekday() != 5 or t >= d:
        t -= timedelta(days=1)
    return t


def fair(icsa, target, strike):
    f = fc(icsa, target)
    if f is None:
        return None
    es = []
    for k in range(1, ERR_WEEKS + 1):
        s = target - timedelta(days=7 * k)
        fs = fc(icsa, s)
        if s in icsa and fs is not None:
            es.append(icsa[s] - fs)
    if len(es) < ERR_WEEKS - 4:
        return None
    n = sum(1 for e in es if f + e >= strike)
    return (n + 0.5) / (len(es) + 1)


def universe(icsa, markets):
    out = {}
    for t, x in markets.items():
        if x["series"] != SERIES or x["strike"] is None or x["type"] != "greater_or_equal":
            continue
        cl = datetime.fromisoformat(x["close"].replace("Z", "+00:00"))
        p = fair(icsa, target_week(cl), x["strike"])
        if p is not None and UNIV_LO <= p <= 1 - UNIV_LO:
            out[t] = dict(x, fair=p, target=target_week(cl).isoformat())
    return out


def fetch() -> None:
    D.mkdir(exist_ok=True)
    if not (D / "ICSA.csv").exists():
        (D / "ICSA.csv").write_text(get_text("https://fred.stlouisfed.org/graph/fredgraph.csv?id=ICSA"))
    mp = D / "markets.json"
    if not mp.exists():
        out = {}
        for s in ("KXJOBLESS", SERIES):
            for path, key in (("/historical/markets", "hist"), ("/markets", "live")):
                cur = None
                while True:
                    p = {"series_ticker": s, "limit": 1000}
                    if key == "live":
                        p["status"] = "settled"
                    if cur:
                        p["cursor"] = cur
                    d = api._get(path, p)
                    for m in d.get("markets", []):
                        if m.get("result") in ("yes", "no"):
                            out[m["ticker"]] = {"t": m["ticker"], "ev": m["event_ticker"], "res": m["result"], "open": m["open_time"], "close": m["close_time"], "strike": m.get("floor_strike"), "type": m.get("strike_type"), "val": m.get("expiration_value"), "vol": m.get("volume_fp"), "src": key, "series": s}
                    cur = d.get("cursor")
                    if not cur or not d.get("markets"):
                        break
        mp.write_text(json.dumps(out))
    uni = universe(load_icsa(), json.loads(mp.read_text()))
    (D / "universe.json").write_text(json.dumps(uni)); print(len(uni), "markets in the universe", flush=True)
    cp = D / "candles.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}
    for i, (tk, m) in enumerate(uni.items()):
        if tk in have and have[tk] and len(have[tk][0]) == 5:
            continue
        close = int(datetime.fromisoformat(m["close"].replace("Z", "+00:00")).timestamp())
        try:
            path = f"/historical/markets/{tk}/candlesticks" if m["src"] == "hist" else f"/series/{m['series']}/markets/{tk}/candlesticks"
            d = api._get(path, {"start_ts": close - 8 * 86400, "end_ts": close, "period_interval": 60})
            have[tk] = [(c["end_period_ts"], pick(c.get("yes_bid")), pick(c.get("yes_ask")), api.f(c.get("volume_fp") or c.get("volume")), pick(c.get("price"))) for c in d.get("candlesticks", [])]
        except Exception:
            pass
        if i % 20 == 0:
            cp.write_text(json.dumps(have)); print(i, len(uni), flush=True)
        time.sleep(0.12)
    cp.write_text(json.dumps(have)); print("done", flush=True)


def fee(p, mult=1.0, c=10):
    """Per contract fee in dollars: 7% x C x p x (1-p), rounded up to the cent per order of C contracts."""
    return math.ceil(round(mult * 0.07 * c * p * (1 - p) * 100, 9)) / 100 / c


def entry(m, cs, edge):
    """Returns (side, price_paid, mode) or None. cs: candles (end_ts, bid, ask, vol, price)."""
    close = int(datetime.fromisoformat(m["close"].replace("Z", "+00:00")).timestamp())
    dec = close - LEAD_S
    q = [c for c in cs if c[0] <= dec and c[1] is not None and c[2] is not None and 0 < c[1] < c[2] < 1 and dec - c[0] <= MAX_AGE_QUOTE_S]
    if q:
        bid, ask = q[-1][1], q[-1][2]
        mode = "quote"
    else:
        t = [c for c in cs if c[0] <= dec and c[4] is not None and 0 < c[4] < 1 and dec - c[0] <= MAX_AGE_TRADE_S]
        if not t:
            return None
        p = t[-1][4]
        bid, ask = max(p - HALF, 0.01), min(p + HALF, 0.99)
        mode = "trade"
    f = m["fair"]
    if f - ask >= edge:
        return "yes", ask, mode
    if bid - f >= edge:
        return "no", 1 - bid, mode
    return None


def pnl(side, price, res, mult=1.0):
    win = (res == "yes") == (side == "yes")
    return ((1.0 if win else 0.0) - price - fee(price, mult)) * 100


def stats(rows):
    """rows: [(event, pnl_cents)]"""
    if not rows:
        return dict(n=0, ev=0, pf=0.0, mean=0.0, z=0.0, loss=0.0)
    w = sum(x for _, x in rows if x > 0)
    l = -sum(x for _, x in rows if x < 0)
    mean, se, z = cluster_mean_z(rows)
    return dict(n=len(rows), ev=len({e for e, _ in rows}), pf=(w / l if l > 0 else float("inf")), mean=mean, z=z, loss=sum(1 for _, x in rows if x < 0) / len(rows))


def line(tag, s):
    return f"{tag}: n {s['n']} events {s['ev']} PF {s['pf']:.2f} mean {s['mean']:+.2f}c z {s['z']:+.2f} loss {s['loss']*100:.0f}%"


def main(argv):
    if len(argv) < 2 or argv[1] not in ("fetch", "run"):
        print(__doc__); return
    if argv[1] == "fetch":
        fetch(); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    uni = json.loads((D / "universe.json").read_text())
    cd = json.loads((D / "candles.json").read_text())
    icsa = load_icsa()
    out = []

    def window(m):
        cl = datetime.fromisoformat(m["close"].replace("Z", "+00:00"))
        return "disc" if cl < DISC_END else ("val" if cl < VAL_END else "hold")

    def collect(edge, mult=1.0, only_mode=None):
        rows = {"disc": [], "val": [], "hold": []}
        modes = {"quote": 0, "trade": 0}
        for tk, m in uni.items():
            cs = cd.get(tk) or []
            e = entry(m, cs, edge)
            if e is None or (only_mode and e[2] != only_mode):
                continue
            side, price, mode = e
            modes[mode] += 1
            rows[window(m)].append((m["ev"], pnl(side, price, m["res"], mult)))
        return rows, modes

    main_rows, modes = collect(EDGE)
    pooled = main_rows["disc"] + main_rows["val"]
    sd, sv, sh, sp = stats(main_rows["disc"]), stats(main_rows["val"]), stats(main_rows["hold"]), stats(pooled)
    sfee = stats(collect(EDGE, 1.2)[0]["disc"] + collect(EDGE, 1.2)[0]["val"])
    out.append(f"universe {len(uni)} markets on {len({m['ev'] for m in uni.values()})} events; entries by price mode {modes}")
    for tag, s in (("discovery", sd), ("validation", sv), ("holdout (latest 12 days)", sh), ("pooled disc+val", sp), ("pooled disc+val, fees x1.2", sfee)):
        out.append(line(tag, s))
    for edge in (0.03, 0.08):
        r, _ = collect(edge)
        out.append(line(f"information only, edge {edge:.2f}, disc+val", stats(r["disc"] + r["val"])))
    tight = {"disc": [], "val": [], "hold": []}
    for tk, m in uni.items():
        cs = cd.get(tk) or []
        e = entry(m, cs, EDGE)
        if e is None:
            continue
        close = int(datetime.fromisoformat(m["close"].replace("Z", "+00:00")).timestamp())
        qq = [c for c in cs if c[0] <= close - LEAD_S and c[1] is not None and c[2] is not None and 0 < c[1] < c[2] < 1 and close - LEAD_S - c[0] <= MAX_AGE_QUOTE_S]
        if e[2] == "quote" and qq and qq[-1][2] - qq[-1][1] <= 0.10:
            tight[window(m)].append((m["ev"], pnl(e[0], e[1], m["res"])))
    out.append(line("information only, quoted spread <= 10c, all windows", stats(tight["disc"] + tight["val"] + tight["hold"])))
    q, _ = collect(EDGE, 1.0, "quote")
    out.append(line("information only, quote-mode entries only, all windows", stats(q["disc"] + q["val"] + q["hold"])))
    # information only: model Brier against the market's, and the look-ahead control (FRED value against Kalshi's first print)
    bm = bk = nb = 0
    diffs = []
    for tk, m in uni.items():
        cs = cd.get(tk) or []
        cl = int(datetime.fromisoformat(m["close"].replace("Z", "+00:00")).timestamp())
        t = [c for c in cs if c[0] <= cl - LEAD_S and c[4] is not None and cl - LEAD_S - c[0] <= MAX_AGE_TRADE_S]
        if not t:
            continue
        y = 1.0 if m["res"] == "yes" else 0.0
        bm += (m["fair"] - y) ** 2; bk += (t[-1][4] - y) ** 2; nb += 1
    out.append(f"information only: Brier model {bm/max(nb,1):.4f} market {bk/max(nb,1):.4f} on {nb} markets with a price")
    for m in uni.values():
        try:
            v = float(str(m["val"]).replace(",", "")); tw = date.fromisoformat(m["target"])
            if tw in icsa:
                diffs.append(icsa[tw] - v)
        except (ValueError, TypeError):
            pass
    ev_first = {}
    for m in uni.values():
        try:
            ev_first[m["ev"]] = abs(icsa[date.fromisoformat(m["target"])] - float(str(m["val"]).replace(",", "")))
        except (ValueError, TypeError, KeyError):
            pass
    if ev_first:
        out.append(f"look-ahead control: FRED value minus Kalshi first print, mean abs {sum(ev_first.values())/len(ev_first):,.0f} claims on {len(ev_first)} weeks")
    # verdict
    nev = len({e for e, _ in pooled})
    if nev < MIN_EVENTS or sp["n"] < MIN_TRADES:
        verdict = "NOT_ENOUGH_DATA"
    elif sd["pf"] < BAR_PF or sv["pf"] < BAR_PF or sp["pf"] < 1.0:
        verdict = "FALSIFIED"
    elif sp["mean"] >= MIN_MEAN_C and sp["z"] >= BAR_Z and sfee["pf"] >= FEE_STRESS_PF and (sh["n"] == 0 or sh["pf"] >= BAR_PF):
        verdict = "NOT_YET_FALSIFIED"
    else:
        verdict = "FALSIFIED"
    out.append(f"VERDICT: {verdict}")
    txt = "\n".join(out)
    RESULT.write_text(txt); print(txt)


if __name__ == "__main__":
    main(sys.argv)
