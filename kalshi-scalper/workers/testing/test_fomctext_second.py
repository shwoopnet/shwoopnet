"""Test for fomctext_second.py: INVENTED data only (FOMCTEXT_SECOND_HAND_CASE.md). Run: python3 -B -W ignore test_fomctext_second.py"""
import csv, datetime, gzip, io, json, os, sys, tempfile, zoneinfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fomctext_second as f

ET = zoneinfo.ZoneInfo("America/New_York")
def end_ts(date, h=14, m=5):
    y, mo, d = map(int, date.split("-")); return int(datetime.datetime(y, mo, d, h, m, tzinfo=ET).timestamp())
assert end_ts("2025-10-29") == 1761761100 and end_ts("2025-12-10") == 1765393500          # 18:05Z (EDT) and 19:05Z (EST)
assert f.candle_end("2025-10-29") == end_ts("2025-10-29") and f.candle_end("2025-12-10") == end_ts("2025-12-10") and f.candle_end("2025-03-19") == end_ts("2025-03-19") and f.candle_end("2025-01-29") == end_ts("2025-01-29")
HDR = "decision_date,event_ticker,market_ticker,strike_word,statement_word,type,word_present,count,threshold,passA_answer,passA_count,passA_type,passB_answer,passB_count,passB_type,third_reading,context"
def trow(date, tk, sw, typ="statement-type"):
    ev = "KXFEDMENTION-" + tk.split("-")[1]
    return [date, ev, tk, "word " + tk, sw, typ, "", "0", "", "", "", "", "", "", "", "", ""]
def table_text(rows): 
    b = io.StringIO(); w = csv.writer(b, lineterminator="\n"); w.writerow(HDR.split(","))
    for r in rows: w.writerow(r)
    return b.getvalue()
def cnode(tk, cs): return {"candlesticks": [{"end_period_ts": ts, "yes_bid": {"close_dollars": "%.2f" % b}, "yes_ask": {"close_dollars": "%.2f" % a}} for ts, b, a in cs]}
def build(d, strikes, extra_candle=None, no_candle_answer=(), lists_extra=()):
    """strikes: list of (date, ticker, sw, type, bid, ask, result); bid None = no 14:05 candle (a 14:04 candle is stored instead)."""
    rows = [trow(s[0], s[1], s[2], s[3]) for s in strikes]
    T = os.path.join(d, "table.csv"); open(T, "w").write(table_text(rows))
    mk = [{"ticker": s[1], "event_ticker": "KXFEDMENTION-" + s[1].split("-")[1], "close_time": "2026-01-01T00:00:00Z", "result": s[6]} for s in strikes] + list(lists_extra)
    L, C = os.path.join(d, "L"), os.path.join(d, "C")
    def mkrun(path, bodies):
        os.makedirs(path); rr = []
        for i, (rid, body) in enumerate(bodies):
            fn = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(path, fn), "wt").write(json.dumps(body)); rr.append({"id": rid, "page": 1, "status": 200, "file": fn})
        json.dump({"job": {}, "rows": rr, "status": "complete"}, open(os.path.join(path, "manifest.json"), "w"))
    mkrun(L, [("l1", {"markets": mk})])
    bodies = []
    for s in strikes:
        if s[1] in no_candle_answer: continue
        e = end_ts(s[0])
        cs = [(e, s[4], s[5])] if s[4] is not None else [(e - 60, 0.30, 0.32)]
        bodies.append(("h_" + s[1], cnode(s[1], cs)))
    mkrun(C, bodies)
    return T, L, C
S = "statement-type"; N = "NOT STATEMENT-TYPE"
A, B = "2025-10-29", "2025-12-10"
D1 = [(A, "KXFEDMENTION-25OCT-A1", "yes", S, .58, .60, "yes"), (A, "KXFEDMENTION-25OCT-A2", "yes", S, .85, .87, "yes"), (A, "KXFEDMENTION-25OCT-A3", "yes", S, .84, .86, "yes"), (A, "KXFEDMENTION-25OCT-A4", "yes", S, .48, .50, "no"),
      (A, "KXFEDMENTION-25OCT-A5", "yes", S, None, None, "yes"), (A, "KXFEDMENTION-25OCT-A6", "yes", S, 0.0, .30, "yes"), (A, "KXFEDMENTION-25OCT-A7", "no", S, .38, .40, "yes"), (A, "KXFEDMENTION-25OCT-A8", "no", S, .88, .90, "yes"),
      (A, "KXFEDMENTION-25OCT-A9", "no", N, .18, .20, "yes"),
      (B, "KXFEDMENTION-25DEC-B1", "yes", S, .18, .20, "yes"), (B, "KXFEDMENTION-25DEC-B2", "yes", S, .28, .30, "void"), (B, "KXFEDMENTION-25DEC-B3", "yes", S, .43, .45, "yes"), (B, "KXFEDMENTION-25DEC-B6", "yes", S, .60, .60, "yes"),
      (B, "KXFEDMENTION-25DEC-B4", "no", S, .08, .10, "no"), (B, "KXFEDMENTION-25DEC-B5", "no", S, .13, .15, "yes"),
      ("2026-06-17", "KXFEDMENTION-26JUN-C1", "yes", S, .30, .32, "yes"), ("2026-07-29", "KXFEDMENTION-26JUL-C2", "no", S, .30, .32, "yes")]
with tempfile.TemporaryDirectory() as d:
    T, L, C = build(d, D1)
    r = f.run(T, [L], [C], hash_check=False)
    k, p = r["kill_arm"], r["placebo"]
    assert r["table_rows"] == 17 and r["heldout_rows_dropped"] == 2 and r["development_rows"] == 15 and r["not_statement_type_n"] == 1 and k["n"] == 10 and p["n"] == 4, r
    assert k["two_sided"] == 7 and abs(k["two_sided_share"] - 0.7) < 1e-12 and k["results"] == {"yes": 8, "no": 1, "void": 1, "other": 0}, k
    assert (k["raw"]["count"], k["raw"]["meetings"]) == (5, 2) and (k["1c"]["count"], k["1c"]["meetings"]) == (4, 2) and (k["2c"]["count"], k["2c"]["meetings"]) == (3, 2), k
    assert k["kill"]["1c"] == {"a": True, "b": True, "c": False} and k["kill"]["2c"] == {"a": True, "b": True, "c": False} and k["kill"]["raw"] == {"a": True, "b": True, "c": False}
    assert r["VERDICT"].startswith("CLOSED") and "upper bound, not fill-checked" in r["VERDICT"]
    assert r["haircut"] == {"1c": "does not count: fails the haircut", "2c": "does not count: fails the haircut"} and r["could_count_toward_20_to_30"] is False
    assert p["two_sided"] == 4 and p["results"] == {"yes": 3, "no": 1, "void": 0, "other": 0} and p["raw"]["count"] == 2 and p["1c"]["count"] == 2 and p["2c"]["count"] == 2 and "kill" not in p
    out = f.render(r); assert "could count toward the 20 to 30: no" in out and "does not count: fails the haircut" in out and "not statement-type, n = 1" in f.render(r) and "upper bound, not fill-checked" in f.render(r) and "KXFEDMENTION" not in f.render(r)
# the held-out rows: their candle and result readers are never touched
with tempfile.TemporaryDirectory() as d:
    T, L, C = build(d, D1)
    # a held-out ticker in the lists answers: poison its dict through the reader hook
    seen = []
    orig = f.read_results
    def spy(lists, wanted):
        out = orig(lists, wanted); seen.append(set(wanted)); return out
    f.read_results = spy
    try: f.run(T, [L], [C], hash_check=False)
    finally: f.read_results = orig
    assert "KXFEDMENTION-26JUN-C1" not in seen[0] and "KXFEDMENTION-26JUL-C2" not in seen[0] and len(seen[0]) == 15
    # a result of an unlisted ticker is never read: add one with a poisoned result and see the run still passes
    cand = f.read_candles
    got = []
    f.read_candles = lambda runs, wanted: (got.append(set(wanted)), cand(runs, wanted))[1]
    try: f.run(T, [L], [C], hash_check=False)
    finally: f.read_candles = cand
    assert "KXFEDMENTION-26JUN-C1" not in got[0]
# --- D2: exactly at the lines ---
dates = ["2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30"]
def d2(modify=None):
    out = []
    for i, dt in enumerate(dates):
        mon = ["25JAN", "25MAR", "25MAY", "25JUN", "25JUL"][i]
        for j in range(3): out.append([dt, "KXFEDMENTION-%s-K%d" % (mon, j), "yes", S, .48, .50, "yes"])
        for j in range(3): out.append([dt, "KXFEDMENTION-%s-N%d" % (mon, j), "yes", S, None, None, "yes"])
    if modify: modify(out)
    return [tuple(x) for x in out]
def verdict(strikes):
    with tempfile.TemporaryDirectory() as d:
        T, L, C = build(d, strikes); r = f.run(T, [L], [C], hash_check=False); return r
r = verdict(d2()); k = r["kill_arm"]
assert k["n"] == 30 and k["two_sided"] == 15 and k["raw"]["count"] == k["1c"]["count"] == k["2c"]["count"] == 15 and k["1c"]["meetings"] == 5 and r["VERDICT"].startswith("NOT CLOSED"), (k, r["VERDICT"])
assert k["kill"]["1c"] == {"a": False, "b": False, "c": False} and r["haircut"] == {"1c": "passes the haircut", "2c": "passes the haircut"} and r["could_count_toward_20_to_30"] is True
def rm_one(o): o[0][6] = "no"
r = verdict(d2(rm_one)); assert r["kill_arm"]["raw"]["count"] == 14 and r["kill_arm"]["kill"]["raw"]["a"] is True and r["VERDICT"].startswith("CLOSED") and r["could_count_toward_20_to_30"] is False
def rm_meeting(o):
    for x in o[:3]: x[6] = "no"
r = verdict(d2(rm_meeting)); kk = r["kill_arm"]; assert kk["1c"]["count"] == 12 and kk["1c"]["meetings"] == 4 and kk["kill"]["1c"]["a"] and kk["kill"]["1c"]["b"] and r["VERDICT"].startswith("CLOSED")
def add_nocandle(o): o.append(["2025-07-30", "KXFEDMENTION-25JUL-N9", "yes", S, None, None, "yes"])
r = verdict(d2(add_nocandle)); kk = r["kill_arm"]; assert kk["n"] == 31 and kk["two_sided"] == 15 and kk["kill"]["1c"]["c"] is True and kk["kill"]["1c"]["a"] is False and r["VERDICT"].startswith("CLOSED")
def on_line(o):
    for x in o[:3]: x[4], x[5] = .85, .86
r = verdict(d2(on_line)); kk = r["kill_arm"]; assert kk["1c"]["count"] == 15 and kk["2c"]["count"] == 12 and kk["kill"]["2c"]["a"] is True and kk["kill"]["1c"]["a"] is False and r["VERDICT"].startswith("NOT CLOSED") and r["haircut"] == {"1c": "passes the haircut", "2c": "does not count: fails the haircut"} and r["could_count_toward_20_to_30"] is False, (kk, r["VERDICT"])          # RAW decides; a haircut line only labels
# more edges: the 1e-9 tolerance on the cap, a 2c-only count, a NOT STATEMENT-TYPE strike with feature yes stays out of the kill arm, no unlisted result is read, the hash check is called by default
assert f.counted("yes", 0.87 + 5e-10, 0.0) and not f.counted("yes", 0.87 + 2e-9, 0.0) and f.counted("yes", 0.85, 0.02) and not f.counted("yes", 0.85, 0.03)
def at_85(o):
    for x in o[:3]: x[4], x[5] = .83, .85
r = verdict(d2(at_85)); kk = r["kill_arm"]; assert kk["raw"]["count"] == kk["1c"]["count"] == kk["2c"]["count"] == 15 and r["VERDICT"].startswith("NOT CLOSED") and r["could_count_toward_20_to_30"] is True          # 0.85 + .02 = .87 is on the line and counts
with tempfile.TemporaryDirectory() as d:
    T, L, C = build(d, D1[:9] + [(A, "KXFEDMENTION-25OCT-Z1", "yes", N, .40, .42, "yes")]); rz = f.run(T, [L], [C], hash_check=False)
    assert rz["not_statement_type_n"] == 2 and rz["kill_arm"]["n"] == 6 and rz["placebo"]["n"] == 2, rz          # A9 and Z1; the 6 kill-arm strikes A1 to A6; placebo A7, A8
with tempfile.TemporaryDirectory() as d:
    T, L, C = build(d, D1[:3])
    saved = f.k.iter_answers
    class Boom(dict):
        def get(self, key, default=None):
            if key == "result": raise AssertionError("read the result of an unwanted market")
            return super().get(key, default)
    def fake(folder, allow_heldout=False):
        for row, body in saved(folder, allow_heldout):
            if "markets" in body and folder == L: body = {"markets": body["markets"] + [Boom({"ticker": "KXFEDMENTION-99XXX-Q", "result": "yes"})]}
            yield row, body
    f.k.iter_answers = fake
    try: f.run(T, [L], [C], hash_check=False)
    finally: f.k.iter_answers = saved
    calls = []; sv = f.check_hashes; f.check_hashes = lambda want=None: calls.append(1)
    try: f.run(T, [L], [C]); f.run(T, [L], [C], hash_check=False); assert calls == [1]
    finally: f.check_hashes = sv
# --- ADDENDUM: the unit rule (Head, 02:28Z) ---
node = lambda **kw: dict(kw)
assert f.quote((node(close="0.5800"), node(close="0.6000")), "T") == (0.58, 0.60) and f.quote((node(close_dollars="0.58"), node(close_dollars="0.60")), "T") == (0.58, 0.60)
assert f.quote((node(close_dollars="0.58", close="9"), node(close_dollars="0.60", close="9")), "T") == (0.58, 0.60)          # close_dollars is used as before
for bad in (0.58, "0.58", "58", "0.58000", " 0.5800", "0.5800\n", "-0.5000", "2.0000", True, None, ["0.5800"]):
    try: f.quote((node(close=bad), node(close="0.6000")), "KXFEDMENTION-25OCT-BAD"); assert 0, bad
    except SystemExit as e: assert "STOP" in str(e) and "KXFEDMENTION-25OCT-BAD" in str(e), (bad, str(e))
assert f.quote((node(close="0.0000"), node(close="0.6000")), "T") == (0.0, 0.60) and f.quote((node(close="0.5800"), node(close="1.0000")), "T") == (0.58, 1.0) and f.quote((node(close="0.5800"), node(close="1.5000")), "T") == (0.58, 1.5)          # read, then rule 18 decides
assert not f.two_sided(0.0, 0.60) and not f.two_sided(0.58, 1.0) and not f.two_sided(0.58, 1.5)
assert f.quote((None, node(close="0.6000")), "T") == (None, 0.60) and f.quote(({}, node(close="0.6000")), "T") == (None, 0.60) and f.quote(("x", None), "T") == (None, None) and f.quote((node(close_dollars=None), node(close="0.6000")), "T") == (None, 0.60)
# end to end in close form: the same strikes score exactly as D1 does; only the 14:05 candle is looked at
def to_close_form(C):
    for fn in sorted(os.listdir(C)):
        if fn.endswith(".json.gz"):
            fp = os.path.join(C, fn); body = json.load(gzip.open(fp, "rt"))
            for c in body["candlesticks"]:
                for side in ("yes_bid", "yes_ask"):
                    c[side] = {"close": "%.4f" % float(c[side]["close_dollars"])}
            body["candlesticks"].append({"end_period_ts": 5, "yes_bid": {"close": "0.0000"}, "yes_ask": {"close": "1.0000"}})          # another minute: never read
            gzip.open(fp, "wt").write(json.dumps(body))
with tempfile.TemporaryDirectory() as d:
    T, L, C = build(d, D1); to_close_form(C)          # includes the placeholder strike A6 (bid 0.00 -> close "0.0000"): read, not two-sided, no stop (the Head, 02:31Z)
    r = f.run(T, [L], [C], hash_check=False); k = r["kill_arm"]
    assert (k["raw"]["count"], k["1c"]["count"], k["2c"]["count"]) == (5, 4, 3) and r["placebo"]["raw"]["count"] == 2 and k["two_sided"] == 7 and k["n"] == 10, r
with tempfile.TemporaryDirectory() as d:
    T, L, C = build(d, D1); to_close_form(C)
    fp = os.path.join(C, "0001.json.gz"); body = json.load(gzip.open(fp, "rt")); body["candlesticks"][0]["yes_bid"] = {"close": "0.58"}; gzip.open(fp, "wt").write(json.dumps(body))
    try: f.run(T, [L], [C], hash_check=False); assert 0
    except SystemExit as e: assert "STOP" in str(e) and "KXFEDMENTION-25OCT-A1" in str(e)
# RAW decides: a strike at ask .87 counts at RAW but not at 1c (.88): RAW 15 not closed, 1c 14 fails the haircut on (a), could count: no
def one_at_87(o): o[0][4], o[0][5] = .85, .87
r = verdict(d2(one_at_87)); kk = r["kill_arm"]; assert kk["raw"]["count"] == 15 and kk["1c"]["count"] == 14 and r["VERDICT"].startswith("NOT CLOSED") and r["haircut"]["1c"] == "does not count: fails the haircut" and r["could_count_toward_20_to_30"] is False
# a haircut that fails on (b) alone (count still 15 or more but from fewer than 5 dates): three extra counted strikes in meeting 1, meeting 5's three strikes at ask .87
def b_only(o):
    for x in o[12:15]: x[4], x[5] = .85, .87          # meeting 5's counted strikes (rows 12 to 14: its K0 to K2)
    for j in range(3): o.append(["2025-01-29", "KXFEDMENTION-25JAN-E%d" % j, "yes", S, .48, .50, "yes"])
r = verdict(d2(b_only)); kk = r["kill_arm"]
assert kk["raw"]["count"] == 18 and kk["raw"]["meetings"] == 5 and kk["1c"]["count"] == 15 and kk["1c"]["meetings"] == 4 and kk["kill"]["1c"] == {"a": False, "b": True, "c": kk["kill"]["1c"]["c"]}, kk
assert r["VERDICT"].startswith("NOT CLOSED") and r["haircut"]["1c"] == "does not count: fails the haircut", (r["VERDICT"], r["haircut"])
# --- guards ---
with tempfile.TemporaryDirectory() as d:
    T, L, C = build(d, D1[:3] + [D1[0][:1] + ("KXFEDMENTION-25OCT-A1",) + D1[0][2:]])          # a table ticker repeated
    try: f.run(T, [L], [C], hash_check=False); assert 0
    except SystemExit as e: assert "repeated" in str(e) and "STOP" in str(e)
with tempfile.TemporaryDirectory() as d:
    T, L, C = build(d, D1[:5], lists_extra=[])
    # remove one market from the lists: rebuild the lists run without it
    import shutil; shutil.rmtree(L); os.makedirs(L)
    gzip.open(os.path.join(L, "0001.json.gz"), "wt").write(json.dumps({"markets": [{"ticker": s[1], "event_ticker": "KXFEDMENTION-25OCT", "result": s[6]} for s in D1[:4]]}))
    json.dump({"job": {}, "rows": [{"id": "l1", "page": 1, "status": 200, "file": "0001.json.gz"}], "status": "complete"}, open(os.path.join(L, "manifest.json"), "w"))
    try: f.run(T, [L], [C], hash_check=False); assert 0
    except SystemExit as e: assert "lists" in str(e) and "1" in str(e) and "STOP" in str(e)
with tempfile.TemporaryDirectory() as d:
    T, L, C = build(d, D1[:5], no_candle_answer=("KXFEDMENTION-25OCT-A2", "KXFEDMENTION-25OCT-A3"))
    try: f.run(T, [L], [C], hash_check=False); assert 0
    except SystemExit as e: assert "candle" in str(e) and "2" in str(e) and "STOP" in str(e)
with tempfile.TemporaryDirectory() as d:
    T, L, C = build(d, D1[:3]); C2 = os.path.join(d, "C2"); shutil_copy = __import__("shutil").copytree(C, C2)
    try: f.run(T, [L], [C, C2], hash_check=False); assert 0
    except SystemExit as e: assert "more than one candle answer" in str(e) and "STOP" in str(e)
# the candle shapes: a batched answer, a node with 'ticker', and the id fallback with the h_ prefix all parse; a candle at another minute is not used
with tempfile.TemporaryDirectory() as d:
    e = end_ts(A)
    C = os.path.join(d, "C"); os.makedirs(C); rr = []
    bodies = [("h_KXFEDMENTION-25OCT-X1", {"candlesticks": [{"end_period_ts": e, "yes_bid": {"close_dollars": "0.40"}, "yes_ask": {"close_dollars": "0.42"}}]}),
              ("b1", {"markets": [{"market_ticker": "KXFEDMENTION-25OCT-X2", "candlesticks": [{"end_period_ts": e, "yes_bid": {"close_dollars": "0.30"}, "yes_ask": {"close_dollars": "0.33"}}]}]}),
              ("h_other", {"ticker": "KXFEDMENTION-25OCT-X3", "candlesticks": [{"end_period_ts": e + 60, "yes_bid": {"close_dollars": "0.30"}, "yes_ask": {"close_dollars": "0.33"}}, {"end_period_ts": e, "yes_bid": {"close_dollars": "0.10"}, "yes_ask": {"close_dollars": "0.12"}}]})]
    for i, (rid, body) in enumerate(bodies):
        fn = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(C, fn), "wt").write(json.dumps(body)); rr.append({"id": rid, "page": 1, "status": 200, "file": fn})
    json.dump({"job": {}, "rows": rr, "status": "complete"}, open(os.path.join(C, "manifest.json"), "w"))
    got = f.read_candles([C], {"KXFEDMENTION-25OCT-X1", "KXFEDMENTION-25OCT-X2", "KXFEDMENTION-25OCT-X3"})
    assert f.quote(got["KXFEDMENTION-25OCT-X1"][e], "x") == (0.40, 0.42) and f.quote(got["KXFEDMENTION-25OCT-X2"][e], "x") == (0.30, 0.33) and f.quote(got["KXFEDMENTION-25OCT-X3"][e], "x") == (0.10, 0.12)
# the pure figure rules
assert f.two_sided(0.58, 0.60) and not f.two_sided(0.0, 0.3) and not f.two_sided(0.6, 1.0) and not f.two_sided(0.6, 0.6) and not f.two_sided(0.7, 0.6) and not f.two_sided(None, 0.5) and f.two_sided(0.01, 0.99)
assert f.counted("yes", 0.87, 0.0) and not f.counted("yes", 0.871, 0.0) and f.counted("yes", 0.86, 0.01) and not f.counted("yes", 0.86, 0.02) and not f.counted("no", 0.5, 0.0) and not f.counted("void", 0.5, 0.0) and f.counted("yes", 0.87 - 5e-10, 0.0) and not f.counted("yes", None, 0.0)
# the hash refusal and no-write
try: f.check_hashes({"scorekit.py": "0" * 16}); assert 0
except SystemExit as e: assert "audited" in str(e)
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fomctext_second.py")).read()
assert '"w"' not in src and "'w'" not in src and "write(" not in src.replace("sys.stdout.write", "")
print("test_fomctext_second: all checks passed")
