"""W-SPREAD-CELL1 scorer (registration: SPORTS_SPREAD_CELL_REGISTRATION.md).

Run once, after the pull is complete:
  python3 -I kalshi-scalper/refine_tools/spread_cell1_score.py CANDLES.jsonl SPREAD_CELL1_EVENTS.json MARKETS.jsonl

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


def observations(candles_path, events_path, markets_path):
    events = {e[1] for e in json.load(open(events_path))["events"]}
    mk = {}
    for l in open(markets_path):
        j = json.loads(l)
        if "_m" in j and j.get("res") in ("yes", "no"):
            mk[j["t"]] = j
    best = {}
    seen = set()
    for l in open(candles_path):
        if not l.strip():
            continue
        j = json.loads(l)
        e = j["_e"]
        if e not in events or e in seen:
            continue
        seen.add(e)
        for t, cs in j["h"].items():
            m = mk.get(t)
            if not m:
                continue
            at = ts(m["ct"]) - LOOK_SEC
            q = None
            for c in sorted(cs):
                if c[0] <= at:
                    q = c
                else:
                    break
            if not q or at - q[0] > STALE:
                continue
            ask, bid = fl(q[1]), fl(q[2])
            if ask is None or bid is None or not (0 < ask < 1) or not (0 <= bid < ask):
                continue
            if not (LO <= ask < HI):
                continue
            o = dict(p=ask, win=(m["res"] == "yes"), dist=abs((ask + bid) / 2 - 0.5))
            if e not in best or o["dist"] < best[e]["dist"]:
                best[e] = o
    return list(best.values())


def main(argv):
    if len(argv) != 4:
        print("usage: spread_cell1_score.py CANDLES.jsonl EVENTS.json MARKETS.jsonl")
        return 2
    cpath, epath, mpath = argv[1:4]
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
    n = len(obs)
    lines = ["W-SPREAD-CELL1 read (once): n = %d events in the cell" % n]
    if n < 100:
        lines.append(label(n, 0, 0, 0))  # under n 100 print only the label: no PF, mean, bound or z
    else:
        res = {}
        for sl in (0.0, 0.01):
            res[sl] = stats([net(o, sl) for o in obs])
            lines.append("+%dc: mean %+.3fc  PF %.3f" % (round(sl * 100), res[sl][0] * 100, res[sl][1]))
        lo = boot_lo([net(o, 0.01) for o in obs])
        m1, pf1, z = res[0.01]
        lines.append("+1c event-clustered 90%% lower bound of the mean: %+.3fc" % (lo * 100))
        lines.append("+1c one-sided z: %.2f" % z)
        lines.append("LABEL: " + label(n, pf1, lo, z))
    print("\n".join(lines))
    open(done, "w").write("read\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
