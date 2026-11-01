"""Plain assert tests for SPORTS-PRE (src/scalper/sportspre.py) on a SYNTHETIC fixture only: made-up games, quotes, ESPN figures and results.
No recorded row is used or fetched. Run with: cd kalshi-scalper && PYTHONPATH=src python tests/test_sportspre.py"""
import contextlib
import io
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import sportspre as S

# 1. the registered numbers: deflated z bar about 5.27, fees 7% x C x p x (1-p) rounded UP to the cent per order at C = 10
assert abs(S.Z_BAR - 5.27) < 0.01 and S.N_COUNT == 728696
assert abs(S.fee(0.50) - 0.18) < 1e-9          # 0.07 x 10 x 0.25 = 0.175 -> 18c
assert abs(S.fee(0.52) - 0.18) < 1e-9          # 0.17472 -> 18c (up, not nearest)
assert abs(S.fee(0.99) - 0.01) < 1e-9          # 0.693c rounds up to 1c
assert abs(S.fee(0.40, S.FEE_STRESS) - 0.21) < 1e-9     # 0.084 x 10 x 0.24 = 0.2016 -> 21c
assert abs(S.net_per_contract(0.40, 1.0) - (0.60 - 0.17 / 10)) < 1e-9       # 0.168 -> 17c per 10 contracts
assert abs(S.net_per_contract(0.40, 0.5) - (0.10 - 0.017)) < 1e-9           # a tie pays 0.50

# 2. fixture builders. Start times are fixed UTC seconds; every quote poll is 3,700 s before the start (inside T-75 .. T-60).
def ts(y, m, d, h=18):
    return datetime(y, m, d, h, tzinfo=timezone.utc).timestamp()

def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def make_game(i, start, league="KXNFLGAME", h_ask=0.30, a_ask=0.72, spread=0.01, h_size=50, a_size=50, hg=50.0, ag=50.0, poll_off=3700, espn=True, espn_http="200", event=True):
    gid = str(1000 + i)
    ev = "%s-G%d" % (league, i)
    g = {"job_ts_ms": 0, "league": league, "espn_id": gid, "start_iso": iso(start), "event_ticker": ev if event else "", "home_ticker": ev + "-H", "away_ticker": ev + "-A", "match": "ok" if event else "none"}
    pms = int((start - poll_off) * 1000)
    q = []
    for side, ask, size in (("home", h_ask, h_size), ("away", a_ask, a_size)):
        q.append({"poll_ts_ms": pms, "league": league, "espn_id": gid, "event_ticker": ev, "ticker": ev + ("-H" if side == "home" else "-A"), "side": side,
                  "yes_bid": round(ask - spread, 4), "yes_ask": ask, "yes_bid_size": 10, "yes_ask_size": size})
    p = []
    if espn:
        p.append({"recv_ms": pms + 5000, "league": league, "espn_id": gid, "kind": "core_predictor", "http": espn_http, "last_modified": iso(start - 7 * 3600), "home_gp": hg, "away_gp": ag})
    return g, q, p

def result(g, home_wins, hs=24, as_=17, tie=False):
    hr, ar = ("no", "no") if tie else (("yes", "no") if home_wins else ("no", "yes"))
    if tie:
        hs = as_ = 20
    elif not home_wins:
        hs, as_ = as_, hs
    return {"recv_ms": 0, "league": g["league"], "espn_id": g["espn_id"], "event_ticker": g["event_ticker"], "home_result": hr, "away_result": ar, "espn_state": "post",
            "espn_completed": "True", "home_score": hs, "away_score": as_, "resolved": 1}

START = ts(2026, 11, 8)

# 3. the look and the universe filters (Amendment 1 included)
cases = [make_game(0, START), make_game(1, START, spread=0.03), make_game(2, START, h_size=5), make_game(3, ts(2026, 10, 31)), make_game(4, START, espn=False),
         make_game(5, START, espn_http="400"), make_game(6, START, poll_off=3500), make_game(7, START, poll_off=5000), make_game(8, ts(2026, 12, 31)),
         make_game(9, START, event=False)]
games = [c[0] for c in cases]; quotes = [r for c in cases for r in c[1]]; pred = [r for c in cases for r in c[2]]
recs, drops = S.build_games(games, quotes, pred)
ids = {r["id"] for r in recs}
assert ids == {"1000", "1002"}, ids                         # 1001 spread 3c, 1003 before Nov 1, 1004/1005 no ESPN figure, 1006/1007 outside T-75..T-60, 1008 after the stop, 1009 unmatched (not a game record at all)
assert drops["no_espn_probability"] == 2 and drops["not_two_sided_or_spread"] == 1 and drops["no_poll"] == 2 and drops["outside_dates"] == 2
r0 = [r for r in recs if r["id"] == "1000"][0]
assert abs(r0["look_t"] - (START - 3700)) < 1e-6 and not r0["espn_recv_after_t60"] and r0["q"]["home"]["pE"] == 0.5

# the look is the LAST poll in the window; a later poll inside T-60 and an earlier one are not used
g, q, p = make_game(20, START)
q2 = [dict(x, poll_ts_ms=int((START - 4200) * 1000), yes_ask=0.60, yes_bid=0.59) for x in q]
p2 = [dict(p[0], recv_ms=int((START - 4200) * 1000) + 5000)]
r, _ = S.build_games([g], q + q2, p + p2)
assert abs(r[0]["q"]["home"]["ask"] - 0.30) < 1e-9
# an ESPN response more than 5 minutes from the Kalshi read is not paired
g, q, p = make_game(21, START)
p[0]["recv_ms"] += 400_000
assert S.build_games([g], q, p)[0] == []

# 4. the two rules. A buys the cheaper side if pE - ask >= 0.06 and ask size >= 10; B takes either side
def rec_of(h_ask, a_ask, hg, ag, h_size=50, a_size=50):
    g, q, p = make_game(30, START, h_ask=h_ask, a_ask=a_ask, hg=hg, ag=ag, h_size=h_size, a_size=a_size)
    return S.build_games([g], q, p)[0][0]
r = rec_of(0.30, 0.72, 40.0, 60.0)
assert S.signals(r) == {"A": "home", "B": "home"}           # gap home 0.10, away -0.12
r = rec_of(0.30, 0.72, 35.0, 65.0)
assert S.signals(r) == {"A": None, "B": None}               # gap home 0.05 < 0.06, away -0.07
r = rec_of(0.30, 0.50, 33.0, 67.0)
assert S.signals(r) == {"A": None, "B": "away"}             # cheaper side has gap 0.03; the dearer side has 0.17: only B takes it
r = rec_of(0.30, 0.50, 36.0, 64.0)
assert S.signals(r) == {"A": "home", "B": "away"}           # A: cheaper home gap 0.06 (exactly at the bar); B: the larger gap
r = rec_of(0.30, 0.72, 40.0, 60.0, h_size=9)
assert S.signals(r) == {"A": None, "B": None}               # ask size under 10 contracts: C = 10 is not real
r = rec_of(0.50, 0.50, 58.0, 42.0)
assert S.signals(r)["A"] == "home"                          # an ask tie goes to the larger gap

# 5. COUNT cannot leak an outcome: it never loads results, and its text holds no outcome, Brier, PF or PnL
loaded = []
def fake_load(kind):
    loaded.append(kind)
    if kind == "results":
        raise AssertionError("count opened the results")
    return {"games": games, "quotes": quotes, "predictor": pred}[kind]
S.load = fake_load
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    assert S.count() == 0
text = buf.getvalue()
assert "results" not in loaded and set(loaded) == {"games", "quotes", "predictor"}
for word in ("brier", "pf ", "pnl", "net ", "win", "won", "lost", "verdict", "result"):
    assert word not in text.lower(), word
assert "universe 2" in text and "KXNFLGAME" in text and "2026-11-08" in text
# count output is the same whatever the outcomes would be (it never sees them)
assert S.count_report(games, quotes, pred) == S.count_report(games, quotes, pred)

# 6. READ refuses before 2027-01-01 12:00 UTC, writes nothing, and a second run refuses
with tempfile.TemporaryDirectory() as d:
    S.RESULT_TXT, S.RESULT_MD, S.MARKER = Path(d) / "r.txt", Path(d) / "r.md", Path(d) / "started"
    S.load = fake_load        # would raise on results: an early refusal must not even load
    for early in (datetime(2027, 1, 1, 11, 59, tzinfo=timezone.utc), datetime(2026, 12, 31, tzinfo=timezone.utc), datetime(2026, 11, 20, tzinfo=timezone.utc)):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            assert S.run(now=early.timestamp()) is None
        assert "Refusing: the read date is 2027-01-01 12:00 UTC" in buf.getvalue()
        assert not S.RESULT_TXT.exists() and not S.MARKER.exists()
    # after the date, below 200 trades: NOT_ENOUGH_DATA, and a second run refuses
    S.load = lambda kind: {"games": games, "quotes": quotes, "predictor": pred, "results": [result(games[0], True)]}[kind]
    with contextlib.redirect_stdout(io.StringIO()):
        v = S.run(now=S.READ_NOT_BEFORE + 1)
    assert v == "NOT_ENOUGH_DATA" and S.RESULT_TXT.exists() and "SPORTSPRE VERDICT NOT_ENOUGH_DATA" in S.RESULT_TXT.read_text()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert S.run(now=S.READ_NOT_BEFORE + 2) is None
    assert "Refusing to run again" in buf.getvalue()

# 7. outcomes: a Kalshi result ESPN disagrees with, an unsettled game and a tie
g1, g2, g3, g4 = (make_game(40 + i, START)[0] for i in range(4))
pay, left = S.outcomes([result(g1, True), dict(result(g2, True), home_score=3, away_score=9), dict(result(g3, True), resolved=0), result(g4, False, tie=True)])
assert pay[("KXNFLGAME", g1["espn_id"])] == 1.0 and left == {"espn_disagrees_or_not_final": 1, "not_settled": 1}
assert ("KXNFLGAME", g2["espn_id"]) not in pay and ("KXNFLGAME", g3["espn_id"]) not in pay and pay[("KXNFLGAME", g4["espn_id"])] == 0.5
# a tie pays each side 0.50
rec = rec_of(0.30, 0.72, 40.0, 60.0)
tr = S.trades_of([rec], {("KXNFLGAME", rec["id"]): 0.5}, "A")
assert abs(tr[0][2] - S.net_per_contract(0.30, 0.5)) < 1e-9

# 8. a full synthetic read. 300 games over Nov 1 to Dec 30, the home side (ask 0.30, ESPN 50) wins 80%: both tries trade it; ESPN beats the market on Brier
def dataset(win_rule, n=300, hg=50.0):
    G, Q, P, R = [], [], [], []
    for i in range(n):
        start = ts(2026, 11, 1) + (i % 60) * 86400 + (i % 4) * 3600
        g, q, p = make_game(100 + i, start, hg=hg, ag=100 - hg)
        G.append(g); Q += q; P += p; R.append(result(g, win_rule(i)))
    return G, Q, P, R
G, Q, P, R = dataset(lambda i: i % 5 != 0)
v, lines = S.score(G, Q, P, R)
txt = "\n".join(lines)
assert "Try A:" in txt and "Try B:" in txt and "rule 1 passes" in txt, txt
assert v in ("NOT_YET_FALSIFIED", "FALSIFIED")
sa = S.try_stats(S.trades_of(S.build_games(G, Q, P)[0], S.outcomes(R)[0], "A"))
assert sa["n"] == 300 and sa["n_h1"] + sa["n_h2"] == 300 and sa["n_h1"] > 100 and sa["n_h2"] > 100
assert sa["z"] > S.Z_BAR and sa["pf_h1"] > 1.2 and sa["pf_h2"] > 1.2 and sa["pf_stress"] > 1.0
assert v == "NOT_YET_FALSIFIED" and "AUDIT FIRST" in txt           # a mean above +3c is an audit trigger first

# the market beats ESPN on Brier (ESPN 50 / 50 while the home side wins 95%, market mid 0.29 is worse; flip: market 0.70, ESPN 50) -> rule 1 FALSIFIED
G2, Q2, P2, R2 = [], [], [], []
for i in range(300):
    start = ts(2026, 11, 1) + (i % 60) * 86400
    g, q, p = make_game(500 + i, start, h_ask=0.70, a_ask=0.31, hg=78.0, ag=22.0)       # ESPN sees a big favourite; the market 0.70 is closer to a 70% truth
    G2.append(g); Q2 += q; P2 += p; R2.append(result(g, i % 10 < 7))
v2, l2 = S.score(G2, Q2, P2, R2)
assert v2 == "FALSIFIED" and "rule 1" in "\n".join(l2) and "FAILS" in "\n".join(l2)

# fewer than 200 trades with Brier passing: NOT_ENOUGH_DATA; PF under 1.2 in a half: FALSIFIED (rule 2)
Gs, Qs, Ps, Rs = dataset(lambda i: i % 5 != 0, n=150)
assert S.score(Gs, Qs, Ps, Rs)[0] == "NOT_ENOUGH_DATA"
st = {"n": 300, "pf_h1": 1.1, "pf_h2": 2.0, "z": 9.0, "pf_stress": 1.5}
w, why = S.try_verdict(st, False)
assert w == "FALSIFIED" and "rule 2" in why[0]
assert S.try_verdict(dict(st, pf_h1=2.0, z=2.9), False)[0] == "FALSIFIED"            # rule 4
assert S.try_verdict(dict(st, pf_h1=2.0, z=5.0), False)[0] == "FALSIFIED"            # rule 5 (under 5.27)
assert S.try_verdict(dict(st, pf_h1=2.0, pf_stress=0.9), False)[0] == "FALSIFIED"    # rule 6
assert S.try_verdict(dict(st, pf_h1=2.0), False)[0] == "NOT_YET_FALSIFIED"
assert S.try_verdict(dict(st, n=199, pf_h1=2.0), False)[0] == "NOT_ENOUGH_DATA"

# 9. audit (c): an NBA whose predictor is re-read after the game with a different figure in over 5% of games is dropped from the verdict
G3, Q3, P3, R3 = [], [], [], []
for i in range(100):
    start = ts(2026, 11, 1) + (i % 60) * 86400
    g, q, p = make_game(900 + i, start, league="KXNBAGAME")
    G3.append(g); Q3 += q; P3 += p; R3.append(result(g, True))
    P3.append({"recv_ms": 1, "league": "KXNBAGAME", "espn_id": g["espn_id"], "kind": "core_predictor_post", "http": "200", "last_modified": "", "home_gp": 70.0 if i < 10 else 50.0, "away_gp": 30.0 if i < 10 else 50.0})
assert S.audit_c(P3, S.build_games(G3, Q3, P3)[0])["KXNBAGAME"][:2] == (10, 100)
v3, l3 = S.score(G3, Q3, P3, R3)
assert "NBA DROPPED" in "\n".join(l3) and v3 == "NOT_ENOUGH_DATA"
print("test_sportspre: all passed")
