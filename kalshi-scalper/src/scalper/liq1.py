"""LIQ1-INFO: does a Deribit liquidation spike move Kalshi's KXBTC15M quote
and revert within 3 minutes? Information check only (research only).

Registration: workers/LIQ1_INFO_REGISTRATION.md. No outcome is read: the
loader never selects `result`; no fill, fee, win, loss or PF is computed.

Run:  PYTHONPATH=src python -m scalper.liq1 fetch   (Deribit, cached)
      PYTHONPATH=src python -m scalper.liq1 thresh  (Deribit only)
      PYTHONPATH=src python -m scalper.liq1         (the check)
"""
import json
import math
import sqlite3
import statistics
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from scalper.paths import DATA_DIR

CACHE = DATA_DIR / "liq1"
URL = ("https://history.deribit.com/api/v2/public/"
       "get_last_trades_by_instrument_and_time")
INSTR = "BTC-PERPETUAL"
START = datetime(2026, 8, 6, tzinfo=timezone.utc)
END = datetime(2026, 10, 28, tzinfo=timezone.utc)
DISC_END = int(datetime(2026, 9, 21, tzinfo=timezone.utc).timestamp())
START_TS, END_TS = int(START.timestamp()), int(END.timestamp())
FILES = ["l1b.sqlite", "book.sqlite", "fresh.sqlite"]
SERIES = "KXBTC15M"
OFFSETS = (-600, -540, -480, -420, -360, -300, -240)
MIN_SPIKES = 20


# ---------------------------------------------------------------- fetch
def _get(params):
    q = "&".join(f"{k}={v}" for k, v in params.items())
    wait = 2.0
    for _ in range(12):
        try:
            with urllib.request.urlopen(f"{URL}?{q}", timeout=60) as r:
                return json.load(r)["result"]
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            pass
        time.sleep(wait)
        wait = min(wait * 2, 60)
    raise RuntimeError("Deribit read failed after retries")


def fetch_day(d):
    """Per minute aggregates for one UTC day, cached as JSON."""
    path = CACHE / f"{d:%Y-%m-%d}.json"
    if path.exists():
        return json.loads(path.read_text())
    s = int(d.timestamp() * 1000)
    e = s + 86_400_000
    seen, minutes, liqs, ntr = set(), {}, [], 0
    cur = s
    while True:
        r = _get({"instrument_name": INSTR, "start_timestamp": cur,
                  "end_timestamp": e, "count": 10000, "sorting": "asc"})
        tr = r["trades"]
        for t in tr:
            if t["trade_id"] in seen:
                continue
            seen.add(t["trade_id"])
            ntr += 1
            ts = t["timestamp"]
            mend = -(-ts // 60000) * 60  # minute end, seconds
            m = minutes.setdefault(str(mend), [0.0, 0.0, None])
            m[2] = t["price"]  # ascending, so the last one stays
            lq = t.get("liquidation")
            if lq:
                amt = float(t["amount"])
                sgn = 1 if t["direction"] == "buy" else -1
                f = {"T": sgn, "M": -sgn}.get(lq, 0) * amt
                m[0] += amt
                m[1] += f
                liqs.append([ts, lq, t["direction"], amt, t["price"]])
        if not r["has_more"] or not tr:
            break
        nxt = tr[-1]["timestamp"]
        cur = nxt if nxt > cur else cur + 1
        time.sleep(0.6)
    out = {"day": f"{d:%Y-%m-%d}", "trades": ntr, "minutes": minutes,
           "liqs": liqs}
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out))
    time.sleep(0.6)
    return out


def fetch():
    d = START
    while d < END:
        o = fetch_day(d)
        print(o["day"], o["trades"], "trades,", len(o["liqs"]), "liqs",
              flush=True)
        d += timedelta(days=1)


def deribit():
    """{minute_end: (liq_usd, forced_flow, last_price)}."""
    mins = {}
    d = START
    while d < END:
        o = json.loads((CACHE / f"{d:%Y-%m-%d}.json").read_text())
        for k, v in o["minutes"].items():
            mins[int(k)] = tuple(v)
        d += timedelta(days=1)
    return mins


# ---------------------------------------------------------------- kalshi
def markets():
    """{ticker: close} only; never selects result."""
    out = {}
    for f in FILES:
        con = sqlite3.connect(DATA_DIR / f)
        for t, close in con.execute(
                "select ticker, close_ts from market where series=? "
                "and close_ts>=? and close_ts<?", (SERIES, START_TS, END_TS)):
            out.setdefault(t, (close, f))
    return out


def candles(mk):
    c = defaultdict(dict)
    for f in FILES:
        con = sqlite3.connect(DATA_DIR / f)
        for t, end, bid, ask, vol in con.execute(
                "select ticker, end_ts, bid_c, ask_c, volume from candle "
                "where series=?", (SERIES,)):
            m = mk.get(t)
            if m is None or m[1] != f:
                continue
            c[t][end - m[0]] = (bid, ask, vol)
    return c


# ---------------------------------------------------------------- logic
def l2(mins, t):
    a, b = mins.get(t - 60), mins.get(t)
    return (a[0] if a else 0.0) + (b[0] if b else 0.0)


def flow2(mins, t):
    a, b = mins.get(t - 60), mins.get(t)
    return (a[1] if a else 0.0) + (b[1] if b else 0.0)


def price_at(mins, t, back=10):
    """Last perp trade price at or before minute end t (looks back 10 min)."""
    for k in range(back + 1):
        m = mins.get(t - 60 * k)
        if m and m[2] is not None:
            return m[2]
    return None


def price_dir(mins, t):
    p1, p0 = price_at(mins, t), price_at(mins, t - 120)
    if p1 is None or p0 is None or p1 == p0:
        return 0
    return 1 if p1 > p0 else -1


def stage(close):
    return "disc" if close < DISC_END else "val"


def threshold(mins, mk):
    vals = sorted(l2(mins, close + o) for close, f in mk.values()
                  if close < DISC_END for o in OFFSETS)
    k = math.ceil(0.99 * len(vals)) - 1
    thr = vals[k]
    note = f"p99 nearest rank over {len(vals)} discovery eligible minutes"
    if thr <= 0:
        pos = [v for v in vals if v > 0]
        thr = pos[math.ceil(0.99 * len(pos)) - 1]
        note += " was 0; fallback p99 of positive values"
    return thr, note, vals


def mid(c, x):
    r = c.get(x)
    if r is None or r[0] is None or r[1] is None:
        return None
    return (r[0] + r[1]) / 2


def measures(c, t_off, d):
    m0, m1, m2 = mid(c, t_off), mid(c, t_off - 60), mid(c, t_off - 120)
    post = [mid(c, t_off + 60 * k) for k in (1, 2, 3)]
    if m0 is None or m2 is None or any(p is None for p in post) or m1 is None:
        return None
    return {"I2": d * (m0 - m2), "I1": d * (m0 - m1),
            "P1": d * (post[0] - m0), "P2": d * (post[1] - m0),
            "P3": d * (post[2] - m0)}


def summarise(rows):
    if not rows:
        return None
    s = {k: statistics.mean(r[k] for r in rows) for k in
         ("I2", "I1", "P1", "P2", "P3")}
    s["n"] = len(rows)
    s["rev_frac"] = (-s["P3"] / s["I2"]) if s["I2"] else float("nan")
    pos = [r for r in rows if r["I2"] > 0]
    s["rev_share"] = (sum(1 for r in pos if r["P3"] <= -r["I2"] / 2)
                      / len(pos)) if pos else float("nan")
    s["n_pos"] = len(pos)
    s["sd_I2"] = statistics.stdev(r["I2"] for r in rows) if len(rows) > 1 else 0
    return s


def fmt(s):
    if s is None:
        return "n 0"
    c = 100
    return (f"n {s['n']:4d}  I2 {s['I2']*c:+.2f}c (sd {s['sd_I2']*c:.2f})  "
            f"I1 {s['I1']*c:+.2f}c  P1 {s['P1']*c:+.2f}c  "
            f"P2 {s['P2']*c:+.2f}c  P3 {s['P3']*c:+.2f}c  "
            f"rev_frac {s['rev_frac']:+.2f}  rev_share {s['rev_share']:.2f} "
            f"(of {s['n_pos']} with I2>0)")


def main():
    mins = deribit()
    mk = markets()
    thr, note, vals = threshold(mins, mk)
    print(f"threshold L2 >= ${thr:,.0f} ({note})")
    print(f"share of discovery eligible minutes with any liquidation: "
          f"{sum(1 for v in vals if v > 0)/len(vals):.3f}")
    if len(sys.argv) > 1 and sys.argv[1] == "thresh":
        return
    cs = candles(mk)
    spikes = defaultdict(list)          # (stage, kind) -> rows
    ctrl = defaultdict(lambda: defaultdict(list))  # stage -> off -> rows
    counts = defaultdict(lambda: defaultdict(int))
    for tk, (close, f) in mk.items():
        st = stage(close)
        c = cs.get(tk, {})
        counts[st]["markets"] += 1
        spike_t = None
        for o in OFFSETS:
            if l2(mins, close + o) >= thr:
                spike_t = o
                break
        if spike_t is not None:
            counts[st]["spikes"] += 1
            t = close + spike_t
            fl = flow2(mins, t)
            pd = price_dir(mins, t)
            d = (1 if fl > 0 else -1) if fl != 0 else pd
            if fl == 0:
                counts[st]["dir_from_price"] += 1
            if d == 0:
                counts[st]["dropped_no_dir"] += 1
                continue
            m = measures(c, spike_t, d)
            if m is None:
                counts[st]["dropped_no_quote"] += 1
                continue
            m["off"] = spike_t
            spikes[(st, "liq")].append(m)
            vol = c.get(spike_t, (None, None, None))[2]
            if vol and vol > 0:
                spikes[(st, "liq_vol>0")].append(m)
            if pd:
                mp = measures(c, spike_t, pd)
                mp["off"] = spike_t
                spikes[(st, "price")].append(mp)
                if fl and (1 if fl > 0 else -1) == pd:
                    counts[st]["liq_dir_agrees_price"] += 1
        for o in OFFSETS:
            if o == spike_t or l2(mins, close + o) >= thr:
                continue
            pd = price_dir(mins, close + o)
            if not pd:
                continue
            m = measures(c, o, pd)
            if m is not None:
                ctrl[st][o].append(m)

    verdicts = {}
    for st, name in (("disc", "DISCOVERY Aug 6 to Sep 20"),
                     ("val", "VALIDATION Sep 21 to Oct 27")):
        print(f"\n== {name} ==")
        print("counts:", dict(counts[st]))
        s = summarise(spikes[(st, "liq")])
        print("spikes, liquidation direction:  ", fmt(s))
        print("spikes, volume>0 at t:           ",
              fmt(summarise(spikes[(st, "liq_vol>0")])))
        print("spikes, perp price direction:    ",
              fmt(summarise(spikes[(st, "price")])))
        # offset-weighted control
        mix = defaultdict(int)
        for r in spikes[(st, "liq")]:
            mix[r["off"]] += 1
        tot = sum(mix.values())
        if tot:
            cw = {}
            for k in ("I2", "I1", "P1", "P2", "P3"):
                cw[k] = sum(mix[o] / tot * statistics.mean(r[k] for r in
                            ctrl[st][o]) for o in mix if ctrl[st][o])
            n_c = sum(len(ctrl[st][o]) for o in mix)
            print(f"control, price direction, offset weighted: n {n_c}  " +
                  "  ".join(f"{k} {cw[k]*100:+.2f}c" for k in cw) +
                  f"  rev_frac {(-cw['P3']/cw['I2']) if cw['I2'] else 0:+.2f}")
        print("spikes by offset:", dict(sorted(mix.items())))
        if s is None or s["n"] < MIN_SPIKES:
            verdicts[st] = "NOT_ENOUGH_DATA"
        else:
            ok1 = s["I2"] >= 0.02
            ok2 = -s["P3"] >= 0.5 * s["I2"]
            verdicts[st] = ("PASS" if ok1 and ok2 else
                            f"FAIL (impact>=2c {ok1}, half reverts {ok2})")
        print("decision-rule check:", verdicts[st])
    print()
    if all(v == "PASS" for v in verdicts.values()):
        print("DECISION: reverting impact in both stages; outcome test earned")
    elif any(v == "NOT_ENOUGH_DATA" for v in verdicts.values()):
        print("DECISION: NOT_ENOUGH_DATA; no outcome test earned now")
    else:
        print("DECISION: no reverting impact, LIQ1 not worth an outcome test")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "fetch":
        fetch()
    else:
        main()
