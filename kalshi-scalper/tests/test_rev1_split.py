"""Synthetic test of the REV1 split (workers/REV1_SPLIT_AMENDMENT.md). No data files."""
from scalper import rev1


def mk(ct, doi, no_ask, res, oi_known=True):
    # yes bid = 1 - no_ask at both entry candles; oi at -360 and -180 differ by doi
    cs = {}
    for ls in (120, 180, 360):
        oi = None if not oi_known else (1000.0 if ls == 360 else 1000.0 + doi if ls == 180 else 1000.0 + doi)
        cs[ct - ls] = (round(1 - no_ask, 4), round(1 - no_ask + 0.01, 4), 1.0, oi)
    return ("T%d" % ct, ct, res, cs)


def test_split():
    base = 1_800_000_000
    wins = [mk(base, 90000, 0.20, "no"),            # fired, NO wins
            mk(base + 900, 0, 0.20, "yes"),         # not fired, NO loses
            mk(base + 1800, 0, 0.20, "no"),         # not fired, wins
            mk(base + 2700, 0, 0.60, "no"),         # ask out of band, no entry
            mk(base + 3600, 0, 0.20, "no", oi_known=False)]   # unknown
    assert rev1.window_doi(wins[0][3], base) == 90000.0
    assert rev1.window_doi(wins[4][3], base + 3600) is None
    rows = rev1.split_entries(wins)
    assert len(rows) == 8                              # 4 windows x 2 looks
    f = {k: [r for r in rows if r["fixed"] == k] for k in ("yes", "no", "unknown")}
    assert len(f["yes"]) == 2 and len(f["no"]) == 4 and len(f["unknown"]) == 2
    assert all(r["p90"] == "unknown" for r in rows)    # fewer than 40 trailing windows
    assert abs(rows[0]["net"] - (1 - 0.20 - rev1.U.fee(0.20))) < 1e-12
    rep = rev1.split_report(rows)
    assert "overlap: 2 entries in 1 windows" in rep and "NOT-fired half alone is not negative" in rep
    neg = rev1.split_report([r for r in rows if r["win"] == 0.0 or r["fixed"] == "yes"])
    assert "NEGATIVE" in neg


def test_trailing_p90():
    items = [(1_000_000 + 900 * i, float(i)) for i in range(120)]
    t = rev1.trailing_p90(items)
    assert t[items[10][0]] is None and t[items[100][0]] is not None
    assert t[items[100][0]] <= 99.0           # uses only windows closed >= 900 s earlier
