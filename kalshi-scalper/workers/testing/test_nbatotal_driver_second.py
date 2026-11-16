import hashlib, json
import nbatotal_driver_second as d, nbatotal_fixture_second as fx
J = fx.build(); candles = {t: {int(k): tuple(v) for k, v in s.items()} for t, s in J["candles"].items()}
L = d.run(J["rungs"], candles)
assert len(L) == 3 + 520 and L[0] == "header m_carried 6290660 m_new 520 m_total 6291180" and L == d.run(J["rungs"], candles)
cnt = dict(eval(L[1][len("counts "):])); assert cnt["m35_dropped_games"] >= 1 and cnt["games_dropped_clock"] == 1 and cnt["inplay_guard_9"] >= 1, cnt
ns = [int(l.split(" n ")[1].split()[0]) for l in L[3:]]; assert max(ns) > 15 and sum(1 for n in ns if n == 0) < 500, (max(ns), sum(1 for n in ns if n == 0))
Lj = d.run(J["rungs"], candles, m_new=1770); assert Lj[0] == "header m_carried 6290660 m_new 1770 m_total 6292430" and Lj[1:] == L[1:]
print("nbatotal driver second tests passed", hashlib.sha256("\n".join(L).encode()).hexdigest(), hashlib.sha256(json.dumps(J, sort_keys=True).encode()).hexdigest())
