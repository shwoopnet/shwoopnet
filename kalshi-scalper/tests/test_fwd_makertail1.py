"""MAKERTAIL1 forward command on synthetic books and tapes (no recorder data, no real outcome)."""
import sys
sys.path.insert(0, __import__("os").path.dirname(__file__))
from _fwdutil import args, assert_rule_verbatim, marker  # noqa: E402

from scalper import fwdread as fr  # noqa: E402
from scalper import makertail1 as mt  # noqa: E402
from scalper import makertail1_fwd as fw  # noqa: E402

AFTER = fr.utc(2026, 11, 13)
BEFORE = fr.utc(2026, 11, 5)


def synth(monkeypatch, n_yes, n_no, dev_closes=5):
    """n_yes YES-tail orders and n_no NO-tail orders after the forward start, plus `dev_closes` closes inside DEV and HOLDOUT that must never be read."""
    polls, closes, trades, results = {}, {}, {}, {}
    k = 0

    def add(side, close, win):
        nonlocal k
        tk = f"T{k}"; k += 1
        t = close - 1505
        polls[tk] = [mt.Poll(t, [0.05], [10], [], [])] if side == "yes" else [mt.Poll(t, [], [], [0.05], [10])]
        closes[tk] = close
        # a print through our price after the look fills the order even in the pessimistic bound
        trades[tk] = [(t + 10, 0.04, 5, "no")] if side == "yes" else [(t + 10, 0.96, 5, "yes")]
        results[tk] = side if win else ("no" if side == "yes" else "yes")
        return tk

    base = int(mt.FWD_FROM) + 3600
    for i in range(n_yes):
        add("yes", base + 3600 * i, i % 5 == 0)
    for i in range(n_no):
        add("no", base + 1800 + 3600 * i, i % 5 == 0)
    for i in range(dev_closes):
        add("yes", int(mt.DEV_FROM) + 3600 * (i + 1), True)                 # DEV
        add("yes", int(mt.HOLD_FROM) + 3600 * (i + 1), True)                # HOLDOUT
    lo = int(min(closes.values())) - 4000
    hi = int(max(closes.values())) + 4000
    tpolls = [float(x) for x in range(lo, hi, 30)]
    monkeypatch.setattr(mt, "load", lambda: (polls, closes, trades, tpolls))
    monkeypatch.setattr(mt, "results", lambda: results)
    return polls, closes


def test_rule_is_verbatim():
    assert_rule_verbatim(fw.SPEC)


def test_refuses_before_due_date_and_writes_nothing(tmp_path, monkeypatch, capsys):
    synth(monkeypatch, 160, 0)
    rc = fw.forward(args(tmp_path), now=BEFORE)
    out = capsys.readouterr().out
    assert rc == 2 and "not due until 2026-11-12" in out
    assert "the side result counts only if the COMBINED" in out          # the registered rule is printed first
    assert not marker(tmp_path, fw.SPEC).exists()


def test_force_info_is_information_only(tmp_path, monkeypatch, capsys):
    synth(monkeypatch, 160, 0)
    rc = fw.forward(args(tmp_path, "--force-info"), now=BEFORE)
    out = capsys.readouterr().out
    assert rc == 0 and "INFORMATION ONLY" in out and "pessimistic fills so far 31" in out   # only closes before the read time count
    assert not marker(tmp_path, fw.SPEC).exists() and not (tmp_path / "README.md").exists()


def test_waits_for_150_fills_even_after_the_date(tmp_path, monkeypatch, capsys):
    synth(monkeypatch, 20, 0)
    assert fw.forward(args(tmp_path), now=AFTER) == 2
    assert "whichever is later" in capsys.readouterr().out
    assert not marker(tmp_path, fw.SPEC).exists()


def test_real_read_then_second_read_refused_and_dev_holdout_never_read(tmp_path, monkeypatch, capsys):
    synth(monkeypatch, 160, 0, dev_closes=7)
    assert fw.forward(args(tmp_path), now=AFTER) == 0
    out = capsys.readouterr().out
    assert "resting orders" in out and "orders 160 fills 160" in out          # 160 forward orders; the 14 DEV/HOLDOUT closes are not in it
    assert "YES-side tails, pess" in out and "NO-side tails, opt" in out        # Amendment 1 split under both bounds
    assert "APPEND THIS EXACT LINE" in out and "FWD-READ MAKERTAIL1F 2026-11-13:" in out
    assert "SIDE CLAIM" in out and "NOT_ENOUGH_DATA" in out                       # only YES tails: fewer than 150 on the NO side
    assert marker(tmp_path, fw.SPEC).exists()
    assert fw.forward(args(tmp_path), now=AFTER) == 2
    assert "spent" in capsys.readouterr().out


def test_readme_line_blocks_a_second_read_even_if_data_was_lost(tmp_path, monkeypatch, capsys):
    synth(monkeypatch, 160, 0)
    (tmp_path / "README.md").write_text("x\nFWD-READ MAKERTAIL1F 2026-11-12: done\n")
    assert fw.forward(args(tmp_path), now=AFTER) == 2
    assert "README already holds a read line" in capsys.readouterr().out


def test_forward_orders_start_at_the_forward_boundary(monkeypatch):
    synth(monkeypatch, 3, 0, dev_closes=4)
    o = fw.forward_orders(4e9, True)
    assert len(o) == 3 and all(x.close >= mt.FWD_FROM for x in o)


def test_side_claim_needs_150_fills_on_each_side_and_positive_combined_and_no(monkeypatch):
    synth(monkeypatch, 150, 150)
    o = fw.forward_orders(4e9, True)
    word, detail = fw.side_claim(o)
    assert word == "CLAIM_COUNTS", detail
    yes_only = [x for x in o if x.side == "yes"]
    assert fw.side_claim(yes_only)[0] == "NOT_ENOUGH_DATA"
    # a NO side that loses (never wins) with enough fills: FALSIFIED
    for x in o:
        if x.side == "no":
            x.won = False
    assert fw.side_claim(o)[0] == "FALSIFIED"


def test_makertail1_forward_command_exists_and_run_still_refuses(tmp_path, monkeypatch):
    assert hasattr(mt, "main")
    src = open(mt.__file__).read()
    assert 'argv[1] == "forward"' in src and "refused: MAKERTAIL1 DEV was already scored once" in src
