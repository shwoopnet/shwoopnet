"""python3 -I test_ingame_drift_grid.py : hand case in IGDRIFTGRID1_CARD_NOV16.md, invented rows."""
import calendar, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingame_drift_grid as G
E = G.E
A = lambda x, y: abs(x - y) < 1e-9
OCC = "2026-11-20T03:00:00Z"; T = calendar.timegm((2026, 11, 20, 0, 0, 0))
mk = lambda rows, res, kind="total", lg="NBA", occ=OCC: {"key": "k", "league": lg, "kind": kind, "rows": rows, "result": res, "occ": {t: occ for t in rows}, "close": {t: T + 14400 for t in rows}}
assert len(G.CELLS) == 11 and (120, 0.08, "follow") not in G.CELLS and G.rid((75, 0.05, "follow")) == "IGDG_75_05_FOLLOW"
ev = mk({"T": [(T + 2700, 0.40, 0.42), (T + 4500, 0.47, 0.49)]}, {"T": "yes"})
w, d = G.decide(ev, (75, 0.05, "follow")); assert w == "ok" and d["side"] == "yes" and A(d["ask"], 0.49) and A(E.cash(ev, d, 0.02), 4.72)
w, d = G.decide(ev, (75, 0.05, "fade")); assert w == "ok" and d["side"] == "no" and A(d["ask"], 0.53) and A(E.cash(ev, d, 0.02), -5.68)
assert G.decide(mk({"T": [(T + 2700, 0.40, 0.42), (T + 4500, 0.43, 0.45)]}, {}), (75, 0.05, "follow"))[0] == "no signal"
assert G.decide(mk({"T": [(T + 2700, 0.80, 0.82), (T + 4500, 0.85, 0.87)]}, {}), (75, 0.05, "follow"))[0] == "ask out of range"
assert G.decide(mk({"T": [(T + 4100, 0.40, 0.42), (T + 4500, 0.47, 0.49)]}, {}), (75, 0.05, "follow"))[0] == "no quote at a mark"
assert G.decide(mk({"T": []}, {}, lg="NFL"), (75, 0.05, "follow"))[0] == "not in wall" and G.decide(mk({"A": []}, {}, kind="ml", lg="NBA"), (75, 0.05, "follow"))[0] == "not in wall"
assert G.decide(mk({"T": []}, {}, occ="2026-11-20T03:10:00Z"), (75, 0.05, "follow"))[0] == "schedule test failed"
print("decide: ok")
r = G.run([ev])
assert r["tries"] == 11 and r["cells"]["IGDG_75_05_FOLLOW"]["n"] == 1 and r["cells"]["IGDG_75_05_FOLLOW"]["rate_gate"].startswith("DROPPED") and r["ranked_by_dollars_a_week"] == []
many = []
for k in range(4):
    many.append(mk({"T%d" % k: [(T + 2700, 0.40, 0.42), (T + 4500, 0.47, 0.49)]}, {"T%d" % k: "yes"}))
r = G.run(many); c = r["cells"]["IGDG_75_05_FOLLOW"]
assert c["n"] == 4 and A(c["rate_per_day"], 4.0) and c["rate_gate"] == "ok" and A(c["mean_net_per_contract_2c"], 0.472) and A(c["dollars_a_week_at_5_contracts"], 4.0 * 7 * 0.472 * 5)
assert r["ranked_by_dollars_a_week"][0] == "IGDG_75_05_FOLLOW" and r["cells"]["IGDG_75_05_FADE"]["dollars_a_week_at_5_contracts"] < 0 and not c["kill_fast"] and r["cells"]["IGDG_75_05_FADE"]["kill_fast"]
print("grid and ranking: ok")
