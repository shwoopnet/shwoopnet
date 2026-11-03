"""BOOKCH1 pooled forward verdict on synthetic ledger trades."""
import json
import sys
sys.path.insert(0, __import__("os").path.dirname(__file__))
from _fwdutil import args, assert_rule_verbatim, marker  # noqa: E402

from scalper import bookch1_fwd as fw  # noqa: E402
from scalper import fwdread as fr  # noqa: E402

DAY = 86400


def trades(n, days, win_every=5, series="KXBTC15M", start=fw.FREEZE + 3600, win=0.70, loss=-0.29):
    out = []
    for i in range(n):
        net = win if i % win_every == 0 or i % win_every == 1 else loss        # 40% winners: PF about 1.6
        out.append({"ticker": f"{series}-{i}", "series": series, "close_ts": start + (i * days * DAY) // n, "side": "no", "entry": 0.27,
                    "net1": net, "net10": net, "net10s": net - 0.01})
    return out


def write(tmp_path, d):
    p = tmp_path / "t.json"
    p.write_text(json.dumps(d))
    return str(p)


def test_rule_is_verbatim():
    assert_rule_verbatim(fw.SPEC)


def test_verdict_words():
    good = sorted(trades(160, 9), key=lambda x: x["close_ts"])
    w, f = fw.verdict(good)
    assert w == "NOT_YET_FALSIFIED" and f["n"] == 160 and f["days"] >= 7
    assert fw.verdict(good[:100])[0] == "NOT_ENOUGH_DATA"
    assert fw.verdict(sorted(trades(160, 5), key=lambda x: x["close_ts"]))[0] == "NOT_ENOUGH_DATA"      # under 7 trade days
    bad = [dict(x, net10=-0.2, net1=-0.2, net10s=-0.2) for x in good]
    assert fw.verdict(bad)[0] == "FALSIFIED"
    stress = [dict(x, net10s=-0.5) for x in good]                                                       # PF at fees x1.2 below 1.0
    assert fw.verdict(stress)[0] == "FALSIFIED"
    first_half_weak = [dict(x, net10=(-0.29 if i < 80 and i % 2 else x["net10"])) for i, x in enumerate(good)]
    assert fw.verdict(first_half_weak)[0] == "FALSIFIED"                                                # a half under 1.5


def test_refuses_before_due(tmp_path, capsys):
    p = write(tmp_path, {"BOOKCH1_BTC": trades(160, 9)})
    assert fw.forward(args(tmp_path, "--trades", p), now=fr.utc(2026, 11, 11)) == 2
    out = capsys.readouterr().out
    assert "not due until 2026-11-12" in out and "NOT_ENOUGH_DATA:** fewer than 150 pooled trades" in out
    assert not marker(tmp_path, fw.SPEC).exists()


def test_waits_until_150_trades_before_the_last_allowed_date_then_reads_anyway(tmp_path, capsys):
    p = write(tmp_path, {"BOOKCH1_BTC": trades(40, 9), "BOOKCH1_XRP": trades(30, 9, series="KXXRP15M")})
    assert fw.forward(args(tmp_path, "--trades", p), now=fr.utc(2026, 11, 12, 12)) == 2
    assert "wait, the last allowed read is 2026-11-14" in capsys.readouterr().out
    assert fw.forward(args(tmp_path, "--trades", p), now=fr.utc(2026, 11, 14, 1)) == 0
    out = capsys.readouterr().out
    assert "PRIMARY (Bitcoin + XRP pooled): NOT_ENOUGH_DATA; n 70" in out and "FWD-READ BOOKCH1F 2026-11-14:" in out


def test_pooled_read_alternative_separate_second_read_refused_and_freeze_respected(tmp_path, capsys):
    pre = [dict(x, close_ts=fw.FREEZE - 100 - i, net10=5.0, net1=5.0, net10s=5.0) for i, x in enumerate(trades(50, 2))]       # before the freeze: ignored
    d = {"BOOKCH1_BTC": trades(80, 9) + pre, "BOOKCH1_XRP": trades(80, 9, series="KXXRP15M"), "BOOKCH1B_BTC": trades(20, 9)}
    p = write(tmp_path, d)
    assert fw.forward(args(tmp_path, "--trades", p), now=fr.utc(2026, 11, 13)) == 0
    out = capsys.readouterr().out
    assert "PRIMARY (Bitcoin + XRP pooled): NOT_YET_FALSIFIED; n 160" in out          # 160 only: the 50 pre-freeze trades are not in it
    assert "ALTERNATIVE (BOOKCH1B, own verdict): NOT_ENOUGH_DATA; n 20" in out
    assert "HOLDOUT COUNTS" in out and "not a pass" in out
    assert fw.forward(args(tmp_path, "--trades", p), now=fr.utc(2026, 11, 13)) == 2
    assert "spent" in capsys.readouterr().out


def test_force_info_counts_only(tmp_path, capsys):
    p = write(tmp_path, {"BOOKCH1_BTC": trades(10, 9)})
    assert fw.forward(args(tmp_path, "--trades", p, "--force-info"), now=fr.utc(2026, 11, 5)) == 0
    out = capsys.readouterr().out
    assert "primary pooled trades so far" in out and not marker(tmp_path, fw.SPEC).exists()


def test_bookch1_module_has_forward_command():
    from scalper import bookch1
    assert callable(bookch1.main)
