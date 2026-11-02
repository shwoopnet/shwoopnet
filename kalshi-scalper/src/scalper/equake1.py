"""EQUAKE1 (workers/EQUAKE1_REGISTRATION.md): Kalshi earthquake markets against a Gutenberg-Richter base rate from USGS. Research only.
 A: KXBIGGESTQUAKE daily world maximum magnitude (UTC day).  B: KXEARTHQUAKEM monthly "at least M before the 1st".
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE. Nothing here means trade.
    python -m scalper.equake1 fetch    (USGS M4.5+ catalog, Kalshi listings, entry-window candles; resumable, public keyless)
    python -m scalper.equake1 run      (the one scored read; refused a second time)
"""
from __future__ import annotations

import json
import math
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone

from . import api
from .calibration import cluster_mean_z
from .candlefield import quote_close
from .econnew1 import fee, line, pnl, stats
from .paths import DATA_DIR

D = DATA_DIR / "equake1"
RESULT = DATA_DIR / "equake1_result.txt"
UTC = timezone.utc
TRAIL_DAYS, MAG_MIN, EDGE, MAX_SPREAD, MAX_AGE_S = 730, 4.5, 0.08, 0.10, 1800
UNIV = (0.05, 0.95)
MIN_TOTAL, MIN_WIN = 150, 50
BAR_PF, BAR_Z, BAR_MEAN = 1.5, 5.27, 2.0
MONTHS = {m: i + 1 for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"])}


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def fit(event_times_mags, t0):
    """(lambda45 per day, b) from the events strictly before t0 within the trailing window. event_times_mags: [(datetime, mag)]."""
    lo = t0 - timedelta(days=TRAIL_DAYS)
    mags = [round(m, 1) for t, m in event_times_mags if lo <= t < t0 and m >= MAG_MIN - 1e-9]
    if len(mags) < 50:
        return None
    mean = sum(mags) / len(mags)
    b = math.log10(math.e) / (mean - (MAG_MIN - 0.05))
    return len(mags) / TRAIL_DAYS, b


def fair(lam, b, strike, days=1.0):
    """P(at least one event of magnitude >= strike within days) for a Poisson Gutenberg-Richter process."""
    return 1.0 - math.exp(-lam * days * 10 ** (-b * (strike - (MAG_MIN - 0.05))))


def day_of(ticker):
    d = ticker.split("-")[1]
    return datetime(2000 + int(d[5:7]), MONTHS[d[2:5]], int(d[0:2]), tzinfo=UTC)


def month_end(ticker):
    """First instant after the ticker's month (04:00Z, the exchange's own midnight), from the ticker only, never from close_time."""
    d = ticker.split("-")[1]
    y, m = 2000 + int(d[0:2]), MONTHS[d[2:5]]
    y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return datetime(y, m, 1, 4, tzinfo=UTC)


def first_quote(cs, t_from, max_age_s):
    """First candle at or after t_from (and within max_age_s) with a valid two-sided quote: (bid, ask) or None."""
    for c in sorted(cs, key=lambda c: c["end_period_ts"]):
        t = c["end_period_ts"]
        if t < t_from.timestamp() or t > t_from.timestamp() + max_age_s:
            continue
        b, a = quote_close(c.get("yes_bid")), quote_close(c.get("yes_ask"))
        if b is not None and a is not None and 0 < b < a < 1:
            return b, a
    return None


def decide(fp, bid, ask):
    """(side, price) when the model says a side is under-priced by EDGE after the fee, else None. Spread cut applied here."""
    if ask - bid > MAX_SPREAD + 1e-9:
        return None
    if fp - ask - fee(ask) >= EDGE - 1e-9:
        return "yes", ask
    if bid - fp - fee(1 - bid) >= EDGE - 1e-9:
        return "no", 1 - bid
    return None


def split_days(days):
    """Sorted eligible days cut into three equal parts, the remainder going to the last: disc, val, hold."""
    days = sorted(days)
    k = len(days) // 3
    return {d: ("disc" if i < k else "val" if i < 2 * k else "hold") for i, d in enumerate(days)}


def brier(pairs):
    return sum((p - y) ** 2 for p, y in pairs) / len(pairs) if pairs else float("nan")


def score(markets, events, candles, angle):
    """markets: listing rows; candles: ticker -> list. Returns (trades, brier_pairs_model, brier_pairs_market, universe_count, window_of)."""
    if angle == "A":
        elig = {}
        for m in markets:
            elig.setdefault(day_of(m["ticker"]), []).append(m)
        elig = {d: v for d, v in elig.items() if len(v) >= 2 and fit(events, d)}
        win = split_days(elig)
        groups = [(d, v, d, 1.0) for d, v in elig.items()]
    else:
        win = {}
        groups = []
        for m in markets:
            o = ts(m["open_time"])
            groups.append((month_end(m["ticker"]), [m], o, (month_end(m["ticker"]) - o).total_seconds() / 86400))
    trades, bm, bk, nuni = [], [], [], 0
    for key, ms, t0, days in groups:
        f = fit(events, t0)
        if not f:
            continue
        for m in ms:
            fp = fair(*f, float(m["floor_strike"]), days)
            if not UNIV[0] <= fp <= UNIV[1]:
                continue
            nuni += 1
            q = first_quote(candles.get(m["ticker"], []), t0, MAX_AGE_S if angle == "A" else 6 * 3600)
            if not q:
                continue
            y = 1.0 if m["result"] == "yes" else 0.0
            bm.append((fp, y)); bk.append(((q[0] + q[1]) / 2, y))
            d = decide(fp, *q)
            if d:
                trades.append(dict(day=str(key.date()), ticker=m["ticker"], win=win.get(key, "pool"), side=d[0], price=d[1],
                                   p=pnl(d[0], d[1], m["result"]), p12=pnl(d[0], d[1], m["result"], 1.2)))
    return trades, bm, bk, nuni


def verdict(trades, bm, bk, angle):
    wins = ("disc", "val", "hold") if angle == "A" else ("pool",)
    S = {w: stats([(t["day"], t["p"]) for t in trades if t["win"] == w]) for w in wins}
    S12 = {w: stats([(t["day"], t["p12"]) for t in trades if t["win"] == w]) for w in wins}
    pooled = stats([(t["day"], t["p"]) for t in trades])
    bs_m, bs_k = brier(bm), brier(bk)
    if len(trades) < MIN_TOTAL or (angle == "A" and (S["disc"]["n"] < MIN_WIN or S["val"]["n"] < MIN_WIN)):
        return "NOT_ENOUGH_DATA", S, S12, pooled, bs_m, bs_k
    bad = (any(S[w]["pf"] < BAR_PF for w in ("disc", "val") if w in S) or any(S12[w]["pf"] < 1.0 for w in S12 if S12[w]["n"])
           or bs_m >= bs_k or pooled["z"] < BAR_Z or pooled["mean"] < BAR_MEAN
           or (angle == "A" and S["hold"]["pf"] < BAR_PF))
    return ("FALSIFIED" if bad else "NOT_YET_FALSIFIED"), S, S12, pooled, bs_m, bs_k


# ---------------------------------------------------------------- data
def get_text(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=90).read().decode()


def fetch_catalog(start, end):
    out, cur = [], start
    while cur < end:
        nxt = min(end, cur + timedelta(days=90))
        u = ("https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&orderby=time-asc&minmagnitude=4.5&limit=20000"
             f"&starttime={cur:%Y-%m-%dT%H:%M:%S}&endtime={nxt:%Y-%m-%dT%H:%M:%S}")
        rows = get_text(u).strip().splitlines()[1:]
        for r in rows:
            p = r.split(",")
            if len(p) > 4 and p[4]:
                out.append((p[0], float(p[4])))
        cur = nxt
    return out


def fetch():
    D.mkdir(parents=True, exist_ok=True)
    mk = {s: list(api.settled_markets(s, 0, 2_000_000_000)) for s in ("KXBIGGESTQUAKE", "KXEARTHQUAKEM")}
    (D / "markets.json").write_text(json.dumps(mk))
    first = min(day_of(m["ticker"]) for m in mk["KXBIGGESTQUAKE"])
    last = max(max(day_of(m["ticker"]) for m in mk["KXBIGGESTQUAKE"]), max(month_end(m["ticker"]) for m in mk["KXEARTHQUAKEM"]))
    (D / "catalog.json").write_text(json.dumps(fetch_catalog(first - timedelta(days=TRAIL_DAYS + 5), min(last, datetime.now(UTC)))))
    cf = D / "candles.json"
    cd = json.loads(cf.read_text()) if cf.exists() else {}
    for s, ms in mk.items():
        for m in ms:
            if m["ticker"] in cd:
                continue
            t0 = ts(m["open_time"]) if s == "KXEARTHQUAKEM" else day_of(m["ticker"])
            end = int((t0 + timedelta(hours=7)).timestamp())
            cd[m["ticker"]] = api.candlesticks(s, m["ticker"], int((t0 - timedelta(minutes=5)).timestamp()), end)
            if len(cd) % 25 == 0:
                cf.write_text(json.dumps(cd))
    cf.write_text(json.dumps(cd))
    print("fetched", {s: len(v) for s, v in mk.items()}, "candle sets", len(cd))


def main(argv):
    if len(argv) < 2 or argv[1] not in ("fetch", "run"):
        print(__doc__); return
    if argv[1] == "fetch":
        fetch(); return
    if RESULT.exists():
        print(f"Refusing to run again: {RESULT} exists."); return
    mk = json.loads((D / "markets.json").read_text())
    events = [(ts(t if t.endswith("Z") else t + "Z"), m) for t, m in json.loads((D / "catalog.json").read_text())]
    cd = json.loads((D / "candles.json").read_text())
    out = []
    for angle, s in (("A", "KXBIGGESTQUAKE"), ("B", "KXEARTHQUAKEM")):
        tr, bm, bk, nuni = score(mk[s], events, cd, angle)
        v, S, S12, pooled, bs_m, bs_k = verdict(tr, bm, bk, angle)
        out.append(f"ANGLE {angle} {s}: {v}; universe strikes {nuni}, quoted {len(bm)}, trades {len(tr)}; model Brier {bs_m:.4f} vs market {bs_k:.4f}; N 728700 z bar {BAR_Z}")
        for w in S:
            if w == "hold" and v != "NOT_YET_FALSIFIED":
                out.append("  hold: frozen, not read (a prior window failed or too few trades)"); continue
            out.append("  " + line(w, S[w]) + f" | x1.2 PF {S12[w]['pf']:.2f}")
        out.append("  " + line("pooled", pooled))
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv)
