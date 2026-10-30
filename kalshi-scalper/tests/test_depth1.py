"""Plain assert tests for DEPTH1 (src/scalper/depth1.py) on a SYNTHETIC fixture only: made-up polls, tape and results. No recorded R6 row is used.
Run with: cd kalshi-scalper && PYTHONPATH=src python tests/test_depth1.py"""
import contextlib
import io
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import depth1 as D
from scalper.quote2b import Poll

# 1. the feature source and settings match the frozen hash (workers/DEPTH1_frozen.json)
fz = json.loads(D.FROZEN_JSON.read_text())
assert fz["feature_hash"] == D.feature_hash(), "feature source or settings changed after the freeze"
assert fz["hashes"] == D.feature_hashes()
assert len(D.FEATURES) == 10 and fz["features"] == list(D.NAMES)

# 2. the read refuses before 2026-11-14 00:00 UTC, writes nothing, and a second run refuses
early = datetime(2026, 11, 13, 23, 59, tzinfo=timezone.utc).timestamp()
with tempfile.TemporaryDirectory() as d:
    D.RESULT_TXT, D.RESULT_MD, D.MARKER = Path(d) / "r.txt", Path(d) / "r.md", Path(d) / "started"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert D.run(now=early) is None
    assert "Refusing: the read date is 2026-11-14 00:00 UTC" in buf.getvalue()
    assert not D.RESULT_TXT.exists() and not D.MARKER.exists()
    # after the date, below 300 usable windows: NOT_ENOUGH_DATA, scoring nothing (coverage faked empty)
    D._coverage = lambda: {}
    with contextlib.redirect_stdout(io.StringIO()):
        v = D.run(now=D.READ_NOT_BEFORE + 1)
    assert v == "NOT_ENOUGH_DATA" and D.RESULT_TXT.exists() and "nothing scored" in D.RESULT_TXT.read_text()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert D.run(now=D.READ_NOT_BEFORE + 2) is None
    assert "Refusing to run again" in buf.getvalue()

# 3. sign conventions on a made-up book (YES terms)
def book(yb, ybs, nb, nbs, t=1000.0):
    return Poll(t, yb, ybs, nb, nbs)
def ctx(S, P30=None, P60=None, tape=()):
    return D.Ctx(S, P30, P60, list(tape))
heavy_yes = book([0.50, 0.49], [90, 80], [0.48, 0.47], [10, 10])        # lots of YES bids, few NO bids: lean YES
assert D.f1_imb5(ctx(heavy_yes)) > 0.5 and D.f2_imb1(ctx(heavy_yes)) > 0.5 and D.f10_imb_3c(ctx(heavy_yes)) > 0.5
assert D.f1_imb5(ctx(book([0.5], [10], [0.48], [90]))) < 0
assert D.f3_dwmid_minus_mid(ctx(book([0.50, 0.40], [10, 10], [0.48, 0.30], [10, 10]))) > 0   # NO side reaches further from the touch: YES
hole_yes = book([0.50, 0.30], [10, 10], [0.48, 0.47], [10, 10])        # hole behind the YES touch: buys NO
assert D.f8_hole_asymmetry(ctx(hole_yes)) < 0 and D.f9_book_slope(ctx(hole_yes)) < 0
prev = book([0.50], [50], [0.48], [50], 940.0)
assert D.f4_d_imb30(ctx(heavy_yes, P30=prev)) > 0 and D.f5_d_imb60(ctx(heavy_yes, P60=prev)) > 0
assert D.f4_d_imb30(ctx(heavy_yes)) is None
thin_no_then = book([0.50], [100], [0.48], [20], 940.0)
thin_no_now = book([0.50], [100], [0.48], [5], 1000.0)
assert D.f6_thin_depletion(ctx(thin_no_now, P60=thin_no_then)) > 0                  # thin NO side emptied: YES
thin_yes_then = book([0.50], [20], [0.48], [100], 940.0)
assert D.f6_thin_depletion(ctx(book([0.50], [5], [0.48], [100]), P60=thin_yes_then)) < 0
sw = [(990.2, 0.51, 3, "yes"), (990.7, 0.52, 3, "yes"), (995.1, 0.49, 2, "no"), (995.4, 0.49, 2, "no"), (999.0, 0.5, 1, "yes")]
assert D.f7_sweep_net(ctx(heavy_yes, tape=sw)) == 1.0       # one YES sweep (2 prices in one second); same price NO is not a sweep
assert D.f1_imb5(ctx(book([], [], [0.48], [10]))) is None

# 4. a window record: one decision at T-480 s, fill at the next poll's ask in the band, held to settlement
CLOSE = 1_800_000_000.0
polls = [book([0.50, 0.49], [90, 80], [0.48, 0.47], [10, 10], CLOSE - 900 + 2 * i) for i in range(0, 440)]
w = D.window_record(polls, [], CLOSE, "yes")
assert w is not None and w["feat"]["f1_imb5"] > 0
t = D.trade_of(w, "f1_imb5")
assert t[0] == "yes" and abs(t[1]["px"] - 0.52) < 1e-9 and t[1]["win"] == 1.0
assert abs(t[1]["pnl"] - (1 - 0.52 - 0.02)) < 1e-9          # 7% x 0.52 x 0.48 = 1.75c, rounded up to 2c
assert D.trade_of(D.window_record(polls, [], CLOSE, "no"), "f1_imb5")[1]["pnl"] < 0
assert D.window_record(polls[:5], [], CLOSE, "yes") is None
assert D.trade_of(w, "f7_sweep_net") is None                # a zero feature makes no trade

# 5. scoring: under 300 scored windows per market is NOT_ENOUGH_DATA; the control runs on a small synthetic set
ws = []
for i in range(40):
    x = dict(w); x.update(series=D.GOLD if i % 2 else D.BTC, date="2026-11-02", ticker="T%d" % i, held=False, close=CLOSE + 900 * i)
    ws.append(x)
v, lines = D.score(ws, {})
assert v == "NOT_ENOUGH_DATA"
obs, best, thr = D.shuffle_control({m: [x for x in ws if x["series"] == m] for m in D.UNIVERSE}, 20)
assert len(best) == 20 and len(obs) == 20

# 6. readiness projection from synthetic run names (no recorder file is opened)
names = ["book15r6/2026-10-29/2203/coverage.csv.gz", "book15r6/2026-10-30/0002/coverage.csv.gz", "book15r6/2026-10-30/0537/coverage.csv.gz",
         "book15r6/2026-10-30/1243/coverage.csv.gz", "book15r6/2026-10-30/1243/book.csv.gz"]
spans = D.run_spans(names)
assert len(spans) == 4 and spans[0][1] - spans[0][0] < 2 * 3600
p = D.project(spans, datetime(2026, 10, 30, 16, 9, tzinfo=timezone.utc).timestamp())
assert 0.5 < p["rate"] < 0.8 and p["bitcoin"]["projected"] > p["gold"]["projected"] > 300 and p["gold"]["so_far"] > 0
assert D.gold_open(datetime(2026, 11, 3, 15, tzinfo=timezone.utc).timestamp()) and not D.gold_open(datetime(2026, 11, 7, 15, tzinfo=timezone.utc).timestamp())
print("test_depth1: all passed")
