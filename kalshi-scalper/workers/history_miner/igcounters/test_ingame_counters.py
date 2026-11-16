"""python3 -I test_ingame_counters.py : hand case IGCOUNTERS_HAND_CASE_NOV16.md, invented rows."""
import calendar, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingame_counters as C
H = calendar.timegm((2026, 11, 17, 5, 0, 0))
mk = lambda t, tk="A": [str(int((H + t) * 1000)), "d", "ev", "total", tk]
rows = [mk(0), mk(20), mk(140), mk(160), mk(3610)]
c = C.cadence_rows(rows)
assert c == {"2026-11-17 05": [3, 2, 2], "2026-11-17 06": [1, 0, 0]}, c
class OnlyTwo(list):
    def __getitem__(s, i):
        if i not in (0, 4):
            raise AssertionError("touched column %r" % i)
        return super().__getitem__(i)
assert C.cadence_rows([OnlyTwo(["1000", "x", "y", "z", "A"]), OnlyTwo(["11000", "x", "y", "z", "A"])]) == {"1970-01-01 00": [1, 1, 1]}
print("cadence: ok")
D = calendar.timegm((2026, 11, 20, 0, 0, 0))
def dr(t, tk, b, a, event="KXNHLTOTAL-26NOV19AB", kind="total"):
    return {"t_recv_ms": str(int(t * 1000)), "ticker": tk, "event": event, "kind": kind, "yes_bid": str(b), "yes_ask": str(a)}
ev = C.signal_rows([dr(D, "KXNHLTOTAL-26NOV19AB-5", 0.40, 0.42), dr(D + 30, "KXNHLTOTAL-26NOV19AB-5", 0.52, 0.54)])
r = C.fade2_counts(ev); assert r["decisions"] == 1 and r["by_day"] == {"2026-11-20": {"NHL_total": 1}} and "provisional" in r["label"]
assert C.fade2_counts(C.signal_rows([dr(D, "KXNHLTOTAL-26NOV19AB-5", 0.40, 0.42), dr(D + 70, "KXNHLTOTAL-26NOV19AB-5", 0.52, 0.54)]))["decisions"] == 0
assert C.fade2_counts(C.signal_rows([dr(D, "KXNHLTOTAL-26NOV19AB-5", 0.40, 0.42), dr(D + 30, "KXNHLTOTAL-26NOV19AB-5", 0.48, 0.50)]))["decisions"] == 0
late = C.Walled({"t_recv_ms": "1794873599000"}); assert C.signal_rows([late]) == {}
assert C.signal_rows([C.Walled({"t_recv_ms": "1797292800000"})]) == {} and C.signal_rows([dr(D, "KXNBAGAME-X-A", 0.4, 0.42)]) == {}
print("fade2: ok")
Tp = calendar.timegm((2026, 11, 20, 0, 0, 0))
e = {"key": "k", "league": "NHL", "kind": "total", "rows": {"T": [(Tp + 5300, 0.40, 0.42), (Tp + 7100, 0.50, 0.52)]}, "result": {}, "close": {}, "occ": {"T": "2026-11-20T03:00:00Z"}}
assert C.latedrift_counts([e])["by_day"] == {"2026-11-20": 1} and C.latedrift_counts([dict(e, kind="spread")])["by_day"] == {}
print("latedrift: ok")
