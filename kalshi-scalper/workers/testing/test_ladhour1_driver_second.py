import hashlib, json
import ladhour1_driver_second as d, ladhour1_fixture_second as fx
J = fx.build(); cd = {t: {int(k): tuple(v) for k, v in s.items()} for t, s in J["candles"].items()}
L = d.run(J["markets"], cd, 6290660)
assert len(L) == 1 + 4 * 97 and L[0] == "header m_carried 6290660 m_new 384 m_total 6291044" and L == d.run(J["markets"], cd, 6290660)
heads = [l for l in L if " header m " in l]; assert len(heads) == 4 and all("m 6291044 entries" in h for h in heads)
ent = [int(h.split("entries ")[1].split()[0]) for h in heads]; assert min(ent) > 50, ent
assert not any("KXINXUD" in l or "KXBTCD" in l for l in L)
print("ladhour1 driver second tests passed", hashlib.sha256("\n".join(L).encode()).hexdigest(), hashlib.sha256(json.dumps(J, sort_keys=True).encode()).hexdigest())
