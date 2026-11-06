#!/usr/bin/env python3
"""FUNDP1, CARRY1, BASIS1 scorer (registered in workers/FUNDP1_REGISTRATION.md etc. before it was run).
Reads every commit of origin/perp-data (git show), de-duplicates by (ts, ticker), keeps ONLY dates <= CUT (the held-out dates are never loaded).
Usage: python3 -I fundcarry.py REPO_DIR OUT_JSON"""
import csv, io, json, math, subprocess, sys, statistics as st
from datetime import datetime as D

CUT = "2026-10-31"          # last development date (inclusive); 2026-11-01 onward is held out and never read
D1_END = "2026-10-26"       # D1 = 2026-10-21..10-26, D2 = 2026-10-27..10-31
UNIVERSE = ["KXGOLDPERP", "KXUS500PERP", "KXUSTECH100PERP", "KXSILVERPERP", "KXWTIFUTURE", "KXCOPPERPERP"]
THRESH = 0.0010
HOLD_MIN, HOLD_MAX = 7 * 3600, 12 * 3600
AMEND1 = len(sys.argv) > 3 and sys.argv[3] == "amend1"
FEES = {"verdict": 0.0005, "stress": 0.0012}


def git(repo, *a):
    return subprocess.run(["git", "-C", repo] + list(a), capture_output=True, text=True, check=True).stdout


def load(repo):
    seen = {}
    for c in git(repo, "log", "origin/perp-data", "--format=%h").split():
        for f in git(repo, "show", c, "--name-only", "--format=").split():
            day = f.rsplit("perps-", 1)[-1][:10]
            if day > CUT:
                continue                      # a held-out day's file is not even opened
            for r in csv.DictReader(io.StringIO(git(repo, "show", c + ":" + f))):
                if r["ts_utc"][:10] <= CUT:
                    seen[(r["ts_utc"], r["ticker"])] = r
    return seen


def ts(s):
    return D.strptime(s, "%Y-%m-%dT%H:%M:%SZ").timestamp()


def quote(r):
    try:
        if r["status"] != "active":
            return None
        b, a, ref = float(r["bid"]), float(r["ask"]), float(r["reference_price"])
        if not (0 < b <= a) or ref <= 0:
            return None
        if AMEND1 and a > 2 * b:      # Amendment 1 (after the as-registered run): an ask of 9.2e14 (int64 no-ask sentinel) is not a quote
            return None
        return dict(b=b, a=a, m=(a + b) / 2, ref=ref, prem=(a + b) / 2 / ref - 1, db=float(r["funding_deadband"]), cap=float(r["funding_cap"]))
    except (ValueError, KeyError):
        return None


def funding(p_in, p_out, q, hold):
    pbar = (p_in + p_out) / 2
    x = min(max(abs(pbar) - q["db"], 0.0), q["cap"])
    return math.copysign(x, pbar) * hold / (8 * 3600)      # sign of premium; positive = longs pay shorts


def day_z(by_day):
    ds = [sum(v) / len(v) for v in by_day.values() if v]
    if len(ds) < 3:
        return None
    sd = st.stdev(ds)
    return st.mean(ds) / (sd / math.sqrt(len(ds))) if sd > 0 else None


def main(repo, out):
    seen = load(repo)
    times = sorted(set(k[0] for k in seen))
    T = {t: ts(t) for t in times}
    qs = {t: {} for t in times}
    for (t, k), r in seen.items():
        if k in UNIVERSE:
            q = quote(r)
            if q:
                qs[t][k] = q
    def exit_time(t):
        for u in times:
            if HOLD_MIN <= T[u] - T[t] <= HOLD_MAX:
                return u
        return None
    res = {}
    fundp = {k: [] for k in FEES}; fund_days = {k: {} for k in FEES}
    carry = {k: [] for k in FEES}
    basis = []
    census = dict(entries=0, over_cap=0, inside_deadband=0)
    for t in times:
        u = exit_time(t)
        if not u:
            continue
        day = t[:10]; hold = T[u] - T[t]
        legs = {}
        for k, q in qs[t].items():
            q2 = qs[u].get(k)
            if not q2:
                continue
            census["entries"] += 1
            census["over_cap"] += abs(q["prem"]) >= q["cap"]
            census["inside_deadband"] += abs(q["prem"]) <= q["db"]
            legs[k] = (q, q2)
            if abs(q["prem"]) > THRESH and abs(q["prem"]) < q["cap"]:
                side = -1 if q["prem"] > 0 else 1                  # fade the premium: short when positive
                entry = q["a"] if side > 0 else q["b"]
                exitp = q2["b"] if side > 0 else q2["a"]
                f = funding(q["prem"], q2["prem"], q, hold)
                gross = side * (exitp / entry - 1)
                recv = -side * f                                    # long pays f when f>0
                for name, fee in FEES.items():
                    r = gross + recv - 2 * fee
                    fundp[name].append((day, r))
                spread_rt = (q["a"] - q["b"]) / q["m"] + (q2["a"] - q2["b"]) / q2["m"]
                basis.append((day, abs(recv) if recv > 0 else recv, spread_rt, side, q["prem"], q2["prem"], recv))
        if len(legs) >= 4:
            ranked = sorted(legs, key=lambda k: legs[k][0]["prem"])
            lo, hi = ranked[0], ranked[-1]
            if legs[lo][0]["prem"] < legs[hi][0]["prem"]:
                tot = {n: 0.0 for n in FEES}
                gross = 0.0
                for k, side in ((lo, 1), (hi, -1)):
                    q, q2 = legs[k]
                    entry = q["a"] if side > 0 else q["b"]
                    exitp = q2["b"] if side > 0 else q2["a"]
                    gross += side * (exitp / entry - 1) - side * funding(q["prem"], q2["prem"], q, hold)
                for name, fee in FEES.items():
                    carry[name].append((day, gross - 4 * fee))
    def summarize(rows):
        out = {}
        if not rows:
            return dict(n=0)
        by = {}
        for d, r in rows:
            by.setdefault(d, []).append(r)
        out["n"] = len(rows); out["days"] = len(by); out["mean_bp"] = 1e4 * st.mean(r for _, r in rows)
        out["win"] = sum(r > 0 for _, r in rows) / len(rows)
        out["z_day"] = day_z(by)
        for nm, sel in (("D1", lambda d: d <= D1_END), ("D2", lambda d: d > D1_END)):
            sub = [r for d, r in rows if sel(d)]
            out[nm] = dict(n=len(sub), mean_bp=1e4 * st.mean(sub) if sub else None)
        return out
    res["FUNDP1"] = {n: summarize(fundp[n]) for n in FEES}
    res["CARRY1"] = {n: summarize(carry[n]) for n in FEES}
    # BASIS1: funding collected by the fading side vs round-trip cost
    if basis:
        b_rows = [(d, recv) for d, _, _, _, _, _, recv in basis]
        cost = [(d, 2 * 0.0005 + sp) for d, _, sp, *_ in basis]
        conv = [1 - abs(p2) / abs(p1) for _, _, _, _, p1, p2, _ in basis]
        diff = [(d, recv - c) for (d, recv), (_, c) in zip(b_rows, cost)]
        res["BASIS1"] = dict(entries=len(basis), mean_funding_bp=1e4 * st.mean(r for _, r in b_rows), mean_cost_bp=1e4 * st.mean(c for _, c in cost),
                             mean_convergence=st.mean(conv), median_convergence=st.median(conv), diff=summarize(diff), days=len(set(d for d, *_ in basis)))
    else:
        res["BASIS1"] = dict(entries=0)
    res["census"] = census
    res["samples"] = len(times)
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
