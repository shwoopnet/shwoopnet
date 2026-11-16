import hashlib, json
import socdrift_driver_second as d, socdrift_fixture_second as fx
J = fx.build(); candles = {t: {int(k): tuple(v) for k, v in s.items()} for t, s in J["candles"].items()}; assert len(J["rungs"]) == 270 and len(set(r["ticker"] for r in J["rungs"])) == 270
L = d.run(J["rungs"], candles); assert len(L) == 603 and L[0].startswith("header m_carried 6290660 m_new 600 m_total 6291260") and L == d.run(J["rungs"], candles)
cnt = dict(eval(L[1][len("counts "):])); assert cnt["clock_dropped_games"] == 2 and cnt["live_guard_dropped_m2"] >= 1 and cnt["m2_dropped_games"] >= 0, cnt
ns = [int(l.split(" n ")[1].split()[0]) for l in L[3:]]; assert max(ns) > 20 and sum(1 for n in ns if n == 0) < 560, (max(ns), sum(1 for n in ns if n == 0))
print("socdrift driver second tests passed", hashlib.sha256("\n".join(L).encode()).hexdigest(), hashlib.sha256(json.dumps(J, sort_keys=True).encode()).hexdigest())
