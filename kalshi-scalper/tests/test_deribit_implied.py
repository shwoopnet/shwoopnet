"""Plain assert tests for DERIBIT-IMPLIED (src/scalper/deribit_implied.py) on a SYNTHETIC fixture only: made-up quotes, made-up option rows, made-up results.
No recorded Deribit row is used. Run with: cd kalshi-scalper && PYTHONPATH=src python tests/test_deribit_implied.py"""
import contextlib
import gzip
import io
import csv
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import deribit_implied as D

CLOSE = int(datetime(2026, 11, 13, 3, 0, tzinfo=timezone.utc).timestamp())   # 03:00 UTC; the next Deribit expiry is 13NOV26 08:00 UTC
CT = "2026-11-13T03:00:00Z"
LOOK_TS = (CLOSE - 2700) * 1000                                              # exactly 45:00 left
S0 = 80000.0


def gz(cols, rows):
    b = io.StringIO()
    w = csv.writer(b)
    w.writerow(cols)
    w.writerows(rows)
    return gzip.compress(b.getvalue().encode())


class Mem:
    """Dict-backed source with the GitSource interface. `forbid` names a file kind that must never be opened."""
    def __init__(self, files, forbid=None):
        self.files, self.forbid, self.opened = files, forbid, []

    def names(self):
        return list(self.files)

    def blob(self, path):
        self.opened.append(path)
        if self.forbid and path.endswith(self.forbid):
            raise AssertionError("opened " + path)
        raw = self.files.get(path)
        return list(csv.DictReader(io.TextIOWrapper(gzip.open(io.BytesIO(raw))))) if raw else []


KC = ["poll_ts_local_ms", "server_date_header", "close_time", "ticker", "strike", "yes_bid", "yes_ask", "no_bid", "no_ask", "last_price", "open_interest", "volume"]
DC = ["poll_ts_local_ms", "deribit_us_out", "close_time", "expiry_rank", "instrument_name", "strike", "kind", "mark_iv", "underlying_price", "underlying_index",
      "bid_price", "ask_price", "mark_price", "open_interest", "creation_timestamp"]
IC = ["poll_ts_local_ms", "deribit_us_out", "close_time", "index_price"]
RC = ["poll_ts_local_ms", "close_time", "ticker", "strike", "result", "expiration_value"]


def deribit(ts, iv=40.0, skew=0.0):
    rows = []
    for k in range(70000, 90001, 1000):
        kind = "P" if k < S0 else "C"
        rows.append([ts, 1, CT, 1, "BTC-13NOV26-%d-%s" % (k, kind), k, kind, iv + skew * (k - S0) / 1000.0, S0, S0, 0, 0, 0, 1, ts])
        rows.append([ts, 1, CT, 1, "BTC-13NOV26-%d-%s" % (k, "C" if kind == "P" else "P"), k, "C" if kind == "P" else "P", 99, S0, S0, 0, 0, 0, 1, ts])  # in the money: ignored
        rows.append([ts, 1, CT, 2, "BTC-14NOV26-%d-%s" % (k, kind), k, kind, iv, S0, S0, 0, 0, 0, 1, ts])
    return rows


def kalshi(ts, strikes_quotes):
    return [[ts, "Fri", CT, "KXBTCD-X-T%d" % k, k, b, a, 1 - a, 1 - b, 0.5, 1, 1] for k, b, a in strikes_quotes]


def files(quotes, result_rows=(), ts=LOOK_TS, iv=40.0, run="deribit/2026-11-13/0000/"):
    return {run + "coverage.csv.gz": gz(["close_time"], [[CT]]),
            run + "kalshi.csv.gz": gz(KC, kalshi(ts, quotes)),
            run + "deribit.csv.gz": gz(DC, deribit(ts, iv)),
            run + "index.csv.gz": gz(IC, [[ts, 1, CT, S0]]),
            run + "results.csv.gz": gz(RC, list(result_rows))}


# 1. fees: 7% x C x p x (1-p) rounded UP to the cent per order at C = 10
assert abs(D.fee(0.5) - 0.18) < 1e-12            # 0.175 -> 0.18
assert abs(D.fee(0.9) - 0.07) < 1e-12            # 0.063 -> 0.07
assert abs(D.fee(0.2) - 0.12) < 1e-12            # 0.112 -> 0.12
assert abs(D.net_pnl("yes", 0.50, "yes") - (5.0 - 0.18)) < 1e-9 and abs(D.net_pnl("yes", 0.50, "no") - (-5.0 - 0.18)) < 1e-9
assert abs(D.net_pnl("no", 0.40, "no") - (6.0 - D.fee(0.40))) < 1e-9 and D.net_pnl("no", 0.40, "yes") < -4.0
assert D.net_pnl("yes", 0.5, "yes", 1.2) < D.net_pnl("yes", 0.5, "yes")      # the x1.2 line costs more

# 2. the model: flat vol gives P_A = P_B; a skew moves only P_B; no extrapolation outside the listed strikes
ci = D.curve_inputs([dict(zip(D.__dict__.get("_c", DC), r)) for r in deribit(LOOK_TS)], S0, CLOSE * 1000)
ivs, f_t, tau_t = ci
assert abs(ivs[70000] - 0.40) < 1e-12 and 0 < tau_t < 1 / 365 and abs(f_t / S0 - 1) < 1e-9
pa, pb = D.probabilities(80000.0, ivs, f_t, tau_t)
assert 0.49 < pa < 0.5 and abs(pa - pb) < 1e-12
rows_skew = [dict(zip(DC, r)) for r in deribit(LOOK_TS, skew=0.5)]
ivs2, f2, t2 = D.curve_inputs(rows_skew, S0, CLOSE * 1000)
pa2, pb2 = D.probabilities(80500.0, ivs2, f2, t2)
assert abs(pb2 - pa2) > 1e-4                      # the skew correction does something
assert D.probabilities(95000.0, ivs, f_t, tau_t) is None and D.probabilities(65000.0, ivs, f_t, tau_t) is None
assert D.probabilities(90000.0, ivs, f_t, tau_t) is not None      # the top strike itself is priced with the pair below
assert D.probabilities(85000.0, ivs, f_t, tau_t)[0] < 0.1 < 0.9 < D.probabilities(75000.0, ivs, f_t, tau_t)[0]
assert 0.001 <= D.probabilities(89000.0, ivs2, f2, t2)[1] <= 0.999

# 3. the universe screen: within 3%, two-sided, spread at most 4c
q = [dict(zip(KC, r)) for r in kalshi(LOOK_TS, [(80000, 0.48, 0.52), (80500, 0.40, 0.45), (81000, 0.0, 0.5), (81500, 0.5, 1.0), (90000, 0.4, 0.42), (79000, 0.5, 0.54)])]
assert [u[0] for u in D.universe_rows(q, S0)] == [80000, 79000]      # 80500 spread 5c, 81000 no bid, 81500 no ask, 90000 beyond 3%

# 4. the rule: larger edge wins, at least 5c; NO uses 1 - yes_bid; the tie goes to the strike nearer S0
uni = [(80000.0, "A", 0.40, 0.42), (81000.0, "B", 0.30, 0.32)]
t = D.pick_trade(uni, {80000.0: 0.60, 81000.0: 0.60}, S0)
assert t[0] == "yes" and t[1] == 81000.0 and abs(t[4] - 0.28) < 1e-9     # edge 0.28 beats 0.18
assert D.pick_trade(uni, {80000.0: 0.45, 81000.0: 0.33}, S0) is None      # edges 0.03 and 0.01: under 5c
no = D.pick_trade([(80000.0, "A", 0.70, 0.72)], {80000.0: 0.50}, S0)      # NO ask 0.30, (1 - 0.5) - 0.30 = 0.20
assert no[0] == "no" and abs(no[3] - 0.30) < 1e-9 and abs(no[4] - 0.20) < 1e-9
tie = D.pick_trade([(81000.0, "B", 0.40, 0.42), (79000.0, "C", 0.40, 0.42), (80500.0, "D", 0.40, 0.42)], {81000.0: 0.6, 79000.0: 0.6, 80500.0: 0.6}, S0)
assert tie[1] == 80500.0                          # equal edges: nearest S0
tie2 = D.pick_trade([(81000.0, "B", 0.40, 0.42), (79000.0, "C", 0.40, 0.42)], {81000.0: 0.6, 79000.0: 0.6}, S0)
assert tie2[1] == 79000.0                         # equal edge and distance: the lower strike

# 5. the look: only the 44:30 to 45:29 minute selects; other minutes are ignored
assert D.in_look(CLOSE, (CLOSE - 2670) * 1000) and D.in_look(CLOSE, (CLOSE - 2729) * 1000)
assert not D.in_look(CLOSE, (CLOSE - 2669) * 1000) and not D.in_look(CLOSE, (CLOSE - 2731) * 1000) and not D.in_look(CLOSE, (CLOSE - 1800) * 1000)
early = Mem(files([(80000, 0.40, 0.42)], ts=(CLOSE - 3000) * 1000))
assert D.load_looks(early) == {}

# 6. count cannot leak an outcome: the results file is never opened, and the output carries no result words
res = [[LOOK_TS, CT, "KXBTCD-X-T80000", 80000, "yes", 80100]]
mem = Mem(files([(80000, 0.40, 0.42), (80500, 0.10, 0.12)], res), forbid="results.csv.gz")
out = []
n = D.count(mem, out=out.append)
text = "\n".join(out)
assert not any(p.endswith("results.csv.gz") for p in mem.opened) and mem.opened
for bad in ("result", "pnl", "win rate", "won", "profit", "brier", "pf ", "settled:"):
    assert bad not in text.lower().replace("nothing settled is read", ""), bad
assert set(n) == {"A", "B"} and "dates (UTC) 2026-11-13 to 2026-11-13" in text and "nothing settled is read" in text
assert "KXBTCD-X-T80000" not in text and "yes" not in text.split("\n")[2].lower()
# the same count with the settled results changed gives the same numbers
mem2 = Mem(files([(80000, 0.40, 0.42), (80500, 0.10, 0.12)], [[LOOK_TS, CT, "KXBTCD-X-T80000", 80000, "no", 79000]]))
out2 = []
assert D.count(mem2, out=out2.append) == n and out2 == out
# a flat 40% surface with a quote 20c under the model buys YES: one qualifying trade per try
assert n["A"] == 1 and n["B"] == 1

# 7. the read refuses before 2027-01-01 00:00 UTC, writes nothing; a second run refuses
early_now = datetime(2026, 12, 31, 23, 59, tzinfo=timezone.utc).timestamp()
with tempfile.TemporaryDirectory() as d:
    D.RESULT_TXT, D.RESULT_MD, D.MARKER = Path(d) / "r.txt", Path(d) / "r.md", Path(d) / "started"
    buf = io.StringIO()
    called = []
    with contextlib.redirect_stdout(buf):
        assert D.run(now=early_now, src=Mem(files([(80000, 0.40, 0.42)]), forbid="results.csv.gz"), fetch_fn=lambda c: called.append(c)) is None
    assert "Refusing: the read date is 2027-01-01 00:00 UTC" in buf.getvalue()
    assert not D.RESULT_TXT.exists() and not D.MARKER.exists() and not called
    # after the date, 1 trade is under 150: NOT_ENOUGH_DATA for both tries, and the result file exists
    with contextlib.redirect_stdout(io.StringIO()):
        v = D.run(now=D.READ_NOT_BEFORE + 1, src=Mem(files([(80000, 0.40, 0.42)], res)), held_fn=lambda cs: {}, fetch_fn=lambda c: {})
    assert v == {"A": "NOT_ENOUGH_DATA", "B": "NOT_ENOUGH_DATA"} and D.RESULT_TXT.exists() and "NOT_ENOUGH_DATA" in D.RESULT_TXT.read_text()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert D.run(now=D.READ_NOT_BEFORE + 2) is None
    assert "Refusing to run again" in buf.getvalue()

# 8. the halves: the recorded span split at its midpoint date
assert D.span_halves(["2026-11-01", "2026-11-09", "2026-11-05"]) == ("2026-11-01", "2026-11-05", "2026-11-09")
assert D.span_halves(["2026-11-01", "2026-11-04"]) == ("2026-11-01", "2026-11-02", "2026-11-04")

# 9. verdicts: synthetic trades (never recorded ones). 200 trades over 40 dates, mostly small wins
def mk(n, days, win=0.5, loss=-0.2, every=5, first="2026-11-01"):
    out = []
    for i in range(n):
        dd = datetime.fromisoformat(first).toordinal() + i % days
        pnl = loss if i % every == 0 else win
        out.append({"date": datetime.fromordinal(dd).date().isoformat(), "pnl": pnl, "pnl_stress": pnl - 0.01})
    return out
span = ("2026-11-01", "2026-11-20", "2026-12-10")
good = (0.10, 0.05, 500)       # (Kalshi Brier, Deribit Brier, n): Deribit better
v, _ = D.judge(mk(149, 40), good, span, "A")
assert v == "NOT_ENOUGH_DATA"                                           # checked first, even with a failing Brier
v, _ = D.judge(mk(149, 40), (0.05, 0.10, 500), span, "A")
assert v == "NOT_ENOUGH_DATA"
v, L = D.judge(mk(400, 40), good, span, "A")
assert v == "NOT_YET_FALSIFIED", L
v, L = D.judge(mk(400, 40), (0.10, 0.10, 500), span, "A")               # Kalshi Brier at or below Deribit's: tie is falsified
assert v == "FALSIFIED" and "Brier" in L[-1]
v, L = D.judge(mk(400, 40), (0.09, 0.10, 500), span, "A")
assert v == "FALSIFIED"
weak_half = [dict(x, pnl=(-1.0 if x["date"] > span[1] and i % 2 else x["pnl"])) for i, x in enumerate(mk(400, 40))]
v, L = D.judge(weak_half, good, span, "A")
assert v == "FALSIFIED" and "second half" in L[-1]
v, L = D.judge(mk(400, 40, win=0.02, loss=-0.01, every=2), good, span, "A")    # PF 2 but z far below the deflated bar
assert v == "FALSIFIED"
assert 5.2 < D.z_bar() < 5.35
v, L = D.judge(mk(400, 1, win=0.5, loss=-0.4, every=2), good, span, "A")       # one day: clustering kills z
assert v == "FALSIFIED"

# 10. the Brier set is every universe strike at the look, with the strike's own result
looks = D.load_looks(Mem(files([(80000, 0.48, 0.52), (79000, 0.55, 0.58)])))
b = D.brier_of(looks, {CLOSE: {80000.0: "yes", 79000.0: "no"}})
assert b["A"][2] == 2 and 0 <= b["A"][0] <= 1 and 0 <= b["A"][1] <= 1
assert abs(b["A"][0] - (((0.5 - 1) ** 2 + (0.565 - 0) ** 2) / 2)) < 1e-9
assert D.brier_of(looks, {})["A"][2] == 0
print("test_deribit_implied: all passed")
