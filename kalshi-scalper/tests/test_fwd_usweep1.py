"""USWEEP1 forward command with a fake scalper.recdaily (the real one is on the unmerged recorder branch)."""
import sys
import types
sys.path.insert(0, __import__("os").path.dirname(__file__))
from _fwdutil import args, assert_rule_verbatim, marker  # noqa: E402

from scalper import fwdread as fr  # noqa: E402
from scalper import usweep1 as us  # noqa: E402
from scalper import usweep1_fwd as fw  # noqa: E402

NOW = fr.utc(2026, 12, 20)


def fake(monkeypatch, n=45, ask=0.92, win=True, pre_freeze=3):
    rows = []
    for i in range(n):
        rows.append({"ticker": f"KXGOLDD-{i}", "series": "KXGOLDD", "close_ts": us.FWD_FREEZE + 86400 * (i + 1)})
    for i in range(pre_freeze):
        rows.append({"ticker": f"KXGOLDD-PRE{i}", "series": "KXGOLDD", "close_ts": us.FWD_FREEZE - 86400 * (i + 1)})
    results = {r["ticker"]: ("yes" if win else "no") for r in rows}
    m = types.ModuleType("scalper.recdaily")
    m.load_quotes = lambda d, series=None: rows
    m.load_results = lambda d: results
    m.tickers = lambda rs, s: [r["ticker"] for r in rs if r["series"] == s]

    def window(rs, res, tk, look):
        r = next(x for x in rs if x["ticker"] == tk)
        return {"series": r["series"], "ticker": tk, "close_ts": r["close_ts"], "candles": {r["close_ts"] - look * 60: (ask - 0.02, ask, 100)}, "result": res.get(tk)}
    m.usweep1_window = window
    monkeypatch.setitem(sys.modules, "scalper.recdaily", m)


def test_rule_is_verbatim():
    assert_rule_verbatim(fw.SPEC)


def test_refuses_without_owner_ruling_even_for_information(tmp_path, monkeypatch, capsys):
    fake(monkeypatch)
    for extra in ((), ("--force-info",)):
        assert fw.forward(args(tmp_path, *extra, "--daily-dir", "x"), now=NOW) == 2
        out = capsys.readouterr().out
        assert "OWNER RULING NEEDED" in out and "REFUSED: run with --owner-asked" in out
    assert not marker(tmp_path, fw.SPEC).exists()


def test_stops_clearly_when_recdaily_is_absent(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "scalper.recdaily", None)
    try:
        fw.forward(args(tmp_path, "--owner-asked", "--force-info", "--daily-dir", "x"), now=NOW)
    except SystemExit as e:
        assert "recdaily is not on this branch" in str(e)
    else:
        raise AssertionError("must stop")


def test_force_info_with_owner_asked_prints_counts_and_writes_nothing(tmp_path, monkeypatch, capsys):
    fake(monkeypatch, n=5)
    assert fw.forward(args(tmp_path, "--owner-asked", "--force-info", "--daily-dir", "x"), now=NOW) == 0
    out = capsys.readouterr().out
    assert "KXGOLDD: 5 forward fills so far" in out and not marker(tmp_path, fw.SPEC).exists()


def test_waits_for_40_fills(tmp_path, monkeypatch, capsys):
    fake(monkeypatch, n=10)
    assert fw.forward(args(tmp_path, "--owner-asked", "--daily-dir", "x"), now=NOW) == 2
    assert "no item has 40 fills yet" in capsys.readouterr().out


def test_real_read_ignores_pre_freeze_and_second_read_is_refused(tmp_path, monkeypatch, capsys):
    fake(monkeypatch, n=45, win=True)
    assert fw.forward(args(tmp_path, "--owner-asked", "--daily-dir", "x"), now=NOW) == 0
    out = capsys.readouterr().out
    assert "KXGOLDD: NOT_YET_FALSIFIED; fills 45" in out and "FWD-READ USWEEP1F 2026-12-20:" in out
    assert "not a lead whatever the sign" in out
    assert fw.forward(args(tmp_path, "--owner-asked", "--daily-dir", "x"), now=NOW) == 2


def test_losing_item_is_killed_at_40_fills(tmp_path, monkeypatch, capsys):
    fake(monkeypatch, n=45, win=False)
    assert fw.forward(args(tmp_path, "--owner-asked", "--daily-dir", "x"), now=NOW) == 0
    assert "KXGOLDD: FALSIFIED; fills 45" in capsys.readouterr().out


def test_judge_words():
    rows = [{"net1": 0.05}] * 39
    assert fw.judge(rows)[0] == "NOT_ENOUGH_DATA"
    assert fw.judge(rows + [{"net1": 0.05}])[0] == "NOT_YET_FALSIFIED"
    assert fw.judge([{"net1": -0.1}] * 40)[0] == "FALSIFIED"
