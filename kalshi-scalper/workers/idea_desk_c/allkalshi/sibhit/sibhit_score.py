#!/usr/bin/env python3
"""SIBHIT scorer, build 1 (Idea Desk C, Nov 15, 2026). Reads the stage A list (time fields, then result last for traded rungs only) and SIBHIT_CANDLES.
Two tries: HIGH-YES and LOW-NO, held to settlement, 1 contract a rung. Label: candle replay, upper bound, not fill-checked.
Usage: python3 -I sibhit_score.py <root>"""
import gzip, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sibhit_lib as L


def num(x):
    try:
        v = float(x)
        return v if v == v else None
    except (TypeError, ValueError):
        return None


def candles(root, keep):
    q = {}
    base = os.path.join(root, "pull", "SIBHIT_CANDLES")
    if not os.path.isdir(base):
        return q
    for run in sorted(os.listdir(base)):
        with open(os.path.join(base, run, "manifest.json")) as fh:
            man = json.load(fh)
        for r in man["rows"]:
            fn = r.get("file")
            if not fn:
                continue
            with gzip.open(os.path.join(base, run, fn), "rt") as fh:
                b = json.load(fh)
            for m in (b.get("markets") or []) if isinstance(b, dict) else []:
                t = m.get("market_ticker")
                if t not in keep:
                    continue
                for c in m.get("candlesticks") or []:
                    yb = num((c.get("yes_bid") or {}).get("close_dollars"))
                    ya = num((c.get("yes_ask") or {}).get("close_dollars"))
                    q.setdefault(t, {}).setdefault(c.get("end_period_ts"), (yb, ya))
    return q


def results(root, tickers):
    """Read LAST, only for tickers traded."""
    out = {}
    base = os.path.join(root, "pull", "KXNBAPTS_LISTS_A")
    for run in sorted(os.listdir(base)):
        with open(os.path.join(base, run, "manifest.json")) as fh:
            man = json.load(fh)
        for r in man["rows"]:
            if not r.get("file") or r.get("id") != "dev_KXNBAPTS":
                continue
            with gzip.open(os.path.join(base, run, r["file"]), "rt") as fh:
                for m in json.load(fh).get("markets") or []:
                    if m.get("ticker") in tickers:
                        out[m["ticker"]] = (m.get("result") or "").strip().lower()
    return out


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


def main(root, info_split=True):
    g = L.games(L.list_rows(root))
    if info_split:
        # Auditor B (Nov 15), information only, not a try: the arm split with the median of the FIRST half of games in time order
        import statistics as st
        order = sorted(g, key=lambda e: (g[e]["T"], e))
        first = order[:len(order) // 2]
        med1 = st.median([g[e]["s"] for e in first]) if first else None
    keep = {t for x in g.values() for t in x["open"]}
    q = candles(root, keep)
    cand, drops = [], {"no_quote": 0, "not_two_sided": 0, "out_of_band": 0}
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
            side, ask = ("yes", round(ya, 6)) if x["arm"] == "HIGH" else ("no", round(1 - yb, 6))
            if not (L.BAND[0] - L.EPS <= ask <= L.BAND[1] + L.EPS):
                drops["out_of_band"] += 1
                continue
            cand.append((x["T"], t, e, x["arm"], side, ask, x["close"][t]))
    res = results(root, {c[1] for c in cand})
    out = {"label": "candle replay, upper bound, not fill-checked", "games": len(g), "arms": {a: sum(1 for x in g.values() if x["arm"] == a) for a in ("HIGH", "LOW")},
           "drops": drops}
    for arm in ("HIGH", "LOW"):
        rows = []
        for T, t, e, a, side, ask, close in sorted(c for c in cand if c[3] == arm):
            r = res.get(t, "")
            if r not in ("yes", "no", "void"):
                out["drops"]["no_result"] = out["drops"].get("no_result", 0) + 1
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
        p1, a1, b1 = pf([r["primary"] for r in rows]), pf([r["primary"] for r in rows][:n // 2]), pf([r["primary"] for r in rows][n // 2:])
        p2 = pf([r["2c"] for r in rows])
        z = lambda v: 0.0 if v is None else v
        blk["bar"] = "PASS (paper bar)" if (z(p1) >= 1.3 and z(a1) >= 1.0 and z(b1) >= 1.0 and z(p2) >= 1.0) else "fail"
        out[arm] = blk
    out["clock_check"] = {"dropped_games": len(L.CLOCK_DROPS), "rule": "occurrence must be one value per game, exactly on :00 or :30 (a schedule time); the tip time itself is not in the data",
                          "note": "the clock is a schedule-shaped time and the tip time is not in the data, so T = O - 60 may differ from the actual tip by minutes; the check proves shape, not truth"}
    shares = sorted(x["s"] for x in g.values())
    if shares:
        import statistics as st
        qs = st.quantiles(shares, n=4) if len(shares) > 1 else [shares[0]] * 3
        out["share_per_game"] = {"min": round(shares[0], 4), "q25": round(qs[0], 4), "median": round(qs[1], 4), "q75": round(qs[2], 4), "max": round(shares[-1], 4),
                                 "note": "share of base rungs closed strictly before T - 240 s; a rung closed for a reason other than a hit (player ruled out) counts"}
    out["s_med_note"] = "S_MED is the median over all development games: in-sample for the arm split (close times only, no price or result)"
    if info_split and g and med1 is not None:
        g2 = {e: dict(x, arm="HIGH" if x["s"] >= med1 - L.EPS else "LOW") for e, x in g.items()}
        saved = L.games
        L.games = lambda rows: g2
        try:
            alt = main(root, info_split=False)
        finally:
            L.games = saved
        out["info_first_half_median_split"] = {"median_first_half": med1, "HIGH": alt.get("HIGH"), "LOW": alt.get("LOW"),
                                               "note": "information line only, not a try"}
    if info_split:
        print(json.dumps(out, indent=1, sort_keys=True))
    return out


if __name__ == "__main__":
    main(sys.argv[1])
