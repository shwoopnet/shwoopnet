import perpsf_second as m, engine1_perps_second as p
D = lambda y, mo, d, hh, mi: __import__("datetime").datetime(y, mo, d, hh, mi, tzinfo=__import__("datetime").timezone.utc).timestamp().__int__()
close = lambda a, b: abs(a - b) < 1e-6
# F3 hand case
s = {D(2026, 11, 19, 21, 0): (100.00, 100.10), D(2026, 11, 20, 14, 31): (100.60, 100.70), D(2026, 11, 20, 21, 0): (100.60, 100.70), D(2026, 11, 23, 14, 31): (100.90, 101.00)}
L19 = D(2026, 11, 19, 0, 0) // 86400; L20 = L19 + 1
fund = {D(2026, 11, 18, 21, 0): 1e-4, D(2026, 11, 19, 21, 0): 1e-4, D(2026, 11, 20, 21, 0): 1e-4, D(2026, 11, 21, 21, 0): 1e-4, D(2026, 11, 22, 21, 0): 1e-4}
tr, c = m.f3(s, [L19], "long", 0.0002, fund); t = tr[0]
assert close(t["gross"], 0.0045931) and t["funding"] == 0 and close(t["net_taker"], 0.0021931) and close(t["net_maker"], 0.0035931), t
tr, c = m.f3(s, [L19], "short", 0.0002, fund); assert close(tr[0]["gross"], -0.0074029) and close(tr[0]["net_taker"], -0.0098029)
tr, c = m.f3(s, [L20], "long", 0.0002, fund); t = tr[0]
assert close(t["gross"], 0.0015854) and close(t["funding"], 0.0002) and close(t["net_taker"], -0.0010146), t
assert m.f3(s, [L20], "short", 0.0002, fund)[0][0]["funding"] == -0.0002 or close(m.f3(s, [L20], "short", 0.0002, fund)[0][0]["funding"], -0.0002)
tr, c = m.f3(s, [L19], "long", 0.0002, None); assert c["funding_not_booked"] == 1 and tr[0]["funding"] is None and "net_taker" not in tr[0]
tr, c = m.f3(s, [L19 + 3], "long", 0.0002, fund); assert tr == [] and c["no_mark"] == 0          # Sunday is not a trading day
tr, c = m.f3({}, [L19], "long", 0.0002, fund); assert tr == [] and c["no_mark"] == 1
# F1 hand case
o = D(2026, 11, 17, 14, 30); prev = D(2026, 11, 16, 21, 0)
cd = {prev: (99.99, 100.01), o - 300: (99.995, 100.005), o + 60: (100.45, 100.55), o + 60 + 900: (100.80, 100.90)}
ev = dict(name="KXSPYPERP", day="2026-11-17", open_ts=o, prev16_ts=prev, u_open=101.0, u_prev=100.0, c=cd)
tr, c = m.f1([ev], "T15", 0.0002, {D(2026, 11, 16, 21, 0): 0.0}); t = tr[0]
assert c["triggered"] == 1 and close(t["gross"], 0.0020854) and close(t["net_taker"], -0.0003146), (t, c)
ev2 = dict(ev, u_open=100.0); assert m.f1([ev2], "T15", 0.0002)[1]["triggered"] == 0
assert m.exit_ts(o + 60, "TC") == D(2026, 11, 17, 21, 0) and m.exit_ts(D(2026, 11, 20, 14, 31), "TO") == D(2026, 11, 23, 14, 31) and m.exit_ts(o + 60, "T240") == o + 60 + 14400
# cooldown: a TO position from Tue blocks nothing at Wed 14:31 (>=); a T240 never blocks the next day; a second event inside the hold is blocked
o2 = o + 86400; cd2 = dict(cd); cd2.update({o2 - 300: (99.995, 100.005), o2 + 60: (100.45, 100.55), D(2026, 11, 16, 21, 0): (99.99, 100.01)}); cd2[D(2026, 11, 17, 21, 0)] = (99.99, 100.01)
cdx = dict(cd2); cdx[D(2026, 11, 18, 14, 31)] = (100.45, 100.55); cdx[D(2026, 11, 19, 14, 31)] = (100.50, 100.60)          # TO exit candles
ev3 = dict(ev, open_ts=o2, prev16_ts=D(2026, 11, 17, 21, 0), day="2026-11-18", c=cdx); ev1 = dict(ev, c=cdx)
tr, c = m.f1([ev1, ev3], "TO", 0.0002, None); assert c["triggered"] == 2 and c["blocked"] == 0 and len(tr) == 2, c
evb = dict(ev, open_ts=o + 600, prev16_ts=prev, c={**cdx, o + 660: (100.45, 100.55), o + 300: (99.995, 100.005)})
tr, c = m.f1([ev1, evb], "T15", 0.0002, None); assert c["blocked"] == 1 and len(tr) == 1, c
assert m.f3(s, [L19 + 2], "long", 0.0002, fund) == ([], {"no_mark": 0, "funding_not_booked": 0})          # Saturday is skipped too (no mark would otherwise be counted)
assert m.f1([dict(ev, u_open=100.07)], "T15", 0.0002)[1]["triggered"] == 0          # g 0.0007 is above 1x but under 2x the half spread fraction 0.000995
assert m.f1([dict(ev, u_open=100.11)], "T15", 0.0002)[1]["triggered"] == 1          # g 0.0011 is above 2x
print("perpsf second tests passed")
