from scalper import fp2


def test_flow_sums_taker_sides():
    f = fp2.flow([{"taker_outcome_side": "yes", "count_fp": "30.0"}, {"taker_outcome_side": "no", "count_fp": "5"}, {"taker_outcome_side": "x", "count_fp": "9"}])
    assert f == {"yes": 30.0, "no": 5.0, "n": 2}


def test_opposed_needs_size_and_share():
    assert fp2.opposed({"yes": 100, "no": 100, "n": 5}, "yes")
    assert not fp2.opposed({"yes": 1000, "no": 100, "n": 5}, "yes")  # 9% share
    assert not fp2.opposed({"yes": 100, "no": 50, "n": 5}, "yes")  # too small
    assert fp2.opposed({"yes": 100, "no": 100, "n": 5}, "no")


def test_judge_not_enough_data_when_few():
    rows = [{"opp": i < 3, "day": f"2026-09-{1 + i % 20:02d}", "net": 0.05, "lost": 0.0} for i in range(100)]
    assert fp2.judge(rows, "2026-09-12")["verdict"] == "NOT_ENOUGH_DATA"
