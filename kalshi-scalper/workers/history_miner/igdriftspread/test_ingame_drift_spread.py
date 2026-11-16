"""python3 -I test_ingame_drift_spread.py : hand case in IGDRIFTSPREAD1_CARD_NOV16.md, invented rows."""
import calendar, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingame_drift_spread as S
E = S.E
A = lambda x, y: abs(x - y) < 1e-9
def mk(rows, res, kind="spread", lg="NBA", occ="2026-11-20T03:00:00Z"):
    T = calendar.timegm((2026, 11, int(occ[8:10]), 0, 0, 0))
    return {"key": "k", "league": lg, "kind": kind, "rows": rows, "result": res, "occ": {t: occ for t in rows}, "close": {t: T + 14400 for t in rows}}
T = calendar.timegm((2026, 11, 20, 0, 0, 0))
assert len(S.CELLS) == 12 and (120, 0.08, "follow") in S.CELLS and S.rid((75, 0.05, "follow")) == "IGDS_75_05_FOLLOW"
ev = mk({"S": [(T + 2700, 0.40, 0.42), (T + 4500, 0.47, 0.49)]}, {"S": "yes"})
w, d = S.decide(ev, (75, 0.05, "follow")); assert w == "ok" and d["side"] == "yes" and A(d["ask"], 0.49) and A(E.cash(ev, d, 0.02), 4.72)
w, d = S.decide(ev, (120, 0.08, "follow")); assert w == "no quote at a mark"
assert S.decide(mk({"S": []}, {}, kind="total"), (75, 0.05, "follow"))[0] == "not in wall" and S.decide(mk({"S": []}, {}, kind="ml", lg="NHL"), (75, 0.05, "follow"))[0] == "not in wall"
assert S.decide(mk({"S": []}, {}, lg="NFL"), (75, 0.05, "follow"))[0] == "not in wall"
print("decide: ok")
def day_events(day, k):
    occ = "2026-11-%02dT03:00:00Z" % day; tip = calendar.timegm((2026, 11, day, 0, 0, 0))
    return [mk({"S%d_%d" % (day, i): [(tip + 2700, 0.40, 0.42), (tip + 4500, 0.47, 0.49)]}, {"S%d_%d" % (day, i): "yes"}, occ=occ) for i in range(k)]
CELL = "IGDS_75_05_FOLLOW"
assert S.compute_gate(day_events(20, 5)) is None
ev9 = [e for d, k in zip(range(20, 27), (4, 3, 3, 3, 3, 3, 3)) for e in day_events(d, k)] + [mk({"Z27": []}, {}, occ="2026-11-27T03:00:00Z"), mk({"Z28": []}, {}, occ="2026-11-28T03:00:00Z")]
g = S.compute_gate(ev9); assert A(g[CELL]["rate"], 22 / 7) and not g[CELL]["dropped"]
r = S.run(ev9); assert r["cells"][CELL]["rate_gate"].startswith("ok") and A(r["cells"][CELL]["games_per_day_all_days"], 22 / 9) and r["m_cells_this_spec"] == 12 and r["m_with_igdriftgrid1"] == 23 and r["m_with_iglatedrift1"] == 24 and "gate_to_store" in r
evr = [e for d in range(20, 27) for e in day_events(d, 2)] + day_events(27, 10) + day_events(28, 10)
rr = S.run(evr); assert rr["cells"][CELL]["rate_gate"].startswith("DROPPED") and CELL not in rr["ranked_by_dollars_a_week"]
r2 = S.run(ev9 + day_events(29, 40), stored_gate=S.compute_gate(ev9)); assert "gate_to_store" not in r2 and r2["ranked_by_dollars_a_week"][0] == CELL and r2["cells"][CELL]["unit"].startswith("games")
print("gate, rank and m: ok")
import shutil, subprocess, tempfile
tmp = tempfile.mkdtemp(); here = os.path.dirname(os.path.abspath(__file__))
for d in ("igdriftspread", "igdriftgrid", "igspecs"):
    os.makedirs(os.path.join(tmp, d))
shutil.copy(os.path.join(here, "ingame_drift_spread.py"), os.path.join(tmp, "igdriftspread"))
shutil.copy(os.path.join(here, "..", "igspecs", "ingame_events.py"), os.path.join(tmp, "igspecs"))
open(os.path.join(tmp, "igdriftgrid", "ingame_drift_grid.py"), "w").write(open(os.path.join(here, "..", "igdriftgrid", "ingame_drift_grid.py")).read() + "\n# changed\n")
p = subprocess.run([sys.executable, "-I", os.path.join(tmp, "igdriftspread", "ingame_drift_spread.py")], capture_output=True, text=True)
assert p.returncode != 0 and "REFUSED" in p.stderr + p.stdout
print("import pin: ok")
