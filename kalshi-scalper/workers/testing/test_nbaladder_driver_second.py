import hashlib, json
import nbaladder_driver_second as d, nbaladder_fixture_second as fx
J = fx.build(); rungs = J["rungs"]; candles = {t: {int(k): tuple(v) for k, v in s.items()} for t, s in J["candles"].items()}
L = d.run(rungs, candles)
assert len(L) == 625 and L[0].startswith("cells 624 m_total 624 games_dropped_clock 1 ")
assert L == d.run(rungs, candles)
ns = [int(l.split(" n ")[1].split()[0]) for l in L[1:]]; assert max(ns) > 20 and sum(1 for n in ns if n == 0) < 600, (max(ns), sum(1 for n in ns if n == 0))
print("nbaladder driver second tests passed", hashlib.sha256("\n".join(L).encode()).hexdigest(), hashlib.sha256(json.dumps(J, sort_keys=True).encode()).hexdigest())
