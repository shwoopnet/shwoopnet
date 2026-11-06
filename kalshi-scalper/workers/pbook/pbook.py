#!/usr/bin/env python3
"""PBOOK1 to PBOOK3 scorer (registered in workers/PBOOK{1,2,3}_REGISTRATION.md before any return was computed).
Order-book shape of Kalshi's perps from the hourly recorder. Reuses the loader of workers/fundcarry/fundcarry.py, which opens only dates <= 2026-10-31
(dates 2026-11-01 onward are held out and never loaded).
Usage: python3 -I pbook.py REPO_DIR [--census]"""
import math, os, sys, statistics as st
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fundcarry"))
import fundcarry as fc

D1_END = "2026-10-26"
MIN_GAP, MAX_GAP = 1800, 12 * 3600       # next sample must be 0.5 to 12 hours later
FEE = {"verdict": 0.0012, "stress": 0.0005}   # per side; 12 bp is the unverified placeholder
SPREAD_MAX_BP = 5.0                       # universe: median recorded spread <= 5 bp of mid
MIN_SAMPLES = 40
MIN_DAYS, MIN_EVENTS = 10, 60
Z_BAR = 5.27


def build(repo):
    seen = fc.load(repo)
    times = sorted(set(k[0] for k in seen))
    T = {t: fc.ts(t) for t in times}
    S = {}
    for (t, k), r in seen.items():
        q = fc.quote(r)
        if not q:
            continue
        if q["a"] > 2 * q["b"]:
            continue
        try:
            bs, as_ = float(r["bid_size"]), float(r["ask_size"])
        except ValueError:
            continue
        if not (math.isfinite(bs) and math.isfinite(as_)) or bs < 0 or as_ < 0 or bs + as_ <= 0 or bs > 1e12 or as_ > 1e12:
            continue
        q["bs"], q["as"] = bs, as_
        S.setdefault(k, []).append((T[t], t, q))
    for k in S:
        S[k].sort(key=lambda x: x[0])
    return S


def universe(S):
    out = []
    for k, v in S.items():
        sp = [(q["a"] - q["b"]) / q["m"] * 1e4 for _, _, q in v]
        if len(v) >= MIN_SAMPLES and st.median(sp) <= SPREAD_MAX_BP:
            out.append(k)
    return sorted(out)


def pairs(v):
    """(index i, index j) with j the first later sample 0.5 to 12 hours after i."""
    out = []
    for i in range(len(v)):
        for j in range(i + 1, len(v)):
            g = v[j][0] - v[i][0]
            if g > MAX_GAP:
                break
            if g >= MIN_GAP:
                out.append((i, j))
                break
    return out


def trade(side, qi, qj, fee):
    """side +1 long: buy the ask, sell the bid; side -1 short: sell the bid, buy the ask. Returns net fraction."""
    if side > 0:
        gross = qj["b"] / qi["a"] - 1
    else:
        gross = 1 - qj["a"] / qi["b"]
    return gross - 2 * fee, gross


def summarize(rows, name):
    """rows: (date, net_verdict, net_stress, gross, extra)"""
    by = {}
    for r in rows:
        by.setdefault(r[0], []).append(r[1])
    days = sorted(by)
    out = {"name": name, "events": len(rows), "days": len(days)}
    if not rows:
        return out
    out["mean_net_bp"] = st.mean(r[1] for r in rows) * 1e4
    out["mean_stress_bp"] = st.mean(r[2] for r in rows) * 1e4
    out["mean_gross_bp"] = st.mean(r[3] for r in rows) * 1e4
    out["win"] = sum(1 for r in rows if r[1] > 0) / len(rows)
    out["day_z"] = fc.day_z(by)
    for lab, sel in (("D1", lambda d: d <= D1_END), ("D2", lambda d: d > D1_END)):
        s = [r for r in rows if sel(r[0])]
        out[lab] = (len(s), st.mean(r[1] for r in s) * 1e4 if s else None, st.mean(r[3] for r in s) * 1e4 if s else None)
    return out


def verdict(o):
    if o["events"] < MIN_EVENTS or o["days"] < MIN_DAYS:
        return "NOT_ENOUGH_DATA"
    if o["mean_net_bp"] <= 0:
        return "FALSIFIED"
    z = o["day_z"]
    if z is not None and z >= Z_BAR and o["D1"][1] and o["D2"][1] and o["D1"][1] > 0 and o["D2"][1] > 0:
        return "LEAD"
    return "FALSIFIED"   # positive but under the deflated bar is not a lead


def t1(S, U):   # PBOOK1: touch-size imbalance, follow the heavy side
    rows = []
    for k in U:
        v = S[k]
        for i, j in pairs(v):
            qi, qj = v[i][2], v[j][2]
            imb = (qi["bs"] - qi["as"]) / (qi["bs"] + qi["as"])
            if abs(imb) < 0.5:
                continue
            side = 1 if imb > 0 else -1
            n, g = trade(side, qi, qj, FEE["verdict"])
            ns, _ = trade(side, qi, qj, FEE["stress"])
            rows.append((v[i][1][:10], n, ns, g))
    return rows


def expanding_median(vals, idx, minprior=10):
    prior = vals[:idx]
    return st.median(prior) if len(prior) >= minprior else None


def t2(S, U):   # PBOOK2: spread blowout (>=3x own prior median), fade the mid displacement since the previous sample
    rows = []
    sig = 0
    for k in U:
        v = S[k]
        sp = [(q["a"] - q["b"]) / q["m"] for _, _, q in (x for x in v)]
        for i, j in pairs(v):
            if i < 1:
                continue
            med = expanding_median(sp, i)
            if med is None or sp[i] < 3 * med:
                continue
            if v[i][0] - v[i - 1][0] > MAX_GAP:
                continue
            d = v[i][2]["m"] / v[i - 1][2]["m"] - 1
            if d == 0:
                continue
            side = -1 if d > 0 else 1
            n, g = trade(side, v[i][2], v[j][2], FEE["verdict"])
            ns, _ = trade(side, v[i][2], v[j][2], FEE["stress"])
            rows.append((v[i][1][:10], n, ns, g))
    return rows


def t3(S, U):   # PBOOK3: mid vs reference gap (>=3x own prior median |gap| and >=10 bp), fade it; also gap closure
    rows = []
    for k in U:
        v = S[k]
        gap = [q["m"] / q["ref"] - 1 for _, _, q in v]
        ag = [abs(x) for x in gap]
        for i, j in pairs(v):
            med = expanding_median(ag, i)
            if med is None or ag[i] < 10e-4 or ag[i] < 3 * med:
                continue
            side = -1 if gap[i] > 0 else 1
            n, g = trade(side, v[i][2], v[j][2], FEE["verdict"])
            ns, _ = trade(side, v[i][2], v[j][2], FEE["stress"])
            rows.append((v[i][1][:10], n, ns, g, 1 - ag[j] / ag[i]))
    return rows


def main(repo):
    S = build(repo)
    U = universe(S)
    print("universe (median spread <= %.0f bp, >= %d samples):" % (SPREAD_MAX_BP, MIN_SAMPLES), U)
    if "--census" in sys.argv:
        return
    for name, f in (("PBOOK1", t1), ("PBOOK2", t2), ("PBOOK3", t3)):
        rows = f(S, U)
        o = summarize(rows, name)
        print(name, verdict(o), o)
        if name == "PBOOK3" and rows:
            cl = [r[4] for r in rows]
            print("PBOOK3 gap closure mean %.3f median %.3f" % (st.mean(cl), st.median(cl)))


if __name__ == "__main__":
    main(sys.argv[1])
