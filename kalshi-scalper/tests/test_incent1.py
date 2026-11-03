import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import incent1 as I

def book(y, n): return {"yes_dollars": [[str(p), str(s)] for p, s in y], "no_dollars": [[str(p), str(s)] for p, s in n]}

def test_ref_level():
    lv = [(0.50, 100), (0.49, 120), (0.40, 900)]
    assert I.ref_level(lv, 1000) == 0.49          # 100 < 200 <= 220
    assert I.ref_level([(0.5, 50)], 1000) is None

def test_discount_below_ref():
    lv = [(0.50, 250), (0.48, 750)]               # ref 0.50, 0.48 is 2 ticks down
    q = I.competing_score(lv, 1000, 0.50)
    assert abs(q - (250 + 750 * 0.25)) < 1e-9

def test_clip_vs_full():
    lv = [(0.50, 300), (0.49, 5000)]
    assert I.competing_score(lv, 1000, 0.50) > I.competing_score(lv, 1000, 0.50, clip=True)

def test_empty_book_needs_gap_and_floor():
    b = book([], [])
    s = I.score_lane(b, 1000, 0.5, 0, 14, 7)
    assert s["counts"] is False and s["s"] == [1.0, 1.0]   # alone: share 1 but snapshot excluded
    v = I.lane_value([s], 1000, 14, 7, 0, "cent")
    assert v["reward100"] == 0.0

def test_thick_two_sided_pays_with_floor():
    b = book([(0.50, 1000)], [(0.49, 1000)])
    s = I.score_lane(b, 1000, 0.5, 100, 14, 7)
    assert s["counts"] and 0.08 < s["s"][0] < 0.10
    v = I.lane_value([s], 1000, 14, 7, 100, "cent")
    assert v["reward100"] > 0
    tiny = I.lane_value([s], 1000, 0.5, 7, 100, "cent")   # pool 0.5/day x 7 x share < $1
    assert tiny["reward100"] == 0.0

def test_verdict_words():
    assert I.verdict([1.0] * 50) == "NOT_ENOUGH_DATA"
    assert I.verdict([0.0] * 200) == "NOT_VIABLE"
    assert I.verdict([1.0] * 12 + [0.0] * 188) == "VIABLE_SMALL_PROBE"
    assert I.verdict([1.0] * 5 + [0.0] * 195) == "NOT_VIABLE"
