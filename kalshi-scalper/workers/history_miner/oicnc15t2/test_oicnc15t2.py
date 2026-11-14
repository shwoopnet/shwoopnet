"""Invented runs for oicnc15t2.py (no Kalshi data): the hand case of OICNC15T2_HAND_CASE_NOV14.md. Run: python3 -I test_oicnc15t2.py"""
import calendar, gzip, hashlib, json, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import oicnc15t2 as O

MONS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def ticker(series, close):
    for off in (4, 5):                                    # the US Eastern wall time of a close
        t = close - off * 3600
        y, mo, d, h, mi = [int(x) for x in __import__("time").strftime("%Y %m %d %H %M", __import__("time").gmtime(t)).split()]
        if O.eastern_epoch(y, mo, d, h, mi) == close:
            return "%s-%02d%s%02d%02d%02d-00" % (series, y % 100, MONS[mo - 1], d, h, mi)
    raise AssertionError("no eastern time")


def weekdays_before(y, mo, d, n):
    out, t = [], calendar.timegm((y, mo, d, 0, 0, 0))
    while len(out) < n:
        t -= 86400
        if calendar.weekday(*__import__("time").gmtime(t)[:3]) < 5:
            out.append(t)
    return sorted(out)


def cs(close, oi360, oi180, drop180=False, null180=False, field="open_interest_fp"):
    out = [{"end_period_ts": close - 360, field: None if oi360 is None else ("%.2f" % oi360 if field == "open_interest_fp" else oi360)}]
    if not drop180:
        out.append({"end_period_ts": close - 180, field: None if null180 else ("%.2f" % oi180 if field == "open_interest_fp" else oi180)})
    return out


def write_run(jb, answers, status="complete", answered=None):
    d = os.path.join(tempfile.mkdtemp(), "run"); os.makedirs(d); rows = []; n = 0
    for r in jb["requests"]:
        if answered is not None and r["id"] not in answered:
            continue
        if r["id"] not in answers:
            continue
        n += 1; raw = json.dumps(answers[r["id"]]).encode(); fn = "%04d.json.gz" % n
        gzip.open(os.path.join(d, fn), "wb").write(raw)
        rows.append({"index": n, "id": r["id"], "path": r["path"], "page": 1, "status": 200, "bytes": len(raw), "file": fn, "sha256": hashlib.sha256(raw).hexdigest(), "truncated": False})
    json.dump({"job": jb, "status": status, "rows": rows}, open(os.path.join(d, "manifest.json"), "w")); return d


def refused(fn, word):
    try:
        fn(); raise AssertionError("not refused: " + word)
    except (SystemExit, O.Stop) as e:
        assert word in str(e), (word, str(e))


def build(windows):
    """windows: list of (request close, [(ticker, candlesticks)]). Returns base jobs split 1/2, a REST job for 1, and the answers."""
    reqs, ans = [], {}
    for i, (close, mks) in enumerate(windows, 1):
        rid = "c%04d" % i
        reqs.append({"id": rid, "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(t for t, _ in mks), "start_ts": close - 420, "end_ts": close - 120, "period_interval": 1}})
        ans[rid] = {"markets": [{"market_ticker": t, "candlesticks": c} for t, c in mks]}
    h = len(reqs) // 2
    j1 = {"job_id": "OICAND_CANDLES_1", "requests": reqs[:h]}
    j1r = {"job_id": "OICAND_CANDLES_1_REST", "requests": reqs[h // 2:h]}
    j2 = {"job_id": "OICAND_CANDLES_2", "requests": reqs[h:]}
    return j1, j1r, j2, ans, reqs


def runs_for(j1, j1r, j2, ans, reqs):
    h = len(reqs) // 2
    r1 = write_run(j1, ans, status="stopped_time", answered={r["id"] for r in reqs[:h // 2]})
    r1r = write_run(j1r, ans)
    r2 = write_run(j2, ans)
    return [(r1, j1), (r1r, j1r), (r2, j2)]


# --- the main fixture: HYPE (rise k on day k), BNB (19 days, rise 7), SILVER in every answer
days = weekdays_before(2026, 11, 13, 24)                      # 24 weekdays before Nov 13 (a Friday), oldest first
W = []
for k, t0 in enumerate(days, 1):
    close = t0 + 15 * 3600                                    # 15:00Z
    mks = []
    if k <= 22:
        mks.append((ticker("KXHYPE15M", close), cs(close, 1000, 1000 + k)))
    elif k == 23:
        mks.append((ticker("KXHYPE15M", close), cs(close, 1000, None, drop180=True)))       # missing candle
    else:
        mks.append((ticker("KXHYPE15M", close), cs(close, 1000, None, null180=True)))       # no open interest
    if 4 <= k <= 22:
        mks.append((ticker("KXBNB15M", close), cs(close, 500, 507, field="open_interest")))  # the plain field
    mks.append((ticker("KXSILVER15M", close), cs(close, 5, 99999)))                         # another series
    W.append((close, mks))
c830 = calendar.timegm((2026, 11, 5, 13, 30, 0))
W.append((c830, [(ticker("KXHYPE15M", c830), cs(c830, 1000, 9999))]))
crep = days[21] + 16 * 3600                                    # day 22, 16:00Z, in two requests
W.append((crep, [(ticker("KXHYPE15M", crep), cs(crep, 1000, 1500))]))
W.append((crep, [(ticker("KXHYPE15M", crep), cs(crep, 1000, 1500))]))
W.sort(key=lambda x: x[0])
j1, j1r, j2, ans, reqs = build(W)
RJ = runs_for(j1, j1r, j2, ans, reqs)
res = O.thresholds(O.merge(RJ))
H, B = res["series"]["KXHYPE15M"], res["series"]["KXBNB15M"]
assert H["dropped"] == {"event830_cut": 1, "missing_candle": 1, "no_open_interest": 1, "repeated_ticker": 2, "outside_20_days": 2}, H
assert H["trading_days_available"] == 22 and H["trading_days_used"] == 20 and H["n"] == 20 and H["rank"] == 18 and H["T"] == 20.0 and H["seated"], H
assert B["trading_days_available"] == 19 and B["T"] == 7.0 and not B["seated"] and B["not_seated_reason"] == ["fewer than 20 trading days (19)"], B
assert res["other_series_candle_sets_skipped_unread"] == 24, res
refused(lambda: O.thresholds(O.merge(RJ), series=("KXSILVER15M",)), "not allowed")
print("main fixture: ok", H["T"], B["T"])

# --- variants Z (T 0) and S (T 4)
for rise, why in ((0, "T is 0"), (4, "T under 5 contracts")):
    Wv = [(t0 + 15 * 3600, [(ticker("KXHYPE15M", t0 + 15 * 3600), cs(t0 + 15 * 3600, 100, 100 + rise))]) for t0 in days[-20:]]
    v = O.thresholds(O.merge(runs_for(*build(Wv))))["series"]["KXHYPE15M"]
    assert v["T"] == float(rise) and not v["seated"] and v["not_seated_reason"] == [why], v
print("variants Z and S: ok")

# --- merge
refused(lambda: O.merge(RJ + [(write_run(j2, ans), j2)]), "two runs")                                   # an id in two runs
refused(lambda: O.merge([RJ[0], RJ[2]]), "in no run")                                                     # REST missing
bad = {"job_id": "OICAND_CANDLES_1_REST", "requests": [dict(r, params=dict(r["params"], end_ts=1)) for r in j1r["requests"]]}
refused(lambda: O.merge([RJ[0], (write_run(bad, ans), bad), RJ[2]]), "differs")
refused(lambda: O.merge([(write_run(j1, ans, status="stopped_429"), j1), RJ[2]]), "not complete or stopped_time")
refused(lambda: O.merge([(RJ[0][0], j2)] + RJ[1:]), "committed job")
tk = ticker("KXHYPE15M", days[0] + 15 * 3600)
Wb = [(days[0] + 16 * 3600, [(tk, cs(days[0] + 15 * 3600, 1, 2))]), (days[1] + 15 * 3600, [(ticker("KXHYPE15M", days[1] + 15 * 3600), cs(days[1] + 15 * 3600, 1, 2))])]
refused(lambda: O.thresholds(O.merge(runs_for(*build(Wb)))), "does not match")                            # a close not matching its ticker
print("merge: ok")

# --- guard
L = os.path.join(tempfile.mkdtemp(), "HELDOUT_PULL_RUNS.md")
open(L, "w").write("| Run folder | Job | What |\n|---|---|---|\n| `OICAND_LISTS/2026-11-14T0227Z_43546384963` | x | y |\n| `OICAND_CANDLES_1/2026-11-14T0253Z_43548715053` | x | y |\n| `OTHER/2026-11-01T0000Z_1` | x | y |\n")
base = tempfile.mkdtemp()
for name, ok in (("2026-11-14T0253Z_43548715053", True), ("2026-11-14T0227Z_43546384963", False), ("2026-11-01T0000Z_1", False)):
    p = os.path.join(base, "pull", "X", name); os.makedirs(p, exist_ok=True)
    if ok:
        O.guard_path(p, L)
    else:
        refused(lambda: O.guard_path(p, L), "REFUSED")
hp = os.path.join(base, "HELDOUT_x"); os.makedirs(hp)
refused(lambda: O.guard_path(hp, L), "HELDOUT_")
refused(lambda: O.guard_path(base, os.path.join(base, "nope.md")), "cannot be read")
print("guard: ok")
