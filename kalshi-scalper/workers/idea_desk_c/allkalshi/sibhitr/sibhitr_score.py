#!/usr/bin/env python3
"""SIBHIT-R scorer, build 1 (Idea Desk C, Nov 16, 2026). One read. Two tries: R-FAST-NO (s >= S_MED, buy NO) and R-SLOW-YES (buy YES).
Order: close_time window first; time fields fix games, arms and rungs; candles at T; the result is read last, only for traded rungs.
Label: candle replay, upper bound, not fill-checked. Usage: python3 -I sibhitr_score.py <root>"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sibhitr_lib as L


def num(x):
    try:
        v = float(x)
        return v if v == v else None
    except (TypeError, ValueError):
        return None


def px(o):
    if not isinstance(o, dict):
        return None
    if "close_dollars" in o:
        return num(o.get("close_dollars"))
    v = num(o.get("close"))
    return None if v is None else v / 100.0


def pf(xs):
    if not xs:
        return None
    w = sum(x for x in xs if x > 1e-9)
    l = -sum(x for x in xs if x < -1e-9)
    return float("inf") if l == 0 else w / l


def cz(xs, ks):
    c = {}
    for x, k in zip(xs, ks):
        c[k] = c.get(k, 0) + x
    v = list(c.values())
    if len(v) < 2:
        return None
    mu = sum(v) / len(v)
    ss = sum((x - mu) ** 2 for x in v)
    return None if ss <= 0 else sum(v) / math.sqrt(len(v) / (len(v) - 1) * ss)


def sh(v):
    return None if v is None else ("inf" if v == float("inf") else round(v, 4))


def main(root):
    out = {"label": "candle replay, upper bound, not fill-checked"}
    if L.truncated(root):
        out["stopped"] = "list truncated: no result read"
        print(json.dumps(out, indent=1))
        return out
    g = L.games(L.list_rows(root))
    keep = {t for x in g.values() for t in x["open"]}
    q = {}
    base = os.path.join(root, "pull")
    for job in sorted(j for j in os.listdir(base) if j.startswith(L.CANDLE_JOB)):
        for r, b in L.bodies(root, job):
            parts = (r.get("path") or "").split("/")
            t = b.get("ticker") or (parts[-2] if len(parts) >= 2 else "")
            if t not in keep:
                continue
            for c in b.get("candlesticks") or []:
                q.setdefault(t, {}).setdefault(c.get("end_period_ts"), (px(c.get("yes_bid")), px(c.get("yes_ask"))))
    drops = {"no_quote": 0, "not_two_sided": 0, "out_of_band": 0, "no_result": 0}
    cand = []
    for e in sorted(g):
        x = g[e]
        for t in x["open"]:
            qt = q.get(t, {})
            ts = max((k for k in qt if isinstance(k, int) and x["T"] - L.LOOKBACK_S <= k <= x["T"]), default=None)
            if ts is None:
                drops["no_quote"] += 1
                continue
            yb, ya = qt[ts]
            if yb is None or ya is None or not (yb > L.EPS and ya < 1 - L.EPS and ya - yb > L.EPS):
                drops["not_two_sided"] += 1
                continue
            side, ask = ("no", round(1 - yb, 6)) if x["arm"] == "HIGH" else ("yes", round(ya, 6))     # REVERSED from SIBHIT
            if not (L.BAND[0] - L.EPS <= ask <= L.BAND[1] + L.EPS):
                drops["out_of_band"] += 1
                continue
            cand.append((x["T"], t, e, x["arm"], side, ask, x["close"][t]))
    keept = {c[1] for c in cand}
    res = {}
    for _r, b in L.bodies(root, L.LIST_JOB, L.LIST_ID):          # result read LAST, only for traded rungs
        for m in b.get("markets") or []:
            if m.get("ticker") in keept:
                res[m["ticker"]] = (m.get("result") or "").strip().lower()
    out.update({"games": len(g), "clock_drops": len(L.B.CLOCK_DROPS), "arms": {a: sum(1 for x in g.values() if x["arm"] == a) for a in ("HIGH", "LOW")}, "drops": drops,
                "disclosure": "PROPS1 (closed) read pre-game candles of at most about 12% of this window's markets; no ticker exclusion (Amendment 2)"})
    for arm, name in (("HIGH", "R_FAST_NO"), ("LOW", "R_SLOW_YES")):
        rows = []
        for T, t, e, a, side, ask, close in sorted(c for c in cand if c[3] == arm):
            r = res.get(t, "")
            if r not in ("yes", "no", "void"):
                drops["no_result"] += 1
                continue
            row = {"e": e}
            for k, h in (("raw", 0.0), ("1c", 0.01), ("2c", 0.02), ("primary", None)):
                hh = (0.02 if close - T <= 120 else 0.01) if h is None else h
                a2 = round(ask + hh, 6)
                cost = a2 + L.fee(a2)
                row[k] = -L.fee(a2) if r == "void" else ((1 - cost) if r == side else -cost)
            rows.append(row)
        n = len(rows)
        blk = {"n": n, "games": len({r["e"] for r in rows})}
        for k in ("raw", "1c", "2c", "primary"):
            xs = [r[k] for r in rows]
            blk[k] = {"pf": sh(pf(xs)), "half1": sh(pf(xs[:n // 2])), "half2": sh(pf(xs[n // 2:])), "mean_c": round(100 * sum(xs) / n, 3) if n else None,
                      "z_game": sh(cz(xs, [r["e"] for r in rows]))}
        p = [r["primary"] for r in rows]
        z = lambda v: 0.0 if v is None else v
        ok = z(pf(p)) >= 1.3 and z(pf(p[:n // 2])) >= 1.0 and z(pf(p[n // 2:])) >= 1.0 and z(pf([r["2c"] for r in rows])) >= 1.0
        blk["bar"] = ("no evidence at n = %d" % n) if n < 100 else ("PASS (paper bar)" if ok else "fail")
        out[name] = blk
    out["result_note"] = "one read of the released 2025-26 window; a pass needs a second build (16b), the Verification Analyst, and the forward read on closes 2026-11-13 to before 2026-12-04 before any shadow"
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


if __name__ == "__main__":
    main(sys.argv[1])
