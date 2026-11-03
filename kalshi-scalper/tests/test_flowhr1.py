"""FLOWHR1 on synthetic books and trades (no recorder data, no real outcome)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
from _fwdutil import args, assert_rule_verbatim, marker  # noqa: E402

from scalper import flowhr1 as fh  # noqa: E402
from scalper import flowhr1_fwd as fw  # noqa: E402
from scalper import fwdread as fr  # noqa: E402
from scalper import makertail1 as mt  # noqa: E402


def test_flow_mapping_taker_side_to_contract_side():
    L = 1000.0
    tr = [(L - 100, 0.10, 30, "yes"), (L - 90, 0.10, 10, "no")]
    assert abs(fh.signed_flow(tr, "yes", L) - 0.5) < 1e-9          # bought 30, sold 10
    assert abs(fh.signed_flow(tr, "no", L) + 0.5) < 1e-9           # exact mirror on the NO contract
    assert fh.signed_flow(tr, "yes", L) <= 1 and fh.signed_flow([(L - 700, .1, 5, "yes")], "yes", L) is None   # outside 10 minutes
    assert fh.signed_flow([(L + 1, .1, 5, "yes")], "yes", L) is None                                       # after the look
    # the threshold: exactly -0.036 is low flow
    t = fh.Tail("T", 0, "yes", .1, 20, 0, -0.036, False)
    assert t.group == "low"
    assert fh.Tail("T", 0, "yes", .1, 20, 0, -0.0359, False).group == "high"
    assert fh.Tail("T", 0, "yes", .1, 20, 0, None, False).group == "noflow"
    assert fh.Tail("T", 0, "yes", .1, 20, 0, None, True).group == "nodata"


def poll(t, yb=None, ys=None, nb=None, ns=None):
    return mt.Poll(t, [yb] if yb is not None else [], [ys] if ys else [], [nb] if nb is not None else [], [ns] if ns else [])


def test_candidate_cheap_side_only_and_one_per_side():
    close = 100000.0
    look = close - 1510
    tpolls = [float(x) for x in range(int(look) - 800, int(look) + 100, 30)]
    # YES ask = 1 - NO bid: NO bid 0.85 => YES ask 0.15 (cheap, eligible). NO ask = 1 - YES bid 0.15 => 0.85 (favourite, never selected)
    p = [poll(look, 0.15, 50, 0.85, 50), poll(close - 1498, 0.15, 50, 0.85, 50)]
    tr = [(look - 60, 0.15, 10, "no")]
    c = fh.candidates("A", close, p, tr, tpolls)
    assert [(t.side, t.ask) for t in c] == [("yes", 0.15)]
    assert abs(c[0].flow + 1.0) < 1e-9 and c[0].group == "low"
    # another strike with a higher ask under the cap wins the YES slot; one above 0.30 is never eligible
    c2 = fh.candidates("B", close, [poll(look, 0.7, 50, 0.72, 50), poll(close - 1498, 0.7, 50, 0.72, 50)], [], tpolls)   # YES ask 0.28, NO ask 0.30
    assert sorted((t.side, t.ask) for t in c2) == [("no", 0.30), ("yes", 0.28)]
    c3 = fh.candidates("C", close, [poll(look, 0.5, 50, 0.5, 50), poll(close - 1498, 0.5, 50, 0.5, 50)], [], tpolls)     # both asks 0.5
    assert c3 == []
    best = fh.select(c + c2)
    assert {(t.side): t.ticker for t in best} == {"yes": "B", "no": "B"} or len(best) == 2
    yes = [t for t in best if t.side == "yes"][0]
    assert yes.ask == 0.28
    # thin ask size is not eligible
    assert fh.candidates("D", close, [poll(look, 0.15, 5, 0.85, 5), poll(close - 1498, 0.15, 5, 0.85, 5)], [], tpolls) == []


def test_tape_hole_is_nodata_not_flow():
    close = 100000.0
    look = close - 1510
    tpolls = [float(x) for x in range(int(look) - 800, int(look) - 400, 30)]       # tape polls stop early
    p = [poll(look, 0.15, 50, 0.85, 50), poll(close - 1498, 0.15, 50, 0.85, 50)]
    c = fh.candidates("A", close, p, [(look - 60, 0.15, 10, "no")], tpolls)
    assert c[0].group == "nodata"


def test_net_and_verdict_words():
    t = fh.Tail("T", 0, "yes", 0.10, 20, 0, -0.5, False)
    t.won = False
    assert abs(fh.net(t) + 100 * (0.10 + mt.taker_fee_per_contract(0.10))) < 1e-9
    # under 150 low-flow trades is NOT_ENOUGH_DATA whatever the numbers
    ts = []
    for i in range(20):
        a = fh.Tail("T", 3600 * i, "yes", 0.10, 20, 0, -0.5, False)
        a.won = i % 2 == 0
        ts.append(a)
    assert fh.verdict(ts, 3600 * 10)[0] == "NOT_ENOUGH_DATA"


def synth(monkeypatch, n_low_win, n_low_lose, n_high):
    polls, closes, trades, results = {}, {}, {}, {}
    k = 0

    def add(close, flow_low, win):
        nonlocal k
        tk = f"T{k}"
        k += 1
        t = close - 1510
        polls[tk] = [poll(t, 0.15, 50, 0.85, 50), poll(close - 1498, 0.15, 50, 0.85, 50)]
        closes[tk] = close
        trades[tk] = [(t - 60, 0.15, 10, "no" if flow_low else "yes")]
        results[tk] = "yes" if win else "no"

    base = int(mt.FWD_FROM) + 3600
    i = 0
    for _ in range(n_low_win):
        add(base + 3600 * i, True, True); i += 1
    for _ in range(n_low_lose):
        add(base + 3600 * i, True, False); i += 1
    for _ in range(n_high):
        add(base + 3600 * i, False, False); i += 1
    for j in range(3):
        add(int(mt.DEV_FROM) + 3600 * (j + 1), True, True)       # DEV and HOLDOUT closes must never be read
        add(int(mt.HOLD_FROM) + 3600 * (j + 1), True, True)
    lo, hi = int(min(closes.values())) - 4000, int(max(closes.values())) + 4000
    tpolls = [float(x) for x in range(lo, hi, 30)]
    monkeypatch.setattr(mt, "load", lambda: (polls, closes, trades, tpolls))
    monkeypatch.setattr(mt, "results", lambda: results)


AFTER = fr.utc(2026, 12, 16)
BEFORE = fr.utc(2026, 11, 20)


def test_rule_is_verbatim():
    assert_rule_verbatim(fw.SPEC)


def test_forward_refuses_early_and_reads_dev_never(tmp_path, monkeypatch, capsys):
    synth(monkeypatch, 5, 40, 10)
    assert fw.forward(args(tmp_path), now=BEFORE) == 2
    assert "only" in capsys.readouterr().out and not marker(tmp_path, fw.SPEC).exists()
    assert fw.forward(args(tmp_path), now=AFTER) == 0
    out = capsys.readouterr().out
    assert "low-flow: n 45" in out and "NOT_ENOUGH_DATA" in out          # the 6 DEV/HOLDOUT closes are not in n
    assert fw.forward(args(tmp_path), now=AFTER) == 2                    # second read refused (marker)


def test_forward_reads_at_150(tmp_path, monkeypatch, capsys):
    synth(monkeypatch, 20, 135, 5)
    assert fw.forward(args(tmp_path), now=BEFORE) == 0
    assert "VERDICT: FALSIFIED" in capsys.readouterr().out
