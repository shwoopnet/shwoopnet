import hashlib, json
import ethlate1_driver_second as d, ethlate1_fixture_second as fx
J = fx.build(); mk = J["markets"]; cd = {t: {int(k): tuple(v) for k, v in s.items()} for t, s in J["candles"].items()}
L = d.run(mk, cd)
assert len(L) == 97 and L[0].startswith("header m 6290756 entries ") and L == d.run(mk, cd)
n_s = [int(l.split(" S n ")[1].split()[0]) for l in L[1:]]; assert max(n_s) > 20 and sum(1 for n in n_s if n == 0) < 60, (max(n_s), sum(1 for n in n_s if n == 0))
print("ethlate1 driver second tests passed", hashlib.sha256("\n".join(L).encode()).hexdigest(), hashlib.sha256(json.dumps(J, sort_keys=True).encode()).hexdigest())
