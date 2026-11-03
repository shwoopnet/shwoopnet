"""COUNT2 forward command: gates and event selection on synthetic data (no SPC file, no candle, no market result of the real series)."""
import sys
sys.path.insert(0, __import__("os").path.dirname(__file__))
from _fwdutil import args, assert_rule_verbatim, marker  # noqa: E402

from scalper import count2 as c2  # noqa: E402
from scalper import count2_fwd as fw  # noqa: E402
from scalper import fwdread as fr  # noqa: E402


def mk(ev, close, strike, res="no", opened="2026-11-01T05:00:00Z"):
    return {"event_ticker": ev, "ticker": f"{ev}-{strike}", "close_time": close, "open_time": opened, "floor_strike": strike, "strike_type": "greater", "result": res}


def test_rule_is_verbatim():
    assert_rule_verbatim(fw.SPEC)


def test_refuses_without_a_development_result(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(fw, "WORKERS", tmp_path)
    assert fw.forward(args(tmp_path), now=fr.utc(2030, 1, 1)) == 2
    out = capsys.readouterr().out
    assert "COUNT2_RESULT.md does not exist" in out and "Nothing was read" in out
    (tmp_path / "COUNT2_RESULT.md").write_text("verdict FALSIFIED")
    assert fw.forward(args(tmp_path), now=fr.utc(2030, 1, 1)) == 2
    assert "does not record NOT_ENOUGH_DATA" in capsys.readouterr().out
    assert not marker(tmp_path, fw.SPEC).exists()


def test_refuses_before_first_look_and_before_40_trades(tmp_path, monkeypatch, capsys):
    (tmp_path / "COUNT2_RESULT.md").write_text("Verdict NOT_ENOUGH_DATA")
    monkeypatch.setattr(fw, "WORKERS", tmp_path)
    monkeypatch.setattr(fw, "all_trades", lambda: [{"month": "2026-11", "net": 0.1}] * 10)
    assert fw.forward(args(tmp_path), now=fr.utc(2026, 11, 10)) == 2
    assert "not due until 2026-11-16" in capsys.readouterr().out
    assert fw.forward(args(tmp_path), now=fr.utc(2026, 11, 20)) == 2
    assert "only 10 forward trades" in capsys.readouterr().out


def test_real_read_once(tmp_path, monkeypatch, capsys):
    (tmp_path / "COUNT2_RESULT.md").write_text("Verdict NOT_ENOUGH_DATA")
    monkeypatch.setattr(fw, "WORKERS", tmp_path)
    monkeypatch.setattr(fw, "all_trades", lambda: [{"month": f"2026-{i:02d}", "net": -0.05} for i in range(40)])
    assert fw.forward(args(tmp_path), now=fr.utc(2027, 3, 1)) == 0
    out = capsys.readouterr().out
    assert "COUNT2 FORWARD NOT_ENOUGH_DATA" in out and "FWD-READ COUNT2F 2027-03-01:" in out
    assert fw.forward(args(tmp_path), now=fr.utc(2027, 3, 1)) == 2


def test_forward_events_exclude_the_development_universe():
    ms = [mk("KXTORNADO-26SEP", "2026-10-01T03:59:00Z", 100), mk("KXTORNADO-26OCT", "2026-11-01T03:59:00Z", 100), mk("KXTORNADO-26NOV", "2026-12-01T04:59:00Z", 100)]
    ev = fw.forward_events(ms)
    assert [e for _, e, _ in ev] == ["KXTORNADO-26NOV"] and ev[0][0] == (2026, 11)


def test_event_trades_applies_the_frozen_rule(monkeypatch):
    look = c2.look_of(2026, 11)
    pmf = [0.0] * 400
    pmf[200] = 0.4; pmf[300] = 0.6        # total about c + 200 or c + 300
    monkeypatch.setattr(c2, "model", lambda y, mo, clim, r: (look, 0, 0.0, pmf))
    L = [mk("E", "2026-12-01T04:59:00Z", 250, "yes")]                       # p_yes = 0.6; YES ask 0.10 -> ratio 6 -> qualifies; NO ask 0.95 -> no
    lt = int(look.timestamp())
    cand = {L[0]["ticker"]: [(lt - 60, 0.10, 0.08), (lt + 60, 0.10, 0.08)]}
    tr = fw.event_trades(2026, 11, L, cand, 1.0, {})
    assert len(tr) == 1 and tr[0]["key"][1] == "yes" and abs(tr[0]["ask"] - 0.10) < 1e-9 and tr[0]["net"] > 0
    late = [mk("E", "2026-12-01T04:59:00Z", 250, "yes", opened="2026-11-16T16:30:00Z")]    # opened after look - 60 min: skipped by design
    assert fw.event_trades(2026, 11, late, cand, 1.0, {}) == []
