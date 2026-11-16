"""python3 -I test_ingame_period.py : hand case in IGPERIOD1_CARD_NOV16.md, invented rows."""
import calendar, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingame_period as P
E = P.E
A = lambda x, y: abs(x - y) < 1e-9
T = calendar.timegm((2026, 11, 20, 0, 0, 0)); OCC = "2026-11-20T03:00:00Z"
def mk(rows, res=None, kind="total", lg="NHL", occ=OCC):
    return {"key": "k", "league": lg, "kind": kind, "rows": rows, "result": res or {}, "occ": {t: occ for t in rows}, "close": {t: T + 14400 for t in rows}}
flat = [(T + 2400, 0.50, 0.52), (T + 2700, 0.50, 0.52), (T + 3000, 0.50, 0.52), (T + 3300, 0.50, 0.52)]
ev = mk({"X": flat + [(T + 3360, 0.55, 0.57)]}, {"X": "yes"})
st = P.stretches(ev["rows"]["X"], T); assert len(st) == 1 and st[0][0] == T + 2400 and A(st[0][1], 0.51) and st[0][2][0] == T + 3360
w, d = P.decide(ev, (1, 0.04, "follow")); assert w == "ok" and d["side"] == "yes" and A(d["ask"], 0.57) and A(E.cash(ev, d, 0.02), 3.93)
w, d = P.decide(ev, (1, 0.04, "fade")); assert w == "ok" and d["side"] == "no" and A(d["ask"], 0.45) and A(E.cash(ev, d, 0.02), -4.88)
assert P.decide(ev, (1, 0.02, "follow"))[0] == "ok" and P.decide(ev, (2, 0.02, "follow"))[0] == "no boundary"
short = mk({"X": flat[:3] + [(T + 3060, 0.55, 0.57)]}); assert P.decide(short, (1, 0.02, "follow"))[0] == "no boundary"          # only 600 s flat
gap = mk({"X": [(T + 2400, 0.50, 0.52), (T + 2800, 0.50, 0.52), (T + 3100, 0.50, 0.52), (T + 3300, 0.50, 0.52), (T + 3360, 0.55, 0.57)]}); assert P.decide(gap, (1, 0.02, "follow"))[0] == "no boundary"   # a 400 s gap breaks the run
early = mk({"X": [(t - 1000, b, a) for t, b, a in flat + [(T + 3360, 0.55, 0.57)]]}); assert P.decide(early, (1, 0.02, "follow"))[0] == "no boundary"      # starts at tip + 23 min
small = mk({"X": flat + [(T + 3360, 0.52, 0.54)]}); assert P.decide(small, (1, 0.04, "follow"))[0] == "no signal"
oor = mk({"X": flat + [(T + 3360, 0.83, 0.85)]}); assert P.decide(oor, (1, 0.04, "follow"))[0] == "ask out of range"
assert P.decide(mk({"X": flat}, lg="NBA"), (1, 0.02, "follow"))[0] == "not in wall" and P.decide(mk({"X": flat}, kind="spread"), (1, 0.02, "follow"))[0] == "not in wall"
assert P.decide(mk({"X": flat}, occ="2026-11-20T03:10:00Z"), (1, 0.02, "follow"))[0] == "schedule test failed"
two = flat + [(T + 3360, 0.55, 0.57)] + [(T + 5400 + 300 * i, 0.55, 0.57) for i in range(4)] + [(T + 6660, 0.60, 0.62)]
assert len(P.stretches(two, T)) == 2
print("decide: ok")
def day_events(day, k):
    occ = "2026-11-%02dT03:00:00Z" % day; tip = calendar.timegm((2026, 11, day, 0, 0, 0))
    return [mk({"X%d_%d" % (day, i): [(t - T + tip, b, a) for t, b, a in flat + [(T + 3360, 0.55, 0.57)]]}, {"X%d_%d" % (day, i): "yes"}, occ=occ) for i in range(k)]
CELL = "IGPD_B1_04_FOLLOW"
assert len(P.CELLS) == 8 and P.rid((1, 0.04, "follow")) == CELL and P.compute_gate(day_events(20, 5)) is None
ev9 = [e for d, k in zip(range(20, 27), (4, 3, 3, 3, 3, 3, 3)) for e in day_events(d, k)] + [mk({"Z": []}, occ="2026-11-27T03:00:00Z"), mk({"Z2": []}, occ="2026-11-28T03:00:00Z")]
g = P.compute_gate(ev9); assert A(g[CELL]["rate"], 22 / 7) and not g[CELL]["dropped"]
r = P.run(ev9); assert r["cells"][CELL]["rate_gate"].startswith("ok") and A(r["cells"][CELL]["games_per_day_all_days"], 22 / 9) and r["m_cells_this_spec"] == 8 and r["m_with_all_ingame_specs"] == 33 and "gate_to_store" in r
evr = [e for d in range(20, 27) for e in day_events(d, 2)] + day_events(27, 10) + day_events(28, 10)
rr = P.run(evr); assert rr["cells"][CELL]["rate_gate"].startswith("DROPPED") and CELL not in rr["ranked_by_dollars_a_week"]
r2 = P.run(ev9 + day_events(29, 40), stored_gate=P.compute_gate(ev9)); assert "gate_to_store" not in r2 and CELL in r2["ranked_by_dollars_a_week"] and "IGPD_B1_04_FADE" not in r2["ranked_by_dollars_a_week"]
print("gate, rank and m: ok")
import shutil, subprocess, tempfile
tmp = tempfile.mkdtemp(); here = os.path.dirname(os.path.abspath(__file__))
for d in ("igperiod", "igdriftgrid", "igspecs"):
    os.makedirs(os.path.join(tmp, d))
shutil.copy(os.path.join(here, "ingame_period.py"), os.path.join(tmp, "igperiod")); shutil.copy(os.path.join(here, "..", "igspecs", "ingame_events.py"), os.path.join(tmp, "igspecs"))
open(os.path.join(tmp, "igdriftgrid", "ingame_drift_grid.py"), "w").write(open(os.path.join(here, "..", "igdriftgrid", "ingame_drift_grid.py")).read() + "\n# changed\n")
p = subprocess.run([sys.executable, "-I", os.path.join(tmp, "igperiod", "ingame_period.py")], capture_output=True, text=True)
assert p.returncode != 0 and "REFUSED" in p.stderr + p.stdout
print("import pin: ok")
