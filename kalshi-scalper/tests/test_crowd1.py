import sys
sys.path.insert(0, "src")
from scalper import crowd1 as C


def e(s, t, net, day="2026-09-01"):
    return {"series": s, "close_ts": t, "net": net, "stress": net, "gross": net, "day": day}


ents = [e("KXBTC15M", 1, 0.1), e("KXETH15M", 1, -0.9), e("KXXRP15M", 2, 0.05), e("KXGOLD15M", 3, 0.05), e("KXSOL15M", 3, 0.0)]
solo, first, extra = C.groups(ents, C.ORDER)
assert [x["close_ts"] for x in solo] == [2, 3], solo
assert [x["series"] for x in first] == ["KXBTC15M"] and [x["series"] for x in extra] == ["KXETH15M"]
first2 = first + [e("KXBTC15M", 9, 0.3, "2026-09-02")]
solo2 = solo + [e("KXBTC15M", 8, 0.1, "2026-09-02")]
m, z, nd = C.diff_z(first2, solo2)
assert nd == 2 and abs(m - ((0.1 - 0.05) + (0.3 - 0.1)) / 2) < 1e-9, (m, nd)
print("ok")
