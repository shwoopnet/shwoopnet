import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "scalper"))
import elect1 as e


def row(series, ticker, bid, ask, vol=500, oi=500, status="active"):
    return dict(series=series, ticker=ticker, status=status, yes_bid=str(bid), yes_ask=str(ask), volume=str(vol), open_interest=str(oi))


def test_universe_regex():
    ok = ["SENATEPARTY-TX", "SENATEPARTYMI", "KXSENATECO", "GOVPARTYPA", "HOUSEPA7", "KXHOUSEUT01", "HOUSE", "CONTROLH", "KXAKSENATE"]
    bad = ["KXSENATEALD", "KXGOVCANOMD", "KXSENATEBILL", "SENATEMOV", "KXHOUSEMOV", "KXGOVSHUT"]
    got = e.series_in_universe(ok + bad)
    assert sorted(got) == sorted(ok)


def test_fee_rounds_up():
    assert e.fee(0.10) == 0.07  # 0.07*10*0.09 = 0.063 -> 0.07
    assert e.fee(0.5) == 0.18   # 0.175 -> 0.18


def test_rating_parse():
    t = "! [[2026 United States Senate election in Ohio|Ohio]]\n<!--Cook-->| {{USRaceRating|Lean|R}}\n<!--IE-->| {{USRaceRating|Toss-up}}\n<!--Sabato-->| {{USRaceRating|Likely|D}}\n"
    r = e.parse_ratings(t)
    assert abs(r["Ohio"] - (0.72 + 0.5 + 0.12) / 3) < 1e-9


def test_build_trades_one_per_race_and_ref():
    rows = [row("SENATEPARTY-TX", "SENATEPARTY-TX-26-R", 0.80, 0.82), row("SENATEPARTY-TX", "SENATEPARTY-TX-26-D", 0.17, 0.19),
            row("SENATEPARTY-OH", "SENATEPARTY-OH-26-R", 0.60, 0.62, vol=10, oi=10)]
    ctrl, ref = e.build_trades(rows, {("SENATE", "TX"): 0.4})
    # TX: cheap sides are D yes at 0.19 and R no at 0.20: lowest ask 0.19 (D yes). OH ineligible (low volume)
    assert len(ctrl) == 1 and ctrl[0]["ticker"].endswith("-D") and ctrl[0]["side"] == "yes"
    # ref P(D)=0.6 >= 3*0.19 -> in ref
    assert len(ref) == 1
    ctrl, ref = e.build_trades(rows, {("SENATE", "TX"): 0.9})  # P(D)=0.1 < 0.57
    assert len(ctrl) == 1 and ref == []


def test_stats_and_unsettled():
    t = [dict(ticker="A", side="yes", ask=0.2), dict(ticker="B", side="no", ask=0.1), dict(ticker="C", side="yes", ask=0.3)]
    s = e.stats(t, {"A": "yes", "B": "yes"})
    assert s["n"] == 2 and s["win_rate"] == 0.5
    assert abs(s["net"] - ((8 - e.fee(0.2)) + (-1 - e.fee(0.1)))) < 1e-9


def test_bound_hard_limit():
    rows = [row("HOUSEPA7", "HOUSEPA7-26-R", 0.69, 0.71), row("HOUSEPA7", "HOUSEPA7-26-D", 0.28, 0.30)]
    ctrl, _ = e.build_trades(rows, None)
    assert ctrl and ctrl[0]["ask"] <= 0.30
