"""Plain assert tests for RAINCAL (src/scalper/raincal.py) on a SYNTHETIC fixture only: made-up quotes, forecasts and results. No recorded row is used.
Run with: cd kalshi-scalper && PYTHONPATH=src python tests/test_raincal.py"""
import contextlib
import csv
import gzip
import io
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scalper import raincal as R

QCOLS = ["t_recv_ms", "server_date_header", "ticker", "city", "event_ticker", "close_time", "min_from_look", "status", "yes_bid", "yes_ask", "yes_bid_size", "yes_ask_size",
         "last_price", "volume", "open_interest"]
PCOLS = ["t_fetch_ms", "ticker", "city", "station", "grid", "nws_update_time", "nws_generated_at", "nws_valid_times", "valid_start", "valid_end", "pop_percent"]
RCOLS = ["t_fetch_ms", "ticker", "city", "event_ticker", "close_time", "status", "result", "expiration_value", "volume"]


def iso(e):
    return datetime.fromtimestamp(e, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ep(y, m, d, h=0):
    return datetime(y, m, d, h, tzinfo=timezone.utc).timestamp()


def put(root, stamp, name, cols, rows):
    p = Path(root) / "raincal" / stamp[0] / stamp[1]
    p.mkdir(parents=True, exist_ok=True)
    with gzip.open(p / f"{name}.csv.gz", "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)


def quote(close, tk, dt_s, bid, ask, status="active", bsz=50, asz=50):
    t = (close - R.LOOK_BEFORE_CLOSE_S + dt_s) * 1000
    return [int(t), "", tk, tk.split("-")[2], "E", iso(close), "", status, bid, ask, bsz, asz, "", "", ""]


def pop(close, tk, dt_s, vals, stale_first=None):
    """vals: PoP percents of 6-hour periods starting 2 h before the look; an optional extra period that ended before the look."""
    t = (close - R.LOOK_BEFORE_CLOSE_S + dt_s + 5) * 1000
    look = close - R.LOOK_BEFORE_CLOSE_S
    rows = []
    if stale_first is not None:
        rows.append([int(t), tk, "X", "K", "g", "u", "", "", iso(look - 8 * 3600), iso(look - 2 * 3600), stale_first])
    for i, v in enumerate(vals):
        s = look - 2 * 3600 + i * 6 * 3600
        rows.append([int(t), tk, "X", "K", "g", "u", "", "", iso(s), iso(s + 6 * 3600), v])
    return rows


# 1. the look: first active poll at or after 7:00 with a forecast; PoP_day = max of periods still running; late or missing polls are no trade
close = ep(2026, 11, 3, 6)                                   # Central: closes 06:00Z, look 13:00Z on Nov 2
tk = "KXRAIN-26NOV02-CHI"
qs = [quote(close, tk, -600, 0.10, 0.12), quote(close, tk, 60, 0.20, 0.22, status="finalized"), quote(close, tk, 1200, 0.30, 0.32)]
ps = pop(close, tk, 60, [10, 60, 20], stale_first=99) + pop(close, tk, 1200, [10, 70, 20])
lk = R.build_looks([dict(zip(QCOLS, r)) for r in qs], [dict(zip(PCOLS, [str(x) for x in r])) for r in ps])
lk = {k: v for k, v in lk.items()}
assert list(lk) == [tk] and lk[tk]["bid_c"] == 30 and lk[tk]["ask_c"] == 32, lk       # the 7:01 poll was not active, the 6:50 poll is before the look
assert lk[tk]["pop"] == 70 and lk[tk]["day"] == "2026-11-02"                         # the stale 99 period ended before the look and is excluded
late = [dict(zip(QCOLS, quote(close, tk, 3 * 3600, 0.1, 0.2)))]
assert R.build_looks(late, [dict(zip(PCOLS, [str(x) for x in r])) for r in pop(close, tk, 3 * 3600, [50])]) == {}   # 10:00 AM is past 8:00
assert R.build_looks([dict(zip(QCOLS, quote(close, tk, 60, 0.1, 0.2)))], []) == {}   # no forecast at the poll: no trade
# the 8:00 limit itself still counts (inclusive), 8:00:01 does not
edge = R.build_looks([dict(zip(QCOLS, quote(close, tk, 3600, 0.1, 0.2)))], [dict(zip(PCOLS, [str(x) for x in r])) for r in pop(close, tk, 3600, [50])])
assert tk in edge

# 2. the rule on whole cents: a gap of exactly 8 cents trades, 7 does not; NO pays 100 - bid
def L1(bid, ask, p, **kw):
    return {"bid_c": bid, "ask_c": ask, "pop": p, "bid_sz": 50, "ask_sz": 50, **kw}
assert R.signal(L1(10, 12, 20)) == ("yes", 12, 50)                      # 20 - 12 = 8: tie trades
assert R.signal(L1(10, 13, 20)) is None                                 # 7
assert R.signal(L1(28, 30, 20)) == ("no", 72, 50)                       # 28 - 20 = 8: tie trades, pays 72c
assert R.signal(L1(27, 29, 20)) is None
assert R.signal(L1(None, 12, 20)) == ("yes", 12, 50) and R.signal(L1(10, None, 20)) is None
assert R.signal(L1(0, 0, 20)) is None and R.signal(L1(10, 100, 100)) is None   # a 0 or 100 quote is not a quote
assert R.signal(L1(50, 10, 30)) is None                                 # crossed quotes would fire both: no trade

# 3. fees: 7% x C x p x (1-p), C = 10, rounded UP to the cent per order, divided by 10 per contract
assert abs(R.net_per_contract("yes", 50, "yes") - (1 - 0.50 - 0.18 / 10)) < 1e-12      # 0.07 x 10 x 0.25 = 17.5c -> 18c
assert abs(R.net_per_contract("yes", 50, "no") - (0 - 0.50 - 0.018)) < 1e-12
assert abs(R.net_per_contract("no", 90, "no") - (1 - 0.90 - 0.07 / 10)) < 1e-12        # 0.07 x 10 x 0.09 = 6.3c -> 7c
assert abs(R.net_per_contract("yes", 50, "yes", 0.07 * 1.2) - (1 - 0.50 - 0.21 / 10)) < 1e-12   # 21.0c: the x1.2 line
assert abs(R.z_bar() - 5.2689) < 1e-3

# 4. universe: median two-sided spread at most 3c over the FIRST 14 UTC days, at least 7 such days; a one-sided quote does not count
def mk(day0, n_days, tag, spread, bad=0):
    out = {}
    for i in range(n_days):
        d = {"ticker": f"{tag}{i}", "city": tag, "day": f"2026-11-{day0 + i:02d}", "bid_c": 50, "ask_c": 50 + spread, "pop": 50, "t": 0.0, "bid_sz": 5, "ask_sz": 5, "pop_union": .5}
        if i < bad:
            d["bid_c"] = None
        out[d["ticker"]] = d
    return out
looks = {}
looks.update(mk(1, 20, "AAA", 3)); looks.update(mk(1, 20, "BBB", 4)); looks.update(mk(1, 20, "CCC", 3, bad=14))     # CCC: only 6 two-sided days in the first 14
looks.update(mk(1, 6, "DDD", 1))                                                                                  # DDD: 6 days
looks.update(mk(16, 10, "EEE", 1))                                                                                # EEE only appears after day 14: never enters
uni, info, days, full = R.universe(looks)
assert uni == {"AAA"} and full and len(days) == 14 and info["BBB"] == (14, 4), (uni, info)
assert R.universe(mk(1, 5, "AAA", 1))[3] is False                                                                 # provisional with under 14 days

# 5. count cannot leak an outcome: it never opens results.csv.gz and prints the same with any result file
def fixture(root, results_yes):
    close = ep(2026, 11, 3, 6)
    qrows, prows, rrows = [], [], []
    for d in range(1, 11):
        c = close + (d - 2) * 86400
        t = f"KXRAIN-26NOV{d:02d}-CHI"
        qrows.append(quote(c, t, 120, 0.10, 0.12)); prows += pop(c, t, 120, [20, 40])           # PoP 40 vs ask 12: YES signal
        rrows.append([0, t, "CHI", "E", iso(c), "finalized", "yes" if results_yes else "no", "", 1])
    put(root, ("2026-11-01", "1300"), "quotes", QCOLS, qrows); put(root, ("2026-11-01", "1300"), "pop", PCOLS, prows)
    put(root, ("2026-11-01", "1750"), "results", RCOLS, rrows)
with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
    fixture(a, True); fixture(b, False)
    opened = []
    out_a = "\n".join(R.count(a, opened)); out_b = "\n".join(R.count(b))
    assert out_a == out_b and "results" not in opened and set(opened) == {"quotes", "pop"}
    assert "trade signals: 10" in out_a and "PROVISIONAL" in out_a
    for word in ("profit", "PF", "pnl", "net", "Brier", "won", "lost", "rained", "yes result"):
        assert word.lower() not in out_a.lower().replace("pop", ""), word
    # and the CLI path agrees
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        R.main(["count", "--dir", a])
    assert buf.getvalue().strip() == out_a.strip()

# 6. read refuses before 2027-01-01 18:00 UTC, writes nothing, and refuses a second time
with tempfile.TemporaryDirectory() as d:
    R.RESULT_TXT, R.RESULT_MD, R.MARKER = Path(d) / "r.txt", Path(d) / "r.md", Path(d) / "started"
    for early in (ep(2027, 1, 1, 17) + 59 * 60, ep(2026, 12, 31, 23), ep(2026, 11, 5)):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            assert R.run(now=early, root=d) is None
        assert "Refusing: the read date is 2027-01-01 18:00 UTC" in buf.getvalue() and not R.RESULT_TXT.exists() and not R.MARKER.exists()
    with tempfile.TemporaryDirectory() as data:
        fixture(data, True)
        with contextlib.redirect_stdout(io.StringIO()):
            v = R.run(now=R.READ_NOT_BEFORE, root=data)           # exactly at the date is allowed; 10 trades is under 150
        assert v == "NOT_ENOUGH_DATA" and R.RESULT_TXT.exists()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            assert R.run(now=R.READ_NOT_BEFORE + 5, root=data) is None
        assert "Refusing to run again" in buf.getvalue()

# 7. the verdicts on synthetic looks (every city has a 2c spread, so the universe is everything)
def synth(n_days, win_rate_fn, pop=40, ask=12, mid_good=False):
    looks, res = {}, {}
    for i in range(n_days):
        for c in ("AAA", "BBB", "CCC"):
            tk = f"KXRAIN-D{i:03d}-{c}"
            looks[tk] = {"ticker": tk, "city": c, "day": datetime.fromordinal(datetime(2026, 11, 1).toordinal() + i).strftime("%Y-%m-%d"), "bid_c": ask - 2, "ask_c": ask,
                         "pop": pop, "bid_sz": 50, "ask_sz": 50, "t": float(i), "pop_union": pop / 100.0}
            res[tk] = "yes" if win_rate_fn(i, c) else "no"
    return looks, res
# a 12c ask that really pays 40% of the time: strong edge everywhere, PoP better than the 11c mid
def hit(i, c):
    return (i + "ABC".index(c[0])) % 5 < 2
looks, res = synth(60, hit)
v, lines = R.score(looks, res, n_tried=728698)
assert v == "NOT_YET_FALSIFIED", "\n".join(lines)        # 180 trades >= 150, PF huge in both halves, PoP Brier beats the mid, z large
# under 150 settled trades: NOT_ENOUGH_DATA and nothing scored
v, lines = R.score(*synth(40, lambda i, c: True))
assert v == "NOT_ENOUGH_DATA" and not any("Brier" in x for x in lines)
# unsettled markets are excluded and listed, not guessed
looks, res = synth(60, lambda i, c: True)
res.pop("KXRAIN-D059-AAA")
v, lines = R.score(looks, res)
assert "unsettled and excluded 1" in lines[0] and "KXRAIN-D059-AAA" in lines[0]
# FALSIFIED when it never rains where PoP said it would (PF under 1.2 in both halves)
v, lines = R.score(*synth(60, lambda i, c: False))
assert v == "FALSIFIED" and "profit factor" in lines[-1]
# Brier tie: a mid Brier equal to the PoP Brier is FALSIFIED ("at or below")
looks, res = synth(60, hit)
real = R.brier
R.brier = lambda pairs: 0.25
try:
    v, lines = R.score(looks, res)
finally:
    R.brier = real
assert v == "FALSIFIED" and "Brier" in lines[-1]
# a PF of exactly the bar passes it: "under 1.2" falsifies, 1.2 does not
assert not (1.2 < R.PF_HALF_MIN) and not (3.0 < R.Z_MIN)
# day-clustered z under 3 is FALSIFIED even when PF holds: one lucky day carries every win
looks, res = synth(60, lambda i, c: i == 30)
v, lines = R.score(looks, res)
assert v == "FALSIFIED"
# the half split: a date exactly on the midpoint goes to the second half
assert R.half_of("2026-11-01", "2026-11-01", "2026-11-03") == 0 and R.half_of("2026-11-02", "2026-11-01", "2026-11-03") == 1 and R.half_of("2026-11-03", "2026-11-01", "2026-11-03") == 1

# 8. the module has no network, key or order code and no em dash
src = Path(R.__file__).read_text()
for bad in ("urllib", "requests", "socket", "api_key", "\u2014"):
    assert bad not in src, bad
print("test_raincal: all passed")
