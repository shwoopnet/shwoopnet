from scalper import bookncaa1 as b


def test_parse_event():
    assert b.parse_event("KXNCAAMBGAME-26JAN15GONZWSU") == ("20260115", "GONZWSU")
    assert b.parse_event("KXNCAAMBGAME-25NOV03ABCDEF")[0] == "20251103"


def test_match_exact_and_fallback():
    gs = [dict(id="1", a="GONZ", h="WSU"), dict(id="2", a="DUKE", h="UNC")]
    assert b.match_game("GONZWSU", gs)[1:] == ("GONZ", "WSU", "exact")
    # Kalshi uses a different home code: anchored by the away abbreviation, unique on the date
    g, ac, hc, how = b.match_game("DUKENC", gs)
    assert (g["id"], ac, hc, how) == ("2", "DUKE", "NC", "fallback")
    # ambiguous fallback (two games share the away team code) is dropped
    gs2 = gs + [dict(id="3", a="GONZ", h="ZZZ")]
    assert b.match_game("GONZXX", gs2) is None
    assert b.match_game("QQQRRR", gs) is None


def test_underdog_and_pickem():
    assert b.underdog(-1000, 700)[0] == "A"
    assert b.underdog(700, -1000)[0] == "H"
    assert b.underdog(-110, -110) is None            # tie
    assert b.underdog(-120, 100) is None             # q about 0.46 > 0.45


def test_look_and_valid():
    ch = {100: (0.04, 0.06), 200: (0.04, 0.06), 300: (0.0, 0.5)}
    assert b.look(ch, 200 + b.LEAD) == 200
    assert b.look(ch, 300 + b.LEAD) == 200            # wide spread is not valid
    assert b.look(ch, 50) is None


def test_fee_net_pf():
    assert b.fee(0.05) == 0.04
    assert abs(b.net(True, 0.10) - (0.9 - b.fee(0.10) / 10)) < 1e-9
    assert b.pf([1, -1]) == 1.0 and b.pf([1]) == float("inf")


def test_score_treated_and_control():
    rows = [dict(ask=0.10, q=0.35, win=True, st=i) for i in range(3)] + [dict(ask=0.10, q=0.12, win=False, st=10 + i) for i in range(5)]
    out = "\n".join(b.score(rows))
    assert "candidates" in out and "treated (q >= 3 x ask): n 3" in out and "NOT_ENOUGH_DATA: 3 treated" in out
