"""SPXOI1 threshold T, derivation script, BUILD 1 (Desk A, Nov 13 2026; the Head of R&D's order of 18:49Z). Offline, sends nothing.
  python3 -I spxoi1_threshold.py <lists dir> <candles dir>
<lists dir>: a kalshi-pull run folder (manifest.json + gz bodies) of KXINX15M market lists; ONLY the fields `ticker` and `close_time` are read from it. <candles dir>: the landed SPXOI1_CANDLES run (1 minute candles, end_ts = close minus 120 s); ONLY `end_period_ts` and `open_interest` are read from each candle (no price field, no result, no volume).
Per KXINX15M window with close_time in [WINDOW_FROM, WINDOW_TO) (a date constant range, closes 2026-11-05T00:00:00Z up to but not including 2026-11-14T00:00:00Z): oi_rise = open_interest at the candle ending at close - 180 s MINUS open_interest at the candle ending at close - 360 s (candle end times matched EXACTLY). A window with either candle missing, or an open_interest that is not a number, is DROPPED and COUNTED. T = the 90th percentile of oi_rise over the kept windows, NEAREST-RANK method: sort ascending, rank = ceil(0.90 x n), T = the value at that rank (1-based). Prints the guard's list-hash line, then 'n = <kept windows>, T = <value>' and, on its own line, the number of dropped windows. Nothing else: no per-window value, no price, no result.
The window range stops at 2026-11-14, well before the research held-out start 2026-12-01T00:00:00Z (a closing window on or after it is never read; WINDOW_TO is asserted to be no later than that). HELDOUT_ folders and pull runs listed in HELDOUT_PULL_RUNS.md are refused by heldout_guard_v2."""
import sys, os, gzip, json, math, calendar, time, re
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
WINDOW_FROM = calendar.timegm(time.strptime("2026-11-05", "%Y-%m-%d"))
WINDOW_TO = calendar.timegm(time.strptime("2026-11-14", "%Y-%m-%d"))
HELDOUT_FIRST = calendar.timegm(time.strptime("2026-12-01", "%Y-%m-%d"))
assert WINDOW_TO <= HELDOUT_FIRST
PERCENTILE = 0.90
def iso(s):
    try: return calendar.timegm(time.strptime(re.sub(r"\.\d+Z$", "Z", s), "%Y-%m-%dT%H:%M:%SZ"))
    except Exception: return None
def bodies(folder):
    import heldout_guard_v2 as G; G.refuse_heldout(folder, "spxoi1_threshold")
    man = json.load(open(os.path.join(folder, "manifest.json")))
    for row in man["rows"]:
        if row.get("status") == 200 and "file" in row: yield json.load(gzip.open(os.path.join(folder, row["file"])))
def closes(lists):
    out = {}
    for b in bodies(lists):
        for m in (b.get("markets", []) if isinstance(b, dict) else []):
            tk, ct = m.get("ticker"), m.get("close_time")      # the only two list fields read
            if not (isinstance(tk, str) and tk.startswith("KXINX15M-") and isinstance(ct, str)): continue
            c = iso(ct)
            if c is not None and WINDOW_FROM <= c < WINDOW_TO: out[tk] = c
    return out
def oi_of(x):
    if isinstance(x, bool) or x is None: return None
    if isinstance(x, dict): x = x.get("close") if x.get("close") is not None else x.get("close_dollars")
    try:
        v = float(x); return v if v == v and abs(v) != float("inf") else None
    except (TypeError, ValueError): return None
def oi_by_end(candles):
    out = {}
    for b in bodies(candles):
        for m in (b.get("markets", []) if isinstance(b, dict) else []):
            tk = m.get("market_ticker") or m.get("ticker")
            for c in m.get("candlesticks", []):
                e = c.get("end_period_ts"); v = oi_of(c.get("open_interest"))      # the only two candle fields read
                if e is not None and isinstance(tk, str):
                    try: out.setdefault(tk, {})[int(e)] = v
                    except (TypeError, ValueError): pass
    return out
def nearest_rank(values, q=PERCENTILE):
    v = sorted(values); n = len(v)
    return v[max(1, math.ceil(q * n - 1e-12)) - 1]      # rank = ceil(q n), 1-based; the 1e-12 guards 0.9 x 10 = 9.000000000000002
def derive(closes_, oi):
    rises, dropped = [], 0
    for tk, c in closes_.items():
        e = oi.get(tk, {}); a, b = e.get(c - 180), e.get(c - 360)
        if a is None or b is None: dropped += 1; continue
        rises.append(a - b)
    return rises, dropped
def main(lists, candles):
    import heldout_guard_v2 as G; print(G.list_line())
    rises, dropped = derive(closes(lists), oi_by_end(candles))
    if not rises: sys.exit("no window kept")
    t = nearest_rank(rises); print("n = %d, T = %s" % (len(rises), ("%d" % t) if t == int(t) else "%s" % t)); print("dropped (a needed candle missing) = %d" % dropped)
if __name__ == "__main__":
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
