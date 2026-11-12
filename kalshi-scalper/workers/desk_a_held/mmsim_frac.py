"""Independent re-derivation of MMSIM1 (development events only) from the protocol TEXT.
Written by Idea Desk A without reading src/scalper/mmsim1.py. Usage: python3 -I mmsim_rederive.py <data_dir> [variant flags]
"""
import sys, os, gzip, csv, glob, calendar, json
from collections import defaultdict
from datetime import datetime

DATA = sys.argv[1]
CUTOFF = "2026-11-07T15:00:00Z"          # development = events closing BEFORE this
FILL_CLOCK = os.environ.get("FILL_CLOCK", "created")   # created | poll
FLAT_SNAP = os.environ.get("FLAT_SNAP", "first_after")  # first_after | last_before
POST_RULE = os.environ.get("POST_RULE", "first_with_bid")  # first_with_bid | first_only
BOTH = os.environ.get("BOTH_SIDES", "0")  # 1 = quote a strike only if both sides have a bid at the first in-window snapshot
PMIN = float(os.environ.get("PMIN", "0")); PMAX = float(os.environ.get("PMAX", "1"))

def iso_ms(s):
    s = s.strip().replace("Z", "")
    if "." in s:
        a, b = s.split("."); b = (b + "000000")[:6]
    else:
        a, b = s, "000000"
    dt = datetime.strptime(a, "%Y-%m-%dT%H:%M:%S")
    return calendar.timegm(dt.timetuple()) * 1000 + int(b) // 1000

def f(x):
    try:
        return float(x)
    except Exception:
        return None

snaps = defaultdict(list)   # ticker -> [(ts, yb, ybs, nb, nbs)]
close_of = {}
strike_of = {}
dropped_rows = 0
for path in sorted(glob.glob(os.path.join(DATA, "book", "*", "*", "book.csv.gz"))):
    with gzip.open(path, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            ct = r["close_time"]
            if ct >= CUTOFF:           # held-out: dropped at load, never stored
                dropped_rows += 1
                continue
            t = r["ticker"]
            close_of[t] = ct
            strike_of[t] = r["strike"]
            snaps[t].append((int(r["poll_ts_local_ms"]), f(r["yes_bid_px_1"]), f(r["yes_bid_sz_1"]), f(r["no_bid_px_1"]), f(r["no_bid_sz_1"])))
for t in snaps:
    snaps[t].sort()

trades = defaultdict(list)  # ticker -> [(created_ms, poll_ms, yes_price, count, side)]
seen = set()
for path in sorted(glob.glob(os.path.join(DATA, "book", "*", "*", "trades.csv.gz"))):
    with gzip.open(path, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            t = r["ticker"]
            if t not in close_of:      # includes every held-out ticker
                continue
            tid = r["trade_id"]
            if tid in seen:
                continue
            seen.add(tid)
            trades[t].append((iso_ms(r["created_time"]), int(r["poll_ts_local_ms"]), round(float(r["yes_price_dollars"]), 4), float(r["count_fp"]), r["taker_outcome_side"]))
for t in trades:
    trades[t].sort()

import math
ROUND = os.environ.get("ROUND_FEE","0")
def fee_t(p):
    f0 = 0.07 * p * (1 - p)
    return math.ceil(f0 * 100 - 1e-9) / 100 if ROUND == "1" else f0

FR = []; QF = [0.0, 0.0]
def simulate(maker_coef):
    events = defaultdict(list)  # close -> list of strike pnl
    st = dict(strikes=0, fy=0, fn=0, pairs=0, singles=0, noflatbid=0)
    for t, ss in snaps.items():
        T = iso_ms(close_of[t])
        w0, w1 = T - 50 * 60000, T - 15 * 60000
        inwin = [s for s in ss if w0 <= s[0] < w1]
        if not inwin:
            continue
        # flatten snapshot
        if FLAT_SNAP == "first_after":
            fl = next((s for s in ss if s[0] >= w1), None)
            if fl is None:
                fl = inwin[-1]
        else:
            fl = [s for s in ss if s[0] <= w1][-1]
        legs = {}
        if BOTH == "1":
            s0 = inwin[0]
            if not (s0[1] and s0[3] and s0[1] > 0 and s0[3] > 0):
                continue
        if BOTH == "2":
            if not any((x[1] and x[3]) for x in inwin):
                continue
            inwin = [x for x in inwin if x[1] and x[3]]
        for side, ip, isz in (("yes", 1, 2), ("no", 3, 4)):
            post = None
            cands = inwin if POST_RULE == "first_with_bid" else inwin[:1]
            for s in cands:
                if s[ip] is not None and s[ip] > 0 and s[isz] is not None:
                    post = s
                    break
            if post is None:
                continue
            p, q_ahead, t_post = post[ip], post[isz], post[0]
            if side == "yes":
                level, hit = round(p, 4), "no"
            else:
                level, hit = round(1 - p, 4), "yes"
            cum, filled, ffrac, fct, wct = 0.0, False, None, 0.0, 0.0
            for (cm, pm, yp, cnt, sd) in trades.get(t, ()):
                clock = cm if FILL_CLOCK == "created" else pm
                if cm <= t_post:
                    continue
                if clock > w1:
                    continue
                if sd == hit and abs(yp - level) < 1e-6:
                    cum += cnt
                    isf = abs(cnt - round(cnt)) > 0.001
                    if isf: fct += cnt
                    else: wct += cnt
                    if cum >= q_ahead + float(os.environ.get("LOT","1")):
                        filled = True; ffrac = isf
                        break
            legs[side] = (p, filled, ffrac, fct, wct)
        if not legs:
            continue
        st["strikes"] += 1
        yf = legs.get("yes", (None, False)); nf = legs.get("no", (None, False))
        pnl = 0.0
        if yf[1]: st["fy"] += 1
        if nf[1]: st["fn"] += 1
        if yf[1] and nf[1]:
            st["pairs"] += 1
            pnl = 1 - yf[0] - nf[0] - maker_coef * (yf[0] * (1 - yf[0]) + nf[0] * (1 - nf[0]))
            FR.append(("pair", int(bool(yf[2])) + int(bool(nf[2])), pnl))
        elif yf[1] or nf[1]:
            st["singles"] += 1
            if yf[1]:
                cost, bid = yf[0], fl[1]
            else:
                cost, bid = nf[0], fl[3]
            if bid is None or bid <= 0:
                st["noflatbid"] += 1
                bid = 0.0
            pnl = bid - fee_t(bid) - cost - maker_coef * cost * (1 - cost)
        if (yf[1] or nf[1]) and not (yf[1] and nf[1]):
            FR.append(("single", int(bool((yf if yf[1] else nf)[2])), pnl))
        for lg in (yf, nf):
            if len(lg) > 3: QF[0] += lg[3]; QF[1] += lg[4]
        events[close_of[t]].append(pnl)
    ev = {k: sum(v) for k, v in events.items()}
    pos = sum(x for x in ev.values() if x > 0); neg = -sum(x for x in ev.values() if x < 0)
    n = len(ev)
    mean_ev = sum(ev.values()) / n if n else 0
    return dict(events=n, pf=(pos / neg if neg else None), mean_event_c=100 * mean_ev, mean_strike_c=100 * sum(ev.values()) / max(1, st["strikes"]), total=sum(ev.values()), **st), ev

all_events = sorted(set(close_of.values()))
print("variant", FILL_CLOCK, FLAT_SNAP, POST_RULE)
print("dev events with any book row:", len(all_events), "first", all_events[0], "last", all_events[-1], "| tickers", len(snaps), "| held-out rows dropped at load", dropped_rows)
for coef in (0.0, 0.0175):
    res, ev = simulate(coef)
    print("maker coef", coef, json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in res.items()}))
    if coef == 0.0:
        import statistics as _s
        for kind in ("single", "pair"):
            for k in (0, 1, 2):
                v = [x[2] for x in FR if x[0] == kind and x[1] == k]
                if v: print("FILLCLASS", kind, "fractional fillers", k, "n", len(v), "mean c", round(100 * _s.mean(v), 2), "sum $", round(sum(v), 2))
        print("QUEUE FLOW at quoted levels: fractional share of contracts", round(QF[0] / (QF[0] + QF[1]), 3))
        byday = defaultdict(float)
        for k, v in ev.items():
            byday[k[:10]] += v
        print("days", len(byday), "positive days", sum(1 for v in byday.values() if v > 0), "per-day $", {d: round(v, 2) for d, v in sorted(byday.items())})
