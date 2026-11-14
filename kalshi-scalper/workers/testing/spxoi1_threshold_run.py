#!/usr/bin/env python3
"""SPXOI1 threshold T (Testing Desk, Nov 14, 2026). Research only: reads the files it is given, sends nothing, writes NO file. Uses my audited spxoi1.py (be22330d) for the rise and scorekit (f219b43c) for the readers.
Reading fixed by the Head (01:17Z) to match Desk A's audited build (spxoi1_threshold.py 4b5ec189): windows = KXINX15M markets with close_time in [2026-11-05T00:00:00Z, 2026-11-14T00:00:00Z);
oi_rise = open interest at the candle ending exactly close - 180 s minus the one ending exactly close - 360 s; a missing candle drops the window ("missing candle"); a non-finite, non-numeric, absent or boolean open interest drops it ("unreadable open interest");
every computable rise is kept (zero and negative included); T = the nearest-rank P90: sort ascending, rank = ceil(0.9 n - 1e-12), 1-based, no interpolation. Prints n, T and the two drop counts; the count of windows with rise >= T is an EXTRA line.
No price, no result and no outcome is read, and nothing is printed per window. Hand case: SPXOI1_THRESHOLD_HAND_CASE.md (committed first). Test: test_spxoi1_threshold_run.py (INVENTED rows only).
Refuses unless spxoi1.py and scorekit.py hash to the audited builds. Run ONCE; commit the print before comparing.
Usage: spxoi1_threshold_run.py <lists run> --candles <candle run>...
"""
import calendar, hashlib, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scorekit as k

SERIES = "KXINX15M"
FROM = calendar.timegm((2026, 11, 5, 0, 0, 0))
TO = calendar.timegm((2026, 11, 14, 0, 0, 0))
AUDITED = {"spxoi1.py": "be22330d6d8d9f03", "scorekit.py": "f219b43c755b4b87"}
TOL = 1e-9


def check_hashes(want=None):
    for name, pre in (want or AUDITED).items():
        got = hashlib.sha256(open(os.path.join(HERE, name), "rb").read()).hexdigest()[:16]
        if got != pre:
            raise SystemExit("refused: %s is not the audited build (%s, wanted %s)" % (name, got, pre))


def nearest_rank_p90(vals):
    n = len(vals)
    if n == 0:
        return None
    rank = math.ceil(0.9 * n - 1e-12)
    return sorted(vals)[rank - 1]


def bool_oi(candle_runs):
    """{(ticker, ts)} of candles whose raw open interest is a JSON boolean (scorekit would read True as 1.0)."""
    out = set()
    for f in candle_runs:
        for row, body in k.iter_answers(f):
            nodes = body.get("markets") if isinstance(body, dict) and isinstance(body.get("markets"), list) else [body]
            for n in nodes:
                if not isinstance(n, dict) or not isinstance(n.get("candlesticks"), list):
                    continue
                tk = n.get("market_ticker") or n.get("ticker") or row["id"]
                for c in n["candlesticks"]:
                    if isinstance(c, dict) and isinstance(c.get("open_interest_fp", c.get("open_interest")), bool):
                        try:
                            out.add((tk, int(c["end_period_ts"])))
                        except (KeyError, TypeError, ValueError):
                            pass
    return out


def compute(markets, cs, bools):
    import spxoi1
    res = {"windows_listed": 0, "outside_range_not_read": 0, "missing_candle": 0, "unreadable_open_interest": 0}
    rises = []
    for tk in sorted(markets):
        m = markets[tk]
        if m["series"] != SERIES:
            continue
        res["windows_listed"] += 1
        c = m["close"]
        if c is None or not (FROM <= c < TO):
            res["outside_range_not_read"] += 1; continue
        cand = cs.get(tk)
        by = {x["ts"]: x for x in (cand or [])}
        a, b = by.get(c - spxoi1.OI_RECENT_S), by.get(c - spxoi1.OI_EARLIER_S)
        if a is None or b is None:
            res["missing_candle"] += 1; continue
        if (tk, a["ts"]) in bools or (tk, b["ts"]) in bools or a.get("oi") is None or b.get("oi") is None:
            res["unreadable_open_interest"] += 1; continue
        rise = spxoi1.oi_rise(cand, c)
        if rise is None or not math.isfinite(rise):
            res["unreadable_open_interest"] += 1; continue
        rises.append(rise)
    res["n"] = len(rises)
    res["T"] = nearest_rank_p90(rises)
    res["extra_windows_with_rise_ge_T"] = sum(1 for r in rises if res["T"] is not None and r >= res["T"] - TOL)
    return res


def run(lists, candle_runs, hash_check=True):
    if hash_check:
        check_hashes()
    for f in list(lists) + list(candle_runs):
        k.guard(f)
    out = compute(k.markets(lists), k.candles(candle_runs), bool_oi(candle_runs))
    out["python"] = "%s at %s" % (sys.version.split()[0], sys.executable)
    return out


def render(r):
    return "\n".join(["python %s" % r["python"], "n = %d" % r["n"], "T = %s" % r["T"], "missing candle = %d" % r["missing_candle"], "unreadable open interest = %d" % r["unreadable_open_interest"],
                      "outside range, not read = %d (of %d KXINX15M windows listed)" % (r["outside_range_not_read"], r["windows_listed"]),
                      "extra: windows with rise >= T = %d" % r["extra_windows_with_rise_ge_T"]])


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--candles" in a and a.index("--candles") >= 1:
        i = a.index("--candles")
        print(render(run(a[:i], a[i + 1:])))
    else:
        print(__doc__)
