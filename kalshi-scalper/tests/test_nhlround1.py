import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import nhlround1 as r


def test_constants_fixed_by_registration():
    assert r.E_SCORERS == 3.9085 and r.MARGIN == 0.3 and abs(r.THRESH - 3.6085) < 1e-9


def test_is_round_threshold_and_min_rungs():
    assert r.is_round(3.60, 12) and not r.is_round(3.62, 12)
    assert not r.is_round(2.0, 7)  # fewer than 8 valid rungs


def test_refuses_before_nhlall1_result(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(r, "ROOT", tmp_path)
    (tmp_path / "workers").mkdir()
    r.score()
    assert "refusing" in capsys.readouterr().out
