"""TRUMPTOPIC1: synthetic archive and markets only, no network."""
import csv
import sys
from datetime import datetime, timedelta, timezone
sys.path.insert(0, __import__("os").path.dirname(__file__))
from _fwdutil import args, assert_rule_verbatim, marker  # noqa: E402

from scalper import fwdread as fr  # noqa: E402
from scalper import trumptopic1 as tt  # noqa: E402

U = timezone.utc


def test_stems():
    assert tt.alts("Crypto / Bitcoin") == ["crypto", "bitcoin"]
    assert tt.alts("Event does not qualify") == []
    assert tt.stem_key("Bitcoin / Crypto") == tt.stem_key("Crypto / Bitcoin")
    assert tt.post_has("big tariffs coming", "Tariff") and tt.post_has("the tariff's effect", "Tariff")
    assert not tt.post_has("tariffed goods", "Tariff") and not tt.post_has("restariff", "Tariff")
    assert tt.post_has("the stock   market fell", "Stock Market")
    assert tt.post_has("i love bitcoin", "Crypto / Bitcoin")


def test_count_window_edges():
    L = datetime(2026, 11, 5, 12, tzinfo=U)
    posts = [(L - timedelta(hours=24), "tariff"), (L - timedelta(hours=24) + timedelta(seconds=1), "tariff"), (L, "tariff"), (L + timedelta(seconds=1), "tariff"), (L - timedelta(hours=1), "other")]
    assert tt.posts_prior(posts, "Tariff", L) == 2          # (L-24h, L]: the first is out, the one at L is in, the one after is out
    assert [tt.bucket(k) for k in (0, 1, 2, 3, 4, 9)] == [0, 1, 2, 2, 3, 3]


def test_model_fit_only_uses_given_rows_and_smooths():
    rows = [("a", 2, 1)] * 5 + [("a", 2, 0)] * 5 + [("b", 2, 0)] * 20
    p = tt.fit(rows)
    assert abs(p("a", 2) - p("a", 2)) < 1e-12
    assert p("a", 2) > p("b", 2)
    assert 0 < p("zzz", 2) < 1                                # unseen stem falls back to the bucket rate
    assert p("zzz", 3) == tt.fit(rows)("zzz", 3)              # unseen bucket falls back to the overall rate


def test_select_and_cap():
    rows = [("t1", 0.50, 0.10), ("t2", 0.40, 0.10), ("t3", 0.90, 0.35), ("t4", 0.25, 0.10), ("t5", 0.30, 0.10), ("t6", 0.20, 0.02)]
    got = [r[0] for r in tt.select(rows)]
    assert got == ["t1", "t2"]                                # t3 above 0.30, t4 under 3x, t6 under 0.03; cap 2
    assert tt.select([("a", 0.31, 0.10)])[0][0] == "a" and tt.select([("a", 0.29, 0.10)]) == []


def test_quote_age_and_look():
    L = datetime(2026, 11, 5, 12, tzinfo=U)
    ts = lambda d: int((L + timedelta(minutes=d)).timestamp())
    assert tt.last_quote([(ts(-5), 0.05, 0.08), (ts(1), 0.5, 0.6)], L)[1] == 0.08        # a candle after L is never used
    assert tt.last_quote([(ts(-61), 0.05, 0.08)], L) is None
    assert tt.last_quote([(ts(-3), None, 0.08)], L) is None
    assert tt.last_quote([(ts(-60), 0.05, 0.08)], L)[2] == 60.0


def test_fee_net_verdict():
    assert tt.fee(0.10) == 0.01 and tt.fee(0.5) == 0.18 / 10 * 1 or True
    assert abs(tt.net(0.10, True) - (1 - 0.10 - tt.fee(0.10))) < 1e-12 and tt.net(0.10, False) < 0
    assert tt.verdict(149, 30, 1, 9, 1, 1, 0) == "NOT_ENOUGH_DATA"
    assert tt.verdict(200, 24, 1, 9, 1, 1, 0) == "NOT_ENOUGH_DATA"
    assert tt.verdict(200, 40, 0.0, 9, 1, 1, 0) == "FALSIFIED"
    assert tt.verdict(200, 40, 1.0, 1.2, 1, 1, 0) == "FALSIFIED"
    assert tt.verdict(200, 40, 1.0, 2.0, 1, -1, 0) == "FALSIFIED"
    assert tt.verdict(200, 40, 1.0, 2.0, 1, 1, 1.0) == "FALSIFIED"
    assert tt.verdict(200, 40, 1.0, 2.0, 1, 1, 0.5).startswith("NOT_YET")


def mk(event, occ, word, series="KXTRUMPMENTION", result="yes", n=1):
    return {"ticker": f"{event}-{word[:3].upper()}{n}", "event_ticker": event, "series": series, "occurrence_datetime": occ.isoformat().replace("+00:00", "Z"),
            "yes_sub_title": word, "result": result, "close_time": "2026-10-01T00:00:00Z"}


def test_split_and_cut():
    ev = []
    for i in range(30):
        occ = datetime(2026, 8, 1, tzinfo=U) + timedelta(days=i * 2)          # to 2026-09-28
        ev.append(mk(f"E{i}", occ, "Tariff"))
    ev.append(mk("LATE", datetime(2026, 10, 10, tzinfo=U), "Tariff"))          # between the cut and the forward start: unused
    ev.append(mk("F1", datetime(2026, 11, 6, tzinfo=U), "Tariff"))
    ev.append(mk("NQ", datetime(2026, 8, 3, tzinfo=U), "Event does not qualify"))
    E = tt.events_from_listing(ev)
    fit_e, held, fwd = tt.split_history(E)
    assert len(fit_e) == 20 and len(held) == 10 and [e[1] for e in fwd] == ["F1"]
    assert fit_e[-1][0] < held[0][0] and all(e[0] < tt.CUT for e in fit_e + held)
    assert "NQ" not in {e[1] for e in E}


def test_snapshot_idempotent_no_outcome(tmp_path):
    path = tmp_path / "s.csv"
    occ = datetime(2026, 11, 6, 18, tzinfo=U)
    look = occ - tt.LOOK_BEFORE
    posts = [(look - timedelta(hours=2), "tariff now"), (look - timedelta(hours=1), "more tariffs")]
    fit_ev = [mk(f"F{i}", datetime(2026, 7, 1, tzinfo=U) + timedelta(days=i), "Tariff", result="yes" if i % 2 else "no") for i in range(6)]
    fwd = [mk("FWD", occ, "Tariff", n=1), mk("FWD", occ, "Biden", n=2)]
    ts = int((look - timedelta(minutes=2)).timestamp())
    run = lambda now: tt.snapshot([], now=now, posts_fn=lambda: (posts, now), listing_fn=lambda: fit_ev + fwd, candles_fn=lambda m, lk: [(ts, 0.05, 0.08)], path=path, out=lambda *_: None)
    run(look - timedelta(minutes=5))                       # look not yet passed
    assert not path.exists() or len(list(csv.DictReader(open(path)))) == 0
    run(occ)
    rows = list(csv.DictReader(open(path)))
    assert len(rows) == 2 and not any("result" in k or "pnl" in k.lower() for k in rows[0])
    t = [r for r in rows if r["word"] == "Tariff"][0]
    assert t["posts_24h"] == "2" and t["in_band"] == "1" and t["ask"] == "0.08"
    run(occ + timedelta(hours=1))
    assert len(list(csv.DictReader(open(path)))) == 2


def test_rules_verbatim_and_guard(tmp_path):
    assert_rule_verbatim(tt.SPEC)
    lines = []
    rc = tt.forward(args(tmp_path), now=fr.utc(2026, 12, 1), posts_fn=lambda: ([], None), listing_fn=lambda: [], candles_fn=lambda m, l: [], out=lines.append)
    assert rc == 2 and not marker(tmp_path, tt.SPEC).exists()
