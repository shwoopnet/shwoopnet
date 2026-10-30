"""Plain assert tests for the GF1 and GF2 scorer (src/scalper/gf12.py) on a SYNTHETIC fixture only: made-up book polls,
made-up tape rows and made-up settlements. No recorded R6 row, coverage file or result is used.
Run with: cd kalshi-scalper && PYTHONPATH=src python tests/test_gf12.py"""
import contextlib
import io
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import gf12 as G
from scalper import r6tests as R6
from scalper.quote2b import Poll

CLOSE = 1_800_000_000.0           # a quarter hour, exchange seconds
OPEN = CLOSE - 900
S_T = CLOSE - 360                 # the signal poll (on the 2 s grid from OPEN)


def poll(t, bid, ask, bsz=5.0, asz=3.0, ybid=None, nbid=None):
    """YES bid `bid` (size bsz), YES ask `ask` (= 1 - NO bid, size asz); ybid / nbid: extra [(px, sz)] levels below the best."""
    yb, ybs = [bid] + [p for p, _ in ybid or []], [bsz] + [s for _, s in ybid or []]
    nb, nbs = [round(1 - ask, 4)] + [p for p, _ in nbid or []], [asz] + [s for _, s in nbid or []]
    return Poll(t, yb, ybs, nb, nbs)


def path(segs):
    """segs: [(until_t, kwargs for poll)]; one poll every 2 s from OPEN."""
    out, t = [], OPEN
    for until, kw in segs:
        while t < until:
            out.append(poll(t, **kw))
            t += 2
    return out


def near(a, b):
    return abs(a - b) < 1e-9


# ---------------- registered constants
assert (G.NEEDED, G.SIZES, G.TAKER, G.MAKER, G.Z_BAR, G.GF2_Z_GATE) == (300, (1, 10), 0.07, 0.0175, 5.17, 2.0)
assert (G.LIVE_S, G.REST_END_S, G.INSIDE, G.CHASE_CAP, G.SIGNAL_S, G.SIGNAL_GAP) == (1.0, 31.0, 0.01, 0.01, 360, 10)
assert G.READ_NOT_BEFORE == datetime(2026, 11, 14, tzinfo=timezone.utc).timestamp()
assert G.LAST_OPEN == datetime(2026, 11, 13, 23, 59, tzinfo=timezone.utc).timestamp()
assert sum(G.TRIES.values()) == 8 and G.SERIES[0] == "KXGOLD15M"

FLAT = dict(bid=0.915, ask=0.92, bsz=5.0, asz=50.0)
flat = path([(CLOSE, FLAT)])

# 1. signal: the YES ask 0.92 at S; L = 0.91; no signal outside the band or with no poll within 10 s of T-360
side, S, _ = G.signal(flat, CLOSE)
assert side == "yes" and near(S.t, S_T) and near(S.ask, 0.92)
assert G.signal(path([(CLOSE, dict(bid=0.50, ask=0.52))]), CLOSE) is None
assert G.signal([p for p in flat if not (S_T - 12 < p.t < S_T + 1)], CLOSE) is None

# 2. a quiet book: the 1c-inside bid never fills, the chase crosses at 0.92 (<= 0.93) for all of C; GF2 enters the same way
w = G.simulate(flat, [], CLOSE, "yes", 1)
assert w["L"] == 0.91 and w["rest_q"] == 0 and w["chase_status"] == "cross" and w["chase"] == [(0.92, 1)]
assert not w["gf2_dip"] and w["gf2_status"] == "cross" and w["gf2"] == [(0.92, 1)]
assert near(G.gf1_pnl(w), 1 - 0.92 - 0.01) and near(G.gf2_pnl(w), 0.07) and near(G.plain_pnl(w), 0.07)
assert near(G.gf1_pnl(G.simulate(flat, [], CLOSE, "no", 1)), -0.92 - 0.01)

# 3. a taker sale strictly through L inside the 30 s fills the whole remainder at L (OUR price); GF2 drops the signal
tr = [(S_T + 10, 0.905, 1, -1)]
for C in (1, 10):
    w = G.simulate(flat, tr, CLOSE, "yes", C)
    assert w["rest_q"] == C and w["chase"] == [] and w["chase_status"] == "not needed" and w["rest_mech"] == "through"
    assert w["gf2_dip"] and w["gf2_status"] == "filtered" and w["gf2"] == [] and G.gf2_pnl(w) == 0
w1 = G.simulate(flat, tr, CLOSE, "yes", 1)
assert near(G.gf1_pnl(w1), 1 - 0.91 - 0.01)
w10 = G.simulate(flat, tr, CLOSE, "yes", 10)
assert near(G.gf1_pnl(w10), 10 * 0.09 - 0.06)                     # 7% x 10 x 0.91 x 0.09 = 5.73c, rounded up to 6c
assert near(G.gf1_pnl(w10, G.MAKER), 10 * 0.09 - 0.02) and near(G.gf1_pnl(w10, 0.0), 0.9)
assert near(G.gf1_pnl(w10, G.TAKER, 1.2), 10 * 0.09 - 1.2 * 0.06)

# 4. trades before live (S + 1.0 s) and at or after the cancel (S + 31.0 s) never fill
for t in (S_T + 0.5, S_T + 31.0, S_T + 40):
    w = G.simulate(flat, [(t, 0.80, 50, -1)], CLOSE, "yes", 1)
    assert w["rest_q"] == 0 and w["chase_status"] == "cross" and not w["gf2_dip"], t
assert G.simulate(flat, [(S_T + 1.0, 0.80, 1, -1)], CLOSE, "yes", 1)["rest_q"] == 1      # live at exactly S + 1.0 s

# 5. queue: 4 displayed at L on our side's bids at S; taker sales AT L must pass it; a taker BUY at L is an ask lifted (full)
qbook = path([(CLOSE, dict(FLAT, ybid=[(0.91, 4.0)]))])
assert G.queue_at(qbook[0], 0.91) == 4.0 and G.queue_at(qbook[0], 0.912) == 0.0
w = G.simulate(qbook, [(S_T + 5, 0.91, 4, -1)], CLOSE, "yes", 1)
assert w["rest_q"] == 0 and not w["gf2_dip"]
w = G.simulate(qbook, [(S_T + 5, 0.91, 4, -1), (S_T + 6, 0.91, 1, -1)], CLOSE, "yes", 10)
assert near(w["rest_q"], 1) and w["chase"] == [(0.92, 9)]
assert w["gf2_dip"] and w["gf2"] == []                           # the C = 1 test decides GF2 for C = 10 too
assert near(G.gf1_pnl(w), (0.09 - 0.01) + (9 * 0.08 - 0.05))        # 1 at 0.91 (fee 1c), 9 at 0.92 (fee 5c, next line)
assert R6.taker_fee([(0.92, 9)]) == 0.05                          # 7% x 9 x 0.92 x 0.08 = 4.64c -> 5c
assert G.simulate(qbook, [(S_T + 5, 0.91, 1, 1)], CLOSE, "yes", 1)["rest_mech"] == "ask_lifted"
# the larger of the size at S and at the first poll at or after live
grow = [p if p.t < S_T + 1 else poll(p.t, **dict(FLAT, ybid=[(0.91, 9.0)])) for p in qbook]
assert G.simulate(grow, [(S_T + 5, 0.91, 5, -1)], CLOSE, "yes", 1)["rest_q"] == 0
# L under all 5 recorded levels of a full side: infinite queue, only a print or quote through L fills
deep = path([(CLOSE, dict(FLAT, ybid=[(0.914, 1), (0.913, 1), (0.912, 1), (0.911, 1)]))])
assert G.queue_at(deep[0], 0.91) == float("inf")
assert G.simulate(deep, [(S_T + 5, 0.91, 5000, -1)], CLOSE, "yes", 1)["rest_q"] == 0
assert G.simulate(deep, [(S_T + 5, 0.909, 1, -1)], CLOSE, "yes", 1)["rest_q"] == 1

# 6. a recorded ask at or under L fills the whole order at L, never the better price; a quote moving away is not a fill
dip = path([(S_T + 12, FLAT), (S_T + 20, dict(bid=0.90, ask=0.905)), (CLOSE, FLAT)])
w = G.simulate(dip, [], CLOSE, "yes", 10)
assert w["rest_q"] == 10 and w["rest_mech"] == "quote" and near(G.rest_pnl(w), 10 * (1 - 0.91) - 0.06)
up = path([(S_T + 12, FLAT), (CLOSE, dict(bid=0.925, ask=0.93))])
assert G.simulate(up, [], CLOSE, "yes", 1)["rest_q"] == 0

# 7. chase cap: ask at S + 31 s over ask(S) + 1c skips; at the cap it walks only levels at or under the cap
hi = path([(S_T + 31, FLAT), (CLOSE, dict(bid=0.93, ask=0.935))])
w = G.simulate(hi, [], CLOSE, "yes", 1)
assert w["chase_status"] == "skip" and w["chase"] == [] and w["gf2_status"] == "skip" and G.gf1_pnl(w) == 0
cap = path([(S_T + 31, FLAT), (CLOSE, dict(bid=0.925, ask=0.93, asz=3.0, nbid=[(0.06, 50.0)]))])
w = G.simulate(cap, [], CLOSE, "yes", 10)
assert w["chase"] == [(0.93, 3.0)] and near(w["chase_unbought"], 7) and w["gf2"] == [(0.93, 3.0)]
# out of the band at the chase poll: no chase even under the cap
band = path([(S_T + 31, dict(bid=0.96, ask=0.965)), (CLOSE, dict(bid=0.965, ask=0.972))])
w = G.simulate(band, [], CLOSE, "yes", 1)
assert G.signal(band, CLOSE)[1].ask - 0.965 < 1e-9 and w["chase_status"] == "skip" and w["gf2_status"] == "skip"
# the chase poll is the first at or after S + 31.0 s (S + 32 on this grid): a move at S + 30 is not it
late = path([(S_T + 30, FLAT), (S_T + 32, dict(bid=0.93, ask=0.935)), (CLOSE, FLAT)])
assert G.simulate(late, [], CLOSE, "yes", 1)["chase_status"] == "cross"

# 8. the NO side: YES bid 0.06 -> NO ask 0.94, L = 0.93; a taker BUYING YES at 0.07 sells NO at 0.93 into our NO bid
nob = path([(CLOSE, dict(bid=0.06, ask=0.065, bsz=5.0, asz=5.0))])
side, S, _ = G.signal(nob, CLOSE)
assert side == "no" and near(S.ask, 0.94)
w = G.simulate(nob, [(S_T + 3, 0.07, 1, 1)], CLOSE, "no", 1)
assert w["side"] == "no" and w["L"] == 0.93 and w["rest_q"] == 1 and w["rest_mech"] == "at" and w["win"]
assert near(G.gf1_pnl(w), 1 - 0.93 - 0.01)
w = G.simulate(nob, [], CLOSE, "yes", 1)
assert w["chase"] == [(0.94, 1)] and not w["win"] and near(G.plain_pnl(w), -0.94 - 0.01)

# 9. plain L1 crosses at the first poll at or after S + 1.0 s, walking the asks; C = 10 fee rounded up per order
w = G.simulate(path([(CLOSE, dict(FLAT, asz=4.0, nbid=[(0.07, 50.0)]))]), [], CLOSE, "yes", 10)
assert [(round(p, 4), q) for p, q in w["plain"]] == [(0.92, 4.0), (0.93, 6.0)]
assert near(G.plain_pnl(w), 10 - (4 * 0.92 + 6 * 0.93) - R6.taker_fee(w["plain"]))

# 10. reports run on a synthetic set and the bar is not met by 3 windows; NOT_ENOUGH_DATA below 300
wins = []
for i in range(6):
    c = CLOSE + 86400 * i
    sh = lambda p, c=c: Poll(p.t - CLOSE + c, p.yb, p.ybs, p.nb, p.nbs)
    ps = [sh(p) for p in flat]
    tr = [(c - 360 + 10, 0.905, 1, -1)] if i % 2 else []
    wins.append((c, G.SERIES[i % 2], {C: G.simulate(ps, tr, c, "yes" if i % 3 else "no", C) for C in G.SIZES}, bool(tr)))
ok1, l1 = G.gf1_report(wins)
ok2, l2 = G.gf2_report(wins)
assert not ok1 and not ok2 and any("GOLD ALONE" in x for x in l1) and any("GOLD ALONE" in x for x in l2)
assert any("card gate" in x for x in l1) and any("card gate" in x for x in l2)

# 11. usable windows: L1Q1's coverage rule, and only windows opening before 2026-11-13 23:59 UTC
row = lambda c: {"ticker": "X", "series": "KXGOLD15M", "polls": "450", "ok_polls": "440", "max_gap_ms": "4000", "tape_pages": "3",
                 "note": "", "first_recv_ms": str(int((c - 899) * 1000)), "last_recv_ms": str(int((c - 1) * 1000)), "result": "yes"}
C6 = datetime(2026, 11, 5, 12, tzinfo=timezone.utc).timestamp()
assert G.usable(C6, row(C6)) and not G.usable(C6, dict(row(C6), result="")) and not G.usable(CLOSE, row(CLOSE))
last_ok = G.LAST_OPEN - 60 + 900                 # opens 23:58
assert G.usable(last_ok, row(last_ok)) and not G.usable(G.LAST_OPEN + 900, row(G.LAST_OPEN + 900))

# 12. refusals: before the read date; a second run (marker or result); after the date it writes NOT_ENOUGH_DATA once
tmp = Path(tempfile.mkdtemp())
G.RESULTS = {c: tmp / f"{c}_result.txt" for c in G.CARDS}
G.MARKERS = {c: tmp / f"gf12_{c}_started" for c in G.CARDS}
calls = []
R6.windows = lambda: calls.append(1) or {}
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    G.run("gf1", now=G.READ_NOT_BEFORE - 1)
assert "Refusing: the read date" in buf.getvalue() and not calls and not G.MARKERS["gf1"].exists()
for card in G.CARDS:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        G.run(card, now=G.READ_NOT_BEFORE + 1)
    assert G.MARKERS[card].exists() and "VERDICT NOT_ENOUGH_DATA" in G.RESULTS[card].read_text(), buf.getvalue()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        G.run(card, now=G.READ_NOT_BEFORE + 2)
    assert "Refusing to run again" in buf.getvalue()
G.RESULTS["gf1"].unlink()                         # a started run without a result is still refused
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    G.run("gf1", now=G.READ_NOT_BEFORE + 3)
assert "Refusing to run again" in buf.getvalue() and len(calls) == 2

# 13. readiness from book rows only: windows, the S poll and the signal side (prices only; no result column exists here)
hdr = lambda t: datetime.fromtimestamp(int(t), timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
ct = datetime.fromtimestamp(CLOSE, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
rows = []
for tk, ser, yb, nb in (("G-1", "KXGOLD15M", 0.915, 0.08), ("B-1", "KXBTC15M", 0.50, 0.48), ("E-1", "KXETH15M", 0.05, 0.935)):
    for t in range(int(OPEN), int(CLOSE), 2):
        rows.append({"t_recv_ms": str(t * 1000), "server_date_header": hdr(t - 0.5), "ticker": tk, "series": ser, "close_time": ct,
                     "yes_bid_px_1": str(yb), "no_bid_px_1": str(nb)})
bs = G.book_signals(rows)
assert bs["G-1"][2:] == [True, "yes"] and bs["B-1"][2:] == [True, ""] and bs["E-1"][2:] == [True, "no"], bs

print("GF12 (GF1, GF2) synthetic tests: all passed")
