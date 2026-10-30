"""NEWH8: the cheap side late in the window on Kalshi's 15 minute gold and Bitcoin markets (research only).

Registration: workers/NEWH8_REGISTRATION.md (pushed before any scoring).

    PYTHONPATH=src python -m scalper.newh8 describe   (features only: no result, no quote after a signal; pre-registration look)
    PYTHONPATH=src python -m scalper.newh8 run        (scores the registered tries once)
    PYTHONPATH=src python -m scalper.newh8 parity     (forward_eval against the history scorer, survivors only)
"""
from __future__ import annotations

import math
import sqlite3
import statistics
import sys
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime, timezone

from .paths import DATA_DIR

GOLD, BTC, ETH = "KXGOLD15M", "KXBTC15M", "KXETH15M"
FILES = {BTC: ("l1b", "book", "fresh"), ETH: ("l1b", "book", "fresh"), GOLD: ("l1b", "book", "fresh", "five")}
START = int(datetime(2026, 8, 6, tzinfo=timezone.utc).timestamp())
DISC_END = int(datetime(2026, 9, 21, tzinfo=timezone.utc).timestamp())
END = int(datetime(2026, 10, 28, tzinfo=timezone.utc).timestamp())
OICORE_TH = 86299.56000000001
LO, HI = 0.05, 0.50


def day(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def stage(close):
    return "disc" if close < DISC_END else "val"


# ---------------------------------------------------------------- data

def load(series, start=START, end=END):
    """{close: {ticker, close, result, strike, c: {offset: (bid_c, ask_c, vol, oi)}, x: {offset: (ask_h, ask_l, bid_h, bid_l, price_c)}}}.
    First file wins per close (the order every NEWH worker used). `result` is carried but only `run` reads it."""
    win = {}
    for name in FILES[series]:
        p = DATA_DIR / f"{name}.sqlite"
        if not p.exists():
            continue
        db = sqlite3.connect(p)
        mk = {tk: (close, res, k) for tk, close, res, k in db.execute(
            "select ticker, close_ts, result, strike from market where series=? and close_ts>=? and close_ts<?",
            (series, start, end))}
        rows = defaultdict(list)
        for r in db.execute("select ticker, end_ts, bid_c, ask_c, volume, oi, ask_h, ask_l, bid_h, bid_l, price_c from candle "
                            "where series=? and bid_c is not null and ask_c is not null", (series,)):
            if r[0] in mk:
                rows[r[0]].append(r)
        for tk, (close, res, k) in mk.items():
            if close in win or res not in ("yes", "no") or not rows.get(tk):
                continue
            c, x = {}, {}
            for _, e, b, a, v, oi, ah, al, bh, bl, pc in rows[tk]:
                c[e - close] = (b, a, v or 0.0, oi)
                x[e - close] = (ah, al, bh, bl, pc)
            win[close] = {"ticker": tk, "close": close, "result": res, "strike": k, "c": c, "x": x}
    return win


def side_ask(q, side):
    a = q[1] if side == "yes" else round(1 - q[0], 6)
    return a if 0 < a < 1 else None


def side_bid(q, side):
    return q[0] if side == "yes" else round(1 - q[1], 6)


def side_mid(q, side):
    m = (q[0] + q[1]) / 2
    return m if side == "yes" else 1 - m


def cheap_side(q, lo=LO, hi=HI):
    for s in ("yes", "no"):
        a = side_ask(q, s)
        if a is not None and lo - 1e-9 <= a <= hi + 1e-9:
            return s
    return None


# ---------------------------------------------------------------- features (closes, volume, oi only: forward-evaluable)

def feats(c, side, L=180):
    """Pre-signal features of the side `side` at the candle ending L s before the close; None for a missing input."""
    t = -L
    q = c.get(t)
    f = {}
    q3 = c.get(t - 180)
    f["doi"] = (q[3] - q3[3]) if (q3 is not None and q[3] is not None and q3[3] is not None) else None
    f["spread"] = q[1] - q[0]
    f["ask"] = side_ask(q, side)
    f["vol1"] = q[2]
    v3 = [c.get(t - 60 * j) for j in range(3)]
    f["vol3"] = sum(r[2] for r in v3) if all(r is not None for r in v3) else None
    f["oi"] = q[3]
    # cheap side's mid path from the first candle to the signal
    keys = sorted(k for k in c if -900 < k <= t)
    mids = [(k, side_mid(c[k], side)) for k in keys]
    f["n_candles"] = len(mids)
    # flips: the 0.5 line crossed by the mid (a mid of exactly 0.5 does not count as a side)
    flips, last_lead, prev = 0, None, None
    for k, m in mids:
        s = 1 if m > 0.5 else (-1 if m < 0.5 else 0)
        if s == 0:
            continue
        if prev is not None and s != prev:
            flips += 1
        prev = s
        if s == 1:
            last_lead = k
    f["flips"] = flips
    f["since_lead"] = (t - last_lead) if last_lead is not None else None   # seconds since the cheap side last led (mid > 0.5)
    f["max_mid"] = max(m for _, m in mids) if mids else None
    q6 = c.get(t - 180)
    f["drop3"] = (side_mid(q6, side) - side_mid(q, side)) if q6 is not None else None   # cheap mid fall over 3 min
    return f


# ---------------------------------------------------------------- describe (no result, no quote after the signal)

def _q(xs, p):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    return xs[min(len(xs) - 1, int(p * (len(xs) - 1) + 0.5))]


def describe():
    print("NEWH8 describe: features at the 180 s signal candle only; no result and no later quote is read.\n")
    for series in (BTC, GOLD):
        W = load(series)
        peers = {s: load(s) for s in (BTC, ETH, GOLD) if s != series}
        for st in ("disc", "val"):
            fire, rest = [], []
            for close, w in W.items():
                if stage(close) != st:
                    continue
                q = w["c"].get(-180)
                if q is None:
                    continue
                s = cheap_side(q)
                if s is None:
                    continue
                f = feats(w["c"], s)
                x = w["x"].get(-180)
                if x is not None and x[4] is not None and q[1] > q[0]:
                    loc = (x[4] - q[0]) / (q[1] - q[0])            # last print in the YES spread (1 = at the YES ask)
                    f["loc_cheap"] = loc if s == "yes" else 1 - loc  # 1 = last print bought the cheap side
                else:
                    f["loc_cheap"] = None
                f["ah_al"] = None if x is None or x[0] is None else (x[0] - x[1] if s == "yes" else x[2] - x[3])
                for ps, PW in peers.items():
                    pw = PW.get(close)
                    a = pw["c"].get(-180) if pw else None
                    b = pw["c"].get(-360) if pw else None
                    f["doi_" + ps] = (a[3] - b[3]) if a and b and a[3] is not None and b[3] is not None else None
                f["hour"] = datetime.fromtimestamp(close, timezone.utc).hour
                f["side_yes"] = 1 if s == "yes" else 0
                if f["doi"] is None:
                    continue
                (fire if (series == BTC and f["doi"] > OICORE_TH) else rest).append(f)
            if series == GOLD:
                # gold has no OICORE; describe its own top decile of doi instead
                th = _q([f["doi"] for f in rest], 0.9)
                fire = [f for f in rest if f["doi"] > th]
                rest = [f for f in rest if f["doi"] <= th]
                print(f"{series} {st}: gold's own doi 90th pct {th:,.0f}")
            print(f"{series} {st}: firing {len(fire)}  rest {len(rest)}")
            keys = ["ask", "spread", "vol1", "vol3", "oi", "doi", "flips", "since_lead", "max_mid", "drop3", "n_candles",
                    "loc_cheap", "ah_al", "hour", "side_yes"] + [k for k in (fire[0] if fire else {}) if k.startswith("doi_K")]
            print(f"  {'feature':14s} {'fire p25':>10s} {'p50':>10s} {'p75':>10s} | {'rest p25':>10s} {'p50':>10s} {'p75':>10s}  fire n/a")
            for k in keys:
                a = [f.get(k) for f in fire]
                b = [f.get(k) for f in rest]
                fmt = lambda v: "-" if v is None else (f"{v:10.3f}" if abs(v) < 100 else f"{v:10,.0f}")
                print(f"  {k:14s} {fmt(_q(a, .25)):>10s} {fmt(_q(a, .5)):>10s} {fmt(_q(a, .75)):>10s} | "
                      f"{fmt(_q(b, .25)):>10s} {fmt(_q(b, .5)):>10s} {fmt(_q(b, .75)):>10s}  {sum(v is None for v in a)}")
            # shares
            for name, fn in (("cheap led within 3 min (since_lead <= 180)", lambda f: f["since_lead"] is not None and f["since_lead"] <= 180),
                             ("cheap ever led", lambda f: f["since_lead"] is not None),
                             ("2+ flips", lambda f: f["flips"] >= 2),
                             ("spread >= 2c", lambda f: f["spread"] >= 0.02 - 1e-9),
                             ("cheap mid fell >= 10c in 3 min", lambda f: f["drop3"] is not None and f["drop3"] >= 0.10)):
                sa = sum(fn(f) for f in fire) / max(1, len(fire))
                sb = sum(fn(f) for f in rest) / max(1, len(rest))
                print(f"  share {name:45s} fire {sa:6.1%}  rest {sb:6.1%}")
            print()


# ---------------------------------------------------------------- rules (shared by history and forward)

class Gap(Exception):
    pass


def _need(c, *offs):
    for o in offs:
        if c.get(o) is None:
            raise Gap(f"no candle at {o}")


def _doi(c):
    a, b = c.get(-180), c.get(-360)
    if a is None or b is None or a[3] is None or b[3] is None:
        raise Gap("open interest missing")
    return a[3] - b[3]


def _fill(c, side):
    fr = c.get(-120)
    if fr is None:
        raise Gap("no fill candle")
    a = side_ask(fr, side)
    return a, fr[2]


def _trade(c, side, rule):
    a, fv = _fill(c, side)
    if a is None:
        return {"fill": None}   # no fillable ask: counted as "no fill" by the caller
    return {"side": side, "fill": a, "zv": c[-180][2] <= 0 or fv <= 0, "rule": rule}


def r_oicore(c, P, peers=None):
    _need(c, -180)
    q = c[-180]
    s = cheap_side(q)
    if s is None:
        return None
    if not _doi(c) > OICORE_TH:
        return None
    return _trade(c, s, "OICORE")


def _not_led_3m(c, s):
    return all(side_mid(c[o], s) <= 0.5 for o in (-360, -300, -240, -180))


def r_busycalm(c, P, peers=None):
    _need(c, -180)
    s = cheap_side(c[-180])
    if s is None:
        return None
    _need(c, -360, -300, -240)
    vol3 = c[-300][2] + c[-240][2] + c[-180][2]
    if not vol3 > P["V90"]:
        return None
    if not _not_led_3m(c, s):
        return None
    if not (side_mid(c[-360], s) - side_mid(c[-180], s)) < 0.10:
        return None
    return _trade(c, s, "BUSYCALM")


def r_peeroi(c, P, peers):
    _need(c, -180)
    s = cheap_side(c[-180])
    if s is None:
        return None
    e = peers.get(ETH)
    if e is None:
        raise Gap("no Ethereum window")
    if not _doi(e) > P["E90"]:
        return None
    if _doi(c) > OICORE_TH:
        return None
    return _trade(c, s, "PEEROI-X")


def r_goldx(c, P, peers):
    _need(c, -180)
    s = cheap_side(c[-180])
    if s is None:
        return None
    b = peers.get(BTC)
    if b is None:
        raise Gap("no Bitcoin window")
    if not _doi(b) > OICORE_TH:
        return None
    return _trade(c, s, "GOLDX")


def r_settled(c, P, peers=None):
    _need(c, -180)
    s = cheap_side(c[-180])
    if s is None:
        return None
    _need(c, -360)
    led = [k for k in c if -900 < k <= -180 and side_mid(c[k], s) > 0.5]
    if led and max(led) > -540:
        return None
    if not abs(side_mid(c[-180], s) - side_mid(c[-360], s)) < 0.03:
        return None
    return _trade(c, s, "SETTLED")


RULES = {"R1 BUSYCALM": (BTC, r_busycalm), "R2 PEEROI-X": (BTC, r_peeroi), "R3 GOLDX": (GOLD, r_goldx),
         "R4 SETTLED btc": (BTC, r_settled), "R4 SETTLED gold": (GOLD, r_settled)}


# ---------------------------------------------------------------- scoring

def fee(p, c=10, m=1.0):
    return math.ceil(round(0.07 * c * p * (1 - p) * m * 100, 9)) / 100


def net(t, c=10, m=1.0):
    return c * ((1.0 if t["won"] else 0.0) - t["fill"]) - fee(t["fill"], c, m)


def pf(v):
    g = sum(x for x in v if x > 0)
    l = -sum(x for x in v if x < 0)
    return float("inf") if l == 0 else g / l


def dayz(tr):
    d = defaultdict(float)
    for t in tr:
        d[day(t["close"])] += net(t)
    v = list(d.values())
    if len(v) < 3:
        return float("nan")
    sd = statistics.stdev(v)
    return statistics.mean(v) / (sd / math.sqrt(len(v))) if sd else float("nan")


def thresholds(W):
    """V90 and E90 from discovery-dated features only (no result, no fill)."""
    v3 = []
    for close, w in W[BTC].items():
        if stage(close) != "disc":
            continue
        c = w["c"]
        if all(c.get(o) is not None for o in (-300, -240, -180)) and cheap_side(c[-180]) is not None:
            v3.append(c[-300][2] + c[-240][2] + c[-180][2])
    ed = []
    for close, w in W[ETH].items():
        if stage(close) != "disc":
            continue
        try:
            ed.append(_doi(w["c"]))
        except Gap:
            pass
    return {"V90": _q90(v3), "E90": _q90(ed), "n_v3": len(v3), "n_ed": len(ed)}


def _q90(xs):
    xs = sorted(xs)
    k = (len(xs) - 1) * 0.9
    lo = math.floor(k)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def apply(series, fn, W, P):
    out, gaps, nofill = [], 0, 0
    for close, w in sorted(W[series].items()):
        peers = {s: W[s][close]["c"] for s in (BTC, ETH, GOLD) if s != series and close in W[s]}
        try:
            t = fn(w["c"], P, peers)
        except Gap:
            gaps += 1
            continue
        if t is None:
            continue
        if t["fill"] is None:
            nofill += 1
            continue
        t.update(close=close, won=w["result"] == t["side"], stage=stage(close))
        out.append(t)
    return out, gaps, nofill


def summ(tr):
    if not tr:
        return {"n": 0}
    n10 = [net(t) for t in tr]
    return {"n": len(tr), "pf10": pf(n10), "pf1": pf([net(t, 1) for t in tr]), "pfx": pf([net(t, 10, 1.2) for t in tr]),
            "netx": sum(net(t, 10, 1.2) for t in tr), "net10": sum(n10), "win": sum(t["won"] for t in tr) / len(tr),
            "fill": statistics.mean(t["fill"] for t in tr), "z": dayz(tr), "days": len({day(t["close"]) for t in tr}),
            "pf10_nz": pf([net(t) for t in tr if not t["zv"]]), "n_zv": sum(t["zv"] for t in tr)}


def fmt(s):
    if s["n"] == 0:
        return "n 0"
    return (f"n {s['n']} ({s['days']} d) PF10 {s['pf10']:.2f} PF1 {s['pf1']:.2f} PFx1.2 {s['pfx']:.2f} netx1.2 ${s['netx']:.2f} "
            f"win {s['win']:.1%} fill {s['fill']:.3f} z {s['z']:.2f} | zero-vol {s['n_zv']}, PF10 without {s['pf10_nz']:.2f}")


def verdict(d, v):
    if d["n"] < 100:
        return "NOT_ENOUGH_DATA"
    if d["pf10"] < 1.5 or d["netx"] <= 0:
        return "FALSIFIED"
    if v["n"] < 50:
        return "NOT_ENOUGH_DATA"
    if v["pf10"] < 1.3 or v["netx"] <= 0:
        return "FALSIFIED"
    return "NOT_YET_FALSIFIED"


def overlap(tr, ref, by_close_only=False):
    out = {}
    for st in ("disc", "val"):
        a = {t["close"] for t in tr if t["stage"] == st}
        b = {t["close"] for t in ref if t["stage"] == st}
        j = len(a & b) / len(a | b) if (a | b) else float("nan")
        out[st] = (j, len(a & b) / len(b) if b else float("nan"), len(a & b) / len(a) if a else float("nan"))
    return out


def run():
    W = {s: load(s) for s in (BTC, ETH, GOLD)}
    P = thresholds(W)
    print("NEWH8 run (once). windows:", {s: len(v) for s, v in W.items()})
    print(f"cut points (discovery features only): V90 = {P['V90']:,.1f} (from {P['n_v3']} windows), "
          f"E90 = {P['E90']:,.1f} (from {P['n_ed']} windows), OICORE {OICORE_TH:,.2f}\n")
    ref, rg, rn = apply(BTC, r_oicore, W, P)
    print("REF OICORE (reproduction):")
    for st in ("disc", "val"):
        print(f"  {st}: " + fmt(summ([t for t in ref if t["stage"] == st])))
    print(f"  gaps {rg}, no fill {rn}\n")
    results = {}
    for name, (series, fn) in RULES.items():
        tr, g, nf = apply(series, fn, W, P)
        d = summ([t for t in tr if t["stage"] == "disc"])
        v = summ([t for t in tr if t["stage"] == "val"])
        vd = verdict(d, v)
        ov = overlap(tr, ref)
        print(f"{name} [{series}]  gaps {g}, no fill {nf}")
        print(f"  disc: {fmt(d)}")
        print(f"  val : {fmt(v)}")
        for st in ("disc", "val"):
            j, sr, sa = ov[st]
            print(f"  overlap with OICORE {st}: Jaccard {j:.3f}, share of OICORE entries {sr:.3f}, share of this rule's entries {sa:.3f}")
        dep = max(max(ov[st][0], ov[st][1], ov[st][2]) for st in ov if not math.isnan(ov[st][0]))
        print(f"  VERDICT {vd}" + ("  (not independent of OICORE: overlap over 0.5)" if dep > 0.5 else "") + "\n")
        results[name] = (d, v, vd)
    # information looks I1, I2 on OICORE's own entries
    print("Information (counted in N, not screened): OICORE entries split")
    for lab, cond in (("I1 calm (|cheap mid change -360..-180| < 0.03)",
                       lambda w, t: abs(side_mid(w["c"][-180], t["side"]) - side_mid(w["c"][-360], t["side"])) < 0.03),
                      ("I2 not led in last 3 min", lambda w, t: _not_led_3m(w["c"], t["side"]))):
        for st in ("disc", "val"):
            x = [t for t in ref if t["stage"] == st]
            yes = [t for t in x if cond(W[BTC][t["close"]], t)]
            no = [t for t in x if not cond(W[BTC][t["close"]], t)]
            print(f"  {lab} {st}: TRUE {fmt(summ(yes))}")
            print(f"  {' ' * len(lab)} {st}: FALSE {fmt(summ(no))}")
    # I3 (added after the first read, counted): R1's entries outside and inside OICORE's windows
    rc = {t["close"] for t in ref}
    r1, _, _ = apply(BTC, r_busycalm, W, P)
    for st in ("disc", "val"):
        x = [t for t in r1 if t["stage"] == st]
        print(f"  I3 BUSYCALM outside OICORE {st}: {fmt(summ([t for t in x if t['close'] not in rc]))}")
        print(f"  I3 BUSYCALM inside OICORE  {st}: {fmt(summ([t for t in x if t['close'] in rc]))}")
    return results


# ---------------------------------------------------------------- forward

FROZEN = {}   # filled by a survivor's candidate params; nothing frozen unless a rule passed both screens


def forward_eval(window, params):
    """A NEWH8 rule on one forward window (source "candles"). params: {"rule": name, "V90": .., "E90": ..}."""
    from .fwdeval import NoData
    name = params["rule"]
    series, fn = RULES[name]
    if window["series"] != series:
        return None
    ct = window["close_ts"]
    c = {k - ct: v for k, v in window["candles"].items()}
    peers = {s: {k - ct: v for k, v in pc.items()} for s, pc in window.get("peers", {}).items()}
    try:
        t = fn(c, params, peers)
    except Gap as e:
        raise NoData(str(e))
    if t is None or t["fill"] is None:
        return None
    return {"side": t["side"], "entry": float(t["fill"]), "exit": None, "t": ct - 120, "zero_volume": bool(t["zv"]),
            "note": f"NEWH8 {name}, cheap side at 180 s, fill at the 120 s candle's ask"}


if __name__ == "__main__":
    {"describe": describe, "run": run}[sys.argv[1]]()
