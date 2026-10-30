"""NEWH3: three new mechanisms on Kalshi's 15 minute Bitcoin market (research only).

Registration: workers/NEWH3_REGISTRATION.md (pushed before any scoring).
H1 BLADX (a: buy the 15 minute side the hourly ladder calls cheap; b: buy the ladder side the 15 minute book calls cheap),
H2 WIDEN (cheap side after the spread widens in the last 5 minutes), H3 EXITOI (L1 exit when open interest falls 5% from 360 s to
180 s). Fill at the next candle's closing ask, held, C = 10 screen, fee rounded up per order.

    PYTHONPATH=src python -m scalper.newh3 run
"""
from __future__ import annotations

import math
import sqlite3
import statistics
from collections import defaultdict

from .newh2 import START, DISC_END, END, day, fee, net, pf, side_ask, mid, dayz, summ, line, verdict
from .paths import DATA_DIR

BTC, LADDER = "KXBTC15M", "KXBTCD"
FILES = ("l1b", "book", "fresh")
LFILES = ("lad2", "conf2_lad")


def load15(files=FILES, start=START, end=END):
    """{close: {ticker, close, result, strike, c: {offset: (bid, ask, vol, oi)}}}; first file wins per ticker."""
    win, seen = {}, set()
    for name in files:
        p = DATA_DIR / f"{name}.sqlite"
        if not p.exists():
            continue
        db = sqlite3.connect(p)
        for tk, close, res, k in db.execute(
                "select ticker, close_ts, result, strike from market where series=? and close_ts>=? and close_ts<?",
                (BTC, start, end)).fetchall():
            if tk in seen or close in win or res not in ("yes", "no"):
                continue
            cs = {e - close: (b, a, v or 0.0, oi) for e, b, a, v, oi in db.execute(
                "select end_ts, bid_c, ask_c, volume, oi from candle where ticker=? and bid_c is not null and ask_c is not null", (tk,))}
            if not cs:
                continue
            seen.add(tk)
            win[close] = {"ticker": tk, "close": close, "result": res, "strike": k, "c": cs}
    return win


def load_ladder(start=START, end=END):
    """{close: [(strike, result, {end_ts: (bid, ask, vol)})]}; first file wins per ticker."""
    lad, seen = defaultdict(list), set()
    for name in LFILES:
        db = sqlite3.connect(DATA_DIR / f"{name}.sqlite")
        for tk, close, res, k in db.execute(
                "select ticker, close_ts, result, strike from market where series=? and close_ts>=? and close_ts<?",
                (LADDER, start, end)).fetchall():
            if tk in seen or res not in ("yes", "no") or k is None:
                continue
            cs = {e: (b, a, v or 0.0) for e, b, a, v in db.execute(
                "select end_ts, bid_c, ask_c, volume from candle where ticker=? and bid_c is not null and ask_c is not null", (tk,))}
            seen.add(tk)
            lad[close].append((k, res, cs))
    return lad


def ok_quote(r):
    return r is not None and r[0] > 0 and r[1] < 1 and r[1] - r[0] <= 0.05 + 1e-9


def lad_at(cs, t, maxage=300):
    best = None
    for e in range(t, t - maxage - 1, -60):
        if e in cs:
            best = cs[e]
            break
    return best


def trade(close, side, a, won, vol0):
    return {"close": close, "day": day(close), "side": side, "fill": a, "won": won, "vol0": vol0,
            "n1": net(a, won, 1), "n10": net(a, won, 10), "n10x": net(a, won, 10, 1.2)}


# ---------- H1 BLADX ----------

def h1(W, L):
    A, B, gaps = [], [], defaultdict(int)
    for close, w in W.items():
        if close % 3600:
            continue
        gaps["closes"] += 1
        strikes = L.get(close)
        k0 = w["strike"]
        if not strikes or k0 is None:
            gaps["no ladder"] += 1
            continue
        lo = max((s for s in strikes if s[0] <= k0), key=lambda s: s[0], default=None)
        hi = min((s for s in strikes if s[0] > k0), key=lambda s: s[0], default=None)
        if lo is None or hi is None or hi[0] - lo[0] > 250:
            gaps["no bracket"] += 1
            continue
        sig = None
        for off in range(-840, -239, 60):
            r15 = w["c"].get(off)
            if not ok_quote(r15):
                continue
            ql, qh = lad_at(lo[2], close + off), lad_at(hi[2], close + off)
            if not (ok_quote(ql) and ok_quote(qh)):
                continue
            p = mid(ql) + (mid(qh) - mid(ql)) * (k0 - lo[0]) / (hi[0] - lo[0])
            d = mid(r15) - p
            if abs(d) >= 0.06 - 1e-9:
                sig = (off, d)
                break
        if sig is None:
            gaps["no signal"] += 1
            continue
        gaps["signals"] += 1
        off, d = sig
        # H1a: the 15 minute side the ladder calls cheap
        side = "yes" if d < 0 else "no"
        fr = w["c"].get(off + 60)
        a = side_ask(fr, side)
        if a is not None and 0.10 <= a <= 0.90:
            A.append(trade(close, side, a, w["result"] == side, fr[2] == 0))
        else:
            gaps["a no fill"] += 1
        # H1b: the ladder side the 15 minute book calls cheap, on the strike nearer K0
        near = lo if (k0 - lo[0]) <= (hi[0] - k0) else hi
        lside = "yes" if d > 0 else "no"
        lr = near[2].get(close + off + 60)
        la = side_ask(lr, lside)
        if la is not None and 0.10 <= la <= 0.90:
            B.append(trade(close, lside, la, near[1] == lside, lr[2] == 0))
        else:
            gaps["b no fill"] += 1
    return A, B, dict(gaps)


# ---------- H2 WIDEN ----------

def h2(W):
    T, C, gaps = [], [], defaultdict(int)
    for close, w in W.items():
        base = [r[1] - r[0] for o, r in w["c"].items() if -840 <= o <= -420 and r[0] > 0 and r[1] < 1]
        if len(base) < 4:
            gaps["no baseline"] += 1
            continue
        b = statistics.median(base)
        sig, ctrl = None, None
        for off in range(-300, -119, 60):
            r = w["c"].get(off)
            if r is None or not (r[0] > 0 and r[1] < 1):
                continue
            m = mid(r)
            if not (0.15 <= m <= 0.85):
                continue
            if r[1] - r[0] >= max(0.04, 2 * b) - 1e-9:
                sig = (off, m)
                break
            if ctrl is None:
                ctrl = (off, m)
        for tgt, s, tag in ((T, sig, "sig"), (C, None if sig else ctrl, "ctrl")):
            if s is None:
                continue
            off, m = s
            if abs(m - 0.5) < 1e-9:
                continue
            side = "no" if m > 0.5 else "yes"
            fr = w["c"].get(off + 60)
            a = side_ask(fr, side)
            if a is not None and 0.05 <= a <= 0.50:
                tgt.append(trade(close, side, a, w["result"] == side, fr[2] == 0))
            else:
                gaps[f"{tag} no fill"] += 1
        if sig:
            gaps["signals"] += 1
    return T, C, dict(gaps)


# ---------- H3 EXITOI ----------

def side_bid(r, side):
    if r is None:
        return None
    b = r[0] if side == "yes" else round(1 - r[1], 6)
    return b if 0 < b < 1 else None


def h3(W):
    E, gaps = [], defaultdict(int)
    for close, w in W.items():
        c = w["c"]
        s = c.get(-360)
        if s is None:
            continue
        side = None
        for sd in ("yes", "no"):
            a = side_ask(s, sd)
            if a is not None and 0.88 <= a <= 0.97:
                side = sd
                break
        if side is None:
            continue
        fr = c.get(-300)
        a = side_ask(fr, side)
        if a is None or a > 0.99:
            gaps["no fill"] += 1
            continue
        won = w["result"] == side
        hold = {k: net(a, won, cc, m) for k, cc, m in (("n1", 1, 1.0), ("n10", 10, 1.0), ("n10x", 10, 1.2))}
        o0, o1 = (c.get(-360) or (0, 0, 0, None))[3], (c.get(-180) or (0, 0, 0, None))[3]
        trig = bool(o0 and o1 is not None and o1 <= 0.95 * o0)
        if not (o0 and o1 is not None):
            gaps["oi missing"] += 1
        rule = dict(hold)
        sold = False
        if trig:
            sb = side_bid(c.get(-120), side)
            if sb is not None:
                sold = True
                rule = {k: cc * (sb - a) - fee(a, cc, m) - fee(sb, cc, m) for k, cc, m in (("n1", 1, 1.0), ("n10", 10, 1.0), ("n10x", 10, 1.2))}
            else:
                gaps["trig no bid"] += 1
        b120, b60 = side_bid(c.get(-120), side), side_bid(c.get(-60), side)
        sag = (b60 - b120) if (b120 is not None and b60 is not None) else None
        E.append({"close": close, "day": day(close), "fill": a, "won": won, "vol0": fr[2] == 0, "trig": trig, "sold": sold,
                  "hold": hold, "rule": rule, "sag": sag})
    return E, dict(gaps)


def h3_report(E, name):
    if not E:
        return {"n": 0}, f"{name}: n 0"
    hp, rp = pf([e["hold"]["n10"] for e in E]), pf([e["rule"]["n10"] for e in E])
    hpx, rpx = pf([e["hold"]["n10x"] for e in E]), pf([e["rule"]["n10x"] for e in E])
    hp1, rp1 = pf([e["hold"]["n1"] for e in E]), pf([e["rule"]["n1"] for e in E])
    tr = [e for e in E if e["trig"]]
    un = [e for e in E if not e["trig"]]
    dd = defaultdict(float)
    for e in E:
        dd[e["day"]] += e["rule"]["n10"] - e["hold"]["n10"]
    v = list(dd.values())
    sd = statistics.stdev(v) if len(v) > 2 else 0
    z = statistics.mean(v) / (sd / math.sqrt(len(v))) if sd else float("nan")
    sg = lambda xs: statistics.mean(xs) if xs else float("nan")
    out = {"n": len(E), "trig": len(tr), "sold": sum(e["sold"] for e in E), "hold_pf": hp, "rule_pf": rp, "diff_net": sum(v), "z": z,
           "dv": v}
    s = (f"{name}: entries {len(E)} triggered {len(tr)} sold {out['sold']} | hold PF10 {hp:.3f} rule PF10 {rp:.3f} (x1.2 {hpx:.3f} / {rpx:.3f};"
         f" C1 {hp1:.3f} / {rp1:.3f}) | rule-hold net10 ${sum(v):+.2f} day z {z:+.2f}\n"
         f"    loss rate triggered {1 - sg([e['won'] for e in tr]):.3f} untriggered {1 - sg([e['won'] for e in un]):.3f}; "
         f"mean fill trig {sg([e['fill'] for e in tr]):.3f}\n"
         f"    sag (side bid 60 s minus 120 s): triggered {sg([e['sag'] for e in tr if e['sag'] is not None]):+.4f} "
         f"(n {sum(e['sag'] is not None for e in tr)}) untriggered {sg([e['sag'] for e in un if e['sag'] is not None]):+.4f}"
         f"\n    triggered only: hold net10 ${sum(e['hold']['n10'] for e in tr):+.2f} sold net10 ${sum(e['rule']['n10'] for e in tr):+.2f}")
    return out, s


def run():
    W = load15()
    L = load_ladder()
    split = lambda xs: ([x for x in xs if x["close"] < DISC_END], [x for x in xs if x["close"] >= DISC_END])
    print(f"NEWH3 run. BTC 15 minute windows {len(W)} (disc {sum(c < DISC_END for c in W)}, val {sum(c >= DISC_END for c in W)}); "
          f"ladder closes {len(L)}; nothing on or after 2026-10-28 loaded.\n")
    verdicts = {}
    A, B, g1 = h1(W, L)
    print("H1 BLADX gaps:", g1)
    for name, tr in (("H1a BLADX_15M", A), ("H1b BLADX_LAD", B)):
        d, v = split(tr)
        sd, sv = summ(d), summ(v)
        print(line(name + " disc", sd)); print(line(name + " val", sv))
        verdicts[name] = verdict(sd, sv)
    T, C, g2 = h2(W)
    print("\nH2 WIDEN gaps:", g2)
    d, v = split(T)
    sd, sv = summ(d), summ(v)
    print(line("H2 WIDEN disc", sd)); print(line("H2 WIDEN val", sv))
    verdicts["H2 WIDEN"] = verdict(sd, sv)
    cd, cv = split(C)
    print(line("H2 control disc", summ(cd))); print(line("H2 control val", summ(cv)))
    E, g3 = h3(W)
    print("\nH3 EXITOI gaps:", g3)
    d, v = split(E)
    od, sd_ = h3_report(d, "H3 disc"); ov, sv_ = h3_report(v, "H3 val")
    print(sd_); print(sv_)
    allv = od.get("dv", []) + ov.get("dv", [])
    sdv = statistics.stdev(allv) if len(allv) > 2 else 0
    zp = statistics.mean(allv) / (sdv / math.sqrt(len(allv))) if sdv else float("nan")
    print(f"    pooled day z of rule minus hold {zp:+.2f}")
    if od["n"] == 0 or od["trig"] < 50 or ov["trig"] < 50:
        verdicts["H3 EXITOI"] = "NOT_ENOUGH_DATA"
    elif od["rule_pf"] >= od["hold_pf"] + 0.03 and ov["rule_pf"] >= ov["hold_pf"] + 0.03 and zp >= 2.0:
        verdicts["H3 EXITOI"] = "NOT_YET_FALSIFIED"
    else:
        verdicts["H3 EXITOI"] = "FALSIFIED"
    print("\nVerdicts:")
    for k, x in verdicts.items():
        print(f"  {k}: {x}")


if __name__ == "__main__":
    run()
