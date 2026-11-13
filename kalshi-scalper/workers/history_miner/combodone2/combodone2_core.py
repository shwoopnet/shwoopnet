"""COMBODONE stage 1, SECOND BUILD (History Miner, Nov 13, 2026): the pure counting rules, from the card only (claude/idea-desk-c 593597e6, COMBODONE_CARD.md, Amendments 1 and 2).
Not built from, and never read against, Desk B's combodone.py. I/O lives in combodone2.py; this module takes parsed rows."""
import calendar, math, statistics

TOL = 1e-9
ASK_MAX_CENTS = 87
SETTLE_LEAD_S = 60
RUNS_PER_DAY, WEEK_DAYS, WEEK_MIN_RUNS, DAY_MIN_RUNS = 48, 7, 269, 24
KILL_MIN_COMBOS = 30


def day_of(ts):
    return "%04d-%02d-%02d" % tuple(__import__("time").gmtime(ts)[:3])


def day_epoch(day):
    return calendar.timegm(tuple(int(x) for x in day.split("-")) + (0, 0, 0))


def next_day(day, k=1):
    return day_of(day_epoch(day) + 86400 * k)


def cents_up(x):
    """Round UP to the whole cent with a 1e-9 tolerance (0.8700 -> 87, 0.8701 -> 88)."""
    return int(math.ceil(x * 100 - TOL))


def pick_week(runs_by_day, last_folder_day):
    """Amendment 1 point 1, Amendment 2 point 10: the earliest 7 consecutive UTC days, each over (a run folder exists on a later day), with at least 269 completed runs in all and at least 24
    on every day. runs_by_day: {day: completed run count by folder date}. Returns the first day, or None."""
    days = sorted(runs_by_day)
    if not days:
        return None
    d = days[0]
    while d < last_folder_day:
        week = [next_day(d, k) for k in range(WEEK_DAYS)]
        if week[-1] < last_folder_day:
            n = [runs_by_day.get(x, 0) for x in week]
            if sum(n) >= WEEK_MIN_RUNS and min(n) >= DAY_MIN_RUNS:
                return d
        d = next_day(d)
    return None


def parse_legs(s):
    """'T1:yes|T2:no' -> [(ticker, side)]; None if empty or cut ('|...'). A part without a yes/no side keeps side None (leg unknown)."""
    if not s:
        return None
    if s.endswith("|..."):
        return None
    out = []
    for p in s.split("|"):
        t, _, side = p.rpartition(":") if ":" in p else (p, "", "")
        out.append((t, side if side in ("yes", "no") else None))
    return out


def classify(t, legs_str, legs_count, close_ts, leg_info):
    """One quotes row at receive time t (seconds). Returns (category, still-unsettled set or None). Amendment 2 point 13 order; the leg-list test (card (a)) comes first.
    leg_info: {ticker: (result or None/'' , settlement_ts or None)}; a leg absent from it is unknown."""
    legs = parse_legs(legs_str)
    if legs is None:
        return ("no_leg_list", None)
    try:
        f = float(legs_count)
        lc = int(f) if f == int(f) else None          # Amendment 4 point 20: a legs value that is not a whole number is "leg unknown"
    except (TypeError, ValueError, OverflowError):
        lc = None
    if lc != len(legs) or any(side is None for _, side in legs) or any(tk not in leg_info for tk, _ in legs):
        return ("leg_unknown", None)
    for tk, _ in legs:
        res, st = leg_info[tk]
        if res and st is None:
            return ("leg_unknown", None)                      # a result with no settlement time
    settled = {tk: (st is not None and st <= t) for tk, (res, st) in ((tk, leg_info[tk]) for tk, _ in legs)}
    for tk, side in legs:
        res, st = leg_info[tk]
        if settled[tk] and res not in ("yes", "no"):
            return ("leg_other_result", None)                 # includes an EMPTY result settled at or before t (point 14)
    for tk, side in legs:
        res, st = leg_info[tk]
        if settled[tk] and res != side:
            return ("leg_against", None)
    if not any(leg_info[tk][1] is not None and leg_info[tk][1] <= t - SETTLE_LEAD_S and leg_info[tk][0] == side for tk, side in legs):
        return ("no_leg_for_60s", None)
    unsettled = sorted("%s:%s" % (tk, side) for tk, side in legs if not settled[tk])
    if not unsettled:
        return ("all_legs_settled", None)
    if close_ts is None or close_ts <= t:
        return ("combo_closed", None)
    return ("eligible", tuple(unsettled))


def resting_ask(yes_ask, yes_ask_size):
    try:
        a, s = float(yes_ask), float(yes_ask_size)
    except (TypeError, ValueError):
        return False
    return a > TOL and cents_up(a) <= ASK_MAX_CENTS and s >= 1 - TOL


def book_ask(no_bid_px_1, no_bid_sz_1):
    try:
        a, s = 1 - float(no_bid_px_1), float(no_bid_sz_1)
    except (TypeError, ValueError):
        return False
    return a > TOL and cents_up(a) <= ASK_MAX_CENTS and s >= 1 - TOL
