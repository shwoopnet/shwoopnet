import calendar
import ladhour1_second as m, ethlate1_second as e
T = lambda *a: calendar.timegm(a)
assert m.M_NEW == 384 and m.m_total(6290660) == 6291044 and m.SERIES == ("KXINXU", "KXNASDAQ100U", "KXWTIH", "KXGOLDH")
assert m.in_series("KXINXU-26NOV17H15-T5800", "KXINXU") and not m.in_series("KXINXUD-26NOV17-T1", "KXINXU") and m.in_series("KXNASDAQ100U-X-T1", "KXNASDAQ100U") and not m.in_series("KXNASDAQ100-X-T1", "KXNASDAQ100U") and not m.in_series("KXWTIHX-1", "KXWTIH")
close = T(2026, 11, 20, 15, 0, 0)
mk = {"KXINXU-A-T1": {"close_ts": close, "result": "yes"}, "KXWTIH-A-T1": {"close_ts": close, "result": "yes"}, "KXOTHER-A-T1": {"close_ts": close, "result": "yes"}}
cd = {t: {close - 120: (0.08, 0.12), close - 60: (0.20, 0.22)} for t in mk}
sp = m.split_by_series(mk, cd); assert sorted(sp["KXINXU"][0]) == ["KXINXU-A-T1"] and sorted(sp["KXWTIH"][0]) == ["KXWTIH-A-T1"] and sp["KXGOLDH"][0] == {} and sp["KXNASDAQ100U"][0] == {} and "KXOTHER-A-T1" not in sum((list(v[0]) for v in sp.values()), [])
res = m.run(mk, cd, 6290660); assert set(res) == set(m.SERIES) and all(r["m"] == 6291044 for r in res.values()) and res["KXINXU"]["entries"] == 1 and res["KXGOLDH"]["entries"] == 0
# per series spread cuts and splits: series A has spreads (cents) 1..9 in SEARCH, series B 1, 2, 3
def world(prefix, spreads, d0):
    mkts, cds = {}, {}
    for i, s in enumerate(spreads):
        c = T(2026, 11, 20, 15, 0, 0) + (d0 + i) * 86400; tk = "%s-E%d-T1" % (prefix, i); mkts[tk] = {"close_ts": c, "result": "yes"}
        bid = 0.10; cds[tk] = {c - 120: (bid, round(bid + s / 100, 4)), c - 60: (0.2, 0.22)}
    return mkts, cds
ma, ca = world("KXINXU", [1, 1, 2, 2, 3, 3, 4, 5, 9, 1], 0); mb, cb = world("KXWTIH", [3, 4, 5, 6], 0)
r = m.run({**ma, **mb}, {**ca, **cb}, 0); ra = e.run(ma, ca, 384); rb = e.run(mb, cb, 384)
assert r["KXINXU"]["cuts"] == ra["cuts"] and r["KXWTIH"]["cuts"] == rb["cuts"] and r["KXINXU"]["cuts"] != r["KXWTIH"]["cuts"] and r["KXINXU"]["last_search_day"] != r["KXWTIH"]["last_search_day"]
assert r["KXINXU"]["rules"] == ra["rules"] and r["KXWTIH"]["rules"] == rb["rules"] and r["KXINXU"]["m"] == 384
print("ladhour1 second tests passed")
