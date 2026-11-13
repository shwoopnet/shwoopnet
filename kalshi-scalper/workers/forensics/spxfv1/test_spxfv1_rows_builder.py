#!/usr/bin/env python3
"""Tests for spxfv1_rows_builder.py and spxfv1_databento_pull.py on INVENTED rows only (Forensics desk, Nov 13, 2026). The expected rows below were worked out by hand from the layout
description in the builder's docstring before the builder was run. Exit 1 on any mismatch. usage: python3 -I test_spxfv1_rows_builder.py"""
import sys, os, json, gzip, csv, hashlib, tempfile, calendar, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import spxfv1_rows_builder as B
import spxfv1_databento_pull as P

T = lambda s: calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))
bad = []
def chk(name, cond, detail=""): print("%-104s %s %s" % (name, "PASS" if cond else "FAIL", detail)); (None if cond else bad.append(name))

def run_folder(root, name, bodies):
    d = os.path.join(root, name); os.makedirs(d); rows = []
    for i, b in enumerate(bodies, 1):
        fn = "%04d.json.gz" % i; gzip.open(os.path.join(d, fn), "wt").write(json.dumps(b)); rows.append({"id": "r%d" % i, "status": 200, "file": fn})
    json.dump({"job": {"job_id": "INVENTED"}, "started": "2026-01-01T0000Z", "rows": rows}, open(os.path.join(d, "manifest.json"), "w")); return d

def cdl(end, bid, ask):
    c = {"end_period_ts": end}
    if bid is not None: c["yes_bid"] = {"close_dollars": "%.4f" % bid}
    if ask is not None: c["yes_ask"] = {"close_dollars": "%.4f" % ask}
    return c

C1, C2, C3, C4, C5, C6 = (T("2026-11-05T15:00:00Z"), T("2026-11-05T15:15:00Z"), T("2026-11-05T15:30:00Z"), T("2026-11-05T15:45:00Z"), T("2026-11-05T16:00:00Z"), T("2026-11-06T15:00:00Z"))
iso = lambda t: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))
mk = lambda t, c, res, ev=None: {"ticker": t, "event_ticker": ev or t, "close_time": iso(c), "result": res}
lists = [{"markets": [mk("KXINX15M-A", C1, "yes"), mk("KXINX15M-B", C2, "no"), mk("KXINX15M-C", C3, "scalar"), mk("KXINX15M-D", C4, "no"), mk("KXINX15M-E", C5, ""), mk("KXINXU-Z", C1, "yes")]}]
candles = [{"markets": [{"market_ticker": "KXINX15M-A", "candlesticks": [cdl(C1 - 180, 0.50, 0.52), cdl(C1 - 120, 0.06, 0.08), cdl(C1 - 60, 0.07, 0.09)]},
                         {"market_ticker": "KXINX15M-B", "candlesticks": [cdl(C2 - 120, 0.20, None)]},
                         {"market_ticker": "KXINX15M-C", "candlesticks": [cdl(C3 - 120, None, 0.30)]},
                         {"market_ticker": "KXINX15M-D", "candlesticks": [cdl(C4 - 60, 0.10, 0.12)]},
                         {"market_ticker": "KXINX15M-E", "candlesticks": [cdl(C5 - 120, 0.40, 0.44)]}]}]
td = tempfile.mkdtemp(prefix="spxrb_"); L = run_folder(td, "lists", lists); Cd = run_folder(td, "candles", candles)
out = os.path.join(td, "windows.csv"); r = B.build_windows([L], [Cd], out); rows = list(csv.reader(open(out)))
want = [["ticker", "event_ticker", "close_ts", "yes_bid", "yes_ask", "result"],
        ["KXINX15M-A", "KXINX15M-A", str(C1), "0.06", "0.08", "yes"],         # the candle ending exactly 120 s before the close, not 180 s or 60 s
        ["KXINX15M-B", "KXINX15M-B", str(C2), "0.2", "1.0", "no"],            # no ask in the candle: 1.0
        ["KXINX15M-C", "KXINX15M-C", str(C3), "0.0", "0.3", "void"],          # no bid: 0.0; scalar result is a void
        ["KXINX15M-D", "KXINX15M-D", str(C4), "0.0", "1.0", "no"],            # only a candle at 60 s: no decision candle
        ["KXINX15M-E", "KXINX15M-E", str(C5), "0.4", "0.44", "empty"]]        # no result: empty (build 2 stops on it)
chk("windows: the rows, bids, asks and results are as worked out by hand (decision candle exactly close - 120 s; missing side 0.0 or 1.0)", rows == want, str(rows[:2]))
chk("windows: counts by reason (1 no ask, 1 no bid, 1 no decision candle, 1 void, 1 empty result) and the other series is left out", r["counts"] == {"no_ask": 1, "no_bid": 1, "no_decision_candle": 1, "void": 1, "empty_result": 1} and r["markets"] == 5, str(r))
def stops(fn, frag):
    try: fn(); return False
    except B.Stop as e: return frag in str(e)
L2 = run_folder(td, "lists2", [{"markets": [mk("KXINX15M-H", T("2026-12-01T00:00:00Z"), "yes")]}])
chk("a market closing at 2026-12-01T00:00:00Z stops the builder (held-out block)", stops(lambda: B.build_windows([L2], [Cd], os.path.join(td, "w2.csv")), "held-out"))
L3 = run_folder(td, "lists3", [{"markets": [mk("KXINX15M-I", T("2026-11-30T23:59:59Z"), "yes")]}])
chk("a market closing at 2026-11-30T23:59:59Z is read", B.build_windows([L3], [Cd], os.path.join(td, "w3.csv"))["markets"] == 1)
HD = os.path.join(td, "HELDOUT_x"); os.makedirs(HD); os.makedirs(os.path.join(HD, "lists")); json.dump({"rows": []}, open(os.path.join(HD, "lists", "manifest.json"), "w"))
chk("a HELDOUT_ folder is refused", stops(lambda: B.build_windows([os.path.join(HD, "lists")], [Cd], os.path.join(td, "w4.csv")), "HELDOUT_"))
LR = os.path.join(td, "pull", "POLGAPH_LISTS", "2026-11-13T0627Z_43378777252"); os.makedirs(LR); json.dump({"rows": []}, open(os.path.join(LR, "manifest.json"), "w"))
chk("a run named in HELDOUT_PULL_RUNS.md is refused", stops(lambda: B.build_windows([LR], [Cd], os.path.join(td, "w5.csv")), "listed as held-out"))
# futures: two instrument ids (a roll), nanosecond starts, one unreadable row
ns = lambda t: str(t * 1_000_000_000)
dbn = os.path.join(td, "es.csv")
with open(dbn, "w", newline="") as f:
    w = csv.writer(f); w.writerow(["ts_event", "rtype", "publisher_id", "instrument_id", "open", "high", "low", "close", "volume", "symbol"])
    w.writerow([ns(T("2026-11-05T14:30:00Z")), 33, 1, 101, 1, 1, 1, "5987.250000000", 10, "ESZ6"]); w.writerow([ns(T("2026-11-05T14:31:00Z")), 33, 1, 101, 1, 1, 1, "5987.500000000", 10, "ESZ6"])
    w.writerow([ns(T("2026-11-05T14:32:00Z")), 33, 1, 102, 1, 1, 1, "5990.000000000", 10, "ESH7"]); w.writerow(["bad", 33, 1, 102, 1, 1, 1, "x", 10, "ESH7"])
fo = os.path.join(td, "futures.csv"); fr = B.build_futures(dbn, fo); frows = list(csv.reader(open(fo)))
chk("futures: ts_event in ns becomes the bar-start second, symbol ES.c.0, instrument id kept, one unreadable row counted", frows[1] == [str(T("2026-11-05T14:30:00Z")), "ES.c.0", "101", "5987.2500000000"] and frows[3][2] == "102" and fr["bars"] == 3 and fr["unreadable_rows"] == 1)
hand = "%d,101,5987.25\n%d,101,5987.50\n%d,102,5990.00\n" % (T("2026-11-05T14:30:00Z"), T("2026-11-05T14:31:00Z"), T("2026-11-05T14:32:00Z"))
chk("futures: the canonical extract hash equals the sha256 of the lines written out by hand", fr["canonical_extract_sha256"] == hashlib.sha256(hand.encode()).hexdigest(), fr["canonical_extract_sha256"][:16])
bad_sym = os.path.join(td, "bad_sym.csv"); open(bad_sym, "w").write(open(dbn).read().replace("ESH7", "NQH7").replace("ESZ6", "NQZ6"))
chk("futures: a non-ES symbol stops the builder", stops(lambda: B.build_futures(bad_sym, os.path.join(td, "f2.csv")), "ES family"))
dup = os.path.join(td, "dup.csv"); open(dup, "w").write(open(dbn).read() + "%s,33,1,101,1,1,1,5987.25,10,ESZ6\n" % ns(T("2026-11-05T14:30:00Z")))
chk("futures: two bars with the same start stop the builder", stops(lambda: B.build_futures(dup, os.path.join(td, "f3.csv")), "same ts_event"))
inrepo = os.path.join(B.REPO, "kalshi-scalper", "should_never_exist.csv")
chk("futures: an input or output path inside the git working tree is refused", stops(lambda: B.build_futures(dbn, inrepo), "git working tree") and not os.path.exists(inrepo))
# the pull: cost first, abort over the cap before any data call
calls = []
def fetch_ok(method, path, q):
    calls.append((method, path))
    if path.endswith("get_cost"): return b"0.03"
    return b"ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol\n%s,33,1,101,1,1,1,5987.25,1,ESZ6\n" % ns(T("2026-11-05T14:30:00Z")).encode()
po = os.path.join(td, "pull.csv"); tot = P.pull(po, 0.25, fetch_ok)
chk("pull: six costs read first, then six data requests, under the cap; one header only; spend equals the sum (0.18)", [c[1] for c in calls[:6]] == ["/metadata.get_cost"] * 6 and [c[1] for c in calls[6:]] == ["/timeseries.get_range"] * 6 and abs(tot - 0.18) < 1e-9 and open(po).read().count("ts_event,rtype") == 1)
calls.clear()
def fetch_dear(method, path, q): calls.append((method, path)); return b"0.05"
pe = os.path.join(td, "pull2.csv")
try: P.pull(pe, 0.25, fetch_dear); ab = False
except P.Stop as e: ab = "ABORTED before any data request" in str(e)
chk("pull: a quoted total of 0.30 is over the 0.25 cap: aborted, only cost calls made, no file written", ab and all(c[1] == "/metadata.get_cost" for c in calls) and not os.path.exists(pe))
chk("pull: the query is the Testing Desk's (GLBX.MDP3, ES.c.0, ohlcv-1m, continuous, 14:30Z to 21:00Z on Nov 5, 6, 9, 10, 11, 12)", P.DATASET == "GLBX.MDP3" and P.SYMBOL == "ES.c.0" and P.SCHEMA == "ohlcv-1m" and P.STYPE == "continuous" and P.DAYS == ["2026-11-05", "2026-11-06", "2026-11-09", "2026-11-10", "2026-11-11", "2026-11-12"] and P.params("2026-11-05")["start"] == "2026-11-05T14:30:00Z" and P.params("2026-11-05")["end"] == "2026-11-05T21:00:00Z")
chk("pull: no Authorization header and no key in the file", "Authorization" not in open(os.path.join(HERE, "spxfv1_databento_pull.py")).read().replace("no Authorization header", "").replace("sends no Authorization header", ""))
print("\n%d FAIL" % len(bad)); sys.exit(1 if bad else 0)
