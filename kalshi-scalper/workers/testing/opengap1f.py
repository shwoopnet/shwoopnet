#!/usr/bin/env python3
"""OPENGAP1-F (Testing Desk, Nov 16, 2026): forward paper read of OPENGAP1. Research only: reads local scratch files, writes nothing, prints aggregates only.
Registration: OPENGAP1F_REGISTRATION.md (with addendum 1). Hand case: OPENGAP1F_HAND_CASE.md. Test: test_opengap1f.py (invented rows only).
The trade logic is that of opengap1_second.py (242f477f), copied with only: the forward date window, a relative haircut, the fee as an argument, and the count / interim / read modes.
Usage: opengap1f.py <count|interim|read> <perp dir> <underlying.csv> [--fee X ...] [--stop]
"""
import csv, datetime, gzip, math, sys

PERPS = {"KXSPYPERP": "SPY", "KXQQQPERP": "QQQ", "KXNVDAPERP": "NVDA", "KXAAPLPERP": "AAPL"}
FIRST_TS = 1793923200          # 2026-11-06T00:00Z: no perp candle before it is read
FWD_FROM, FWD_TO, DST_CHANGE = "2026-11-17", "2027-01-31", "2027-03-14"
FEES = (0.0012, 0.0005)          # 12 bps (the PERP1 assumption) and the 5 bps placeholder; Kalshi's verified fee is added with --fee
REL = (0.0002, 0.0005)          # the primary 1c-equivalent and 2c-equivalent lines (addendum 2): relative to the fill price
STRESS = (0.001, 0.002)          # printed as stress lines (addendum 2); addendum 1 had these as the primary lines
ABS = (0.01, 0.02)          # the literal price-unit lines, information only
TRIGGERS_FINAL, TRIGGERS_INTERIM = 100, 50


def two_sided(q): return q is not None and q[0] is not None and q[1] is not None and 0 < q[0] < q[1]
def mid(q): return (q[0] + q[1]) / 2
def r9(x): return round(x, 9)


def score_event(ev, mode, x, fee):
    """mode 'abs' (x = price units) or 'rel' (x = fraction of the fill price) -> (status, result); status 'no_exit' still counts as a triggered event"""
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
    if mode == "abs": up, dn = (lambda p: round(p + x, 6)), (lambda p: round(p - x, 6))
    else: up, dn = (lambda p: round(p * (1 + x), 6)), (lambda p: round(p * (1 - x), 6))
    entry = up(e[1]) if sgn > 0 else dn(e[0])
    exitp = dn(c[ex][0]) if sgn > 0 else up(c[ex][1])
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


def block(rows):
    rows = sorted(rows, key=lambda r: (r["open_ts"], r["name"])); v = [r["net"] for r in rows]; k = len(v); h2 = k // 2
    return {"n": k, "wins": sum(1 for x in v if x > 0), "pf": pf(v), "h1": pf(v[:h2]), "h2": pf(v[h2:]), "z": day_z([(r["day"], r["net"]) for r in rows])}


def triggered(evs):
    """pooled and per-name count of triggered events (trade or no_exit), integers only: never a return, a gap or a PF"""
    per = {}
    for e in evs:
        if score_event(e, "abs", 0.0, 0.0)[0] in ("trade", "no_exit"): per[e["name"]] = per.get(e["name"], 0) + 1
    return sum(per.values()), per


def run(evs, mode, x, fee):
    return [r for st, r in (score_event(e, mode, x, fee) for e in evs) if st == "trade"]


def interim(evs, fees=FEES, verified=None):
    """PF at the 0.02% line for every fee; the KILL decision only on the verified fee (Kalshi's own page); with none, 'no kill: fee unverified'"""
    n, _ = triggered(evs)
    if n < TRIGGERS_INTERIM: raise SystemExit("REFUSED: %d triggered events, the interim look needs %d" % (n, TRIGGERS_INTERIM))
    pfs = {fee: block(run(evs, "rel", REL[0], fee))["pf"] for fee in fees}
    if verified is None: verdict = "no kill: fee unverified"
    else: verdict = "KILL" if block(run(evs, "rel", REL[0], verified))["pf"] < 1.0 else "CONTINUE"
    return {"triggers": n, "pf_by_fee": pfs, "verified_fee": verified, "verdict": verdict}


def read_ok(evs, stop=False):
    n, _ = triggered(evs)
    if n < TRIGGERS_FINAL and not (stop and max(e["day"] for e in evs) >= FWD_TO): raise SystemExit("REFUSED: %d triggered events, the final read needs %d (or the stop date %s with --stop)" % (n, TRIGGERS_FINAL, FWD_TO))
    return n


def verdict(b1, b2): return b1["n"] >= 100 and b1["pf"] >= 1.3 and b1["h1"] >= 1.0 and b1["h2"] >= 1.0 and b2["pf"] >= 1.0


def _ts(date, hh, mm): return int(datetime.datetime(int(date[:4]), int(date[5:7]), int(date[8:]), hh + 5, mm, tzinfo=datetime.timezone.utc).timestamp())          # ET = UTC - 5 until DST_CHANGE


def load(perp_dir, ucsv):
    cand = {}
    with open(ucsv) as fh: ur = list(csv.DictReader(fh))
    if any(r["date"] >= DST_CHANGE for r in ur): raise SystemExit("REFUSED: an event date on or after %s (DST), ET = UTC - 5 no longer holds" % DST_CHANGE)
    for d in sorted(set(r["date"] for r in ur) | set(r["prev_date"] for r in ur)):
        try: fh = gzip.open("%s/%s.csv.gz" % (perp_dir, d), "rt")
        except OSError: continue
        with fh:
            for r in csv.DictReader(fh):
                if r["ticker"] not in PERPS: continue          # the ticker wall: every other row is dropped before any other column is parsed
                if r["bid_close"] == "" or r["ask_close"] == "": continue
                ts = int(r["end_period_ts"])
                if ts < FIRST_TS: continue
                cand.setdefault(r["ticker"], {})[ts] = (float(r["bid_close"]), float(r["ask_close"]))
    evs, fl = [], (lambda x: float(x) if x not in ("", "None") else None)
    for r in ur:
        if not (FWD_FROM <= r["date"] <= FWD_TO): continue
        evs.append({"name": r["perp"], "day": r["date"], "open_ts": _ts(r["date"], 9, 30), "prev16_ts": _ts(r["prev_date"], 16, 0), "u_open": fl(r["u_open"]), "u_prev": fl(r["u_prev_close"]), "c": cand.get(r["perp"], {})})
    return evs


def main(mode, perp_dir, ucsv, fees, stop, verified=None):
    evs = load(perp_dir, ucsv)
    n, per = triggered(evs)
    if mode == "count":
        print("OPENGAP1-F triggered events pooled", n, "per name", {PERPS[k]: v for k, v in sorted(per.items())}, "events", len(evs)); return
    if mode == "interim":
        print("OPENGAP1-F interim", interim(evs, fees, verified)); return
    read_ok(evs, stop)
    print("OPENGAP1-F final read: triggered events pooled", n, "per name", {PERPS[k]: v for k, v in sorted(per.items())}, "events", len(evs), "(upper bound, not fill-checked; paper only; one try)")
    for fee in fees:
        for label, sel in [("pooled", evs)] + [(PERPS[k], [e for e in evs if e["name"] == k]) for k in PERPS]:
            bl = {("rel", r): block(run(sel, "rel", r, fee)) for r in REL}; bs = {("rel", r): block(run(sel, "rel", r, fee)) for r in STRESS}; bi = {("abs", h): block(run(sel, "abs", h, fee)) for h in ABS}
            for key, b, tag in [(k, v, "(primary)") for k, v in bl.items()] + [(k, v, "(stress, information only)") for k, v in bs.items()] + [(k, v, "(information only)") for k, v in bi.items()]:
                print(f"{label} fee/side {fee} haircut {key[0]} {key[1]} {tag}: n {b['n']} wins {b['wins']} PF {b['pf']:.4f} half1 {b['h1']:.4f} half2 {b['h2']:.4f} dayz {b['z'] if b['z'] is None else round(b['z'], 4)}" + ("  no evidence at n = %d (under 100)" % b["n"] if b["n"] < 100 else ""))
            if label == "pooled": print(f"pooled fee/side {fee} ({'VERIFIED' if fee == verified else 'assumed, not verified'}) bar (rel 0.02% PF >= 1.3, both halves >= 1.0, rel 0.05% PF >= 1.0, n >= 100): {verdict(bl[('rel', REL[0])], bl[('rel', REL[1])])}")


if __name__ == "__main__":
    a = sys.argv[1:]; fees = list(FEES); verified = None
    while "--fee" in a: i = a.index("--fee"); verified = float(a[i + 1]); fees.append(verified); del a[i:i + 2]          # the last --fee is Kalshi's verified fee
    stop = "--stop" in a; a = [x for x in a if x != "--stop"]
    main(a[0], a[1], a[2], fees, stop, verified)
