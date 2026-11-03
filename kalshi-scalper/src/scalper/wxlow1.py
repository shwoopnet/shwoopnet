"""WXLOW1 (README, Pre-registration: WXLOW1; workers/WXLOW1_REGISTRATION.md): the WXENS1 rule, unchanged, on the Kalshi daily LOW temperature markets (KXLOWT*). Research only.
Every constant, the probability model, the trade choice, the fees and the verdict come from `scalper.wxens1` (nothing is copied or changed here); this module only reads the `_low` tables
the recorder writes and adds the lows-alone read and the pooled highs + lows read. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. No order of any kind exists here.

Usage (DATA is the checked out `quote-data` branch directory that holds wxens/):
  python -m scalper.wxlow1 snapshot [DATA] [--wide] [--results]   one manual snapshot (highs and lows), same as the hourly recorder
  python -m scalper.wxlow1 cities DATA     freeze the 8 tested LOW cities from the first 7 low target dates of volume (refuses to overwrite)
  python -m scalper.wxlow1 count DATA      trade COUNTS only (lows, highs, pooled; no outcome is read)
  python -m scalper.wxlow1 run DATA        WXLOW1-L, the one registered lows read (refused before 300 low trades or 2027-02-28, and a second time)
  python -m scalper.wxlow1 pooled DATA     WXLOW1-P, the one pooled read (refused before 300 pooled trades or 2027-02-28, before both city sets are frozen, and a second time); prints pooled numbers only
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone

from . import wxens1 as W

SFX, VCOL, OCOL = "_low", "tmin_f", "iem_min_tmpf"


def _low_cities_file(d):
    return os.path.join(d, "wxlow1_cities.json")


def _low_frozen(d):
    try:
        return json.load(open(_low_cities_file(d)))["cities"]
    except (OSError, ValueError, KeyError):
        return None


def build_low(data_dir, watchlist):
    return W.build(data_dir, watchlist, SFX, VCOL, OCOL)


def _stop():
    return datetime.now(timezone.utc).date().isoformat() >= W.STOP_DATE


def _eta(have, per_day, target):
    left = max(0, target - have)
    if left == 0:
        return "reached"
    return (datetime.now(timezone.utc) + timedelta(days=left / per_day)).date().isoformat() if per_day > 0 else "unknown"


def cmd_cities(data_dir, watchlist):
    f = _low_cities_file(data_dir)
    if os.path.exists(f):
        print("refused: the low city set is already frozen:", open(f).read())
        return 1
    days, _ = build_low(data_dir, watchlist)
    dates = sorted({d for (_, d) in days})
    if len(dates) < W.CITY_DAYS:
        print("NOT YET: %d of %d low target dates have a primary poll" % (len(dates), W.CITY_DAYS))
        return 1
    cs = W.choose_cities(days)
    json.dump({"cities": cs, "from_dates": dates[:W.CITY_DAYS]}, open(f, "w"))
    print("frozen (lows):", cs)
    return 0


def cmd_count(data_dir, watchlist):
    dl, _ = build_low(data_dir, watchlist)
    dh, _ = W.build(data_dir, watchlist)
    cl = _low_frozen(data_dir) or sorted({c for (c, _) in dl})
    ch = W._frozen(data_dir) or sorted({c for (c, _) in dh})
    sl, ctl_l = W.trade_list(dl, cl)
    sh, ctl_h = W.trade_list(dh, ch)
    nl, nh = len({d for (_, d) in dl}), len({d for (_, d) in dh})
    rl, rh = (len(sl) / nl if nl else 0.0), (len(sh) / nh if nh else 0.0)
    pooled = len(sl) + len(sh)
    print("lows: city set %s, %d target dates, %d selected (%.2f a day), control %d, 150 about %s" % (
        "frozen" if _low_frozen(data_dir) else "NOT frozen", nl, len(sl), rl, len(ctl_l), _eta(len(sl), rl, W.MIN_TRADES)))
    print("highs: city set %s, %d target dates, %d selected (%.2f a day), 150 about %s" % (
        "frozen" if W._frozen(data_dir) else "NOT frozen", nh, len(sh), rh, _eta(len(sh), rh, W.MIN_TRADES)))
    print("pooled: %d selected (%.2f a day), 150 about %s, 300 about %s; counts only, no outcome read" % (
        pooled, rl + rh, _eta(pooled, rl + rh, W.MIN_TRADES), _eta(pooled, rl + rh, W.FULL_TRADES)))
    return 0


def _report(v, info, sel, ctl):
    cm = sum(t["net"] for t in ctl) / len(ctl) if ctl else 0.0
    text = "%s\n%s\ncontrol (all cheap brackets): n %d mean %+.4f\nwin rate %.4f vs mean price %.4f\n" % (
        v, json.dumps(info, sort_keys=True), len(ctl), cm, (sum(t["won"] for t in sel) / len(sel)) if sel else 0.0, (sum(t["price"] for t in sel) / len(sel)) if sel else 0.0)
    if info.get("mde", 0) > 0.02 and v == "FALSIFIED":
        text += "not shown at this sample size: minimum detectable mean %.4f\n" % info["mde"]
    return text


def cmd_run(data_dir, watchlist):
    out = os.path.join(data_dir, "wxlow1_result.txt")
    if os.path.exists(out):
        print("refused: the registered lows run was already done:", out)
        return 1
    cities = _low_frozen(data_dir)
    if not cities:
        print("refused: the low city set is not frozen (python -m scalper.wxlow1 cities DATA)")
        return 1
    days, _ = build_low(data_dir, watchlist)
    sel, _ = W.trade_list(days, cities)
    stop = _stop()
    if len(sel) < W.FULL_TRADES and not stop:
        print("refused: %d of %d low trades and before %s; use count" % (len(sel), W.FULL_TRADES, W.STOP_DATE))
        return 1
    sel, ctl = W.trade_list(days, cities, W.results_by_ticker(data_dir, SFX))
    v, info = W.verdict(sel, stop)
    text = "WXLOW1-L (lows alone)\n" + _report(v, info, sel, ctl)
    open(out, "w").write(text)
    print(text)
    return 0


def cmd_pooled(data_dir, watchlist):
    out = os.path.join(data_dir, "wxlow1_pooled_result.txt")
    if os.path.exists(out):
        print("refused: the registered pooled run was already done:", out)
        return 1
    cl, ch = _low_frozen(data_dir), W._frozen(data_dir)
    if not cl or not ch:
        print("refused: both city sets must be frozen (python -m scalper.wxens1 cities DATA, python -m scalper.wxlow1 cities DATA)")
        return 1
    dl, _ = build_low(data_dir, watchlist)
    dh, _ = W.build(data_dir, watchlist)
    sl, _ = W.trade_list(dl, cl)
    sh, _ = W.trade_list(dh, ch)
    stop = _stop()
    if len(sl) + len(sh) < W.FULL_TRADES and not stop:
        print("refused: %d of %d pooled trades and before %s; use count" % (len(sl) + len(sh), W.FULL_TRADES, W.STOP_DATE))
        return 1
    sl, ctl_l = W.trade_list(dl, cl, W.results_by_ticker(data_dir, SFX))
    sh, ctl_h = W.trade_list(dh, ch, W.results_by_ticker(data_dir))
    # pooled numbers only: no figure is printed for the highs or the lows alone. The date is the cluster, so a highs and a lows trade of one day share a cluster.
    sel, ctl = sl + sh, ctl_l + ctl_h
    v, info = W.verdict(sel, stop)
    text = "WXLOW1-P (highs on the WXENS1 city set + lows, pooled numbers only)\n" + _report(v, info, sel, ctl)
    open(out, "w").write(text)
    print(text)
    return 0


def main(argv):
    watch = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "workers", "WXENS1_WATCHLIST.json")
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "snapshot":
        return W.cmd_snapshot(argv[1:])
    if cmd in ("cities", "count", "run", "pooled") and len(argv) >= 2:
        return {"cities": cmd_cities, "count": cmd_count, "run": cmd_run, "pooled": cmd_pooled}[cmd](argv[1], watch)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
