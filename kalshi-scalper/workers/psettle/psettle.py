#!/usr/bin/env python3
"""PSET2 and PSET3 scorer (Strategy Research V2, 2026-11-06). Written and committed BEFORE it is run.
Data: Kalshi's own public keyless endpoint GET /trade-api/v2/margin/funding_rates/historical (one call, no ticker) saved as JSON, and the
development perp-data csv files (dates up to 2026-10-31 only) for the median relative spread used as the cost and to pick the universe.
Everything with funding_time >= CUT is dropped before any computation. Usage: psettle.py HISTORY_JSON PERPDATA_DEV_DIR"""
import csv, glob, json, math, statistics as st, sys, datetime as dt, collections

CUT = "2026-09-15T00:00:00Z"
MID = "2026-07-24T00:00:00Z"
FEE = 0.0012  # the stated 12 bps a side placeholder
Z_BAR = 5.27
CRYPTO = ["KXBTCPERP", "KXETHPERP", "KXSOLPERP", "KXXRPPERP", "KXKSHIBPERP", "KXHYPEPERP", "KXNEARPERP", "KXLINKPERP", "KXDOGEPERP", "KXLTCPERP", "KXSUIPERP"]
EIGHT = 8 * 3600


def parse(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def spreads(d):
    sp = collections.defaultdict(list)
    for f in sorted(glob.glob(d + "/perps-*.csv")):
        for r in csv.DictReader(open(f)):
            if r["ts_utc"] >= "2026-11-01" or r["status"] != "active":
                continue
            try:
                b, a = float(r["bid"]), float(r["ask"])
            except ValueError:
                continue
            if a > b > 0:
                sp[r["ticker"]].append((a - b) / ((a + b) / 2))
    return {k: st.median(v) for k, v in sp.items() if v}


def cluster_z(trades):
    """trades: list of (datetime, net). Day mean then z over days."""
    by = collections.defaultdict(list)
    for t, x in trades:
        by[t.strftime("%Y-%m-%d")].append(x)
    dm = [sum(v) / len(v) for v in by.values()]
    n = len(dm)
    if n < 2:
        return n, float("nan")
    sd = st.stdev(dm)
    return n, (sum(dm) / n) / (sd / math.sqrt(n)) if sd > 0 else float("nan")


def summarize(name, trades):
    if not trades:
        print(name, "no trades"); return {}
    m = sum(x for _, x in trades) / len(trades)
    d, z = cluster_z(trades)
    h1 = [x for t, x in trades if t.isoformat() < parse(MID).isoformat()]
    h2 = [x for t, x in trades if t.isoformat() >= parse(MID).isoformat()]
    mm = lambda v: (sum(v) / len(v)) if v else float("nan")
    print("%s n=%d days=%d mean_net_bp=%.2f z=%.2f D1_n=%d D1_bp=%.2f D2_n=%d D2_bp=%.2f win=%.1f%%" % (
        name, len(trades), d, 1e4 * m, z, len(h1), 1e4 * mm(h1), len(h2), 1e4 * mm(h2), 100 * sum(1 for _, x in trades if x > 0) / len(trades)))
    return dict(n=len(trades), days=d, z=z, d1=mm(h1), d2=mm(h2), mean=m)


def load(hist, sp):
    raw = json.load(open(hist))["funding_rates"]
    ser = collections.defaultdict(list)
    for r in raw:
        if r["market_ticker"] in CRYPTO and r["funding_time"] < CUT:
            ser[r["market_ticker"]].append((parse(r["funding_time"]), float(r["mark_price"]), float(r["funding_rate"])))
    for k in ser:
        ser[k].sort()
    return ser


def pset2(ser, sp):
    print("== PSET2 funding-window seasonality (dev only, funding_time < %s)" % CUT)
    cells = collections.defaultdict(list)
    for tk, s in ser.items():
        c = 2 * (FEE + sp[tk] / 2)
        for (t0, m0, r0), (t1, m1, r1) in zip(s, s[1:]):
            if (t1 - t0).total_seconds() != EIGHT:
                continue
            g = m1 / m0 - 1
            w = t1.hour  # 4, 12, 20 UTC = 00, 08, 16 ET
            cells[(w, "long")].append((t1, g - r1 - c))
            cells[(w, "short")].append((t1, -g + r1 - c))
    out = {}
    for k in sorted(cells):
        out[k] = summarize("PSET2 end_hourUTC=%d %s" % k, cells[k])
    return out


def pset3(ser, sp):
    print("== PSET3 funding-extreme fade with recorded funding (dev only)")
    trades = {"short_on_high": [], "long_on_low": []}
    gross = {"short_on_high": [], "long_on_low": []}
    for tk, s in ser.items():
        c = 2 * (FEE + sp[tk] / 2)
        hist = []
        i = 0
        busy_until = -1
        for i in range(len(s)):
            t, m, r = s[i]
            earlier = list(hist)
            hist.append(r)
            if i <= busy_until or len(earlier) < 30 or i + 3 >= len(s):
                continue
            if any((s[i + j + 1][0] - s[i + j][0]).total_seconds() != EIGHT for j in range(3)):
                continue
            srt = sorted(earlier)
            p90 = srt[int(0.9 * (len(srt) - 1))]
            p10 = srt[int(0.1 * (len(srt) - 1))]
            m3 = s[i + 3][1]
            g = m3 / m - 1
            fsum = sum(s[i + j][2] for j in (1, 2, 3))
            if r > 0 and r >= p90:
                trades["short_on_high"].append((t, -g + fsum - c)); gross["short_on_high"].append((t, -g)); busy_until = i + 3
            elif r < 0 and r <= p10:
                trades["long_on_low"].append((t, g - fsum - c)); gross["long_on_low"].append((t, g)); busy_until = i + 3
    out = {}
    for k in trades:
        out[k] = summarize("PSET3 " + k, trades[k])
        summarize("PSET3 " + k + " (price only, no funding, no cost)", gross[k])
    allt = trades["short_on_high"] + trades["long_on_low"]
    out["both"] = summarize("PSET3 both", allt)
    return out


if __name__ == "__main__":
    sp = spreads(sys.argv[2])
    for tk in CRYPTO:
        assert tk in sp and sp[tk] <= 0.0010, tk
    print("spreads %:", {k: round(100 * sp[k], 4) for k in CRYPTO})
    ser = load(sys.argv[1], sp)
    print("dev periods per ticker:", {k: len(v) for k, v in ser.items()})
    pset2(ser, sp)
    pset3(ser, sp)
