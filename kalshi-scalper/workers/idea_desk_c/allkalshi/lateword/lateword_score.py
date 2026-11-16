#!/usr/bin/env python3
"""LATEWORD scorer, build 1 (Idea Desk C, Nov 16, 2026). One try: YES on late-listed words at D, ask 0.30 to 0.70, held to settlement.
Order: time fields fix the words; candles at D; the result is read last and only for traded words. Label: candle replay, upper bound, not fill-checked.
Usage: python3 -I lateword_score.py <root>"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lateword_lib as L


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
    tr = L.truncated(root)
    if tr:
        out["stopped"] = "list truncated %s: no result read" % tr
        print(json.dumps(out, indent=1))
        return out
    w = L.late_words(L.list_rows(root))
    q = {}
    if os.path.isdir(os.path.join(root, "pull", "LATEWORD_CANDLES")):
        for r, b in L._bodies(root, "LATEWORD_CANDLES"):
            parts = (r.get("path") or "").split("/")
            t = b.get("ticker") or (parts[-2] if len(parts) >= 2 else "")
            if t not in w:
                continue
            for c in b.get("candlesticks") or []:
                q.setdefault(t, {}).setdefault(c.get("end_period_ts"), (px(c.get("yes_bid")), px(c.get("yes_ask"))))
    drops = {"no_quote": 0, "not_two_sided": 0, "out_of_band": 0, "no_result": 0}
    cand = []
    for t in sorted(w):
        D = w[t]["D"]
        qt = q.get(t, {})
        ts = max((k for k in qt if isinstance(k, int) and D - L.LOOKBACK_S <= k <= D), default=None)
        if ts is None:
            drops["no_quote"] += 1
            continue
        yb, ya = qt[ts]
        if yb is None or ya is None or not (yb > L.EPS and ya < 1 - L.EPS and ya - yb > L.EPS):
            drops["not_two_sided"] += 1
            continue
        if not (L.BAND[0] - L.EPS <= ya <= L.BAND[1] + L.EPS):
            drops["out_of_band"] += 1
            continue
        cand.append((D, t, round(ya, 6)))
    res = {}
    keep = {c[1] for c in cand}
    for _r, b in L._bodies(root, L.LIST_JOB):          # result read LAST, only for traded words
        for m in b.get("markets") or []:
            if m.get("ticker") in keep:
                res[m["ticker"]] = (m.get("result") or "").strip().lower()
    rows = []
    for D, t, ask in sorted(cand):
        r = res.get(t, "")
        if r not in ("yes", "no", "void"):
            drops["no_result"] += 1
            continue
        row = {"e": w[t]["event"]}
        for k, h in (("raw", 0.0), ("1c", 0.01), ("2c", 0.02), ("primary", None)):
            hh = (0.02 if w[t]["close"] - D <= 120 else 0.01) if h is None else h
            a = round(ask + hh, 6)
            cost = a + L.fee(a)
            row[k] = -L.fee(a) if r == "void" else ((1 - cost) if r == "yes" else -cost)
        rows.append(row)
    n = len(rows)
    out.update({"late_words": len(w), "events": len({x["event"] for x in w.values()}), "drops": drops, "n": n, "events_traded": len({r["e"] for r in rows})})
    for k in ("raw", "1c", "2c", "primary"):
        xs = [r[k] for r in rows]
        out[k] = {"pf": sh(pf(xs)), "half1": sh(pf(xs[:n // 2])), "half2": sh(pf(xs[n // 2:])), "mean_c": round(100 * sum(xs) / n, 3) if n else None,
                  "z_event": sh(cz(xs, [r["e"] for r in rows]))}
    p = [r["primary"] for r in rows]
    z = lambda v: 0.0 if v is None else v
    ok = z(pf(p)) >= 1.3 and z(pf(p[:n // 2])) >= 1.0 and z(pf(p[n // 2:])) >= 1.0 and z(pf([r["2c"] for r in rows])) >= 1.0
    out["bar"] = ("no evidence at n = %d" % n) if n < 100 else ("PASS (paper bar)" if ok else "fail")
    out["result_note"] = ("development data only (event occurrence 2026-04-17 to before 2026-08-06), no held-out read; a pass is a lead for the Head of R&D's go "
                          "on the 2026-10-03 to before 2026-11-05 block; the unit is the event (%d events traded, z clustered by event)" % out["events_traded"])
    print(json.dumps(out, indent=1, sort_keys=True))
    return out


if __name__ == "__main__":
    main(sys.argv[1])
