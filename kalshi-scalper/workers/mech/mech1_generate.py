"""MECH1 generator, Desk A (Nov 17, 2026), built to MECH1_SCREEN_SPEC_NOV17.md sections 1, 3, 12. Reads the perps minute candles (kalshi1m/<date>.only.csv.gz, gold, US 500, US Tech 100) for the SEARCH and VALIDATE windows ONLY (a file dated after validate_to is never opened; no held-out row is read) and writes the record file the screen reads (section 12.0).
  python3 -I mech1_generate.py <dir holding kalshi1m/<date>.only.csv.gz> <out.jsonl>        (nothing is read unless the allow line is on main; see the run log)
First run: signals volume and open_interest, families metal_perp (gold) and index_perp (US 500, US Tech 100), clock any_minute, entry taker, exit fixed_time (15 minutes after entry), sides follow and fade: 8 signatures, one canonical setting each."""
import sys, os, csv, gzip, json, math, hashlib, collections, datetime
WIN = {"search_from": "2026-09-02", "search_to": "2026-10-06", "validate_from": "2026-10-07", "validate_to": "2026-10-26", "half1_to": "2026-09-28", "half2_from": "2026-09-29"}
FAMILIES = {"metal_perp": ["KXGOLDPERP"], "index_perp": ["KXUS500PERP", "KXUSTECH100PERP"]}
HOLD_S = 900; FEE_BP = 12.0
def day_of(ts): return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d")
def dates_between(a, b):
    d0 = datetime.date.fromisoformat(a); d1 = datetime.date.fromisoformat(b)
    return [(d0 + datetime.timedelta(days=i)).isoformat() for i in range((d1 - d0).days + 1)]
def f(x):
    try: return float(x) if x not in ("", None) else None
    except ValueError: return None
def load(base, tickers):
    """-> {ticker: {end_ts: (bid_open, ask_open, bid_close, ask_close, open_interest, volume)}}, first date with data per ticker. Reads only dates <= validate_to."""
    out = {t: {} for t in tickers}; first = {}
    for d in dates_between(WIN["search_from"], WIN["validate_to"]):
        p = os.path.join(base, "kalshi1m", d + ".only.csv.gz")
        if not os.path.exists(p): continue
        for r in csv.DictReader(gzip.open(p, "rt")):
            t = r["ticker"]
            if t not in out: continue
            out[t][int(r["end_period_ts"])] = (f(r["bid_open"]), f(r["ask_open"]), f(r["bid_close"]), f(r["ask_close"]), f(r["open_interest"]), f(r["volume"]))
            first.setdefault(t, d)
    return out, first
def mid(c): return (c[2] + c[3]) / 2 if c[2] is not None and c[3] is not None and 0 < c[2] < c[3] else None
def sig_value(name, cs, t):
    """signal at the candle ending t; None when an input is missing."""
    c = cs.get(t)
    if c is None or mid(c) is None: return None
    if name == "volume":
        vs = [cs.get(t - 60 * k) for k in range(0, 6)]
        if any(v is None or v[5] is None for v in vs): return None
        m = sum(v[5] for v in vs[1:]) / 5.0
        return vs[0][5] / m if m > 0 else None
    if name == "open_interest":
        p = cs.get(t - 900)
        if p is None or p[4] is None or c[4] is None or p[4] <= 0: return None
        return c[4] / p[4] - 1.0
    raise ValueError(name)
def direction(name, cs, t, x, side):
    """+1 long, -1 short, 0 no trade (12.2): signed fields use sign(x); unsigned use the signal bar's own mid change."""
    if name == "open_interest": d = (x > 0) - (x < 0)
    else:
        a, b = cs.get(t), cs.get(t - 60)
        if a is None or b is None or mid(a) is None or mid(b) is None: return 0
        d = (mid(a) > mid(b)) - (mid(a) < mid(b))
    return d if side == "follow" else -d
def sig_id(s): return hashlib.sha256("|".join(s[k] for k in ("market", "signal", "clock", "entry", "exit", "side")).encode()).hexdigest()[:16]
def main(base, out_path):
    tickers = [t for v in FAMILIES.values() for t in v]; data, first = load(base, tickers); lines = []
    for fam, tks in FAMILIES.items():
        have = [t for t in tks if first.get(t)]
        if not have: continue
        fam_first = min(first[t] for t in have)
        cds = max(0, (datetime.date.fromisoformat(WIN["search_to"]) - datetime.date.fromisoformat(max(WIN["search_from"], fam_first))).days + 1)
        cdv = (datetime.date.fromisoformat(WIN["validate_to"]) - datetime.date.fromisoformat(WIN["validate_from"])).days + 1
        for name in ("volume", "open_interest"):
            vals = []                                   # SEARCH observations pooled across the family (12.3)
            for t in have:
                for ts in sorted(data[t]):
                    if WIN["search_from"] <= day_of(ts) <= WIN["search_to"]:
                        x = sig_value(name, data[t], ts)
                        if x is not None: vals.append(abs(x))
            n = len(vals)
            thr = sorted(vals)[math.ceil(0.9 * n) - 1] if n else None
            for side in ("follow", "fade"):
                s = {"market": fam, "signal": name, "clock": "any_minute", "entry": "taker", "exit": "fixed_time", "side": side}; sid = sig_id(s)
                head = {"sig": s, "settings": 1, "primary": "bp", "units": "bp", "tail": "abs", "threshold_value": thr, "hold_s": HOLD_S, "tp_mult": None, "stop_mult": None, "calendar_days_search": cds, "calendar_days_validate": cdv, "data": "kalshi1m", "tickers": have}
                head.update({k: WIN[k] for k in ("search_from", "search_to", "validate_from", "validate_to", "half1_to", "half2_from")})
                lines.append(head)
                if thr is None: continue
                for t in have:
                    cs = data[t]; busy_until = 0
                    for ts in sorted(cs):
                        d = day_of(ts)
                        if d < WIN["search_from"] or d > WIN["validate_to"]: continue
                        window = "search" if d <= WIN["search_to"] else ("validate" if d >= WIN["validate_from"] else None)
                        if window is None: continue
                        x = sig_value(name, cs, ts)
                        if x is None or abs(x) < thr: continue
                        dr = direction(name, cs, ts, x, side)
                        if dr == 0: continue
                        e_end, x_end = ts + 60, ts + 60 + HOLD_S
                        ce, cx = cs.get(e_end), cs.get(x_end)
                        traded = ts >= busy_until and ce is not None and cx is not None
                        if ce is None or cx is None:
                            continue                                       # no entry bar or no exit bar: no trade and no record (counted nowhere; a missing candle is missing, not zero)
                        entry = ce[1] if dr > 0 else ce[0]                 # long buys the ask open of the next bar, short sells its bid open
                        exitp = cx[2] if dr > 0 else cx[3]                 # long sells the bid close of the exit bar, short buys its ask close
                        if entry is None or exitp is None or entry <= 0: continue
                        gross = dr * (exitp - entry) / entry * 1e4; cost = 2 * FEE_BP
                        if traded: busy_until = x_end
                        lines.append({"sig_id": sid, "window": window, "day": d, "entry_end": e_end, "market_id": t, "traded": bool(traded), "gross": gross, "cost": cost, "net": round(gross - cost, 9), "net_1c": None, "net_2c": None})
    with open(out_path, "w") as fo:
        for L in lines: fo.write(json.dumps(L, sort_keys=True, separators=(",", ":")) + "\n")
    print("wrote", out_path, len(lines), "lines")
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(*sys.argv[1:])
