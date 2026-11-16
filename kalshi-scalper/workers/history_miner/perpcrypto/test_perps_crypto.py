"""python3 -I test_perps_crypto.py : the loader walls and the plugin hand cases of PERPCRYPTO1 (invented rows; Auditor B's list of 20:48Z)."""
import calendar, collections, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perps_crypto_load as L, perps_crypto_events as E
A = lambda x, y: abs(x - y) < 1e-9
T = lambda *a: calendar.timegm(a + (0,) * (6 - len(a)))


class Strict(dict):
    """only the keys in `ok` may be read"""
    def __init__(s, ok, d):
        super().__init__(d); s.ok = ok
    def __getitem__(s, k):
        if k not in s.ok:
            raise AssertionError("touched %r" % k)
        return super().__getitem__(k)


snap = lambda ts, tk, ok=L.SNAP_COLS, **kw: Strict(ok, dict({"ts_utc": ts, "ticker": tk, "bid": "99.9", "ask": "100.1", "price": "100.0", "reference_price": "100.0", "funding_cap": "0.02", "status": "active", "bid_size": "1", "ask_size": "1",
    "settlement_mark": "1", "liquidation_mark": "1", "open_interest": "1", "volume_24h": "1", "notional_oi_usd": "1", "funding_deadband": "0.0001"}, **kw))
cnt = collections.Counter()
# snapshot wall: time first (an out-of-window row may only be asked for its time), then the ticker wall, then only the named columns
assert L.snapshot_rows([snap("2026-11-17T00:00:00Z", "KXBTCPERP", ok=("ts_utc",)), snap("2026-10-20T23:00:00Z", "KXBTCPERP", ok=("ts_utc",))], cnt) == {} and cnt["snapshot row outside the window (dropped)"] == 2
assert L.snapshot_rows([snap("2026-11-01T00:00:00Z", "KXAAPLPERP", ok=("ts_utc", "ticker"))], cnt) == {} and cnt["snapshot ticker outside the wall (dropped)"] == 1
r = L.snapshot_rows([snap("2026-11-01T00:00:00Z", "KXBTCPERP", reference_price=None)], cnt); assert r["KXBTCPERP"][0][4] is None        # a missing reference is kept for the plugin to skip
print("snapshot wall: ok")
# the 1 minute candle wall: end_period_ts first, KXBTCPERP, only bid.close and ask.close, the top of the hour only
cnd = lambda t: Strict(("end_period_ts", "bid", "ask"), {"end_period_ts": t, "bid": Strict(("close",), {"close": "99.9", "high": "1"}), "ask": Strict(("close",), {"close": "100.1", "high": "1"}), "price": 1, "volume": 1, "open_interest": 1})
rows = L.btc_candle_rows([Strict(("end_period_ts",), {"end_period_ts": T(2026, 11, 17)}), cnd(T(2026, 11, 1, 10)), cnd(T(2026, 11, 1, 10, 1))], cnt)
assert rows == [(T(2026, 11, 1, 10), 99.9, 100.1, None, None, None)] and cnt["btc candle not at the top of an hour (not used)"] == 1 and cnt["btc candle outside the window (dropped)"] == 1
print("btc candle wall: ok")
# Coinbase wall: product, then start time (index 0), then only the close (index 4)
class Arr(list):
    def __init__(s, ok, v):
        super().__init__(v); s.ok = ok
    def __getitem__(s, i):
        if i not in s.ok:
            raise AssertionError("touched index %r" % i)
        return super().__getitem__(i)
sp = L.spot_rows([Arr((0,), [T(2026, 11, 17), 1, 2, 3, 4, 5]), Arr((0, 4), [T(2026, 11, 1, 9), 1, 2, 3, 100.0, 5])], "BTC-USD", cnt)
assert sp == {T(2026, 11, 1, 9): 100.0} and L.spot_rows([Arr((), [0])], "HYPE-USD", cnt) == {}
assert L.spot_at(sp, T(2026, 11, 1, 10)) == 100.0 and L.spot_at(sp, T(2026, 11, 1, 10, 0, 30)) == 100.0 and L.spot_at(sp, T(2026, 11, 1, 9)) is None     # the candle starting at 09:00 closes at 10:00: never used before 10:00
print("spot wall and alignment: ok")
# funding: a blank ticker refuses the whole file
try:
    L.funding_rows([{"ticker": "KXBTCPERP", "funding_time": "2026-11-01T00:00:00Z", "funding_rate": "0.0001"}, {"ticker": "", "funding_time": "2026-11-01T01:00:00Z", "funding_rate": "0.0002"}], cnt); assert False
except SystemExit as e:
    assert "blank ticker" in str(e)
assert L.funding_rows([{"ticker": "KXBTCPERP", "funding_time": "2026-11-01T00:00:00Z", "funding_rate": "0.0001"}], cnt) == {"KXBTCPERP": [(T(2026, 11, 1), 0.0001)]}
print("funding refusal: ok")
# BASIS hand case: next-row entry
H = 3600; t0 = T(2026, 11, 1)
def row(i, bid, ask, price, ref): return (t0 + i * H, bid, ask, price, ref, 0.02)
rows = [row(0, 99.9, 100.1, 100.0, 100.0), row(1, 100.1, 100.3, 100.2, 100.0), row(2, 100.1, 100.3, 100.2, 100.2), row(3, 99.0, 99.2, 99.1, 99.1)]
tr = E.basis_trades({"KXBTCPERP": rows}, (10, "converge", 1))
assert len(tr) == 1 and tr[0]["signal_ts"] == t0 + H and tr[0]["trade"]["entry_ts"] == t0 + 2 * H and tr[0]["trade"]["side"] == -1
t = tr[0]["trade"]; assert A(t["entry"], 100.1) and A(t["exit"], 99.2) and A(t["adverse"], (100.3 - 100.1) / 100.1)       # entry is the NEXT row's far touch (the bid of a sell), not the signal row's
assert A(E.net(t, E.FEE_TAKER, 0.0002), (100.1 - 99.2) / 100.1 - 0.0024 - 0.0004)
f = E.basis_trades({"KXBTCPERP": rows}, (10, "follow", 1)); assert f[0]["trade"]["side"] == 1 and A(f[0]["trade"]["entry"], 100.3)                                       # follow buys the next row's ask
assert E.basis_trades({"KXBTCPERP": rows}, (5, "converge", 1))[0]["signal_ts"] == t0 + H and E.basis_trades({"KXBTCPERP": [row(0, 99.9, 100.1, 100.0, 100.0), row(1, 99.9, 100.1, 100.04, 100.0), row(2, 99.9, 100.1, 100.0, 100.0)]}, (5, "converge", 1)) == []
print("basis hand case: ok")
# reference_price None: skipped and counted, no trade
sk = collections.Counter(); r2 = [row(0, 99.9, 100.1, 100.0, None), row(1, 99.9, 100.1, 100.0, None), row(2, 99.9, 100.1, 100.0, None)]
assert E.basis_trades({"KXBTCPERP": r2}, (5, "converge", 1), sk) == [] and sk["price or reference_price missing"] == 2
# liquidation: an adverse spike of 8.9 percent liquidates at 50 percent of max (8.5 percent to liquidation) but not at 25 or 10 percent
spike = [row(0, 99.9, 100.1, 100.0, 100.0), row(1, 100.1, 100.3, 100.2, 100.0), row(2, 100.1, 100.3, 100.2, 100.2), row(3, 108.0, 109.0, 108.5, 108.5), row(4, 99.0, 99.2, 99.1, 99.1)]
ts = E.basis_trades({"KXBTCPERP": spike}, (10, "converge", 2))[0]; assert A(ts["trade"]["adverse"], (109.0 - 100.1) / 100.1)
ret = E.net(ts["trade"], E.FEE_TAKER, 0.0002)
assert E.margin_return(ts["trade"], "KXBTCPERP", 0.50, ret) == (-1.0, True) and E.margin_return(ts["trade"], "KXBTCPERP", 0.25, ret)[1] is False and E.margin_return(ts["trade"], "KXBTCPERP", 0.10, ret)[1] is False
d, lev = E.liquidation_distance("KXBTCPERP", 0.5); assert A(lev, 7.7) and A(d, 1 / 7.7 - 0.045)
print("None reference and liquidation: ok")
# funding extremes: own earlier prints only, at least 60, nearest rank; clamp at the cap
ear = [i * 1e-4 for i in range(1, 101)]
assert E.funding_extreme(ear, 95e-4, 0.02, "decile") == 1 and E.funding_extreme(ear, 2e-4, 0.02, "decile") == 0 and E.funding_extreme(ear, 50e-4, 0.02, "decile") == 0
assert E.funding_extreme([-x for x in ear], -95e-4, 0.02, "decile") == -1 and E.funding_extreme(ear[:59], 95e-4, 0.02, "decile") == 0
assert E.funding_extreme([], 0.02, 0.02, "clamp") == 1 and E.funding_extreme([], -0.02, 0.02, "clamp") == -1 and E.funding_extreme([], 0.0199, 0.02, "clamp") == 0
try:
    E.fundx_trades({"KXBTCPERP": rows}, {}, ("clamp", "fade", 8)); assert False
except SystemExit as e:
    assert "no labelled funding" in str(e)
print("funding extremes: ok")
# FUNDX on labelled prints: a clamp print at row 1's time, fade the longs: short; row 1 is the signal row and the ENTRY is row 2's bid (a quote at the print instant is never used)
fr = [row(i, 100.0 - 0.01 * i, 100.2 - 0.01 * i, 100.1, 100.1) for i in range(12)]
fx = E.fundx_trades({"KXBTCPERP": fr}, {"KXBTCPERP": [(t0 + H, 0.02)]}, ("clamp", "fade", 8))
assert len(fx) == 1 and fx[0]["trade"]["side"] == -1 and fx[0]["trade"]["entry_ts"] == t0 + 2 * H and A(fx[0]["funding"], 0.0)
fx2 = E.fundx_trades({"KXBTCPERP": fr}, {"KXBTCPERP": [(t0 + H, 0.02), (t0 + 3 * H, 0.0003)]}, ("clamp", "fade", 8)); assert A(fx2[0]["funding"], 0.0003)    # a later print inside the hold is booked
print("fundx: ok")
# the gate: fixed on the first 7 days
mk = lambda day_i, k: [{"signal_ts": T(2026, 11, 1 + day_i), "trade": None} for _ in range(k)]
tb = {"c": sum((mk(d, 4) for d in range(7)), []) + mk(7, 0), "d": sum((mk(d, 2) for d in range(7)), []) + mk(7, 30)}
assert E.gate({"c": mk(0, 5)}) is None
g = E.gate({"c": sum((mk(d, 4) for d in range(7)), []) + mk(7, 1), "d": sum((mk(d, 2) for d in range(7)), []) + mk(7, 30)})
assert A(g["c"]["rate"], 4.0) and not g["c"]["dropped"] and A(g["d"]["rate"], 2.0) and g["d"]["dropped"]
print("gate: ok")

# proxy rows are printed apart from the snapshot rows and never pooled (Auditor B, 20:52Z)
a = E.basis_trades({"KXBTCPERP": rows}, (10, "converge", 1)); rp = E.report(a, [])
assert rp["snapshot_rows"]["n"] == 1 and rp["proxy_rows"]["n"] == 0 and "not the basis against Kalshi's reference_price" in rp["proxy_rows"]["note"] and "not a pass" in rp["rule"]
rp2 = E.report(a, a + a); assert rp2["snapshot_rows"]["n"] == 1 and rp2["proxy_rows"]["n"] == 2
print("proxy rows apart: ok")
