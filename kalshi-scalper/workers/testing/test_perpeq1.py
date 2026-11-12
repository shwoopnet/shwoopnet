"""Synthetic test for perpeq1.py (made-up candles, no real perp file opened). Run: python3 -W ignore test_perpeq1.py"""
import calendar, gzip, json, os, tempfile
from datetime import date
import perpeq1 as p
import scorekit as k

def cd(ts, bid, ask): return {"end_period_ts": ts, "yes_bid": {"close_dollars": str(bid)}, "yes_ask": {"close_dollars": str(ask)}}
def day(series, d, prev_close, entry_mid, exit_bid, exit_ask, half_spread=0.0005, prev=True):
    out = []
    if prev: out.append(cd(p.ny_ts(p.prev_trading_date(d), 16, 0), prev_close - .0005, prev_close + .0005))
    out.append(cd(p.ny_ts(d, 8, 55), entry_mid - half_spread, entry_mid + half_spread)); out.append(cd(p.ny_ts(d, 10, 0), exit_bid, exit_ask)); return out

def folder(d, cs):
    rows = []
    for i, (t_, cl) in enumerate(cs.items()):
        f = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(d, f), "wt").write(json.dumps({"markets": [{"market_ticker": t_, "candlesticks": cl}]})); rows.append({"id": t_, "status": 200, "file": f})
    json.dump({"job": {}, "rows": rows}, open(os.path.join(d, "manifest.json"), "w"))
def load(cs):
    with tempfile.TemporaryDirectory() as dd:
        folder(dd, cs); return k.candles(dd)
_ev = p.events
p.events = lambda cs, cmap, today=None: _ev(load(cs) if cs and isinstance(next(iter(cs.values()))[0], dict) and "end_period_ts" in next(iter(cs.values()))[0] else cs, cmap)
assert p.prev_trading_date(date(2026, 11, 9)) == date(2026, 11, 6) and p.prev_trading_date(date(2026, 11, 27)) == date(2026, 11, 25) and p.prev_trading_date(date(2027, 1, 19)) == date(2027, 1, 15)
assert len(p.trading_dates(p.DEV_START, p.DEV_END)) == 30            # Amendment 2: exactly 30 development trading dates
assert len(p.UNIVERSE) == 19

T = "KXAAPLPERP"; cmap = {T: 2.0}
# 1: gap up 60 bps with 1 bp spread at entry -> SELL at bid, buy back at ask; the perp falls back 40 bps -> profit
d = date(2026, 11, 9); prev = 7.00; entry = prev * 1.006; hs = entry * 0.00005
cs = {T: day(None, d, prev, entry, bid := entry * 0.9965, ask := entry * 0.9965 * 1.0001, half_spread=hs)}
tr, ct, cnt = p.events(cs, cmap)
assert len(tr) == 1 and tr[0]["side"] == "sell" and ct[0]["side"] == "buy" and cnt["traded"] == 1
gross = ((entry - hs) - ask) / entry; assert abs(tr[0]["net"] - (gross - 0.0024)) < 1e-9 and tr[0]["net"] > 0 and ct[0]["net"] < 0
assert tr[0]["net_stress"] < tr[0]["net"]
# 2: gap too small (20 bps), gap that is small relative to 5x spread, spread over 3x median, missing exit, sentinel/defect quote, dev-end filter
small = {T: day(None, d, prev, prev * 1.002, prev, prev)}; assert p.events(small, cmap)[2]["no_trigger"] == 1
wide = {T: day(None, d, prev, prev * 1.006, prev, prev, half_spread=prev * 0.0004)}
c = p.events(wide, cmap)[2]; assert c["spread_over_3x_median"] == 1 and c["traded"] == 0      # gap 60 bps passes 5 x 8 bps, but 8 bps spread is over 3 x the 2 bps median
noexit = {T: day(None, d, prev, prev * 1.006, prev, prev)[:2]}; assert p.events(noexit, cmap)[2]["no_exit"] == 1
bad = {T: day(None, d, prev, prev * 1.006, prev, prev)}; bad[T][1]["yes_ask"]["close_dollars"] = "9.2e14"; assert p.events(bad, cmap)[2]["defect_quote"] == 1
late = {T: day(None, date(2026, 12, 22), prev, prev * 1.006, prev, prev)}; c = p.events(late, cmap)[2]; assert c["traded"] == 0 and c["dropped_after_dev_end"] == 1
monday = {T: day(None, date(2026, 11, 16), prev, prev * 1.006, prev, prev)}; assert p.events(monday, cmap)[2]["traded"] == 1          # Monday uses Friday 16:00 as the previous close

# verdicts
v, info = p.verdict(tr, ct); assert v.startswith("NOT_ENOUGH_DATA") and info["trades"] == 1
# 100+ trades on 30 clusters with a real edge -> LEAD only if every bar holds; build 30 dates x 4 names, all profitable
import itertools
def synth(win=True):
    trs, cts = [], []
    for dd in p.trading_dates(p.DEV_START, p.DEV_END):
        for j in range(4):
            e = 0.004 if win else -0.004
            base = {"event": "N%d %s" % (j, dd), "cluster": str(dd), "ts": 1, "date": dd}
            trs.append(dict(base, net=e + (j % 2) * 0.0005, net_stress=e - 0.0005 + (j % 2) * 0.0005, side="sell")); cts.append(dict(base, net=-e, net_stress=-e, side="buy"))
    return trs, cts
trs, cts = synth(True); v, info = p.verdict(trs, cts); assert info["trades"] == 120 and info["clusters"] == 30
assert v.startswith(("LEAD", "FALSIFIED")), v
trs, cts = synth(False); v, _ = p.verdict(trs, cts); assert v.startswith("FALSIFIED"), v
# guard: refuses before 2026-12-22 21:00Z, and on a second read
with tempfile.TemporaryDirectory() as dd:
    folder(dd, cs); cm = os.path.join(dd, "cm.csv"); open(cm, "w").write("ticker,n_obs,median_spread_bp\n%s,7,2.0\n" % T)
    try: p.run([dd], cm, now=calendar.timegm((2026, 12, 21, 23, 0, 0))); raise SystemExit("ran before the read date")
    except RuntimeError as e: assert "before the registered read date" in str(e)
    out = p.run([dd], cm, now=calendar.timegm((2026, 12, 22, 21, 30, 0)))
    assert out["freshness"] == "perp candle freshness assumed, not measured" and out["label_head_rules"].startswith("no evidence at n = 1") and out["counts"]["traded"] == 1
    assert "plus_1c" not in out and "READ ON" in out["next"]
txt = open(p.MARKER_FILE).read(); assert any(l.startswith("READ-ONCE MARKER: not yet read") for l in txt.splitlines())
print("perpeq1 synthetic tests passed")
