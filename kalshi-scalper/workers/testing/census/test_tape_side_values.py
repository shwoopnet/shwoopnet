import gzip, json, os, shutil, sys, tempfile, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tape_side_values as S
def sha(b): return hashlib.sha256(b).hexdigest()
d = tempfile.mkdtemp(); os.makedirs(d + "/tape")
HDR = "t_recv_ms,server_date_header,ticker,created_time,price,count,taker_side,is_block_trade\n"
def wr(day, rows):
    with gzip.open(d + "/tape/%s.csv.gz" % day, "wt") as f: f.write(HDR + "".join(r + "\n" for r in rows))
wr("2026-09-18", ["1,x,KXA,2026-09-18T00:00:01Z,7777.7,1,bid,false", "1,x,KXA,2026-09-18T00:00:02Z,7777.7,1,ask,false", "1,x,KXOTHER,2026-09-18T00:00:02Z,7777.7,1,weird,false", "1,x,KXA,2026-09-18T00:00:03Z,7777.7,1,Bid,false"])
wr("2026-09-19", ["1,x,KXHELD,2026-09-19T00:00:01Z,7777.7,1,buy,false", "1,x,KXA,2026-09-19T00:00:01Z,7777.7,1,ask,true"])
wr("2026-11-16", ["1,x,KXA,2026-11-16T00:00:01Z,1,1,SECRET,false"])
open(d + "/tickers.txt", "w").write("KXA\nKXHELD\n")
holds = {"version": "t", "forward_default_deny_from": 1794787200, "rows": [{"id": "T1", "status": "OPEN", "tickers": ["KXHELD*"], "from": 0, "to": None}]}
open(d + "/holds.json", "w").write(json.dumps(holds)); hs = sha(open(d + "/holds.json", "rb").read()); ts = sha(open(d + "/tickers.txt", "rb").read())
paths = [d + "/tape/2026-09-18.csv.gz", d + "/tape/2026-09-19.csv.gz"]
man = sorted((os.path.relpath(p, d), sha(open(p, "rb").read())) for p in paths); ms = sha(repr(man).encode()); me = sha(open(S.__file__, "rb").read())
def allow(ok=True, **kw):
    v = dict(me=me, ms=ms, hs=hs, ts=ts, a="2026-09-18", b="2026-09-19"); v.update(kw)
    open(d + "/allow.md", "w").write("x\n" + (S.MARK if ok else "other") + " tape_side_values.py %(me)s %(ms)s %(hs)s %(ts)s %(a)s %(b)s\n" % v)
call = lambda a="2026-09-18", b="2026-09-19": S.run(d, d + "/tickers.txt", a, b, d + "/allow.md", d + "/holds.json", hs)
allow(); out = json.loads(call())
assert out["all"]["bid"] == 1 and out["all"]["ask"] == 2 and out["all"]["other_distinct"] == 1 and out["all"]["other_rows"] == 1 and out["all"]["other_first_12_cut_16"] == [["'Bid'", 1]] and out["all"]["other_truncated"] is False, out["all"]
assert out["rows_other_tickers_not_read"] == 1 and out["rows_held_not_read"] == 1 and out["only_bid_and_ask"] is False and "7777" not in json.dumps(out)
for bad in (dict(me="0" * 64), dict(ms="0" * 64), dict(hs="0" * 64), dict(a="2026-09-17"), dict(b="2026-09-20"), dict(ts="0" * 64)):
    allow(**bad)
    try: call(); raise AssertionError("allowed " + str(bad))
    except SystemExit: pass
allow(False)
try: call(); raise AssertionError("no mark")
except SystemExit: pass
allow()
open(d + "/tickers2.txt", "w").write("KXA\nKXOTHER\nKXHELD\n")
try: S.run(d, d + "/tickers2.txt", "2026-09-18", "2026-09-19", d + "/allow.md", d + "/holds.json", hs); raise AssertionError("another ticker list was accepted")
except SystemExit: pass
for a, b in (("2026-09-18Z", "2026-09-19"),):
    try: call(a, b); raise AssertionError("date format")
    except SystemExit: pass
# a long free text value is cut to 16 characters and flagged
wr("2026-09-20", ["1,x,KXA,2026-09-20T00:00:01Z,1,1," + "9" * 200 + ",false"])
paths2 = paths + [d + "/tape/2026-09-20.csv.gz"]; man2 = sorted((os.path.relpath(p, d), sha(open(p, "rb").read())) for p in paths2); ms2 = sha(repr(man2).encode())
allow(ms=ms2, b="2026-09-20"); o2 = json.loads(call("2026-09-18", "2026-09-20")); big = o2["all"]["other_first_12_cut_16"]
assert all(len(k) <= 18 for k, _ in big) and o2["all"]["other_truncated"] is True and "9" * 40 not in json.dumps(o2), o2["all"]
allow()
for a, b in (("2026-11-16", "2026-11-16"), ("2026-10-27", "2026-10-28"), ("2026-09-17", "2026-09-18")):
    try: call(a, b); raise AssertionError("range " + a)
    except SystemExit: pass
try: S.load_holds(d + "/holds.json", "0" * 64); raise AssertionError("holds sha")
except SystemExit: pass
print("tape_side_values: ok")
