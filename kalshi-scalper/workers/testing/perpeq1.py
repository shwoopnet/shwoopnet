#!/usr/bin/env python3
"""PERPEQ1 scorer (Testing Desk, written Nov 12, 2026 from the registered text; NO perp candle was opened to write or test it; synthetic rows only).
Registration: PERPEQ1_REGISTRATION.md + PERPEQ_COMMON.md + PERPEQ_AMENDMENT1/2 (claude/epic-ptolemy-0amjd9) and PERPEQ1_AMENDMENT3.md (this directory, which corrects the stale marker line and moves no cutoff).
Rule: event = (perp, trading date). Entry candle ending 08:55 New York. g_p = mid(08:55) / mid(16:00 NY of the PREVIOUS trading day) - 1, mid = (close bid + close ask) / 2.
  Missing candle at either end skips the event (counted). Trigger: |g_p| >= 30 bps AND >= 5 x the entry candle's own spread in bps AND entry spread <= 3 x the perp's cost-map median.
  Trade AGAINST the gap sign: g_p > 0 sell at the close bid, g_p < 0 buy at the close ask. Exit at the candle ending 10:00 NY (buy back at the close ask / sell at the close bid); missing exit = no trade (counted).
  One event per perp and date. Control = the same entries, opposite direction. Only CLOSE fields are used; ask over twice the bid, a non-positive bid or the int64 sentinel (> 1e6) = missing quote.
Cost: 0.12 percent of notional a side (placeholder, not confirmed against Kalshi's fee page), 0.24 percent round trip; stress x1.2. Net is a fraction of the entry mid.
Universe (19): the 21 of PERPEQ_COMMON minus the two index perps. Calendar (Amendment 2): closed 2026-11-26, 2026-12-25, 2027-01-01, 2027-01-18; early closes 2026-11-27 and 2026-12-24 count as trading dates.
Dates are date constants: development 2026-11-09 to 2026-12-21; halves D1 = to 2026-11-30, D2 = from 2026-12-01; HELD OUT from 2026-12-22 (never loaded here: any later date is dropped before scoring and counted);
the scorer REFUSES to run before 2026-12-22 21:00Z (after the close). Held-out read: 2027-02-02 or later, only after a LEAD, once.
Result carries: 'perp candle freshness assumed, not measured'; under 100 trades 'no evidence at n = x'; output goes to the Verification Analyst through Main before any figure travels.
Usage: python3 -W ignore perpeq1.py <candle run folder> [<more folders>] <costmap.csv>      (folders = kalshi-pull style; the candles are fetched through a job file, never by this script)
"""
import calendar, csv, math, os, statistics as st, sys, time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k

NY = ZoneInfo("America/New_York")
UNIVERSE = ["KXXOMPERP", "KXQQQPERP", "KXAAPLPERP", "KXSPYPERP", "KXSPCXPERP", "KXGOOGLPERP", "KXMUPERP", "KXNFLXPERP", "KXNVDAPERP", "KXTSLAPERP", "KXKOPERP", "KXMSFTPERP", "KXCOSTPERP", "KXAMZNPERP", "KXVZPERP", "KXCVXPERP", "KXPGPERP", "KXPLTRPERP", "KXMETAPERP"]
HOLIDAYS = {date(2026, 11, 26), date(2026, 12, 25), date(2027, 1, 1), date(2027, 1, 18)}
DEV_START, DEV_END, D1_END = date(2026, 11, 9), date(2026, 12, 21), date(2026, 11, 30)
NOT_BEFORE = calendar.timegm((2026, 12, 22, 21, 0, 0))            # first development read: 2026-12-22 after the close
CUTOFF_TS = calendar.timegm((2026, 12, 22, 5, 0, 0))              # 2026-12-22 00:00 New York: held out from here, never loaded
MARKER_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PERPEQ1_AMENDMENT3.md")
GAP_BPS, SPREAD_MULT, COST_MULT, FEE_SIDE, STRESS = 30.0, 5.0, 3.0, 0.0012, 1.2
BARS = {"trades": 100, "clusters": 30, "pf": 1.5, "pf_stress": 1.2, "z": 5.27}
FRESH = "perp candle freshness assumed, not measured"


def trading_dates(lo, hi):
    d, out = lo, []
    while d <= hi:
        if d.weekday() < 5 and d not in HOLIDAYS:
            out.append(d)
        d += timedelta(days=1)
    return out


def prev_trading_date(d):
    p = d - timedelta(days=1)
    while p.weekday() >= 5 or p in HOLIDAYS:
        p -= timedelta(days=1)
    return p


def ny_ts(d, h, m):
    return int(datetime(d.year, d.month, d.day, h, m, tzinfo=NY).timestamp())


def quote(by_ts, ts):
    c = by_ts.get(ts)
    if not c or c["bid"] is None or c["ask"] is None:
        return None
    b, a = c["bid"], c["ask"]
    if b <= 0 or a <= 0 or a > 1e6 or b > a or a > 2 * b:
        return None
    return b, a


def costmap(path):
    return {r["ticker"]: float(r["median_spread_bp"]) for r in csv.DictReader(open(path))}


def events(cs, cmap, today=None):
    """-> (trades, controls, counts). trades/controls are scorekit trades with `net` in fractions of the entry mid (stress variants in net_stress)."""
    counts = {"events_considered": 0, "dropped_after_dev_end": 0, "missing_candle": 0, "defect_quote": 0, "no_trigger": 0, "spread_over_3x_median": 0, "no_exit": 0, "traded": 0}
    trades, controls = [], []
    for t in UNIVERSE:
        series = {c["ts"]: c for c in cs.get(t, [])}
        if not series:
            continue
        days = sorted({datetime.fromtimestamp(ts, NY).date() for ts in series})
        counts["dropped_after_dev_end"] += sum(1 for d in days if d > DEV_END)
        for d in trading_dates(DEV_START, DEV_END):
            counts["events_considered"] += 1
            e_ts, p_ts, x_ts = ny_ts(d, 8, 55), ny_ts(prev_trading_date(d), 16, 0), ny_ts(d, 10, 0)
            if e_ts not in series or p_ts not in series:
                counts["missing_candle"] += 1; continue
            qe, qp = quote(series, e_ts), quote(series, p_ts)
            if qe is None or qp is None:
                counts["defect_quote"] += 1; continue
            mid_e, mid_p = sum(qe) / 2, sum(qp) / 2
            g = mid_e / mid_p - 1
            sp = (qe[1] - qe[0]) / mid_e * 1e4
            if abs(g) * 1e4 < GAP_BPS or abs(g) * 1e4 < SPREAD_MULT * sp:
                counts["no_trigger"] += 1; continue
            med = cmap.get(t)
            if med is not None and sp > COST_MULT * med:
                counts["spread_over_3x_median"] += 1; continue
            qx = quote(series, x_ts)
            if qx is None:
                counts["no_exit"] += 1; continue
            counts["traded"] += 1
            def mk(sell):
                gross = (qe[0] - qx[1]) / mid_e if sell else (qx[0] - qe[1]) / mid_e
                return {"event": "%s %s" % (t, d), "cluster": str(d), "ts": e_ts, "date": d, "side": "sell" if sell else "buy",
                        "net": gross - 2 * FEE_SIDE, "net_stress": gross - 2 * FEE_SIDE * STRESS, "gap_bps": g * 1e4}
            trades.append(mk(g > 0)); controls.append(mk(g < 0))
    return trades, controls, counts


def pfof(xs):
    return k.pf(xs)


def verdict(trades, controls):
    n = len(trades)
    dates = sorted({t["date"] for t in trades})
    d1 = [t for t in trades if t["date"] <= D1_END]; d2 = [t for t in trades if t["date"] > D1_END]
    nets = lambda ts, key="net": [t[key] for t in ts]
    z = k.cluster_z(trades)
    info = {"trades": n, "clusters": len(dates), "D1": {"n": len(d1), "pf": pfof(nets(d1)), "net": sum(nets(d1))}, "D2": {"n": len(d2), "pf": pfof(nets(d2)), "net": sum(nets(d2))},
            "pf_stress": pfof(nets(trades, "net_stress")), "mean_net_trigger": (sum(nets(trades)) / n) if n else None, "mean_net_control": (sum(nets(controls)) / len(controls)) if controls else None, "z_clustered": z["z"]}
    if n < BARS["trades"] or len(dates) < BARS["clusters"]:
        return "NOT_ENOUGH_DATA (%d trades of %d needed, %d trading-date clusters of %d needed; reported with the observed rate of %.1f trades a date)" % (n, BARS["trades"], len(dates), BARS["clusters"], n / max(1, len(dates))), info
    ok = lambda x, b: x is not None and x >= b
    fail = []
    if not (ok(info["D1"]["pf"], BARS["pf"]) and ok(info["D2"]["pf"], BARS["pf"])): fail.append("PF under 1.5 in a half")
    if not (info["D1"]["net"] > 0 and info["D2"]["net"] > 0): fail.append("net not above 0 in both halves")
    if not ok(info["pf_stress"], BARS["pf_stress"]): fail.append("PF under 1.2 at fee x1.2")
    if not (info["mean_net_control"] is not None and info["mean_net_trigger"] > info["mean_net_control"]): fail.append("trigger not better than control")
    if not ok(z["z"], BARS["z"]): fail.append("clustered z under 5.27")
    return ("FALSIFIED (%s)" % "; ".join(fail)) if fail else "LEAD (held-out read once on or after 2027-02-02, PF under 1.5 there is FALSIFIED)", info


def run(folders, costmap_path, now=None):
    guard = k.Cutoff(CUTOFF_TS, MARKER_FILE, not_before=NOT_BEFORE)
    now = time.time() if now is None else now
    guard.check([], now)                                    # refuses before 2026-12-22 21:00Z and if the marker already says READ ON
    cs = k.candles(folders)
    trades, controls, counts = events(cs, costmap(costmap_path))
    guard.check(trades, now)                                # belt and braces: no trade at or after the cutoff
    v, info = verdict(trades, controls)
    head = k.score(trades, {"name": "PERPEQ1", "price_source": "exchange 1 minute perp candle CLOSE bid and ask at fixed New York clock minutes", "freshness": FRESH,
                            "book_replay": "NOT PROVIDED: the candles carry no sizes and no book; a perp touch is $1,000 to $3,000 notional so this is a one or two contract test"})
    head.pop("plus_1c", None)                               # scorekit's +1c line is in dollars of a 0..1 contract; meaningless for a perp return
    return {"registered_verdict": v, "label_head_rules": head["label"], "info": info, "counts": counts, "haircut_line": head["haircut_line"], "price_source": head["price_source"],
            "freshness": FRESH, "cash_pf_by_window": head["windows"], "marker": "the Head's rule: cash PF with n by cluster above; output goes to the Verification Analyst through Main before any figure travels",
            "next": guard.mark_read("<date>", "<hash>") + "  (replace the marker line with this, committed, after the one read)"}


if __name__ == "__main__":
    import json
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
    else:
        print(json.dumps(run(a[:-1], a[-1]), indent=1, default=str))
