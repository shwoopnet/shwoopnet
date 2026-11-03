"""COUNT1D forward command: synthetic archive and brackets only, no network."""
import csv
import sys
from datetime import datetime, timedelta, timezone
sys.path.insert(0, __import__("os").path.dirname(__file__))
from _fwdutil import args, assert_rule_verbatim, marker  # noqa: E402

from scalper import count1 as c1  # noqa: E402
from scalper import count1d_fwd as fw  # noqa: E402
from scalper import fwdread as fr  # noqa: E402

ET = c1.ET


def day_start(y, m, d):
    return datetime(y, m, d, tzinfo=ET).astimezone(timezone.utc)


def posts_for(days, per_hour=2, extra_on=None):
    """per_hour posts every ET hour for every day in [days]; archive covers 40 days back from the first forward day."""
    out = []
    t = day_start(2026, 10, 1)
    end = day_start(2026, 11, 4) + timedelta(days=days)
    while t < end:
        for k in range(per_hour):
            out.append(t + timedelta(minutes=10 + 20 * k))
        t += timedelta(hours=1)
    return sorted(out)


def markets(y, m, d, winner=None):
    s = f"begins at 12:00:00 AM ET on {datetime(y, m, d):%b} {d}, {y} and ends at 11:59:59 PM ET on {datetime(y, m, d):%b} {d}, {y}"
    ev = f"KXTRUTHSOCIALD-{y % 100}{m:02d}{d:02d}"
    spec = [("less", None, 20), ("between", 20, 39), ("between", 40, 49), ("between", 50, 59), ("greater_or_equal", 60, None)]
    L = []
    for i, (t, lo, hi) in enumerate(spec):
        L.append({"ticker": f"{ev}-B{i}", "event_ticker": ev, "strike_type": t, "floor_strike": lo, "cap_strike": hi, "rules_primary": "x", "rules_secondary": s,
                  "result": ("yes" if winner == i else "no") if winner is not None else ""})
    return L


def test_rule_is_verbatim():
    assert_rule_verbatim(fw.SPEC)


def test_period_filter_excludes_before_forward_start():
    ev = fw.forward_events(markets(2026, 11, 3) + markets(2026, 10, 15) + markets(2026, 11, 4) + markets(2026, 11, 5))
    assert [e[1] for e in ev] == ["KXTRUTHSOCIALD-261104", "KXTRUTHSOCIALD-261105"]
    assert fw.forward_events(markets(2026, 11, 3)) == []


def test_d1_count_on_et_day_across_dst():
    s = day_start(2026, 11, 1)                      # 25 hour day (DST ends)
    posts = [s + timedelta(hours=h) for h in range(25)] + [s - timedelta(minutes=1), s + timedelta(hours=25)]
    per = c1.parse_period(markets(2026, 11, 1)[0])
    assert sum(1 for x in posts if per[0] <= x < per[1]) == 25


def test_source_gate_prefix_latch():
    assert fw.gate_status([True] * 19)[0] == "PENDING"
    assert fw.gate_status([True] * 20)[0] == "OK"
    assert fw.gate_status([True] * 18 + [False, False] + [True] * 30)[0] == "OK"      # exactly 90% at day 20 passes
    assert fw.gate_status([True] * 17 + [False] * 3)[0] == "VOID"                    # 85%
    assert fw.gate_status([True] * 18 + [False, True])[0] == "OK"
    assert fw.gate_status([False] * 3 + [True] * 17 + [True] * 100)[0] == "VOID"      # latched at day 20: 17/20 = 85%
    assert fw.gate_status([True] * 100 + [False] * 5)[0] == "OK"


def test_verdicts():
    assert fw.verdict(40, 0.5, 9.0, .1, .1, 0, "OK") == "NOT_ENOUGH_DATA"
    assert fw.verdict(400, 0.5, 9.0, .1, .1, 0, "VOID") == "VOID"
    assert fw.verdict(150, 0.0, 9.0, .1, .1, 0, "OK") == "FALSIFIED"
    assert fw.verdict(150, 0.1, 1.2, .1, .1, 0, "OK") == "FALSIFIED"
    assert fw.verdict(150, 0.1, 2.0, .1, -.1, 0, "OK") == "FALSIFIED"
    assert fw.verdict(150, 0.1, 2.0, .1, .1, 0.095, "OK") == "FALSIFIED"
    assert fw.verdict(150, 0.1, 2.0, .1, .1, 0.0, "OK").startswith("SURVIVES")


def cand_fn(ask_by_idx):
    def f(ticker, look):
        i = int(ticker[-1])
        a = ask_by_idx[i]
        lt = int(look.timestamp())
        return [(lt - 60, a), (lt + 60, a)]
    return f


def test_snapshot_idempotent_no_outcome_and_refusals(tmp_path):
    path = tmp_path / "snap.csv"
    posts = posts_for(3)
    L = markets(2026, 11, 4, winner=2)
    cf = cand_fn([0.60, 0.50, 0.10, 0.06, 0.02])
    run = lambda now, a=(): fw.snapshot(list(a), now=now, posts_fn=lambda: (posts, now), markets_fn=lambda: L, candles_fn=cf, path=path, out=lambda *_: None)
    assert run(fr.utc(2026, 11, 4, 16, 30)) == 2             # 11:30 ET, fill window not complete
    assert run(fr.utc(2026, 11, 4, 17, 30), ["--date", "2026-11-03"]) == 2   # before the forward start
    assert not path.exists()
    assert run(fr.utc(2026, 11, 4, 17, 30)) == 0             # 12:30 ET
    rows = list(csv.DictReader(open(path)))
    assert len(rows) == 5 and "result" not in rows[0] and not any("result" in k or "pnl" in k.lower() for k in rows[0])
    assert rows[0]["date"] == "2026-11-04" and rows[2]["in_band"] == "1" and rows[0]["in_band"] == "0"
    run(fr.utc(2026, 11, 4, 18, 0))                          # second run the same day adds nothing
    assert len(list(csv.DictReader(open(path)))) == 5


def test_takeup_refuses_before_20_days(tmp_path):
    path = tmp_path / "s.csv"
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(fw.SNAP_FIELDS)
        for d in range(19):
            w.writerow([f"2026-11-{d + 4:02d}"] + ["x"] * 11 + ["1", "1", "", ""])
    assert fw.takeup(path=path, out=lambda *_: None) == 2
    with open(path, "a", newline="") as fh:
        csv.writer(fh).writerow(["2027-01-01"] + ["x"] * 11 + ["1", "1", "", ""])
    lines = []
    assert fw.takeup(path=path, out=lines.append) == 0 and "20 days" in lines[0] and "1.00 a day" in lines[0]


def forward_fixture(ndays):
    posts = posts_for(ndays + 1)
    mk = []
    for d in range(ndays):
        dt = datetime(2026, 11, 4) + timedelta(days=d)
        mk += markets(dt.year, dt.month, dt.day, winner=2)
    return posts, mk


def test_forward_guard_refuses_early_and_twice(tmp_path):
    posts, mk = forward_fixture(3)
    kw = dict(posts_fn=lambda: (posts, None), markets_fn=lambda: mk, candles_fn=lambda t, look: [(int(look.timestamp()) - 60, 0.10), (int(look.timestamp()) + 60, 0.10)])
    lines = []
    assert fw.forward(args(tmp_path), now=fr.utc(2026, 11, 8, 12), out=lines.append, **kw) == 2
    assert any("under 150" in x for x in lines) and not marker(tmp_path, fw.SPEC).exists()
    lines = []
    assert fw.forward(args(tmp_path, "--force-info"), now=fr.utc(2026, 11, 8, 12), out=lines.append, **kw) == 0
    assert any("forward days with a complete fill window: 3" in x for x in lines) and not marker(tmp_path, fw.SPEC).exists()
    lines = []
    assert fw.forward(args(tmp_path), now=fr.utc(2027, 3, 1, 12), out=lines.append, **kw) == 0     # due date: reads once
    assert marker(tmp_path, fw.SPEC).exists() and any(x.startswith("FWD-READ COUNT1D") for x in lines)
    assert any("NOT_ENOUGH_DATA" in x for x in lines)
    lines = []
    assert fw.forward(args(tmp_path), now=fr.utc(2027, 3, 2, 12), out=lines.append, **kw) == 2
    assert any("spent" in x for x in lines)


def test_read_uses_only_forward_days():
    posts, mk = forward_fixture(2)
    mk += markets(2026, 11, 3, winner=1)                    # a pre-forward day must not be scored
    seen = []
    cf = lambda t, look: (seen.append(t), [(int(look.timestamp()) - 60, 0.10), (int(look.timestamp()) + 60, 0.10)])[1]
    lines, body = fw.read(fr.utc(2027, 3, 1), posts_fn=lambda: (posts, None), markets_fn=lambda: mk, candles_fn=cf)
    assert not any("261103" in t for t in seen) and "days scored 2" in lines[0]
