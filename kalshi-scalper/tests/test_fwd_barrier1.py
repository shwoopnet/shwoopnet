"""BARRIER1 forward command with a fake scalper.recdaily and a fake OKX series."""
import sys
import types
sys.path.insert(0, __import__("os").path.dirname(__file__))
from _fwdutil import args, assert_rule_verbatim, marker  # noqa: E402

from scalper import barrier1 as b1  # noqa: E402
from scalper import barrier1_fwd as fw  # noqa: E402
from scalper import fwdread as fr  # noqa: E402

DUE = fr.utc(2027, 11, 1)
OPEN = int(fr.utc(2026, 11, 10).timestamp())


def okx(inst, lo, hi):
    return {h: 100.0 + (h // 3600 % 7) for h in range(lo // 3600 * 3600, hi + 7200, 3600)}


def fake(monkeypatch, n=45, pre=3, res="no"):
    rows, results = [], {}
    days = [(m, d) for m in ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG") for d in range(1, 29)]
    for i in range(n + pre):
        mon, d = days[i]
        op = OPEN + 86400 * i if i < n else int(fw.FWD_FREEZE.timestamp()) - 86400 * (i - n + 1)
        tk = f"KXBTCMAXMON-27{mon}{d:02d}-T200"
        rows.append({"ticker": tk, "series": "KXBTCMAXMON", "event_ticker": tk.rsplit("-", 1)[0], "open_ts": op, "close_ts": op + 86400 * 30, "strike_type": "greater",
                     "floor_strike": 120.0, "cap_strike": None, "yes_bid": 0.15, "yes_ask": 0.20, "poll_ts": op + 2880 * 60})
        results[tk] = res
    m = types.ModuleType("scalper.recdaily")
    m.load_quotes = lambda d, series=None: rows
    m.load_results = lambda d: results
    m.nearest_to_look = lambda rs, tk, minutes_after_open=None, **k: next(r for r in rs if r["ticker"] == tk)
    monkeypatch.setitem(sys.modules, "scalper.recdaily", m)


def test_rule_is_verbatim():
    assert_rule_verbatim(fw.SPEC)


def test_refuses_before_the_october_2027_event(tmp_path, monkeypatch, capsys):
    fake(monkeypatch)
    assert fw.forward(args(tmp_path, "--daily-dir", "x"), now=fr.utc(2027, 10, 31), okx=okx) == 2
    out = capsys.readouterr().out
    assert "not due until 2027-11-01" in out and "2027 event or 40 fills, whichever is later." in out
    assert not marker(tmp_path, fw.SPEC).exists()


def test_force_info_writes_nothing(tmp_path, monkeypatch, capsys):
    fake(monkeypatch)
    assert fw.forward(args(tmp_path, "--force-info"), now=fr.utc(2026, 11, 11), okx=okx) == 0
    assert "INFORMATION ONLY" in capsys.readouterr().out and not marker(tmp_path, fw.SPEC).exists()


def test_needs_40_fills_after_the_date(tmp_path, monkeypatch, capsys):
    fake(monkeypatch, n=10)
    assert fw.forward(args(tmp_path, "--daily-dir", "x"), now=DUE, okx=okx) == 2
    assert "forward fills; the registered read" in capsys.readouterr().out


def test_real_read_excludes_pre_freeze_events_and_is_not_repeatable(tmp_path, monkeypatch, capsys):
    fake(monkeypatch, n=45, pre=3)
    rows, drop = fw.build(sys.modules["scalper.recdaily"], sys.modules["scalper.recdaily"].load_quotes("x"), sys.modules["scalper.recdaily"].load_results("x"), okx)
    assert len(rows) == 45
    assert fw.forward(args(tmp_path, "--daily-dir", "x"), now=DUE, okx=okx) == 0
    out = capsys.readouterr().out
    assert "BAR-CHEAP: NOT_ENOUGH_DATA; n 45" in out and "BAR-RICH" in out and "FWD-READ BARRIER1F 2027-11-01:" in out
    assert fw.forward(args(tmp_path, "--daily-dir", "x"), now=DUE, okx=okx) == 2


def test_judge_words():
    assert fw.judge([{"net": 0.1}] * 149) == "NOT_ENOUGH_DATA"
    assert fw.judge([{"net": -0.1}] * 150) == "FALSIFIED"
    assert fw.judge([{"net": 0.5}] * 100 + [{"net": -0.1}] * 50) == "NOT_YET_FALSIFIED"
