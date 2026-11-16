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
# end to end, loader to plugin
tmp = tempfile.mkdtemp(); lst = os.path.join(tmp, "lst"); os.makedirs(lst)
page = {"markets": [{"close_time": "2026-11-20T06:00:00Z", "ticker": "KXNHLTOTAL-26NOV19AB-5", "result": "no", "occurrence_datetime": OCC}]}
raw = gzip.compress(json.dumps(page).encode()); open(os.path.join(lst, "p.json.gz"), "wb").write(raw)
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
open(allow, "w").write("%s ingame_fwd_load.py %s %s\n" % (L.ALLOW_MARK, L.self_sha(), hashlib.sha256(raw).hexdigest()))
evs, c = L.load(os.path.join(tmp, "ig"), lst)
assert len(evs) == 1 and evs[0]["league"] == "NHL" and evs[0]["kind"] == "total"
r = E.run(evs, "IGFADE2"); assert r["h2"]["n"] == 1 and A(r["h2"]["net"], 4.82) and r["h2"]["evidence"] == "no evidence at n = 1" and r["kill_fast"] is False
print("end to end: ok")
