import gzip, json, hashlib, pool1_driver_second as d, pool1_fixture_second as fx
J = fx.build(); raw = json.dumps(J, sort_keys=True)
assert hashlib.sha256(raw.encode()).hexdigest() == open("POOL1_FIXTURE_SECOND.sha").read().split()[0], "fixture changed"
data = {n: {int(t): tuple(v) for t, v in s.items()} for n, s in J["data"].items()}; fund = {n: {int(t): r for t, r in f.items()} for n, f in J["funding"].items()}
L = d.run(data, fund)
assert len(L) == 220 and L[1] == "m 218 + carried 103444 = 103662" and len(set(l.split(" | ")[0] for l in L[2:])) == 218
assert L == d.run(data, fund)          # deterministic
assert sum(1 for l in L if l.startswith("gap")) == 72 and sum(1 for l in L if l.startswith("fund")) == 48 and sum(1 for l in L if l.startswith("carry")) == 2 and sum(1 for l in L if l.startswith("tr")) == 96
print("pool1 driver second tests passed", hashlib.sha256("\n".join(L).encode()).hexdigest())
