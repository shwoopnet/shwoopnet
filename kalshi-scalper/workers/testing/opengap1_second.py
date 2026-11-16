#!/usr/bin/env python3
"""OPENGAP1 (Testing Desk, Nov 16, 2026): card (b) opening gap on stock perps, as amended. Research only: reads local scratch files, writes nothing,
prints aggregates only. Rule: OPENGAP1_REGISTRATION.md. Hand case: OPENGAP1_HAND_CASE.md (committed first). Test: test_opengap1_second.py (invented rows only).
Usage: opengap1_second.py <dir with kalshi1m <date>.csv.gz files> <underlying.csv: perp,date,prev_date,u_open,u_prev_close,x_open,x_prev_close>
"""
import csv, datetime, gzip, math, sys

PERPS = {"KXSPYPERP": "SPY", "KXQQQPERP": "QQQ", "KXNVDAPERP": "NVDA", "KXAAPLPERP": "AAPL"}
FEE, HAIRCUTS = 0.0012, (0.0, 0.01, 0.02)
DEV_FROM, DEV_TO = "2026-11-06", "2026-11-30"          # development dates only (UTC days); nothing from December


def two_sided(q): return q is not None and q[0] is not None and q[1] is not None and 0 < q[0] < q[1]
def mid(q): return (q[0] + q[1]) / 2
def r9(x): return round(x, 9)


def score_event(ev, h, fee=FEE):
    """ev: name, day, open_ts (09:30 ET), prev16_ts (previous 16:00 ET candle end), u_open, u_prev, c {end_ts: (bid_close, ask_close)} -> (status, result)"""
    if ev["u_open"] is None or ev["u_prev"] is None or ev["u_prev"] <= 0: return "no_underlying", None
    o, c = ev["open_ts"], ev["c"]
    pp, p25, e = c.get(ev["prev16_ts"]), c.get(o - 300), c.get(o + 60)
    if not (two_sided(pp) and two_sided(p25) and two_sided(e)): return "no_perp", None
    g = (ev["u_open"] / ev["u_prev"] - 1) - (mid(p25) / mid(pp) - 1)
    half = ((e[1] - e[0]) / 2) / mid(e)
    if r9(g) == 0 or not r9(abs(g)) > r9(2 * half): return "no_trigger", None
    sgn = 1 if g > 0 else -1
    after = [t for t in sorted(c) if o + 60 < t <= o + 900 and two_sided(c[t])]
    if not after: return "no_exit", None
    ex = after[-1]
    for t in after:
        if sgn * (g - (mid(c[t]) - mid(p25)) / mid(pp)) <= 0.5 * abs(g) + 1e-12: ex = t; break
    entry = round(e[1] + h, 6) if sgn > 0 else round(e[0] - h, 6)
    exitp = round(c[ex][0] - h, 6) if sgn > 0 else round(c[ex][1] + h, 6)
    ret = sgn * (exitp - entry) / entry
    return "trade", {"open_ts": o, "name": ev["name"], "day": ev["day"], "ret": ret, "net": ret - 2 * fee}


def pf(v):
    pos = sum(x for x in v if x > 0); neg = -sum(x for x in v if x < 0)
    if neg == 0: return math.inf if pos > 0 else math.nan
    return pos / neg


def day_z(rows):
    by = {}
    for d, x in rows: by[d] = by.get(d, 0.0) + x
    v = list(by.values())
    if len(v) < 2: return None
    m = sum(v) / len(v); sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))
    return None if sd == 0 else m / (sd / math.sqrt(len(v)))


def block(rows, key="net"):
    rows = sorted(rows, key=lambda r: (r["open_ts"], r["name"])); v = [r[key] for r in rows]; k = len(v); h2 = k // 2
    return {"n": k, "wins": sum(1 for x in v if x > 0), "sum": sum(v), "pf": pf(v), "h1": pf(v[:h2]), "h2": pf(v[h2:]), "z": day_z([(r["day"], r[key]) for r in rows]),
            "breakeven_fee": (sum(r["ret"] for r in rows) / k / 2) if k else None}


def run(events, fee=FEE):
    out, sk = {h: [] for h in HAIRCUTS}, {"no_underlying": 0, "no_perp": 0, "no_trigger": 0, "no_exit": 0}
    for ev in events:
        for h in HAIRCUTS:
            st, r = score_event(ev, h, fee)
            if st == "trade": out[h].append(r)
            elif h == 0.0: sk[st] += 1
    return out, sk


def _ts(date, hh, mm): return int(datetime.datetime(int(date[:4]), int(date[5:7]), int(date[8:]), hh + 5, mm, tzinfo=datetime.timezone.utc).timestamp())          # ET = UTC - 5 on the dates read (DST ended 2026-11-01)


def load(perp_dir, ucsv):
    cand, sk = {}, 0
    with open(ucsv) as fh: ur = list(csv.DictReader(fh))
    dates = set(r["date"] for r in ur) | set(r["prev_date"] for r in ur)
    for d in sorted(dates):
        try: fh = gzip.open("%s/%s.csv.gz" % (perp_dir, d), "rt")
        except OSError: continue
        with fh:
            for r in csv.DictReader(fh):
                if r["ticker"] in PERPS and r["bid_close"] != "" and r["ask_close"] != "": cand.setdefault(r["ticker"], {})[int(r["end_period_ts"])] = (float(r["bid_close"]), float(r["ask_close"]))
    evs = []
    for r in ur:
        if not (DEV_FROM <= r["date"] <= DEV_TO): continue
        fl = lambda x: float(x) if x not in ("", "None") else None
        evs.append({"name": r["perp"], "day": r["date"], "open_ts": _ts(r["date"], 9, 30), "prev16_ts": _ts(r["prev_date"], 16, 0), "u_open": fl(r["u_open"]), "u_prev": fl(r["u_prev_close"]), "c": cand.get(r["perp"], {}),
                    "x": (fl(r["x_open"]), fl(r["x_prev_close"]))})
    return evs


def main(perp_dir, ucsv):
    evs = load(perp_dir, ucsv)
    xs = [max(abs(e["u_open"] / e["x"][0] - 1), abs(e["u_prev"] / e["x"][1] - 1)) * 1e4 for e in evs if None not in (e["u_open"], e["u_prev"], e["x"][0], e["x"][1])]
    print("OPENGAP1 events", len(evs), "cross-check EQUS.SUMMARY max abs difference bps", round(max(xs), 3) if xs else None, "(information only)")
    for label, sel in [("pooled (information only)", evs)] + [(PERPS[n], [e for e in evs if e["name"] == n]) for n in PERPS]:
        for fee in (FEE, 0.0):
            out, sk = run(sel, fee)
            print(f"{label} fee/side {fee}: skips {sk}")
            for h in HAIRCUTS:
                b = block(out[h]); print(f"  h {h:.2f}: n {b['n']} wins {b['wins']} sum {b['sum']:.6f} PF {b['pf']:.4f} half1 {b['h1']:.4f} half2 {b['h2']:.4f} dayz {b['z'] if b['z'] is None else round(b['z'], 4)} break-even fee/side {b['breakeven_fee'] if b['breakeven_fee'] is None else round(b['breakeven_fee'], 6)}" + ("  no evidence at n = %d (under 100)" % b["n"] if b["n"] < 100 else ""))
    print("tries: one rule x four names; every name under 100 trades = no evidence; upper bound, not fill-checked")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
