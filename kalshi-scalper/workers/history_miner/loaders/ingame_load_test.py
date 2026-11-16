"""python3 -I ingame_load_test.py : the wall on invented files; rows and markets outside the window raise on any column but the time."""
import collections, csv, gzip, hashlib, io, json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingame_load as L


class Late(dict):
    def __init__(s, key, d):
        super().__init__(d); s.key = key
    def __getitem__(s, k):
        if k != s.key:
            raise AssertionError("touched column %r of a row outside the window" % k)
        return super().__getitem__(k)


cnt = collections.Counter()
assert L.obs_rows([Late("t_recv_ms", {"t_recv_ms": "1794528000000", "ticker": "KXNHLTOTAL-A"})], cnt) == [] and cnt["row outside the window (dropped)"] == 1
assert L.obs_rows([{"t_recv_ms": "t_recv_ms"}], cnt) == []
base = {"event": "KXNHLTOTAL-26NOV10AB", "kind": "total", "yes_bid": "0.4", "yes_ask": "0.42", "last_price": "0.41", "volume": "10", "bid_size": "5", "ask_size": "6"}
assert L.obs_rows([dict(base, t_recv_ms="1794200000000", ticker="KXNBAGAME-X-A")], cnt) == [] and cnt["row ticker outside the wall (dropped)"] == 1
assert L.listing_markets([Late("close_time", {"close_time": "2026-11-13T00:00:00Z", "ticker": "KXNHLTOTAL-B", "result": "no"})], cnt) == {}
assert L.listing_markets([Late("close_time", {"close_time": "2026-11-07T23:59:59Z", "ticker": "KXNHLTOTAL-B"})], cnt) == {} and cnt["market outside the window (dropped)"] == 2
print("guards: ok")

tmp = tempfile.mkdtemp(); lst = os.path.join(tmp, "lst"); os.makedirs(lst)
page = {"markets": [{"close_time": "2026-11-10T09:46:40Z", "ticker": "KXNHLTOTAL-26NOV10AB-5", "result": "no"},
                    {"close_time": "2026-11-10T09:46:40Z", "ticker": "KXNBAGAME-X-A", "result": "yes"}]}
raw = gzip.compress(json.dumps(page).encode()); open(os.path.join(lst, "P_0001.json.gz"), "wb").write(raw)
d = os.path.join(tmp, "ig", "2026-11-10", "0000"); os.makedirs(d)
hdr = ["t_recv_ms", "server_date", "event", "kind", "ticker", "strike", "yes_bid", "yes_ask", "bid_size", "ask_size", "last_price", "volume"]
b = io.StringIO(); w = csv.writer(b); w.writerow(hdr)
for t in (1794300000000, 1794320000000):
    w.writerow([t, "d", "KXNHLTOTAL-26NOV10AB", "total", "KXNHLTOTAL-26NOV10AB-5", "5", 0.4, 0.42, 5, 6, 0.41, 10])
w.writerow(hdr); w.writerow([1794300000000, "d", "KXNBAGAME-X", "ml", "KXNBAGAME-X-A", "", 0.5, 0.52, 1, 1, 0.5, 1])
gzip.open(os.path.join(d, "obs.csv.gz"), "wt").write(b.getvalue())
late = os.path.join(tmp, "ig", "2026-11-13", "0000"); os.makedirs(late); open(os.path.join(late, "obs.csv.gz"), "wb").write(b"not gzip")
allow = os.path.join(tmp, "A.md"); L.ALLOW_FILE = allow; open(allow, "w").write("x\n")
try:
    L.load(os.path.join(tmp, "ig"), lst); assert False
except SystemExit as e:
    assert "REFUSED" in str(e)
L.LISTING_SHA = {hashlib.sha256(raw).hexdigest()}
open(allow, "w").write("%s ingame_load.py %s %s\n" % (L.ALLOW_MARK, L.self_sha(), hashlib.sha256(raw).hexdigest()))
m, c, k = L.load(os.path.join(tmp, "ig"), lst)
assert m == [("KXNHLTOTAL-26NOV10AB-5", "KXNHLTOTAL", 1794304000, "no")], m
assert c["KXNHLTOTAL-26NOV10AB-5"] == [(1794300000, 0.4, 0.42, 0.41, 10.0, None, 5.0, 6.0, "total", "KXNHLTOTAL-26NOV10AB")], c
assert k["candle after close (dropped)"] == 1 and k["row ticker outside the wall (dropped)"] == 1 and k["market ticker outside the wall (dropped)"] == 1, k
open(os.path.join(lst, "Q_0002.json.gz"), "wb").write(b"other")
try:
    L.load(os.path.join(tmp, "ig"), lst); assert False
except SystemExit as e:
    assert "not one of the five" in str(e)
print("end to end: ok")
