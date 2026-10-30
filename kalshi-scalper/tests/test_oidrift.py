"""Plain assert tests for OIDRIFT (src/scalper/oidrift.py) and OIFILL (src/scalper/oifill.py); run with: python tests/test_oidrift.py."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import oidrift as D
from scalper import oifill as O
from scalper.fwdeval import NoData
from scalper.quote2b import Poll

DAY = 86400
close = 1_800_000_000 - 1_800_000_000 % DAY + 12 * 3600       # noon UTC on some day

# threshold: earlier UTC days only, 30 day span, 20 days needed, p90 by index int(0.9 * (n - 1))
bd = {close - close % DAY - k * DAY: [float(k)] * 10 for k in range(1, 31)}
bd[close - close % DAY] = [1e9]                                  # the scored day itself must never count
v = sorted(x for k in range(1, 31) for x in [float(k)] * 10)
assert D.threshold(close, bd) == v[int(0.9 * (len(v) - 1))]
bd[close - close % DAY - 31 * DAY] = [1e12]                     # outside the 30 day span
assert D.threshold(close, bd) == v[int(0.9 * (len(v) - 1))]
few = {close - close % DAY - k * DAY: [1.0] for k in range(1, 20)}
assert D.threshold(close, few) is None, "19 days is fewer than 20"

def win(c):
    return {"series": "KXBTC15M", "close_ts": close, "candles": c}

base = {close - 360: (0.70, 0.72, 100.0, 1000.0), close - 180: (0.80, 0.82, 100.0, 2000.0), close - 120: (0.83, 0.85, 50.0, 2100.0)}
tr = D.decide(win(base), 900.0)                                  # doi 1000 > 900; YES ask 0.82 out of band, NO ask 0.20 in band
assert tr["side"] == "no" and abs(tr["entry"] - 0.17) < 1e-9 and tr["exit"] is None, tr
assert D.decide(win(base), 1000.0) is None, "doi must be strictly above the threshold"
try:
    D.decide(win(base), None); raise AssertionError
except NoData:
    pass
for drop in (close - 360, close - 180):
    c = dict(base); del c[drop]
    try:
        D.decide(win(c), 900.0); raise AssertionError
    except NoData:
        pass
c = dict(base); c[close - 360] = (0.70, 0.72, 100.0, 0.0)        # the ledger stores a missing oi as 0: NoData, never a signal
try:
    D.decide(win(c), 900.0); raise AssertionError
except NoData:
    pass
c = dict(base); del c[close - 120]
try:
    D.decide(win(c), 900.0); raise AssertionError
except NoData:
    pass
mid = dict(base); mid[close - 180] = (0.48, 0.52, 100.0, 2000.0)   # neither side in 5c to 50c
assert D.decide(win(mid), 900.0) is None
yes = dict(base); yes[close - 180] = (0.20, 0.22, 100.0, 2000.0)
assert D.decide(win(yes), 900.0)["side"] == "yes"
assert D.forward_eval(dict(win(base), series="KXETH15M"), {"series": "KXBTC15M"}) is None

# OIFILL: YES buy lifts the NO bids (ask 1 - p), NO buy lifts the YES bids; +2c window inclusive
p = Poll(close - 178, [0.80, 0.79, 0.77], [5, 7, 9], [0.82, 0.81, 0.80, 0.79], [3, 4, 6, 8])
assert O.depth(p, "yes") == (0.18, 3, 3 + 4 + 6)
assert O.depth(p, "no") == (0.20, 5, 5 + 7)
assert O.depth(Poll(0, [], [], [], []), "yes") is None
ps = [Poll(close - 185, [], [], [], []), p, Poll(close - 170, [], [], [], [])]
assert O.nearest_after(ps, close - 180) is p
assert O.nearest_after([Poll(close - 160, [], [], [], [])], close - 180) is None, "more than 10 s late"

with tempfile.TemporaryDirectory() as d:
    out = Path(d) / "OIFILL.md"
    O.run(out=out, sigs={i: [] for i in O.IDS}, polls={})        # 0 signals runs cleanly
    assert "0 forward signals" in out.read_text()
    sig = {"REF_GEN6_OICORE": [{"ticker": "T", "close_ts": close, "side": "yes", "entry": 0.19}], "REF_GEN6_OIDRIFT": []}
    O.run(out=out, sigs=sig, polls={"T": ps})
    txt = out.read_text()
    assert "| REF_GEN6_OICORE | 1 | 1 | 0 |" in txt and "+2c" in txt and txt.count("## ") == 2, txt
print("test_oidrift: ok")
