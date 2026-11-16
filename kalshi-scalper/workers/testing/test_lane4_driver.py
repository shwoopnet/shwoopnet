import hashlib, json
import lane4_driver as d, lane4_fixture_second as fx
J = fx.build(); data = {n: {int(t): tuple(v) for t, v in s.items()} for n, s in J["data"].items()}; fund = {n: {int(t): r for t, r in f.items()} for n, f in J["funding"].items()}
under = {n: {int(L): tuple(v) for L, v in u.items()} for n, u in J["under"].items()}
L = d.run(data, fund, under, 6290660)
assert len(L) == 1 + 2 * 101 and L[0].startswith("header m_carried 6290660 m_new 101 m_total 6290761") and L == d.run(data, fund, under, 6290660)
ns = [int(l.split(" n ")[1].split()[0]) for l in L[1:]]; assert max(ns) > 50 and sum(1 for n in ns if n == 0) < 150, (max(ns), sum(1 for n in ns if n == 0))
bd = [int(l.split("boundary ")[1]) for l in L[1:]]; assert max(bd) >= 1
print("lane4 driver tests passed", hashlib.sha256("\n".join(L).encode()).hexdigest(), hashlib.sha256(json.dumps(J, sort_keys=True).encode()).hexdigest())
