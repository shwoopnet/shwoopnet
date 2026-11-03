"""MAKERMID1 forward command on synthetic books and tapes."""
import sys
sys.path.insert(0, __import__("os").path.dirname(__file__))
from _fwdutil import args, assert_rule_verbatim, marker  # noqa: E402

from scalper import fwdread as fr  # noqa: E402
from scalper import makermid1 as mm  # noqa: E402
from scalper import makertail1 as mt  # noqa: E402
from scalper import makermid1_fwd as fw  # noqa: E402

AFTER, BEFORE = fr.utc(2026, 11, 13), fr.utc(2026, 11, 5)


def synth(monkeypatch, n, dev_closes=4):
    polls, closes, trades, results = {}, {}, {}, {}
    k = 0

    def add(close, win):
        nonlocal k
        tk = f"T{k}"; k += 1
        t = close - 1505
        polls[tk] = [mt.Poll(t, [0.30], [10], [0.60], [10])]
        closes[tk] = close
        trades[tk] = [(t + 10, 0.29, 5, "no")]
        results[tk] = "yes" if win else "no"

    base = int(mt.FWD_FROM) + 3600
    for i in range(n):
        add(base + 3600 * i, i % 3 == 0)
    for i in range(dev_closes):
        add(int(mt.DEV_FROM) + 3600 * (i + 1), True)
        add(int(mt.HOLD_FROM) + 3600 * (i + 1), True)
    lo, hi = int(min(closes.values())) - 4000, int(max(closes.values())) + 4000
    monkeypatch.setattr(mt, "load", lambda: (polls, closes, trades, [float(x) for x in range(lo, hi, 30)]))
    monkeypatch.setattr(mt, "results", lambda: results)


def test_rule_is_verbatim():
    assert_rule_verbatim(fw.SPEC)


def test_refuses_early_and_waits_for_fills(tmp_path, monkeypatch, capsys):
    synth(monkeypatch, 160)
    assert fw.forward(args(tmp_path), now=BEFORE) == 2
    assert not marker(tmp_path, fw.SPEC).exists()
    synth(monkeypatch, 20)
    assert fw.forward(args(tmp_path), now=AFTER) == 2


def test_real_read_once_no_dev_holdout_and_no_bid_over_40c(tmp_path, monkeypatch, capsys):
    synth(monkeypatch, 160, dev_closes=6)
    assert fw.forward(args(tmp_path), now=AFTER) == 0
    out = capsys.readouterr().out
    assert "orders 160 fills 160" in out and "MR2" in out and "FWD-READ MAKERMID1F" in out
    assert all(x.price <= 0.40 for x in fw.forward_orders(4e9, True))
    assert fw.forward(args(tmp_path), now=AFTER) == 2


def test_run_refuses_a_second_dev_score():
    assert "refused: MAKERMID1 DEV was already scored once" in open(mm.__file__).read()
