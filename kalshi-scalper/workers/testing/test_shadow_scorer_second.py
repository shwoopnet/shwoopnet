import shadow_scorer_second as m
T0 = 1_000_000
def sg(i, side, price, result, **o):
    d = dict(spec="T1", ticker="K-%d" % i, side=side, price=price, ts=T0 + i * 1000, fill_checked=True, result=result); d.update(o); return d
rows = [sg(1, "yes", 0.10, "yes"), sg(2, "yes", 0.10, "no"), sg(3, "no", 0.50, "no")]
r = m.score("T1", rows, T0, T0 + 10**6)
assert (r["signals"], r["settled"], r["wins"], r["losses"]) == (3, 3, 2, 1)
assert r["slip"]["cash"]["net"] == 1.268 and r["slip"]["cash"]["pf"] == 12.85
assert r["slip"]["+1c"]["net"] == 1.238
assert r["slip"]["+2c"]["net"] < r["slip"]["+1c"]["net"] < r["slip"]["cash"]["net"]
F = m.F
assert m.fee(F("0.1")) == F(7, 1000) and m.fee(F("0.5")) == F(18, 1000) and m.fee(F("0.2")) == F(12, 1000) and m.fee(F("0.11")) == F(7, 1000) and m.fee(F("0.51")) == F(18, 1000)
assert m.fee(F("0.99")) == F(1, 1000) and m.fee(F(1)) is None and m.fee(F(0)) is None
assert m.pnl(0.985, "yes", "yes", 2) == F(9, 1000) and m.pnl(0.985, "yes", "no", 2) == F(-991, 1000)
w = m.score("T1", [sg(1, "yes", 0.10, "yes")], T0, T0 + 10**6)["slip"]["cash"]; assert (w["pf"], w["no_losses"]) == (None, True)
e = m.score("T1", [], T0, T0 + 10**6)["slip"]["cash"]; assert (e["net"], e["pf"], e["no_losses"]) == (0, None, False)
rows = [sg(1, "yes", .1, "yes"), sg(1, "yes", .1, "yes", ts=T0 + 5000), sg(2, "yes", .1, "no", fill_checked=False), sg(3, "yes", .1, "no", ts=T0 - 1), sg(4, "yes", .1, None), sg(5, "yes", .1, "no", spec="OTHER"), sg(6, "yes", .1, "yes", ts=T0 + 9 * 10**9)]
r = m.score("T1", rows, T0, T0 + 10**6); assert (r["signals"], r["settled"], r["wins"]) == (2, 1, 1), r
print("shadow scorer second tests passed")
