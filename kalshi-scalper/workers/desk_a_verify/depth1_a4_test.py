"""Amendment 4 tests on INVENTED values (Desk A, Nov 13 2026). No R6 file. python3 -I depth1_a4_test.py <V2 kalshi-scalper dir>
 T1: the verdict bars compare in integers (a float-failing exact 1.5 PF passes; an exact 1.0 half fails 'above 1.0'; 1.2 stress is not above 1.2).
 T2: f6 near-tie at 1e-9 is zero in the wrapper and a side in V2's own function."""
import sys, random, itertools
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).resolve() / "src")); sys.path.insert(0, str(Path(__file__).parent))
from scalper import depth1 as D
from scalper.quote2b import Poll
orig_passes, orig_wr = D.passes, D.window_record
import depth1_wrapper as W
st = W.install(D)
# T1: find an invented trade sequence whose profit factor is EXACTLY 1.5 in cents but that V2's float passes() refuses
def window(close, date, pnl, stress):
    return {"close": close, "date": date, "series": "KXGOLD15M", "feat": {n: (1.0 if n == "f1_imb5" else None) for n in D.NAMES}, "fill": {"yes": {"px": 0.5, "pnl": pnl, "pnl_stress": stress, "win": 1.0 if pnl > 0 else 0.0}, "no": None}}
dates = ["2026-10-31", "2026-11-05", "2026-11-10"]
def build(seq, reps=110):
    ws = []; t = 0
    for bi, d in enumerate(dates):
        for _ in range(reps):
            for v in seq: t += 1; ws.append(window(t, d, v, v))
    return ws
rng = random.Random(3); found = None
for _ in range(4000):
    xs = [round(rng.randint(1, 9) * 0.01, 2) for _ in range(rng.randint(2, 7))]; ys = [-round(rng.randint(1, 9) * 0.01, 2) for _ in range(rng.randint(2, 7))]
    wi, li = sum(round(v * 100) for v in xs), -sum(round(v * 100) for v in ys)
    if not (li and 2 * wi == 3 * li): continue
    seq = xs + ys; rng.shuffle(seq); ws = build(seq); s = D.try_stats(ws, "f1_imb5")
    if not orig_passes(s, True, 0.0): found = (seq, ws, s); break
assert found, "no float-failing exact 1.5 found"; seq, ws, s = found
assert D.passes(s, True, 0.0), "integer bar must pass an exact 1.5"
print("T1 OK exact 1.5 (pooled float %.17g, blocks %s): V2's float passes() refuses it, the wrapper passes it; seq %s" % (s["pf"], [round(p, 17) for _, p in s["blocks"]], seq))
# exact ties must NOT pass: halves at exactly 1.0, stress profit factor at exactly 1.2
def build2(pairs, reps=110):
    ws = []; t = 0
    for d in dates:
        for _ in range(reps):
            for v, sv in pairs: t += 1; ws.append(window(t, d, v, sv))
    return ws
tie_half = build2([(0.30, 0.30), (-0.10, -0.10), (-0.10, -0.10), (-0.10, -0.10)])          # PF 1.0 exactly, half PF 1.0: fails (not above 1.0) and fails PF 1.5 too
assert not D.passes(D.try_stats(tie_half, "f1_imb5"), True, 0.0)
good = build2([(0.30, 0.24), (-0.20, -0.20)])                     # PF 1.5 normal; stress PF 0.24/0.20 = 1.2 exactly: must NOT pass (needs above 1.2)
sg = D.try_stats(good, "f1_imb5"); assert not D.passes(sg, True, 0.0) and sg["int"]["stress"] == (sg["int"]["stress"][0], sg["int"]["stress"][1]) and 5 * sg["int"]["stress"][0] == 6 * sg["int"]["stress"][1]
good2 = build2([(0.30, 0.2412), (-0.20, -0.20)]); assert D.passes(D.try_stats(good2, "f1_imb5"), True, 0.0)           # stress 1.206: above 1.2 passes
print("T1b OK: stress PF exactly 1.2 does not pass, 1.206 passes; a half at exactly 1.0 does not pass")
# T2: f6 tie
close = 2_000_000
def poll(t, ys, ns): return Poll(t, [0.50 - 0.01 * i for i in range(len(ys))], ys, [0.45 - 0.01 * i for i in range(len(ns))], ns)
polls = [poll(close - 560, [0.1, 0.2], [0.3]), poll(close - 500, [0.1, 0.2], [0.2]), poll(close - 481, [0.1, 0.2], [0.2]), poll(close - 480, [0.1, 0.2], [0.2]), poll(close - 478, [0.1, 0.2], [0.2])]
# P60 is the poll at or before S.t-60 = close-540: use polls with times to hit it
polls = [poll(close - 540, [0.1, 0.2], [0.3]), poll(close - 480, [0.1, 0.2], [0.2])]
wo = orig_wr(polls, [], close, "yes"); ww = D.window_record(polls, [], close, "yes")
print("T2 raw V2 f6 =", wo["feat"]["f6_thin_depletion"], "| wrapper f6 =", ww["feat"]["f6_thin_depletion"])
assert wo["feat"]["f6_thin_depletion"] not in (None, 0.0) and ww["feat"]["f6_thin_depletion"] == 0.0
print("T2 OK")
