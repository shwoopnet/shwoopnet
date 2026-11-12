import os, sys, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
from scalper import mmmap1 as M

CLOSE = 1_800_000_000_000
def snap(t, y, n, ys=100, ns=100): return (t, y, ys, n, ns)

def make(ndrift, e_c=1.0, drift_c=0.0, ntr=40, nwin=30, touch=100, close=CLOSE):
    """Book: yes bid 0.49, no bid 0.49 (mid 0.50, half-spread 1c). A YES buyer pays 0.51 (e = +1c); after 60 s the
    mid moves by drift_c cents toward the buyer. 5 s snapshots."""
    wins = []
    for w in range(nwin):
        c = close + w * 900_000 * 0
        t0 = c - 800_000
        snaps = []
        for k in range(0, 161):
            t = t0 + k * 5000
            shift = drift_c / 100.0 if (k >= 40) else 0.0
            snaps.append(snap(t, 0.49 + shift, 0.49 - shift, ns=touch, ys=touch))
        trades = [(t0 + 100_000 + i * 5000 + 1500, 0.50 + e_c / 100.0, 1.0, "yes") for i in range(ntr)]
        recs, qs, qn, span, dropped = M.window_records(snaps, trades, c)
        assert not dropped
        wins.append({"key": "T%d" % w, "recs": recs, "qsum": qs, "qn": qn, "span": span})
    return wins

def test_effective_and_markout_exact():
    st = M.summarize(make(0, e_c=1.0, drift_c=0.0))
    assert abs(st["e"] - 1.0) < 1e-9 and abs(st["m60"]) < 1e-9 and abs(st["r60"] - 1.0) < 1e-9
    assert abs(st["qhalf"] - 1.0) < 1e-9

def test_adverse_markout_lowers_realized_spread():
    st = M.summarize(make(0, e_c=1.0, drift_c=1.5))
    # buyer of YES: mid rises 1.5c -> realized = 1.0 - 1.5
    assert st["r60"] < 0 and not st["qualifies"] and "r60" in st["why"]

def test_sign_for_no_taker():
    snaps = [snap(CLOSE - 600_000 + k * 5000, 0.49, 0.49) for k in range(100)]
    t = CLOSE - 600_000 + 50_000
    recs, *_ = M.window_records(snaps, [(t + 100, 0.49, 2.0, "no")], CLOSE)   # NO buyer sells YES at 0.49: e = -(0.49-0.50)=+1c
    assert abs(recs[0]["e"] - 1.0) < 1e-9

def test_drops_last_minute_and_stale_snapshot_and_gap():
    snaps = [snap(CLOSE - 600_000 + k * 5000, 0.49, 0.49) for k in range(100)]
    last = snaps[-1][0]
    recs, *_ = M.window_records(snaps, [(CLOSE - 30_000, 0.51, 1.0, "yes")], CLOSE)
    assert recs == []                                    # inside the last 60 s
    recs, *_ = M.window_records(snaps, [(last + 20_000, 0.51, 1.0, "yes")], CLOSE + 10_000_000)
    assert recs == []                                    # no snapshot in the 10 s before it
    gapped = snaps[:20] + snaps[40:]
    _, _, _, _, dropped = M.window_records(gapped, [], CLOSE)
    assert dropped                                       # 100 s poll gap

def test_unusable_snapshots_have_no_mid():
    snaps = [(CLOSE - 600_000,), snap(CLOSE - 595_000, 0.49, 0.49)]
    recs, *_ = M.window_records(snaps, [(CLOSE - 599_000, 0.51, 1.0, "yes")], CLOSE)
    assert recs == []                                    # last snapshot before the trade has an empty side

def test_qualification_rule_boundaries():
    good = make(0, e_c=1.2, drift_c=0.0, ntr=40, nwin=30)         # 1200 trades
    # all in one date -> fails dates
    assert M.summarize(good)["why"] == ["dates"]
    # three dates
    for i, w in enumerate(good):
        sh = (i % 3) * 86_400_000
        for r in w["recs"]: r["close"] += sh; r["t"] += sh
    st = M.summarize(good)
    assert st["dates"] == 3 and st["qualifies"], st["why"]
    # touch at or over 2000 fails
    big = make(0, e_c=1.2, touch=2000)
    for i, w in enumerate(big):
        for r in w["recs"]: r["close"] += (i % 3) * 86_400_000; r["t"] += (i % 3) * 86_400_000
    assert M.summarize(big)["why"] == ["touch"]
    # too few trades
    few = make(0, e_c=1.2, ntr=10, nwin=30)
    for i, w in enumerate(few):
        for r in w["recs"]: r["close"] += (i % 3) * 86_400_000; r["t"] += (i % 3) * 86_400_000
    assert M.summarize(few)["why"] == ["trades"]
    # r60 below +0.5c
    low = make(0, e_c=0.4)
    for i, w in enumerate(low):
        for r in w["recs"]: r["close"] += (i % 3) * 86_400_000; r["t"] += (i % 3) * 86_400_000
    assert "r60" in M.summarize(low)["why"]

def test_interval_straddling_zero_fails():
    rng = random.Random(3); wins = []
    for w in range(40):
        recs = [{"t": CLOSE - 300_000, "close": CLOSE + (w % 3) * 86_400_000, "e": 0, "m": {30: 0, 60: 0, 180: 0}, "r60": rng.choice([-8.0, 9.0]),
                 "cnt": 1.0, "touch": 10, "touch_min": 10, "frac": False} for _ in range(20)]
        wins.append({"key": "W%d" % w, "recs": recs, "qsum": 0, "qn": 0, "span": 1})
    st = M.summarize(wins)
    assert st["lo"] < 0 and "interval" in st["why"]

def test_thin_cells_are_blank_and_fractional_share():
    wins = make(0, ntr=1, nwin=5)
    recs = [r for w in wins for r in w["recs"]]
    c = M.cells(recs, M.bucket_of, ("15-10", "10-5", "5-1"))
    assert all(v[1] is None for v in c.values())          # 5 trades, under the floor of 30
    recs[0]["frac"] = True
    assert M.summarize(wins)["fracshare"] == 1.0 / 5

def test_refuses_without_pushed_registration(monkeypatch=None):
    orig = M.registration_ok
    M.registration_ok = lambda: (False, "registration not committed")
    try:
        assert M.main() == 2
    finally:
        M.registration_ok = orig

def test_hourly_cutoff_constant():
    import datetime as dt
    assert M.HOURLY_CUTOFF_MS == int(dt.datetime(2026, 11, 7, 15, tzinfo=dt.timezone.utc).timestamp() * 1000)
    assert M.HOURLY_CUTOFF_MS < int(dt.datetime(2026, 11, 8, tzinfo=dt.timezone.utc).timestamp() * 1000)

if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"): v()
    print("ok")
