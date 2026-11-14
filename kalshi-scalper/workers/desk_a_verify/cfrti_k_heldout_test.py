"""CFRTI-K held-out reader test on a MADE-UP fixture (synthetic candles from cfrti_k.synth, shifted). python3 -I cfrti_k_heldout_test.py"""
import sys, os, gzip, json, tempfile, calendar, time, io, contextlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import cfrti_k as K, cfrti_k_heldout as H
def iso(t): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))
def folder(d, name, body):
    import hashlib
    p = os.path.join(d, name); os.makedirs(p); raw = json.dumps(body).encode()
    with gzip.open(p + "/a.json.gz", "wb") as f: f.write(raw)
    json.dump({"job": {"job_id": "FIXTURE", "requests": [{"id": "r1"}]}, "requests_sent": 1, "status": "complete", "rows": [{"index": 1, "id": "r1", "page": 1, "status": 200, "bytes": len(raw), "file": "a.json.gz", "sha256": hashlib.sha256(raw).hexdigest(), "truncated": False, "body_kind": "object"}]}, open(p + "/manifest.json", "w")); return p
def build(days, start, edge, seed, override=None):
    M, B, P = K.synth(days=days, edge=edge, seed=seed)
    sh = calendar.timegm(time.strptime(start, "%Y-%m-%d")) - calendar.timegm(time.strptime("2026-08-01", "%Y-%m-%d"))
    d = tempfile.mkdtemp()
    lists = folder(d, "lists", {"markets": [{"ticker": tk, "close_time": iso(m["close"] + sh), "result": (override or {}).get(tk, "yes" if m["yes"] else "no"), "floor_strike": m["strike"]} for tk, m in M.items()]})
    cands = folder(d, "cands", {"markets": [{"market_ticker": tk, "candlesticks": [{"end_period_ts": ts + sh, "yes_bid": {"close": b}, "yes_ask": {"close": a}} for ts, (b, a) in cs.items()]} for tk, cs in B.items()]})
    perp = folder(d, "perp", {"candlesticks": [{"end_period_ts": ts + sh, "bid": {"close": p / 10000 - 0.00005}, "ask": {"close": p / 10000 + 0.00005}} for ts, p in P.items()]})
    return lists, cands, perp
H_MON = calendar.timegm(time.strptime("2026-11-14", "%Y-%m-%d"))
# 1. the held-out filter: a series spanning Oct 25 to Dec 24 loads only closes on or after 2026-11-14
lists, cands, perp = build(60, "2026-10-25", True, 7)
mk = H.load_markets_ho(lists); assert mk and min(m["close"] for m in mk.values()) >= H_MON, "a close before HELD_FROM was loaded"
assert max(m["close"] for m in mk.values()) > H_MON + 30 * 86400
tr, _why = H.trades_of(mk, K.load_binary(cands), K.load_perp(perp)); assert len(tr) >= 50 and min(t["close"] for t in tr) >= H_MON, len(tr)
# 1b. the boundary (the Head, Nov 14, 2026): DEPTH1 read the window closing EXACTLY at HELD_FROM first, so the held-out is closes STRICTLY after it; the excluded count is returned for printing
_d = tempfile.mkdtemp()
_L = folder(_d, "lists_b", {"markets": [{"ticker": "KXBTC15M-B%d" % i, "close_time": iso(H_MON + off), "result": "yes", "floor_strike": 80000.0} for i, off in enumerate((-900, 0, 900, 900 + 900))]})
_b = H.load_markets_ho(_L); assert sorted(m["close"] - H_MON for m in _b.values()) == [900, 1800], "the window closing exactly at HELD_FROM must be excluded"
assert H.boundary_excluded(_L) == 1, "the count of windows closing exactly at HELD_FROM"
# 2. the label rule
def T(c): return dict(pnl=c, win=1 if c > 0 else 0, day=0, close=0)
assert H.label([T(0.5)] * 29) == "NOT_ENOUGH_DATA"                              # n under 30: never a call
assert H.label([T(0.1)] * 10 + [T(-0.2)] * 20) == "NOT_ENOUGH_DATA"           # n 30, PF under 1.0: still under 50, so no call (the card's latest dated line: every label needs n >= 50)
assert H.label([T(0.1)] * 10 + [T(-0.1)] * 39) == "NOT_ENOUGH_DATA"           # n 49, PF under 1.0: no call
assert H.label([T(0.1)] * 10 + [T(-0.1)] * 40) == "FAIL"                      # n 50, PF under 1.0: FAIL
assert H.label([T(0.3)] * 15 + [T(-0.2)] * 15) == "NOT_ENOUGH_DATA"           # n 30 to 49 and PF 1.5: no call, no marker
assert H.label([T(0.2)] * 20 + [T(-0.2)] * 20) == "NOT_ENOUGH_DATA"           # n 40 and PF exactly 1.0: not under 1.0, so no call
assert H.label([T(0.5)] * 49) == "NOT_ENOUGH_DATA"                            # n 49, all wins: not a fail, no call
assert H.label([T(0.30)] * 30 + [T(-0.20)] * 20) == "PASS"                    # PF 1.5, mean positive, n 50
assert H.label([T(0.13)] * 20 + [T(-0.10)] * 30) == "FAIL"                   # PF 0.87
assert H.label([T(0.25)] * 20 + [T(-0.20)] * 30) == "FAIL"                   # PF 0.83: under 1.0
assert H.label([T(0.30)] * 12 + [T(-0.20)] * 38) == "FAIL"                   # PF 0.47 at n 50
assert H.label([T(0.20)] * 24 + [T(-0.30)] * 26) == "FAIL"                   # PF 0.62
mid = [T(0.22)] * 30 + [T(-0.20)] * 30; assert 1.0 < K.pf([t["pnl"] for t in mid]) < 1.3 and H.label(mid) == "NO CALL"   # PF from 1.0 up to 1.3 at n >= 50: the registration's own "no call" (the Head, 17:04Z)
assert H.label([T(0.20)] * 25 + [T(-0.20)] * 25) == "NO CALL"                # PF exactly 1.0 is NO CALL, not FAIL
assert H.label([T(0.26)] * 25 + [T(-0.20)] * 25) == "PASS"                   # PF exactly 1.3 and mean above 0 is PASS
assert H.label([T(0.30)] * 10 + [T(-0.01)] * 40) == "PASS"                   # large PF
assert H.label([T(0.199)] * 25 + [T(-0.20)] * 25) == "FAIL"                  # PF just under 1.0
# 2b. zero volatility: the window is DROPPED and COUNTED (reasons), never a trade
cl = H_MON + 900 * 10; mk0 = dict(tk="KXBTC15M-Z", close=cl, strike=100.0, yes=True)
flat = {cl - 120 - 60 * k: 100.0 for k in range(11)}; flat[cl - 900] = 100.0
tr0, why0 = H.trades_of({"KXBTC15M-Z": mk0}, {"KXBTC15M-Z": {cl - 120: (0.10, 0.12)}}, flat)
assert tr0 == [] and why0["no volatility"] == 1, (tr0, dict(why0))
# 3. under 50 prints only the count and spends nothing
lists2, cands2, perp2 = build(2, "2026-11-14", False, 3)
mk_ = os.path.join(tempfile.mkdtemp(), "m.txt")
buf = io.StringIO()
with contextlib.redirect_stdout(buf): t2 = H.run(lists2, cands2, perp2, now=H.READ_NOT_BEFORE + 1, marker=mk_)
out = buf.getvalue(); assert len(t2) < 50 and "NOT_ENOUGH_DATA" in out and "cash PF" not in out and not os.path.exists(mk_), out
# 4. before the read date it refuses; at 50 or more it writes the marker, prints a label, and a second run refuses before reading
try:
    with contextlib.redirect_stdout(io.StringIO()): H.run(lists, cands, perp, now=H.READ_NOT_BEFORE - 1, marker=mk_)
    raise AssertionError("ran before the read date")
except SystemExit as e: assert "2026-11-20" in str(e)
buf = io.StringIO()
with contextlib.redirect_stdout(buf): H.run(lists, cands, perp, now=H.READ_NOT_BEFORE + 5, marker=mk_)
out = buf.getvalue(); assert os.path.exists(mk_) and ("LABEL: PASS" in out or "LABEL: FAIL" in out or "LABEL: NO CALL" in out) and "HELDOUT_PULL_RUNS.md copy read by the guard: sha256" in out, out
try:
    with contextlib.redirect_stdout(io.StringIO()): H.run(lists, cands, perp, now=H.READ_NOT_BEFORE + 9, marker=mk_)
    raise AssertionError("second read not refused")
except SystemExit as e: assert "has been made" in str(e)
# 5. n 30 to 49: always NOT_ENOUGH_DATA, no marker, and the run is LOGGED with date and n
fake_fail = [dict(pnl=-0.2 if i % 3 else 0.1, win=0, day=i % 5, close=H_MON + i) for i in range(35)]
fake_ok = [dict(pnl=0.3 if i % 2 else -0.2, win=1, day=i % 5, close=H_MON + i) for i in range(35)]
orig = H.trades_of; lg = os.path.join(tempfile.mkdtemp(), "log.txt")
try:
    H.trades_of = lambda m, b, p: (fake_fail, __import__("collections").Counter())
    mk1 = os.path.join(tempfile.mkdtemp(), "m1.txt")
    with contextlib.redirect_stdout(io.StringIO()) as _b1: H.run(lists, cands, perp, now=H.READ_NOT_BEFORE + 3, marker=mk1, log=lg)
    assert not os.path.exists(mk1) and "NOT_ENOUGH_DATA, n trades = 35" in _b1.getvalue(), _b1.getvalue()      # n 35, PF under 1.0: no call, no marker
    H.trades_of = lambda m, b, p: (fake_ok, __import__("collections").Counter())
    mk2 = os.path.join(tempfile.mkdtemp(), "m2.txt")
    with contextlib.redirect_stdout(io.StringIO()) as _b2: H.run(lists, cands, perp, now=H.READ_NOT_BEFORE + 4, marker=mk2, log=lg)
    assert not os.path.exists(mk2) and "NOT_ENOUGH_DATA, n trades = 35" in _b2.getvalue() and "cash PF" not in _b2.getvalue()
    rows = open(lg).read().strip().split("\n"); assert len(rows) == 2 and all("n=35" in r for r in rows) and "2026-11-20" in rows[0], rows      # only the run that wrote no marker is logged
finally: H.trades_of = orig
# ---- Auditor B's four items (Nov 14, 2026), test first
import shutil, subprocess, hashlib
# ITEM 1: void and other results. A void window that trades is a trade with pnl = -fee(p), counted in n; a result that is not yes, no or void STOPS naming the window; the void count is printed
base_tr, _ = H.trades_of(H.load_markets_ho(lists), K.load_binary(cands), K.load_perp(perp)); tk0 = base_tr[3]["tk"]; p0 = base_tr[3]["p"]
lv, cv, pv = build(60, "2026-10-25", True, 7, override={tk0: "void"})
vtr, _ = H.trades_of(H.load_markets_ho(lv), K.load_binary(cv), K.load_perp(pv))
assert len(vtr) == len(base_tr), "a void window that trades must stay in n"
tv = [t for t in vtr if t["tk"] == tk0][0]; assert abs(tv["pnl"] + K.fee(p0)) < 1e-12 and not tv["win"] and tv.get("void") is True, tv
assert sum(1 for t in vtr if t.get("void")) == 1
for bad in ("", "cancelled", None):
    lb, _c, _p = build(60, "2026-10-25", True, 7, override={tk0: bad})
    try: H.load_markets_ho(lb); raise AssertionError("result %r was not refused" % (bad,))
    except SystemExit as e: assert tk0 in str(e), str(e)
# ITEM 2: tolerance on the bars (1e-9): PF 1.3 - 1e-12 is PASS, 1.0 - 1e-12 is NO CALL, 1.3 - 1e-6 is NO CALL
def pfset(pf): w = pf / 25; return [T(w)] * 25 + [T(-1.0 / 25)] * 25
assert H.label(pfset(1.3 - 1e-12)) == "PASS", H.label(pfset(1.3 - 1e-12))
assert H.label(pfset(1.0 - 1e-12)) == "NO CALL", H.label(pfset(1.0 - 1e-12))
assert H.label(pfset(1.3 - 1e-6)) == "NO CALL" and H.label(pfset(1.0 - 1e-6)) == "FAIL"
# ITEM 3: fixture mode only from Python; a MADE_UP_DATA file on the command line must not switch off the date lock (checked only before the read date, so the test never spends the real marker)
if time.time() < H.READ_NOT_BEFORE:
    lf, cf, pf_ = build(2, "2026-11-14", False, 3); open(os.path.join(lf, "MADE_UP_DATA"), "w").write("x")
    r = subprocess.run([sys.executable, "-I", os.path.join(here, "cfrti_k_heldout.py"), lf, cf, pf_], capture_output=True, text=True)
    assert r.returncode != 0 and "2026-11-20" in (r.stdout + r.stderr), (r.returncode, r.stdout[-300:], r.stderr[-300:])
# ITEM 4: the run must be proven whole, for each of the three folders, before anything is read and before the marker
def mkcopy(src):
    dst = tempfile.mkdtemp(); shutil.rmtree(dst); shutil.copytree(src, dst); return dst
def edit(dst, fn):
    m = json.load(open(dst + "/manifest.json")); fn(m["rows"], dst); json.dump(m, open(dst + "/manifest.json", "w"))
def d_sha(rows, dst): rows[0]["sha256"] = "0" * 64
def d_trunc(rows, dst): rows[0]["truncated"] = True
def d_404(rows, dst): rows[0]["status"] = 404
def d_gap(rows, dst): rows[0]["page"] = 2
def d_cursor(rows, dst):
    body = json.load(gzip.open(dst + "/a.json.gz")); body["cursor"] = "more"; raw = json.dumps(body).encode()
    with gzip.open(dst + "/a.json.gz", "wb") as f: f.write(raw)
    rows[0]["sha256"] = hashlib.sha256(raw).hexdigest(); rows[0]["bytes"] = len(raw)
def d_status(rows, dst): pass
for which in range(3):
    for fn in (d_sha, d_trunc, d_404, d_gap, d_cursor):
        folders = [lists, cands, perp]; folders[which] = mkcopy(folders[which]); edit(folders[which], fn)
        mkx = os.path.join(tempfile.mkdtemp(), "m.txt")
        try:
            with contextlib.redirect_stdout(io.StringIO()): H.run(folders[0], folders[1], folders[2], now=H.READ_NOT_BEFORE + 5, marker=mkx)
            raise AssertionError("a broken run was read: folder %d defect %s" % (which, fn.__name__))
        except SystemExit as e: assert "REFUSED" in str(e) and not os.path.exists(mkx), (which, fn.__name__, str(e))
    folders = [lists, cands, perp]; folders[which] = mkcopy(folders[which])
    m = json.load(open(folders[which] + "/manifest.json")); m["status"] = "stopped_429"; json.dump(m, open(folders[which] + "/manifest.json", "w"))
    mkx = os.path.join(tempfile.mkdtemp(), "m.txt")
    try:
        with contextlib.redirect_stdout(io.StringIO()): H.run(folders[0], folders[1], folders[2], now=H.READ_NOT_BEFORE + 5, marker=mkx)
        raise AssertionError("an incomplete manifest was read")
    except SystemExit as e: assert "REFUSED" in str(e) and not os.path.exists(mkx)
# Auditor B's follow-up (a): every request id of the manifest's embedded job must have rows (a request that never appears is a missing request); a manifest with no embedded job request list is refused
def d_missreq(rows, dst):
    m = json.load(open(dst + "/manifest.json")); m["job"]["requests"].append({"id": "r2"}); json.dump(m, open(dst + "/manifest.json", "w"))
def d_nojob(rows, dst):
    m = json.load(open(dst + "/manifest.json")); m.pop("job"); json.dump(m, open(dst + "/manifest.json", "w"))
def edit_raw(dst, fn):
    fn(None, dst)
for which in range(3):
    for fn in (d_missreq, d_nojob):
        folders = [lists, cands, perp]; folders[which] = mkcopy(folders[which]); fn(None, folders[which])
        mkx = os.path.join(tempfile.mkdtemp(), "m.txt")
        try:
            with contextlib.redirect_stdout(io.StringIO()): H.run(folders[0], folders[1], folders[2], now=H.READ_NOT_BEFORE + 5, marker=mkx)
            raise AssertionError("a run with a missing request or no job was read: folder %d %s" % (which, fn.__name__))
        except SystemExit as e: assert "REFUSED" in str(e) and not os.path.exists(mkx), (which, fn.__name__, str(e))
print("CFRTI-K HELD-OUT TEST OK (filter strictly after Nov 14 00:00Z, boundary count, label rule, under 50 prints only the count and spends nothing, refuses before Nov 20, marker, second run refused)")
print(out.strip())
