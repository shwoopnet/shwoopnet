"""SPXOI1 threshold T, derivation script, BUILD 1 (Desk A, Nov 13 2026; the Head of R&D's order of 18:49Z). Offline, sends nothing.
  python3 -I spxoi1_threshold.py <lists dir> <candles dir> [<patch candles dir> ...]      (patch folders: Nov 14, 2026; each is run-checked and merged by ticker and end, a conflicting value STOPS)
<lists dir>: a kalshi-pull run folder (manifest.json + gz bodies) of KXINX15M market lists; ONLY the fields `ticker` and `close_time` are read from it. <candles dir>: the landed SPXOI1_CANDLES run (1 minute candles, end_ts = close minus 120 s); ONLY `end_period_ts` and the open interest (`open_interest_fp`, a string, read FIRST; `open_interest` as the fallback) are read from each candle (no price field, no result, no volume). Both run folders must pass the run-integrity check first (manifest status complete; every request answered 200 on pages 1 to k, not truncated, each file matching its manifest sha256 and bytes, the last page without a cursor), or the script refuses.
Per KXINX15M window with close_time in [WINDOW_FROM, WINDOW_TO) (a date constant range, closes 2026-11-05T00:00:00Z up to but not including 2026-11-14T00:00:00Z): oi_rise = open_interest at the candle ending at close - 180 s MINUS open_interest at the candle ending at close - 360 s (candle end times matched EXACTLY). A window with either candle missing is DROPPED and COUNTED as 'missing candle'; a window whose open interest is not a finite number (not nan, not inf, not bool) is DROPPED and COUNTED as 'unreadable open interest'. T = the 90th percentile of oi_rise over the kept windows, NEAREST-RANK method: sort ascending, rank = ceil(0.90 x n), T = the value at that rank (1-based). Prints the guard's list-hash line, then 'n = <kept windows>, T = <value>' and two lines of dropped counts (missing candle; unreadable open interest). Nothing else: no per-window value, no price, no result.
The window range stops at 2026-11-14, well before the research held-out start 2026-12-01T00:00:00Z (a closing window on or after it is never read; WINDOW_TO is asserted to be no later than that). HELDOUT_ folders and pull runs listed in HELDOUT_PULL_RUNS.md are refused by heldout_guard_v2."""
import sys, os, gzip, json, math, calendar, time, re, hashlib, collections
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
WINDOW_FROM = calendar.timegm(time.strptime("2026-11-05", "%Y-%m-%d"))
WINDOW_TO = calendar.timegm(time.strptime("2026-11-14", "%Y-%m-%d"))
HELDOUT_FIRST = calendar.timegm(time.strptime("2026-12-01", "%Y-%m-%d"))
assert WINDOW_TO <= HELDOUT_FIRST
PERCENTILE = 0.90
def iso(s):
    try: return calendar.timegm(time.strptime(re.sub(r"\.\d+Z$", "Z", s), "%Y-%m-%dT%H:%M:%SZ"))
    except Exception: return None
def check_run(folder):
    """run-integrity refusals (Auditor B F2), before any body is used: the manifest status is 'complete'; every request id has pages 1 to k each answered 200 exactly once (a 429 or failed retry row before the 200 is allowed), not truncated, a stored file whose decompressed bytes match the row's sha256 and bytes, and the LAST page of each request carries no cursor. Anything else is refused."""
    import heldout_guard_v2 as G; G.refuse_heldout(folder, "spxoi1_threshold")
    try: man = json.load(open(os.path.join(folder, "manifest.json")))
    except Exception as e: sys.exit("REFUSED: %s has no readable manifest.json (%s)" % (folder, e))
    if man.get("status") != "complete": sys.exit("REFUSED: %s manifest status is %r, not 'complete'" % (folder, man.get("status")))
    rows = man.get("rows")
    if not isinstance(rows, list) or not rows: sys.exit("REFUSED: %s manifest has no rows" % folder)
    byid = collections.defaultdict(list)
    for r in rows: byid[r.get("id")].append(r)
    for rid, rs in byid.items():
        ok = [r for r in rs if r.get("status") == 200]
        if any(r.get("status") not in (200, 429) for r in rs) or not ok: sys.exit("REFUSED: request %r in %s was not answered 200 (a status other than 200 or a retried 429)" % (rid, folder))
        pages = sorted(r.get("page") for r in ok)
        if pages != list(range(1, len(ok) + 1)): sys.exit("REFUSED: request %r in %s has pages %r, not 1 to %d each answered 200 once" % (rid, folder, pages, len(ok)))
        for r in ok:
            if r.get("truncated") is not False or not isinstance(r.get("file"), str) or not isinstance(r.get("sha256"), str) or not isinstance(r.get("bytes"), int): sys.exit("REFUSED: request %r page %r in %s is truncated or lacks file, sha256 or bytes" % (rid, r.get("page"), folder))
            try: raw = gzip.open(os.path.join(folder, r["file"])).read()
            except Exception as e: sys.exit("REFUSED: %s file %s unreadable (%s)" % (folder, r["file"], e))
            if hashlib.sha256(raw).hexdigest() != r["sha256"] or len(raw) != r["bytes"]: sys.exit("REFUSED: %s file %s does not match its manifest sha256 or bytes" % (folder, r["file"]))
        last = max(ok, key=lambda r: r["page"]); body = json.loads(gzip.open(os.path.join(folder, last["file"])).read())
        if isinstance(body, dict) and isinstance(body.get("cursor"), str) and body["cursor"]: sys.exit("REFUSED: request %r in %s: its last page still carries a cursor (paging incomplete)" % (rid, folder))
    return man
def bodies(folder):
    man = check_run(folder)
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
def _num(x):
    if isinstance(x, bool) or x is None: return None
    try:
        v = float(x); return v if math.isfinite(v) else None      # not nan, not inf
    except (TypeError, ValueError): return None
def oi_of(c):
    """open interest of a candle: `open_interest_fp` (the real candles carry it as a STRING) is read first; `open_interest` is the fallback when fp is absent, None or empty. A non-empty fp that is not a finite number is unreadable (no silent fallback). Bool, nan and inf are unreadable."""
    if not isinstance(c, dict): return None
    fp = c.get("open_interest_fp")
    if fp is not None and fp != "": return _num(fp)
    return _num(c.get("open_interest"))
def oi_by_end(candles):
    """candles: one run folder, or a list of run folders (a main run and PATCH runs, the Head's order of Nov 14, 2026). Every folder passes check_run (through bodies()). Merged by (ticker, end_period_ts); a second value for the same key that is not the same number STOPS (conflict), an identical value is fine, and None (unreadable) never overrides a readable value from another folder."""
    folders = candles if isinstance(candles, (list, tuple)) else [candles]
    out = {}
    for folder in folders:
        for b in bodies(folder):
            for m in (b.get("markets", []) if isinstance(b, dict) else []):
                tk = m.get("market_ticker") or m.get("ticker")
                for c in m.get("candlesticks", []):
                    e = c.get("end_period_ts"); v = oi_of(c)      # the only candle fields read: end_period_ts and open_interest_fp / open_interest
                    if e is not None and isinstance(tk, str):
                        try: e = int(e)
                        except (TypeError, ValueError): continue
                        prev = out.setdefault(tk, {})
                        if e in prev and prev[e] is not None and v is not None and prev[e] != v: sys.exit("REFUSED: conflict for %s at end %d: %r in an earlier folder, %r in %s" % (tk, e, prev[e], v, folder))
                        if e not in prev or prev[e] is None: prev[e] = v
    return out
def nearest_rank(values, q=PERCENTILE):
    v = sorted(values); n = len(v)
    return v[max(1, math.ceil(q * n - 1e-12)) - 1]      # rank = ceil(q n), 1-based; the 1e-12 guards 0.9 x 10 = 9.000000000000002
def derive(closes_, oi):
    """(rises, dropped for a missing candle, dropped for unreadable open interest); a missing candle is counted first"""
    rises, miss, unread = [], 0, 0
    for tk, c in closes_.items():
        e = oi.get(tk, {})
        if (c - 180) not in e or (c - 360) not in e: miss += 1; continue
        a, b = e[c - 180], e[c - 360]
        if a is None or b is None: unread += 1; continue
        rises.append(a - b)
    return rises, miss, unread
def main(lists, candles, *patches):
    import heldout_guard_v2 as G; print(G.list_line())
    rises, miss, unread = derive(closes(lists), oi_by_end([candles] + list(patches)))
    if not rises: sys.exit("no window kept")
    t = nearest_rank(rises); print("n = %d, T = %s" % (len(rises), ("%d" % t) if t == int(t) else "%s" % t)); print("dropped, missing candle = %d" % miss); print("dropped, unreadable open interest = %d" % unread)
if __name__ == "__main__":
    if len(sys.argv) < 3: sys.exit(__doc__)
    main(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), *[os.path.abspath(a) for a in sys.argv[3:]])
