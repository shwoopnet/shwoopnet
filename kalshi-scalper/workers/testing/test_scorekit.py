"""Synthetic tests for scorekit.py (made-up data only; no Kalshi, no real file opened). Run: python3 -W ignore test_scorekit.py"""
import gzip, json, os, random, tempfile
import scorekit as k

def mkrun(d, rows_bodies):
    rows = []
    for i, (rid, body) in enumerate(rows_bodies):
        f = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(d, f), "wt").write(json.dumps(body)); rows.append({"id": rid, "status": 200, "file": f})
    rows.append({"id": "bad", "status": 429})
    json.dump({"job": {}, "rows": rows, "status": "complete"}, open(os.path.join(d, "manifest.json"), "w"))

with tempfile.TemporaryDirectory() as d:
    c = lambda ts, b, a: {"end_period_ts": ts, "yes_bid": {"close_dollars": str(b), "low_dollars": str(b - .01)}, "yes_ask": {"close": int(a * 100)}, "volume_fp": "5"}
    mkrun(d, [("b0", {"markets": [{"market_ticker": "T-1", "candlesticks": [c(100, .4, .42), c(160, .41, .43)]}]}), ("T-2", {"candlesticks": [c(100, .1, .2)]}),
              ("l", {"markets": [{"ticker": "KXA-26NOV-T4", "event_ticker": "KXA-26NOV", "open_time": "2026-11-01T00:00:00Z", "close_time": "2026-11-05T12:00:00Z", "result": "yes", "strike_type": "greater", "floor_strike": 4.4, "volume_fp": "900", "title": "x"}]}),
              ("ob", {"orderbook": {"yes": [[40, 5], [45, 9]], "no": [[50, 7]]}, "ts": 7})])
    cs = k.candles(d); assert [x["ts"] for x in cs["T-1"]] == [100, 160] and abs(cs["T-1"][0]["ask"] - .42) < 1e-9 and cs["T-2"][0]["ask"] == .2 and cs["T-1"][0]["bid_low"] == .39   # cents and dollars both read
    ms = k.markets(d); assert ms["KXA-26NOV-T4"]["close"] == 1793880000 and ms["KXA-26NOV-T4"]["floor"] == 4.4 and ms["KXA-26NOV-T4"]["series"] == "KXA"
    bk = k.books(d); assert bk["ob"][0]["yes_bids"][0] == (0.45, 9.0) and bk["ob"][0]["no_bids"] == [(0.5, 7.0)]
    assert len(list(k.iter_answers(d))) == 4              # the 429 row is skipped

# arithmetic: win at .5, loss at .5
t = [{"event": "a", "ts": 1, "price": .5, "win": True}, {"event": "b", "ts": 2, "price": .5, "win": False}]
fee5 = .07 * .25
assert abs(k.net_of(t[0]) - (.5 - fee5)) < 1e-12 and abs(k.net_of(t[1]) + (.5 + fee5)) < 1e-12 and abs(k.net_of({"net": .1, "event": "x"}, .01) - .09) < 1e-12
assert abs(k.stats(t)["pf"] - (.5 - fee5) / (.5 + fee5)) < 1e-3

random.seed(3)
def mk(n, edge, nclusters=40, price=.5):
    out = []
    for i in range(n):
        out.append({"event": "E%d" % i, "cluster": "C%d" % (i % nclusters), "ts": 1000 + i, "price": price, "win": random.random() < price + edge})
    return out
small = k.score(mk(60, .2), {"name": "s"})
assert small["label"] == "no evidence at n = 60" and small["haircut_line"]["label_on_this_line"] == "no evidence at n = 40"
big_good = k.score(mk(4000, .25, 200), {"name": "g", "price_source": "R6 book", "freshness": "within 2 s"})
assert big_good["label"].startswith("PASS"), big_good["label"]
assert len(big_good["windows"]) == 3 and sum(w["n"] for w in big_good["windows"]) == 4000
bad = k.score(mk(300, -.15), {}); assert bad["label"].startswith("FALSIFIED"), bad["label"]
mid = k.score(mk(300, .02), {"registered_bar": {"pf": 1.0, "z": 0.0}}); assert mid["label"].startswith(("cleared its registered bar", "NO SURVIVOR", "FALSIFIED")), mid["label"]
assert "NOT STATED" in bad["price_source"] and "NOT PROVIDED" in bad["book_replay_line"]
assert "11 seconds" in k.score(mk(10, 0), {"price_source": "market list quote"})["warning"]
# slow screen: 2 windows, 30 events, PF 1.3, both halves positive
sl = k.score(mk(40, .3, 40), {"slow": True}); assert len(sl["windows"]) == 2 and sl["label"] in ("on the paper list (unproven)", "off the list (failed the screen)")
assert k.score(mk(20, .3), {"slow": True})["label"] == "no evidence at n = 20"
# clustering: one cluster of identical trades has no z; clusters are not trades
z1 = k.cluster_z([dict(x, cluster="ONE") for x in mk(50, .1)]); assert z1["z"] is None and z1["clusters"] == 1
zc = k.cluster_z(mk(400, .1, 8)); assert zc["clusters"] == 8

# guard
with tempfile.TemporaryDirectory() as d:
    f = os.path.join(d, "REG.md"); open(f, "w").write("x\nREAD-ONCE MARKER: not yet read; first read on or after 2026-12-22\n")
    g = k.Cutoff(5000, f, not_before=2000)
    tr = [{"event": "a", "ts": 1000}]
    for args, why in (((tr, 1999), "before the registered read date"),):
        try: g.check(*args); raise SystemExit("guard failed: " + why)
        except RuntimeError as e: assert "before" in str(e)
    assert g.check(tr, 2000)
    try: g.check([{"event": "late", "ts": 5000}], 2000); raise SystemExit("late trade passed")
    except RuntimeError as e: assert "held-out" in str(e)
    assert k.Cutoff(5000, f, held_out=True).check([{"event": "h", "ts": 5001}], 1)
    try: k.Cutoff(5000, f, held_out=True).check(tr, 1); raise SystemExit("dev trade in held-out passed")
    except RuntimeError as e: assert "development trade" in str(e)
    line = g.mark_read("2026-12-22", "abc1234"); assert line.endswith("READ ON 2026-12-22, commit abc1234")
    open(f, "w").write(line + "\n")
    try: g.check(tr, 2000); raise SystemExit("second read passed")
    except RuntimeError as e: assert "already read" in str(e)
    open(f, "w").write("nothing\n")
    try: g.check(tr, 2000); raise SystemExit("missing marker passed")
    except RuntimeError as e: assert "no marker line" in str(e)
print("scorekit synthetic tests passed")
