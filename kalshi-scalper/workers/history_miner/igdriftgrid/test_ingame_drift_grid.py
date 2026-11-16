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
# gate: fixed once on the first 7 tip days, stored, never recomputed (Auditor B's fix 1)
def day_events(day, k, prefix):
    occ = "2026-11-%02dT03:00:00Z" % day; tip = calendar.timegm((2026, 11, day, 0, 0, 0))
    return [mk({"%s%d_%d" % (prefix, day, i): [(tip + 2700, 0.40, 0.42), (tip + 4500, 0.47, 0.49)]}, {"%s%d_%d" % (prefix, day, i): "yes"}, occ=occ) for i in range(k)]
CELL = "IGDG_75_05_FOLLOW"
assert G.compute_gate(day_events(20, 5, "a")) is None and G.run(day_events(20, 5, "a"))["cells"][CELL]["rate_gate"].startswith("pending")
# 22 trades on 7 days (3.14 a day), then nothing on 2 more days: 22 / 9 = 2.44 over all 9, NOT dropped
ev9 = [e for d, k in zip(range(20, 27), (4, 3, 3, 3, 3, 3, 3)) for e in day_events(d, k, "x")] + day_events(27, 0, "y") + [mk({"Z27": []}, {}, occ="2026-11-27T03:00:00Z"), mk({"Z28": []}, {}, occ="2026-11-28T03:00:00Z")]
g = G.compute_gate(ev9); assert A(g[CELL]["rate"], 22 / 7) and not g[CELL]["dropped"] and g[CELL]["days"][0] == "2026-11-20" and g[CELL]["days"][-1] == "2026-11-26"
r = G.run(ev9); assert r["cells"][CELL]["rate_gate"].startswith("ok") and A(r["cells"][CELL]["rate_per_day_all_days"], 22 / 9) and r["cells"][CELL]["days_with_games"] == 9 and "gate_to_store" in r
# the reverse: 14 trades on the first 7 days (2.0 a day, DROPPED), 20 more on the next 2 days: 34 / 9 = 3.78 over all 9, still DROPPED and not ranked
evr = [e for d in range(20, 27) for e in day_events(d, 2, "u")] + day_events(27, 10, "v") + day_events(28, 10, "w")
gr = G.compute_gate(evr); assert A(gr[CELL]["rate"], 2.0) and gr[CELL]["dropped"]
rr = G.run(evr); assert A(rr["cells"][CELL]["rate_per_day_all_days"], 34 / 9) and rr["cells"][CELL]["rate_gate"].startswith("DROPPED") and CELL not in rr["ranked_by_dollars_a_week"]
# a stored gate is used as given and not recomputed: store the 9-day verdict, then run on a shorter or longer list
st = G.compute_gate(ev9); r2 = G.run(ev9 + day_events(29, 40, "q"), stored_gate=st)
assert r2["cells"][CELL]["rate_gate"].startswith("ok (first-7-day rate 3.14)") and "gate_to_store" not in r2 and r2["ranked_by_dollars_a_week"][0] == CELL
assert r["m_cells_this_spec"] == 11 and r["m_with_iglatedrift1"] == 12
many = day_events(20, 4, "m")
r = G.run(many); c = r["cells"]["IGDG_75_05_FOLLOW"]
assert c["n"] == 4 and A(c["rate_per_day_all_days"], 4.0) and A(c["mean_net_per_contract_2c"], 0.472) and A(c["dollars_a_week_at_5_contracts"], 4.0 * 7 * 0.472 * 5)
assert r["cells"]["IGDG_75_05_FADE"]["dollars_a_week_at_5_contracts"] < 0 and not c["kill_fast"] and r["cells"]["IGDG_75_05_FADE"]["kill_fast"]
print("gate, rank and m: ok")
# the import pin: a changed ingame_events.py is refused
import hashlib, shutil, subprocess, tempfile
tmp = tempfile.mkdtemp(); os.makedirs(os.path.join(tmp, "igspecs")); os.makedirs(os.path.join(tmp, "igdriftgrid"))
shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ingame_drift_grid.py"), os.path.join(tmp, "igdriftgrid"))
open(os.path.join(tmp, "igspecs", "ingame_events.py"), "w").write(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "igspecs", "ingame_events.py")).read() + "\n# changed\n")
p = subprocess.run([sys.executable, "-I", os.path.join(tmp, "igdriftgrid", "ingame_drift_grid.py")], capture_output=True, text=True)
assert p.returncode != 0 and "REFUSED" in p.stderr + p.stdout, (p.returncode, p.stderr[-200:])
print("import pin: ok")
