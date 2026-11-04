from scalper import out1_census as o


def test_norm():
    assert o.norm("A.J. Brown Jr.") == "a j brown"


def test_top2_uses_prior_games_only():
    tg = {}
    order = {"X": []}
    for w in range(1, 6):
        gid = f"2025_{w:02d}_X_Y"
        tg[(gid, "X")] = {"a": ("WR", 70, gid), "b": ("TE", 60, gid), "c": ("WR", 10 + 100 * (w == 5), gid)}
        order["X"].append((2025, w, gid))
    assert [n for n, _ in o.top2(tg, order, "X", 2025, 5)] == ["a", "b"]  # week 5's own snaps are not used
    assert o.top2(tg, order, "X", 2025, 3) is None  # under 3 prior games
