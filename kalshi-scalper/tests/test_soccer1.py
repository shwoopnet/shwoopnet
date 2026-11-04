from scalper import soccer1 as s


def test_devig3_sums_to_one_and_orders():
    q = s.devig3(390, 340, -160)
    assert abs(sum(q) - 1) < 1e-12 and q[2] > q[1] > q[0]


def test_devig2_symmetric():
    assert abs(s.devig2(-110, -110) - 0.5) < 1e-12


def test_cheap_side_and_look():
    assert s.cheap_side((0.05, 0.08)) == ("Y", 0.08)
    assert s.cheap_side((0.72, 0.76))[0] == "N" and abs(s.cheap_side((0.72, 0.76))[1] - 0.28) < 1e-9
    assert s.cheap_side((0.45, 0.50)) is None
    cands = {100: (0.1, 0.12), 900: (0.2, 0.22), 990: (0.3, 0.32)}
    assert s.look(cands, 1100) == (0.2, 0.22)  # 990 is within 120 s of the start


def test_net_and_pf():
    assert abs(s.net(True, 0.10) - (0.9 - s.fee(0.10) / 10)) < 1e-12
    assert s.pf([0.2, -0.1]) == 2.0


def test_same_team_and_book_join():
    assert s.same_team("Manchester United", "Manchester United") and s.same_team("Inter", "Inter Milan")
    assert not s.same_team("Fulham", "Everton")
    r = dict(odds=dict(h=390, a=-160, d=340, ou=2.5, ov=-110, un=-110), home="Ipswich Town", away="Liverpool",
             game=[dict(ticker="T-TIE", sub="Tie"), dict(ticker="T-LIV", sub="Liverpool"), dict(ticker="T-IPS", sub="Ipswich Town")],
             total=[dict(ticker="X-3", k=2.5), dict(ticker="X-4", k=3.5)])
    q = s._book(r)
    assert q["T-TIE"][0] == "G" and q["T-LIV"][1] > q["T-IPS"][1] and set(q) == {"T-TIE", "T-LIV", "T-IPS", "X-3"}
    assert abs(q["X-3"][1] - 0.5) < 1e-12
