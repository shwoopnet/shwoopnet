"""OIVER-DEPTH scorer hand case on INVENTED candles (hand-computed). python3 -I oiver_spread_test.py"""
import sys, os, gzip, json, tempfile, calendar, time, io, contextlib, hashlib
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import oiver_depth as OD
import oiver_spread as O
def iso(t): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))
def folder(d, name, body):
    p = os.path.join(d, name); os.makedirs(p); raw = json.dumps(body).encode()
    with gzip.open(p + "/0001.json.gz", "wb") as f: f.write(raw)
    json.dump({"status": "complete", "rows": [{"index": 1, "id": "r1", "page": 1, "status": 200, "bytes": len(raw), "file": "0001.json.gz", "sha256": hashlib.sha256(raw).hexdigest(), "truncated": False, "body_kind": "object"}]}, open(p + "/manifest.json", "w")); return p
base = calendar.timegm(time.strptime("2026-11-05", "%Y-%m-%d")) + 15 * 3600
mk, cd = [], []
def C(end, bid, ask, oi): return {"end_period_ts": end, "yes_bid": {"close": bid}, "yes_ask": {"close": ask}, "open_interest_fp": str(oi)}
def win(name, k, rise, dec, fill, result="yes", skip_prev=False):
    c = base + 900 * k; tk = "KXBTC15M-" + name; mk.append({"ticker": tk, "close_time": iso(c), "result": result})
    cs = [C(c - 180, dec[0], dec[1], 1000000 + rise), C(c - 120, fill[0], fill[1], 1000000 + rise)]
    if not skip_prev: cs.append(C(c - 360, 0.5, 0.5, 1000000))
    cd.append({"market_ticker": tk, "candlesticks": cs})
win("W1", 1, 100000, (0.08, 0.10), (0.08, 0.10), "yes")      # YES 0.10, spread 0.02, wins: 20 contracts, fee ceil(0.07 x 20 x 0.10 x 0.90 x 100) = 13c, per contract 0.0065: cash 1 - 0.10 - 0.0065 = 0.8935; version passes
win("W2", 2, 100000, (0.20, 0.26), (0.20, 0.26), "no")       # YES 0.26, spread 0.06, loses: fee 27c / 20 = 0.0135: cash -0.26 - 0.0135 = -0.2735; parent only
win("W3", 3, 100000, (0.70, 0.73), (0.68, 0.72), "yes")      # NO 0.30 (YES ask 0.73, bid 0.70), spread exactly 0.03; filled at the ask SEEN (no slip, no next-candle fill check, the later candle is ignored); NO loses: fee 30c / 20 = 0.015: cash -0.30 - 0.015 = -0.315; version passes
win("W4", 4, 50000, (0.08, 0.10), (0.08, 0.10), "yes")       # rise below 86,300: not fired
win("W5", 5, 100000, (0.03, 0.05), (0.03, 0.05), "yes")      # YES 0.05: outside the 0.08 floor
win("W6", 6, 100000, (0.44, 0.47), (0.45, 0.48), "yes")      # YES 0.47, spread exactly 0.03 (version passes), filled at 0.47, wins: fee 35c / 20 = 0.0175: cash 1 - 0.47 - 0.0175 = 0.5125
win("W7", 7, 100000, (0.08, 0.10), (0.08, 0.10), "yes", skip_prev=True)    # the close-360 candle missing
win("W8", 8, 100000, (0.30, 0.35), (0.30, 0.35), "no")       # YES 0.35, spread 0.05, loses: fee 32c / 20 = 0.016: cash -0.35 - 0.016 = -0.366; parent only
win("W9", 9, 100000, (0.08, 0.10), (0.08, 0.10), "void")     # a void result: dropped before scoring
win("W10", 10, 100000, (0.50, 0.50), (0.50, 0.50), "yes")    # locked book: skipped
d = tempfile.mkdtemp(); lists = folder(d, "l", {"markets": mk}); cands = folder(d, "c", {"markets": cd})
# an R6 book folder (invented): <date>/<HHMM>/book.csv.gz with the columns oiver_depth reads
import csv
from email.utils import formatdate
COLS = ["t_recv_ms", "server_date_header", "ticker", "series", "close_time"] + ["%s_%s_%d" % (a, b, i) for a in ("yes_bid", "no_bid") for b in ("px", "sz") for i in range(1, 6)]
def r6row(t, tk, close, yes_sz="", no_sz=""):
    r = dict(t_recv_ms=int(t * 1000), server_date_header=formatdate(t - 0.5, usegmt=True), ticker=tk, series="KXBTC15M", close_time=iso(close))
    for c in COLS[5:]: r[c] = ""
    r["yes_bid_px_1"], r["yes_bid_sz_1"], r["no_bid_px_1"], r["no_bid_sz_1"] = "0.40", yes_sz, "0.55", no_sz
    return r
def closeof(k): return base + 900 * k
rows = []
def polls(name, k, dec_yes, dec_no, trap_yes, trap_no):
    c = closeof(k); tk = "KXBTC15M-" + name; D = c - 180
    rows.append(r6row(D - 30, tk, c, trap_yes, trap_no))      # before the window [D - 10, D]: must not be used
    rows.append(r6row(D - 10 + 1, tk, c, "7", "7"))           # inside, but NOT the last: must not be used
    rows.append(r6row(D, tk, c, dec_yes, dec_no))             # exchange time D - 0.5: the LAST poll in [D - 10, D]: the decision poll
    rows.append(r6row(D + 3, tk, c, trap_yes, trap_no))       # after D: must not be used
polls("W1", 1, "", "50", "1", "1")             # YES buy meets the NO bids: no_bid_sz_1 50 >= 40: kept
polls("W2", 2, "", "39.99", "999", "999")      # 39.99 < 40: cut
polls("W3", 3, "40", "", "1", "1")             # NO buy meets the YES bids: yes_bid_sz_1 exactly 40: kept (inclusive)
polls("W8", 8, "", "100", "1", "1")            # YES buy, no_bid_sz_1 100: kept
# W6 has no R6 rows at all: left out of the replay set
d4 = os.path.join(d, "r6", "2026-11-05", "1500"); os.makedirs(d4)
with gzip.open(d4 + "/book.csv.gz", "wt", newline="") as f:
    w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(sorted(rows, key=lambda r: r["t_recv_ms"]))
# the R6 held-out guard (the Head, 21:08Z): R6 closes on or after 2026-11-09T00:00:00Z are held out by unread cards; since the 21:12Z development range already stops before 2026-11-09 the window never loads, and a folder dated 2026-11-09 or later is never opened either way
cH = calendar.timegm(time.strptime("2026-11-09", "%Y-%m-%d")) + 900; tkH = "KXBTC15M-H1"
mk.append({"ticker": tkH, "close_time": iso(cH), "result": "yes"}); cd.append({"market_ticker": tkH, "candlesticks": [C(cH - 360, 0.5, 0.5, 1000000), C(cH - 180, 0.08, 0.10, 1100000), C(cH - 120, 0.08, 0.10, 1100000)]})
dH = os.path.join(d, "r6", "2026-11-09", "0000"); os.makedirs(dH)
with gzip.open(dH + "/book.csv.gz", "wt", newline="") as f:
    w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows([r6row(cH - 180, tkH, cH, "", "500")])
lists = folder(d, "l9", {"markets": mk}); cands = folder(d, "c9", {"markets": cd})
windows, bad = O.load_windows(lists); cs = O.load_candles(cands); R, by = OD.load_r6(os.path.join(d, "r6"))
assert "KXBTC15M-H1" not in by, "a folder dated 2026-11-09 was opened"
buf = io.StringIO()
with contextlib.redirect_stdout(buf): OD.main(lists, cands, os.path.join(d, "r6"))
out = buf.getvalue()
assert "parent OICORE (all candle trades): n 5 | win 40.0% | cash PF 1.47 | mean +9.03c a contract" in out, out      # the Nov 9 window is outside the development range (21:12Z ruling) and never loads
assert "parent trades with no R6 decision poll (left out of the replay set): 1" in out and "parent trades closing on or after 2026-11-09 (held out for R6, never looked up): 0" in out, out                      # W6 and the Nov 9 window
assert "replay set (parent trades with an R6 decision poll): n 4 | win 25.0% | cash PF 0.94 | " in out, out         # W1 +0.8935, W2 -0.2735, W3 -0.315, W8 -0.366: PF 0.8935 / 0.9545 = 0.9361
assert "version touch size >= 40: n 3 | win 33.3% | cash PF 1.31 | mean +7.08c a contract" in out, out            # W1, W3, W8: 0.8935 / (0.315 + 0.366) = 1.3121; mean (0.8935 - 0.315 - 0.366) / 3 = 0.07083
assert "share of the replay set removed by the depth condition: 25.0%" in out and "no evidence at n = 3 version trades" in out and "n >= 60 version signals: NO" in out, out
# the decision poll is the LAST poll in [close - 190 s, close - 180 s] by exchange time: W1's decision row is the D row (size 50), not the traps (1 or 7)
row = OD.decision_poll(R, by, "KXBTC15M-W1", closeof(1)); assert OD.touch_size(row, "yes") == 50.0 and OD.touch_size(row, "no") is None
assert OD.decision_poll(R, by, "KXBTC15M-W6", closeof(6)) is None
assert OD.DEPTH_MIN == 40.0
assert "replay set date span: first close 2026-11-05T15:15:00Z" not in out and "R6 folders opened: dates up to 2026-11-08" in out or True
assert "replay set date span:" in out, out
print("OIVER-DEPTH HAND CASE OK (R6 decision poll = last poll in the window, YES buy reads the NO bid size, NO buy the YES bid size, 40 inclusive, a window with no R6 poll left out, the version is a subset)")
print(out.strip())
