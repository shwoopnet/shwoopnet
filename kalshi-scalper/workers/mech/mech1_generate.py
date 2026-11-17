"""MECH1 generator, Desk A (Nov 17, 2026), built to MECH1_SCREEN_SPEC_NOV17.md sections 1, 3, 12. Reads the perps minute candles (kalshi1m/<date>.only.csv.gz, gold, US 500, US Tech 100) for the SEARCH and VALIDATE windows ONLY (a file dated after validate_to is never opened; no held-out row is read) and writes the record file the screen reads (section 12.0).
  python3 -I mech1_generate.py <dir holding kalshi1m/<date>.only.csv.gz> <out.jsonl>
REFUSES unless the allow file (HELDOUT_PULL_RUNS.md in the folder above this one) carries a line with the mark, "mech1_generate.py", this file's sha256 and the sha256 of the FILE LIST (the sorted lines "<name> <sha256 of the file>" of every file in the window, computed before any file is parsed). The form read is the `.only.csv.gz` form for every date (it exists for every date from 2026-09-02; the plain `.csv.gz` form exists only from 2026-11-06 and is never opened). Sidecar `<out>.log.json` counts every drop.
First run: signals volume and open_interest, families metal_perp (gold) and index_perp (US 500, US Tech 100), clock any_minute, entry taker, exit fixed_time (15 minutes after entry), sides follow and fade: 8 signatures, one canonical setting each."""
import sys, os, csv, gzip, json, math, hashlib, collections, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
ALLOW_FILE = os.path.join(HERE, "..", "HELDOUT_PULL_RUNS.md"); ALLOW_MARK = "readable ONLY by Desk A's MECH1 generator"
LOG = collections.Counter()
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
def window_files(base):
    return [(d, os.path.join(base, "kalshi1m", d + ".only.csv.gz")) for d in dates_between(WIN["search_from"], WIN["validate_to"]) if os.path.exists(os.path.join(base, "kalshi1m", d + ".only.csv.gz"))]
def manifest_sha(files):
    text = "\n".join("%s %s" % (os.path.basename(p), hashlib.sha256(open(p, "rb").read()).hexdigest()) for d, p in sorted(files))
    return hashlib.sha256(text.encode()).hexdigest()
def refuse_unless_allowed(files):
    me = hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest(); ms = manifest_sha(files)
    try: text = open(ALLOW_FILE, encoding="utf-8").read()
    except OSError: raise SystemExit("REFUSED: the allow file cannot be read")
    for line in text.splitlines():
        if ALLOW_MARK in line and "mech1_generate.py" in line and me in line and ms in line: return ms
    raise SystemExit("REFUSED: no allow line names mech1_generate.py sha256 %s and the file list sha256 %s" % (me, ms))
def load(base, tickers):
    """-> {ticker: {end_ts: (bid_open, ask_open, bid_close, ask_close, open_interest, volume)}}, first date with data per ticker. Reads only dates <= validate_to; the FIRST row of a repeated end_ts is kept (counted)."""
    out = {t: {} for t in tickers}; first = {}
    for d, p in window_files(base):
        for r in csv.DictReader(gzip.open(p, "rt")):
            t = r["ticker"]
            if t not in out: continue
            k = int(r["end_period_ts"])
            if k in out[t]: LOG["candle_duplicate_first_kept"] += 1; continue
            out[t][k] = (f(r["bid_open"]), f(r["ask_open"]), f(r["bid_close"]), f(r["ask_close"]), f(r["open_interest"]), f(r["volume"]))
            first.setdefault(t, d)
    return out, first
def ok2(b, a): return b is not None and a is not None and 0 < b <= a < 1e9          # usable pair (Auditor B, PERPSCALP2 Amendment 5): 0 < bid <= ask < 1e9; locked is usable; the extract's 9.22e14 ask placeholder is not
def mid(c): return (c[2] + c[3]) / 2 if c is not None and ok2(c[2], c[3]) else None
def sig_value(name, cs, t):
    """signal at the candle ending t; None when an input is missing."""
    c = cs.get(t)
    if c is None or mid(c) is None: LOG["signal_candle_unusable_or_missing"] += 1; return None
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
        if mid(a) is None or mid(b) is None: LOG["direction_candle_unusable_or_missing"] += 1; return 0
        d = (mid(a) > mid(b)) - (mid(a) < mid(b))
    return d if side == "follow" else -d
def sig_id(s): return hashlib.sha256("|".join(s[k] for k in ("market", "signal", "clock", "entry", "exit", "side")).encode()).hexdigest()[:16]
def main(base, out_path):
    files = window_files(base); mfs = refuse_unless_allowed(files)
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
                head = {"sig": s, "settings": 1, "primary": "bp", "units": "bp", "tail": "abs", "threshold_value": thr, "hold_s": HOLD_S, "tp_mult": None, "stop_mult": None, "calendar_days_search": cds, "calendar_days_validate": cdv, "data": "kalshi1m (funding not booked)", "tickers": have}
                head.update({k: WIN[k] for k in ("search_from", "search_to", "validate_from", "validate_to", "half1_to", "half2_from")})
                lines.append(head)
                if thr is None: continue
                for t in have:
                    cs = data[t]; busy_until = 0
                    for ts in sorted(cs):
                        sig_day = day_of(ts)
                        if sig_day < WIN["search_from"] or sig_day > WIN["validate_to"]: continue
                        x = sig_value(name, cs, ts)
                        if x is None or abs(x) < thr: continue
                        dr = direction(name, cs, ts, x, side)
                        if dr == 0: continue
                        e_end, x_end = ts + 60, ts + 60 + HOLD_S
                        d = day_of(e_end)                                  # the window and the record's day are the ENTRY bar's UTC end date (Auditor B 5)
                        window = "search" if WIN["search_from"] <= d <= WIN["search_to"] else ("validate" if WIN["validate_from"] <= d <= WIN["validate_to"] else None)
                        if window is None: LOG["fire_entry_date_outside_windows"] += 1; continue
                        if day_of(x_end) > WIN["validate_to"]: LOG["fire_exit_after_validate_to_dropped_not_read"] += 1; continue
                        ce, cx = cs.get(e_end), cs.get(x_end)
                        if ce is None or cx is None: LOG["fire_dropped_missing_entry_or_exit_bar"] += 1; continue
                        if not (ok2(ce[0], ce[1]) and ok2(cx[2], cx[3])): LOG["fire_dropped_unusable_entry_or_exit_pair"] += 1; continue
                        traded = ts >= busy_until
                        entry = ce[1] if dr > 0 else ce[0]                 # long buys the ask open of the next bar, short sells its bid open
                        exitp = cx[2] if dr > 0 else cx[3]                 # long sells the bid close of the exit bar, short buys its ask close
                        if entry <= 0: LOG["fire_dropped_unusable_entry_or_exit_pair"] += 1; continue
                        gross = dr * (exitp - entry) / entry * 1e4; cost = 2 * FEE_BP
                        if traded: busy_until = x_end
                        lines.append({"sig_id": sid, "window": window, "day": d, "entry_end": e_end, "market_id": t, "traded": bool(traded), "gross": gross, "cost": cost, "net": round(gross - cost, 9), "net_1c": None, "net_2c": None})
    with open(out_path, "w") as fo:
        for L in lines: fo.write(json.dumps(L, sort_keys=True, separators=(",", ":")) + "\n")
    json.dump({"file_list_sha256": mfs, "counts": dict(LOG), "generator_sha256": hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest(), "funding": "not booked", "files_read": len(files)}, open(out_path + ".log.json", "w"), sort_keys=True, indent=1)
    print("wrote", out_path, len(lines), "lines;", dict(LOG))
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(*sys.argv[1:])
