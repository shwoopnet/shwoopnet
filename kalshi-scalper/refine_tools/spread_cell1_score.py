"""W-SPREAD-CELL1 scorer (registration: SPORTS_SPREAD_CELL_REGISTRATION.md).

Run once, after the pull is complete:
  python3 -I kalshi-scalper/refine_tools/spread_cell1_score.py CANDLES.jsonl SPREAD_CELL1_EVENTS.json MARKETS.jsonl [SPREAD_CELL1_EXPECTED.json]

The optional 4th argument (made by spread_cell1_times_convert.py) adds LINE 2 to the same single
read: the same cell with the look measured from expected_expiration_time (else
occurrence_datetime) minus 48 h, a field known in advance. LINE 1 uses the realised close_time.
Without the file (or if it cannot be read) it prints 'line 2 not available'.

CANDLES.jsonl, one JSON object per line (the format of candles_sp.jsonl):
  {"_e": event ticker, "s": series, "c": event close ts,
   "h": {market ticker: [[end_period_ts, yes_ask, yes_bid, price, volume], ...]}}
  yes_ask / yes_bid are dollar strings or null.
SPREAD_CELL1_EVENTS.json: {"events": [[series, event ticker, close ts], ...]}
  An event not listed is in no sample.
MARKETS.jsonl, lines with "_m" (others ignored):
  {"_m": 1, "t": market ticker, "e": event ticker, "ct": "YYYY-MM-DDTHH:MM:SSZ" close,
   "res": "yes" or "no"}  (only settled yes/no markets count)

Cell (same as the original scorer): SPREAD, buy YES at the ask when the ask is
0.05 to <0.15, look = last one hour candle at or before close minus 48 h (not
older than 2 h before that point), per event the qualifying market whose YES mid
is nearest 0.5, hold to settlement, fee 0.07*p*(1-p) unrounded, slippage 0c and 1c.

Prints nothing about results until SPREADCELL1_PULL_COMPLETE (same folder as the
candles file, content 274) exists; prints once, then writes SPREADCELL1_READ_DONE.
"""
import sys, os, json, calendar, time, random

REQUESTS = 274
LO, HI = 0.05, 0.15
LOOK_SEC = 48 * 3600
STALE = 2 * 3600
MIN_N = 100


def ts(s):
    return calendar.timegm(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S"))


def fl(x):
    try:
        return float(x)
    except Exception:
        return None


def net(o, sl):
    p = o["p"]
    return (1.0 if o["win"] else 0.0) - p - sl - 0.07 * p * (1 - p)


def stats(xs):
    n = len(xs)
    m = sum(xs) / n
    gp = sum(x for x in xs if x > 0)
    gl = -sum(x for x in xs if x < 0)
    sd = (sum((x - m) ** 2 for x in xs) / (n - 1)) ** .5 if n > 1 else 0
    return m, (gp / gl if gl > 0 else float("inf")), (m / (sd / n ** .5) if sd > 0 else 0.0)


def boot_lo(xs, B=2000, seed=1):
    r = random.Random(seed)
    n = len(xs)
    ms = sorted(sum(xs[r.randrange(n)] for _ in range(n)) / n for _ in range(B))
    return ms[int(.05 * B)]


def label(n, pf1, lo, z):
    if n < MIN_N:
        return "UNDERPOWERED: no evidence at n = %d" % n
    if pf1 >= 1.5 and lo > 0 and z >= 3.1:
        return "PASS"
    if pf1 < 1.2 or lo < 0:
        return "FAIL"
    return "LEAD"


def event_time(rec):
    """Line 2 time of an event: expected_expiration_time, else occurrence_datetime, else None."""
    if not isinstance(rec, dict):
        return None
    return rec.get("expected_expiration_time") or rec.get("occurrence_datetime") or None


def _observations(candles_path, events_path, markets_path, expected=None):
    """Returns (observations, missing). expected None: Line 1 (each market's realised close).
    expected {event: times}: Line 2; missing counts events with no usable look (no time, or no
    fresh candle at the look, i.e. the look is outside the pulled candles)."""
    events = {e[1] for e in json.load(open(events_path))["events"]}
    mk = {}
    for l in open(markets_path):
        j = json.loads(l)
        if "_m" in j and j.get("res") in ("yes", "no"):
            mk[j["t"]] = j
    best = {}
    seen = set()
    missing = 0
    for l in open(candles_path):
        if not l.strip():
            continue
        j = json.loads(l)
        e = j["_e"]
        if e not in events or e in seen:
            continue
        seen.add(e)
        et = None
        if expected is not None:
            et = event_time(expected.get(e))
            if et is None:
                missing += 1
                continue
        fresh = False
        for t, cs in j["h"].items():
            m = mk.get(t)
            if not m:
                continue
            at = (ts(et) if expected is not None else ts(m["ct"])) - LOOK_SEC
            q = None
            for c in sorted(cs):
                if c[0] <= at:
                    q = c
                else:
                    break
            if not q or at - q[0] > STALE:
                continue
            fresh = True
            ask, bid = fl(q[1]), fl(q[2])
            if ask is None or bid is None or not (0 < ask < 1) or not (0 <= bid < ask):
                continue
            if not (LO <= ask < HI):
                continue
            o = dict(p=ask, win=(m["res"] == "yes"), dist=abs((ask + bid) / 2 - 0.5))
            if e not in best or o["dist"] < best[e]["dist"]:
                best[e] = o
        if expected is not None and not fresh:
            missing += 1
    return list(best.values()), missing


def observations(candles_path, events_path, markets_path):
    return _observations(candles_path, events_path, markets_path)[0]


def block(obs):
    """Read lines and (label, n, pf1 or None) for one line."""
    n = len(obs)
    lines = []
    if n < MIN_N:
        lab = label(n, 0, 0, 0)  # under n 100 print only the label: no PF, mean, bound or z
        lines.append(lab)
        return lines, lab, n, None
    res = {}
    for sl in (0.0, 0.01):
        res[sl] = stats([net(o, sl) for o in obs])
        lines.append("+%dc: mean %+.3fc  PF %.3f" % (round(sl * 100), res[sl][0] * 100, res[sl][1]))
    lo = boot_lo([net(o, 0.01) for o in obs])
    m1, pf1, z = res[0.01]
    lines.append("+1c event-clustered 90%% lower bound of the mean: %+.3fc" % (lo * 100))
    lines.append("+1c one-sided z: %.2f" % z)
    lab = label(n, pf1, lo, z)
    lines.append("LABEL: " + lab)
    return lines, lab, n, pf1


def main(argv):
    if len(argv) not in (4, 5):
        print("usage: spread_cell1_score.py CANDLES.jsonl EVENTS.json MARKETS.jsonl [EXPECTED.json]")
        return 2
    cpath, epath, mpath = argv[1:4]
    xpath = argv[4] if len(argv) == 5 else None
    d = os.path.dirname(os.path.abspath(cpath))
    marker = os.path.join(d, "SPREADCELL1_PULL_COMPLETE")
    done = os.path.join(d, "SPREADCELL1_READ_DONE")
    try:
        complete = int(open(marker).read().strip()) == REQUESTS
    except Exception:
        complete = False
    if not complete:
        print("pull incomplete")
        return 0
    if os.path.exists(done):
        print("already read")
        return 0
    obs = observations(cpath, epath, mpath)
    l1, lab1, n1, _ = block(obs)
    lines = ["W-SPREAD-CELL1 read (once): n = %d events in the cell" % n1] + l1
    expected = None
    if xpath:
        try:
            expected = json.load(open(xpath))
            if not isinstance(expected, dict):
                expected = None
        except Exception:
            expected = None
    lines.append("")
    if expected is None:
        lines.append("line 2 not available")
    else:
        obs2, missing = _observations(cpath, epath, mpath, expected)
        l2, lab2, n2, pf2 = block(obs2)
        lines.append("LINE 2 (look from expected_expiration_time, else occurrence_datetime, minus 48 h): n = %d events in the cell" % n2)
        lines += l2
        lines.append("events with no Line 2 observation (no time, or look outside the pulled candles): %d" % missing)
        eligible = lab1 == "PASS" and n2 >= MIN_N and pf2 is not None and pf2 >= 1.3
        lines.append("probe-eligible only if LINE 2 is PF 1.3 or more at +1c with n 100 or more: %s"
                     % ("YES (LINE 1 is PASS and LINE 2 meets it)" if eligible else "NO"))
    print("\n".join(lines))
    open(done, "w").write("read\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
