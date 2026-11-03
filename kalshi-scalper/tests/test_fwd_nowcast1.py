"""NOWCAST1 forward command with a fake scalper.recdaily and a hand-made nowcast file."""
import json
import sys
import types
sys.path.insert(0, __import__("os").path.dirname(__file__))
from _fwdutil import args, assert_rule_verbatim, marker  # noqa: E402

from scalper import fwdread as fr  # noqa: E402
from scalper import nowcast1_fwd as fw  # noqa: E402

DUE = fr.utc(2027, 3, 1)
FZ = int(fw.FWD_FREEZE.timestamp())


def fake(monkeypatch, tmp_path, n_events=12, pre=2, result="no"):
    rows, results, nowc = [], {}, {}
    for i in range(n_events + pre):
        close = FZ + 86400 * (10 + i) if i < n_events else FZ - 86400 * (i - n_events + 1)
        ev = f"KXCPI-E{i}"
        nowc[ev] = {"nowcast": 0.3, "sd": 0.1}
        for j, (bid, ask) in enumerate(((0.03, 0.05), (0.40, 0.45))):
            tk = f"{ev}-T{j}"
            rows.append({"ticker": tk, "series": "KXCPI", "event_ticker": ev, "close_ts": close, "open_ts": close - 86400 * 30, "strike_type": "greater",
                         "floor_strike": 0.3 if j == 0 else 0.1, "yes_bid": bid, "yes_ask": ask, "poll_ts": close - 86400})
            results[tk] = result
    m = types.ModuleType("scalper.recdaily")
    m.load_quotes = lambda d, series=None: rows
    m.load_results = lambda d: results
    m.nearest_to_look = lambda rs, tk, minutes_before_close=None, **k: next(r for r in rs if r["ticker"] == tk)
    monkeypatch.setitem(sys.modules, "scalper.recdaily", m)
    p = tmp_path / "nowcast.json"
    p.write_text(json.dumps(nowc))
    return str(p)


def test_rule_is_verbatim():
    assert_rule_verbatim(fw.SPEC)


def test_refuses_before_2027_03_01(tmp_path, monkeypatch, capsys):
    p = fake(monkeypatch, tmp_path)
    assert fw.forward(args(tmp_path, "--nowcast-file", p, "--daily-dir", "x"), now=fr.utc(2027, 2, 28)) == 2
    out = capsys.readouterr().out
    assert "not due until 2027-03-01" in out and "read the first 12 forward release-series on or after 2027-03-01, decides nothing." in out
    assert not marker(tmp_path, fw.SPEC).exists()


def test_force_info_lists_the_four_looks(tmp_path, monkeypatch, capsys):
    p = fake(monkeypatch, tmp_path)
    assert fw.forward(args(tmp_path, "--force-info", "--nowcast-file", p, "--daily-dir", "x"), now=fr.utc(2026, 11, 5)) == 0
    out = capsys.readouterr().out
    for d in ("2026-11-09 13:30Z", "2026-11-24 13:30Z", "2026-12-09 13:30Z", "2026-12-22 13:30Z"):
        assert d in out
    assert "12 of the 12 needed" in out and not marker(tmp_path, fw.SPEC).exists()


def test_needs_the_nowcast_file_and_12_series(tmp_path, monkeypatch, capsys):
    p = fake(monkeypatch, tmp_path, n_events=5)
    assert fw.forward(args(tmp_path, "--daily-dir", "x"), now=DUE) == 2
    assert "needs --nowcast-file" in capsys.readouterr().out
    assert fw.forward(args(tmp_path, "--nowcast-file", p, "--daily-dir", "x"), now=DUE) == 2
    assert "only 5 settled forward release-series" in capsys.readouterr().out


def test_real_read_uses_only_forward_series_and_is_not_repeatable(tmp_path, monkeypatch, capsys):
    p = fake(monkeypatch, tmp_path, n_events=12, pre=3)
    assert fw.forward(args(tmp_path, "--nowcast-file", p, "--daily-dir", "x"), now=DUE) == 0
    out = capsys.readouterr().out
    assert "first 12 forward release-series, 12 trades" in out        # the 3 pre-freeze series are not read; the cheap YES strike trades once per series
    assert "NOT_ENOUGH_DATA" in out and "Decides nothing" in out and "FWD-READ NOWCAST1F 2027-03-01:" in out
    assert fw.forward(args(tmp_path, "--nowcast-file", p, "--daily-dir", "x"), now=DUE) == 2


def test_choose_is_the_registered_one(tmp_path, monkeypatch):
    p = fake(monkeypatch, tmp_path, n_events=1, pre=0)
    rd = sys.modules["scalper.recdaily"]
    nw = json.loads(open(p).read())
    rs = fw.release_series(rd, rd.load_quotes("x"), rd.load_results("x"), nw)
    assert len(rs) == 1
    tr = fw.trades(rs)
    assert len(tr) == 1 and tr[0]["side"] == "yes" and abs(tr[0]["price"] - 0.05) < 1e-9 and tr[0]["net"] < 0
