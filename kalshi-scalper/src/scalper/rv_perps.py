"""RV1 to RV3 (workers/RV*_REGISTRATION.md): relative value between Kalshi perps. Research only.
Reads origin/perp-data hourly snapshots; rows from 2026-11-01 on (holdout) are dropped on load."""
from __future__ import annotations
import csv, io, math, statistics as st, subprocess, sys
from collections import defaultdict

CUT = "2026-11-01"
D1_END = "2026-10-27"
FEE, FUND_DAY, MAXQ = 0.0012, 0.0002, 5.0
H = ["ts", "tk", "ac", "status", "bid", "ask", "bs", "as_", "price", "ref"]


def tsec(s):
    import datetime as d
    return d.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=d.timezone.utc).timestamp()


def load(repo="."):
    g = lambda *a: subprocess.run(["git", *a], cwd=repo, capture_output=True, text=True).stdout
    seen, rows = set(), []
    for c in g("log", "--format=%h", "origin/perp-data").split():
        for f in g("show", c, "--name-only", "--format=").split():
            if not f.endswith(".csv"):
                continue
            for r in csv.reader(io.StringIO(g("show", f"{c}:{f}"))):
                if not r or r[0] == "ts_utc" or r[0] >= CUT:
                    continue
                k = (r[0], r[1])
                if k in seen:
                    continue
                seen.add(k)
                rows.append(dict(zip(H, r[:10])))
    return rows


def quote(r):
    try:
        b, a = float(r["bid"]), float(r["ask"])
    except ValueError:
        return None
    if r["status"] != "active" or b <= 0 or a <= 0 or a < b or a > 10 * b:  # Amendment 1: a > 10 x bid is the int64 sentinel, a data defect
        return None
    ref = float(r["ref"]) if r["ref"] else 0.0
    return b, a, ref


def spread_bp(r):
    q = quote(r)
    return (q[1] - q[0]) / ((q[1] + q[0]) / 2) * 1e4 if q else None


def trades(series, legs, sign=1, thr=1.0):
    """series: list of (ts, s, quotes-by-leg). legs: dict leg -> unit (+1 buy when z<-thr). Returns list of trades."""
    out, i, n = [], 0, len(series)
    while i < n:
        hist = [x[1] for x in series[max(0, i - 20):i]]
        if len(hist) < 12:
            i += 1; continue
        sd = st.pstdev(hist)
        if sd <= 0:
            i += 1; continue
        z = (series[i][1] - st.mean(hist)) / sd
        if abs(z) < thr:
            i += 1; continue
        j = next((k for k in range(i + 1, n) if 4 * 3600 <= series[k][0] - series[i][0] <= 8 * 3600), None)
        if j is None:
            i += 1; continue
        side = -sign if z > 0 else sign   # side +1 = long the 'A' leg (rich when z>0 is shorted)
        gross = cost = 0.0
        days = (series[j][0] - series[i][0]) / 86400
        for leg, u in legs.items():
            q0, q1 = series[i][2][leg], series[j][2][leg]
            d = side * u
            if d > 0:
                gross += q1[0] / q0[1] - 1
            else:
                gross += 1 - q1[1] / q0[0]
            cost += 2 * FEE + FUND_DAY * days
        out.append(dict(ts=series[i][0], day=None, gross=gross, net=gross - cost, cost=cost))
        i = j
    return out


def summarize(name, tr, tsday, nlegs=1):
    if not tr:
        return f"{name}: n 0"
    def pf(v):
        w = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0)
        return w / l if l > 0 else float("inf")
    net = [t["net"] for t in tr]; gr = [t["gross"] for t in tr]
    days = defaultdict(float)
    for t in tr:
        days[tsday(t["ts"])] += t["net"]
    z = None
    if len(days) > 2:
        v = list(days.values()); sd = st.stdev(v)
        z = st.mean(v) / (sd / math.sqrt(len(v))) if sd > 0 else None
    d1 = [t["net"] for t in tr if tsday(t["ts"]) < D1_END]; d2 = [t["net"] for t in tr if tsday(t["ts"]) >= D1_END]
    f = lambda v: f"{st.mean(v)*1e4:+.1f}bp (n {len(v)})" if v else "n 0"
    cost_mean = st.mean(t["cost"] for t in tr)
    return (f"{name}: n {len(tr)}, gross {st.mean(gr)*1e4:+.1f}bp, cost {cost_mean*1e4:.1f}bp, net {st.mean(net)*1e4:+.1f}bp, PF {pf(net):.2f}, "
            f"D1 {f(d1)}, D2 {f(d2)}, day-z {z if z is None else round(z,2)}, win {sum(1 for x in net if x>0)/len(net):.0%}; "
            f"break-even fee/side (gross, spread already in gross) {st.mean(gr)/(2*nlegs)*1e4:.1f}bp")


def day(ts):
    import datetime as d
    return d.datetime.fromtimestamp(ts, d.timezone.utc).strftime("%Y-%m-%d")


def main():
    rows = load()
    by = defaultdict(dict)
    for r in rows:
        by[r["tk"]][r["ts"]] = r
    stamps = sorted({r["ts"] for r in rows})
    print("dev snapshots", len(stamps), stamps[0], stamps[-1])
    stock = [t for t in by if by[t] and next(iter(by[t].values()))["ac"] == "Equities"]
    nq = sum(1 for t in stock for r in by[t].values() if quote(r))
    print("RV1 equities-class perps", len(stock), "valid quotes in development:", nq)
    # RV2
    ser, ser_ctl = [], []
    for ts in stamps:
        a, b = by["KXUSTECH100PERP"].get(ts), by["KXUS500PERP"].get(ts)
        qa, qb = (quote(a), quote(b)) if a and b else (None, None)
        if qa and qb:
            s = math.log((qa[0] + qa[1]) / 2) - math.log((qb[0] + qb[1]) / 2)
            ser.append((tsec(ts), s, {"A": qa, "B": qb}))
    legs = {"A": 1, "B": -1}
    print("RV2 usable snapshots", len(ser))
    t2 = trades(ser, legs); print(summarize("RV2 reversion", t2, day, 2))
    c2 = trades(ser, legs, sign=-1); print(summarize("RV2 control (trend)", c2, day, 2))
    # RV3
    pool, ctl, per = [], [], {}
    for tk in ["KXGOLDPERP", "KXSILVERPERP", "KXUS500PERP", "KXUSTECH100PERP", "KXWTIFUTURE", "KXCOPPERPERP"]:
        sp = [spread_bp(r) for r in by[tk].values() if quote(r)]
        print("  spread median", tk, round(st.median(sp), 2), "snapshots", len(sp))
        s3 = []
        for ts in stamps:
            r = by[tk].get(ts); q = quote(r) if r else None
            if q and q[2] > 0:
                s3.append((tsec(ts), math.log((q[0] + q[1]) / 2 / q[2]), {"A": q}))
        a = trades(s3, {"A": 1}); b = trades(s3, {"A": 1}, sign=-1)
        # reversion: premium z>thr -> sell perp => side -1 (= -sign with sign=1)
        per[tk] = a; pool += a; ctl += b
        print(" ", summarize(tk, a, day))
    print(summarize("RV3 pooled", pool, day)); print(summarize("RV3 control pooled", ctl, day))


if __name__ == "__main__":
    main()
