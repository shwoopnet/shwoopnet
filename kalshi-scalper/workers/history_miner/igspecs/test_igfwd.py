"""python3 -I test_igfwd.py : hand case IGFWD_HAND_CASE_NOV16.md for ingame_fwd_load.py and ingame_events.py (invented)."""
import collections, csv, gzip, hashlib, io, json, os, sys, tempfile, calendar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingame_fwd_load as L, ingame_events as E
A = lambda x, y: abs(x - y) < 1e-9
assert A(E.fee(0.50), 0.18) and A(E.fee(0.54), 0.18) and A(E.fee(0.32), 0.16)


class Late(dict):
    def __init__(s, key, d):
        super().__init__(d); s.key = key
    def __getitem__(s, k):
        if k != s.key:
            raise AssertionError("touched %r outside the window" % k)
        return super().__getitem__(k)


cnt = collections.Counter()
assert L.obs_rows([Late("t_recv_ms", {"t_recv_ms": "1797292800000"})], cnt) == [] and L.obs_rows([Late("t_recv_ms", {"t_recv_ms": "1794873599000"})], cnt) == []
assert L.listing_markets([Late("close_time", {"close_time": "2026-12-15T00:00:00Z"})], cnt) == {}
assert L.obs_rows([{"t_recv_ms": "1794900000000", "ticker": "KXNBAGAME-X-A"}], cnt) == [] and cnt["row ticker outside the wall (dropped)"] == 1
assert L.DATES[0] == "2026-11-17" and L.DATES[-1] == "2026-12-14"
print("loader guards: ok")
OCC = "2026-11-20T03:00:00Z"; T = calendar.timegm((2026, 11, 20, 0, 0, 0))
mk = lambda rows, res, kind="total", lg="NHL", occ=OCC: {"key": "k", "league": lg, "kind": kind, "rows": rows, "result": res, "occ": {t: occ for t in rows}, "close": {}}
assert E.tip_of(mk({"T": []}, {})) == T and E.tip_of(mk({"T": []}, {}, occ="2026-11-20T03:15:00Z")) is None and E.tip_of(mk({"T": []}, {}, lg="NFL", occ="2026-11-20T03:15:00Z")) == T + 900
ev = mk({"T": [(T, 0.40, 0.42), (T + 30, 0.52, 0.54)]}, {"T": "no"})
w, d = E.fade2(ev); assert w == "ok" and d["side"] == "no" and A(d["ask"], 0.48) and A(E.cash(ev, d, 0.02), 4.82)
assert E.fade2(mk({"T": [(T, 0.40, 0.42), (T + 70, 0.52, 0.54)]}, {}))[0] == "no signal"
ev = mk({"T": [(T + 5300, 0.40, 0.42), (T + 7100, 0.50, 0.52)]}, {"T": "yes"})
w, d = E.latedrift(ev); assert w == "ok" and d["side"] == "yes" and A(d["ask"], 0.52) and A(E.cash(ev, d, 0.02), 4.42)
assert E.latedrift(mk({"T": [(T + 4900, 0.40, 0.42), (T + 7100, 0.50, 0.52)]}, {}))[0] == "no quote at a mark"
ev = mk({"A": [(T + 4400, 0.28, 0.30)], "B": [(T + 4400, 0.70, 0.72)]}, {"A": "yes", "B": "no"}, kind="ml")
w, d = E.dog(ev); assert w == "ok" and d["ticker"] == "A" and A(E.cash(ev, d, 0.02), 6.64)
assert E.dog(mk({"A": [(T + 4400, 0.28, 0.30)], "B": [(T + 4400, 0.20, 0.25)]}, {}, kind="ml"))[0] == "no single underdog"
assert E.dog(mk({"A": []}, {}, kind="ml", lg="NBA"))[0] == "not in wall" and E.latedrift(mk({"S": []}, {}, kind="spread"))[0] == "not in wall"
print("plugin: ok")
# end to end, loader to plugin, with a listing RUN folder (Auditor B's note 4)
tmp = tempfile.mkdtemp(); lst = os.path.join(tmp, "lst"); run = os.path.join(lst, "run1"); os.makedirs(run)
job = {"job_id": "X", "requests": [{"id": "settled_KXNHLTOTAL"}]}
jf = os.path.join(tmp, "job.json"); open(jf, "w").write(json.dumps(job)); L.JOB_FILE = jf; L.JOB_SHA256 = hashlib.sha256(open(jf, "rb").read()).hexdigest()
page = {"markets": [{"close_time": "2026-11-20T06:00:00Z", "ticker": "KXNHLTOTAL-26NOV19AB-5", "result": "no", "occurrence_datetime": OCC}], "cursor": ""}
body = json.dumps(page).encode(); open(os.path.join(run, "0001.json.gz"), "wb").write(gzip.compress(body))
man = {"job": job, "rows": [{"id": "settled_KXNHLTOTAL", "page": 1, "status": 200, "truncated": False, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(), "file": "0001.json.gz"}]}
json.dump(man, open(os.path.join(run, "manifest.json"), "w")); open(os.path.join(run, "STATUS"), "w").write("complete")
d = os.path.join(tmp, "ig", "2026-11-20", "0000"); os.makedirs(d)
b = io.StringIO(); w = csv.writer(b); w.writerow(["t_recv_ms", "server_date", "event", "kind", "ticker", "strike", "yes_bid", "yes_ask", "bid_size", "ask_size", "last_price", "volume"])
for t, bb, aa in ((T, 0.40, 0.42), (T + 30, 0.52, 0.54)):
    w.writerow([t * 1000, "d", "KXNHLTOTAL-26NOV19AB", "total", "KXNHLTOTAL-26NOV19AB-5", 5, bb, aa, 1, 1, 0.5, 1])
gzip.open(os.path.join(d, "obs.csv.gz"), "wt").write(b.getvalue())
allow = os.path.join(tmp, "A.md"); L.ALLOW_FILE = allow; open(allow, "w").write("%s ingame_fwd_load.py %s\n" % (L.ALLOW_MARK, L.self_sha()))
try:
    L.load(os.path.join(tmp, "ig"), lst); assert False
except SystemExit as e:
    assert "REFUSED" in str(e)
open(allow, "w").write("%s ingame_fwd_load.py %s %s\n" % (L.ALLOW_MARK, L.self_sha(), L.JOB_SHA256))
def refused(msg):
    try:
        L.load(os.path.join(tmp, "ig"), lst); assert False, msg
    except SystemExit as e:
        assert msg in str(e), (msg, str(e))
evs, c = L.load(os.path.join(tmp, "ig"), lst)
assert len(evs) == 1 and evs[0]["league"] == "NHL" and evs[0]["kind"] == "total"
r = E.run(evs, "IGFADE2"); assert r["h2"]["n"] == 1 and A(r["h2"]["net"], 4.82) and r["h2"]["evidence"] == "no evidence at n = 1" and r["kill_fast"] is False
assert r["pairs_le60_by_day"] == {"2026-11-20": 1} and r["entries_within_120s_of_close"]["n"] == 0
r0 = E.run([{"key": "k", "league": "NHL", "kind": "total", "rows": {"T": [(T, 0.4, 0.42), (T + 120, 0.5, 0.52)]}, "result": {"T": "no"}, "occ": {"T": OCC}, "close": {"T": T + 200}}], "IGFADE2")
assert r0["cadence"].startswith("no signal: cadence") and r0["pairs_le60_by_day"] == {}
evl = [{"key": "k", "league": "NHL", "kind": "total", "rows": {"T": [(T, 0.40, 0.42), (T + 30, 0.52, 0.54)]}, "result": {"T": "no"}, "occ": {"T": OCC}, "close": {"T": T + 100}}]
assert E.run(evl, "IGFADE2")["entries_within_120s_of_close"]["n"] == 1
assert c["listing runs accepted"] == 1
# structure failures refuse the run
import shutil
for what, edit, msg in (("status", lambda: open(os.path.join(run, "STATUS"), "w").write("running"), "STATUS is not complete"),):
    edit(); refused(msg); open(os.path.join(run, "STATUS"), "w").write("complete")
m2 = json.load(open(os.path.join(run, "manifest.json"))); m2["job"]["job_id"] = "Y"; json.dump(m2, open(os.path.join(run, "manifest.json"), "w")); refused("embedded job differs"); json.dump(man, open(os.path.join(run, "manifest.json"), "w"))
open(os.path.join(run, "0001.json.gz"), "wb").write(gzip.compress(body + b" ")); refused("fails the manifest check"); open(os.path.join(run, "0001.json.gz"), "wb").write(gzip.compress(body))
open(os.path.join(run, "extra.txt"), "w").write("x"); refused("files differ from the manifest"); os.remove(os.path.join(run, "extra.txt"))
cur = dict(page, cursor="next"); body2 = json.dumps(cur).encode(); open(os.path.join(run, "0001.json.gz"), "wb").write(gzip.compress(body2))
m3 = json.loads(json.dumps(man)); m3["rows"][0]["bytes"] = len(body2); m3["rows"][0]["sha256"] = hashlib.sha256(body2).hexdigest(); json.dump(m3, open(os.path.join(run, "manifest.json"), "w")); refused("cursor on its last page")
print("end to end: ok")
