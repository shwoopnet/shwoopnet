import sys
sys.path.insert(0, "src")
from scalper import tail1 as T

cl = 1_700_000_000
c = (cl - 360, 0.93, 0.95, 0.93, 0.95)          # yes bid .93 ask .95 -> no ask .07 qualifies, yes ask .95 does not
m = [("A", "KXGOLD15M", [c], cl, "no"), ("B", "KXGOLD15M", [c], cl, "yes"), ("C", "KXBTC15M", [c], cl, "no")]
e = T.entries(m)
assert len(e) == 2 and e[0]["net"] > 0.9 and e[1]["net"] < -0.07          # the no side wins in A, loses its stake plus fee in B
assert len(T.entries(m, series=None)) == 3
assert T.judge(e)["verdict"] == "NOT_ENOUGH_DATA"
print("ok")
