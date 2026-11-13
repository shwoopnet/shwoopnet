#!/usr/bin/env python3
"""NHLOT (card 17, workers/IDEA_DESK_B_WAVE3.md): the PRICE measurement, zero tries.
Committed Nov 12, 2026, BEFORE any NHL list or candle was pulled.

It measures two things and nothing else:
  1. how often the overtime detection rule fires, and
  2. the price of the cheaper side of the moneyline at that minute.
No outcome is read: the script never looks at a minute later than one minute after the
detection minute, never reads a result field, and scores no trade.

Kill rules for the card (as written in the card):
  - the cheaper side's ask is 43c or lower (spread 3c or less) in fewer than 30% of detected
    overtimes: CLOSED, the market already prices overtime as close to even;
  - the rule fires in fewer than 12% or more than 35% of games: CLOSED, it is not detecting
    overtime;
  - fewer than 30 detections: NOT_ENOUGH_DATA.

Usage: python3 measure_prices.py <folder of the candle pull run> <games.json>
games.json: [{"game": ..., "ml": [t1, t2], "total": [strike tickers...], "close_ts": ...}, ...]
"""
import gzip
import hashlib
import json
import statistics
import os
import sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
from deskb_guard import refuse_all as _refuse_all
_refuse_all()   # standing rule (h): refuse any HELDOUT_ folder before the first open or glob

# ---- pinned constants (the card carries the same values) ----
LOW, HIGH = 0.07, 0.93      # a total strike is decided NO if its YES ask is at or under LOW, decided YES if its YES bid is at or over HIGH
MIN_STRIKES = 4             # at least this many total strikes must have a quote that minute
ML_BAND = (0.30, 0.70)      # both moneyline mids must be inside
LAST_MIN = 45               # the 45 one-minute candles ending after the close minus 2,700 s and at or before the close (third amendment)
EDGE_MIN = 5                # "the first 5 minutes of the window": a candle ending at or before the close minus 2,400 s
OT_YES, OT_NO = 0.93, 0.07  # the overtime market cross-check (third amendment, point 3)
ASK_BAR = 0.43              # the cheaper side's ask
SPREAD_BAR = 0.03
SHARE_BAR = 0.30            # under this share of detections at ASK_BAR or lower closes the card
FIRE_RANGE = (0.12, 0.35)   # share of games in which the rule should fire if it detects overtime
MIN_DETECTIONS = 30


def price(side):
    if not isinstance(side, dict):
        return None
    for k in ("close_dollars", "close"):
        v = side.get(k)
        if v in (None, ""):
            continue
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        return v / 100.0 if v > 1.0 else v
    return None


def walk(node, found, hint=None):
    if isinstance(node, dict):
        tk = node.get("market_ticker") or node.get("ticker") or hint
        c = node.get("candlesticks")
        if isinstance(c, list) and c and isinstance(c[0], dict) and "end_period_ts" in c[0]:
            if tk:
                found.setdefault(tk, []).extend(c)
        for v in node.values():
            walk(v, found, tk)
    elif isinstance(node, list):
        for v in node:
            walk(v, found, hint)


def quotes(candles):
    """minute -> (yes bid, yes ask); a missing side is None. Fourth amendment: a bid of 0.00 is NO bid and an ask of
    1.00 is NO ask (Kalshi's candles show an empty side that way), so both become None here, once, for every use."""
    out = {}
    for c in candles:
        b, a = price(c.get("yes_bid")), price(c.get("yes_ask"))
        out[int(c["end_period_ts"]) // 60] = (b if b is not None and b > 1e-9 else None, a if a is not None and a < 1 - 1e-9 else None)
    return out


def detect(g, cand):
    ml = [quotes(cand.get(t, [])) for t in g["ml"]]
    tot = [quotes(cand.get(t, [])) for t in g["total"]]
    if len(ml) != 2 or not ml[0] or not ml[1]:
        return None, False
    last = int(g["close_ts"]) // 60
    for m in range(last - LAST_MIN + 1, last + 1):
        sides = []
        for q in ml:
            b, a = q.get(m, (None, None))
            if b is None or a is None or b <= 0 or a > 1 or a < b:
                sides = None
                break
            sides.append((b, a))
        if not sides or not all(ML_BAND[0] - 1e-9 <= (b + a) / 2 <= ML_BAND[1] + 1e-9 for b, a in sides):
            continue
        known = hi = lo = open_ = 0
        for q in tot:
            b, a = q.get(m, (None, None))
            if b is None and a is None:
                continue
            known += 1
            if b is not None and b >= HIGH - 1e-9:
                hi += 1
            elif a is not None and a <= LOW + 1e-9:
                lo += 1
            else:
                open_ += 1
        if known >= MIN_STRIKES and open_ == 0 and hi >= 1 and lo >= 1:
            k = min(range(2), key=lambda i: (round(sides[i][1], 9), g["ml"][i]))   # the cheaper side; equal asks: the ticker that sorts first
            cheap = sides[k]
            b, a = ml[k].get(m + 1, (None, None))             # the SAME contract one minute later (amendment of Nov 13)
            same_next = (b, a) if (b is not None and a is not None and b > 0 and a <= 1 and a >= b) else None
            nxt = []
            for q in ml:
                b, a = q.get(m + 1, (None, None))
                if b is not None and a is not None and b > 0 and a <= 1 and a >= b:
                    nxt.append((b, a))
            cheap_next = min(nxt, key=lambda s: s[1]) if len(nxt) == 2 else None
            return {"game": g["game"], "minute": m, "minutes_before_close": last - m, "ask": cheap[1], "spread": cheap[1] - cheap[0],
                    "same_ask_next": same_next[1] if same_next else None, "same_spread_next": (same_next[1] - same_next[0]) if same_next else None, "window_edge": m <= last - LAST_MIN + EDGE_MIN,
                    "ask_next": cheap_next[1] if cheap_next else None, "spread_next": (cheap_next[1] - cheap_next[0]) if cheap_next else None}, True
    return None, True


def ot_state(g, cand, minute=None):
    """Cross-check only (third amendment, point 3): the 'game goes to overtime' market at one candle: the detection
    minute if given, else its last candle inside the window. 'yes' = YES bid 0.93 or more, 'no' = YES ask 0.07 or less,
    'open' = a quote that is neither, 'none' = no candle, or a candle showing neither side."""
    q = quotes(cand.get(g.get("ot", ""), []))
    if minute is None:
        last = int(g["close_ts"]) // 60
        inside_window = [m for m in q if last - LAST_MIN + 1 <= m <= last]
        if not inside_window:
            return "none"
        minute = max(inside_window)
    b, a = q.get(minute, (None, None))
    if b is None and a is None:
        return "none"
    if b is not None and b >= OT_YES - 1e-9:
        return "yes"
    if a is not None and a <= OT_NO + 1e-9:
        return "no"
    return "open"


def read_run(run):
    """Third amendment, point 8: the run is read by its manifest, whole or refused."""
    root = os.path.realpath(run)
    man = json.load(open(os.path.join(run, "manifest.json")))
    reqs = (man.get("job") or {}).get("requests")
    rows = man.get("rows", [])
    if man.get("status") != "complete" or not isinstance(reqs, list) or not reqs:
        sys.exit("REFUSED: the candle run did not finish, or its manifest does not carry its job")
    good = {r.get("id") for r in rows if r.get("status") == 200 and not r.get("truncated") and r.get("file")}
    if any(r.get("status") != 200 or r.get("truncated") or not r.get("file") for r in rows) or not {r.get("id") for r in reqs} <= good:
        sys.exit("REFUSED: the candle run is not whole (a request was refused, cut short or not answered)")
    cand = {}
    for r in rows:
        path = os.path.join(run, str(r["file"]))
        if os.path.islink(path) or not (os.path.realpath(path) + os.sep).startswith(root + os.sep):
            sys.exit("REFUSED: %s is not a plain file of the run" % r["file"])
        _refuse_all([path])
        raw = gzip.decompress(open(path, "rb").read())
        if (r.get("sha256") and hashlib.sha256(raw).hexdigest() != r["sha256"]) or (r.get("bytes") is not None and r["bytes"] != len(raw)):
            sys.exit("REFUSED: %s does not match the sha256 or the length the manifest records for its unpacked body" % r["file"])
        walk(json.loads(raw.decode("utf-8")), cand)
    return cand


HINDSIGHT = "  [hindsight window: detection uses the close time; upper bound, not a live rule]"


def main():
    import builtins
    def print(*a, **k):                      # every figure carries the label (Head of R&D, Nov 13, 00:09Z)
        builtins.print(" ".join(str(x) for x in a) + HINDSIGHT, **k)
    run, games = sys.argv[1], json.load(open(sys.argv[2]))
    cand = read_run(run)
    usable, hits = 0, []
    cross = {"detected": {"yes": 0, "no": 0, "open": 0, "none": 0}, "not detected": {"yes": 0, "no": 0, "open": 0, "none": 0}}
    for g in games:
        d, ok = detect(g, cand)
        usable += 1 if ok else 0
        if d:
            hits.append(d)
            cross["detected"][ot_state(g, cand, d["minute"])] += 1
        elif ok:
            cross["not detected"][ot_state(g, cand)] += 1
    n = len(hits)
    print("candle freshness measured on Bitcoin 15 minute only, not on sports; one-minute resolution, no seconds-level claim")
    print(f"games in the list {len(games)} | with moneyline candles {usable} | detections {n}" + (f" ({n / usable:.1%} of usable games)" if usable else ""))
    for k in ("detected", "not detected"):
        c = cross[k]
        print(f"cross-check, the game-goes-to-overtime market in games {k} by the rule: says overtime {c['yes']} | says no overtime {c['no']} | undecided {c['open']} | no quote {c['none']}")
    if n:
        asks = sorted(h["ask"] for h in hits)
        q1, q3 = (asks[0], asks[0]) if n == 1 else (lambda q: (q[0], q[2]))(statistics.quantiles(asks, n=4, method="inclusive"))
        print(f"cheaper side's ask at the detection minute: median {statistics.median(asks) + 1e-9:.2f} | quartiles {q1 + 1e-9:.2f} to {q3 + 1e-9:.2f} | lowest {asks[0]:.2f}")
        for cut in (0.40, 0.43, 0.45, 0.47):
            print(f"  at {cut:.2f} or lower: {sum(1 for a in asks if a <= cut + 1e-9)} of {n}")
        mins = sorted(h["minutes_before_close"] for h in hits)
        print(f"detection minute, minutes before the game market closed: median {statistics.median(mins):g} | range {mins[0]} to {mins[-1]}")
    print("HINDSIGHT LABEL: the search is bounded to the last 45 minutes before the game market closed, a time known only afterwards. "
          "Inside that window the scan runs forward and takes the FIRST qualifying minute. This is a price measurement with no bet and no outcome; "
          "a rule would need candles anchored on the scheduled start.")
    print(f"detections in the first 5 minutes of the window (the state may have begun before the window): {sum(1 for h in hits if h['window_edge'])} of {n}")
    if n < MIN_DETECTIONS:
        print(f"VERDICT: NOT_ENOUGH_DATA ({n} detections, need {MIN_DETECTIONS})")
        return
    fire = n / usable
    if not (FIRE_RANGE[0] - 1e-9 <= fire <= FIRE_RANGE[1] + 1e-9):
        print(f"VERDICT: CARD CLOSED (the rule fires in {fire:.0%} of games; overtime is about 20% to 23%, so it is not detecting overtime)")
        return
    def optimistic(h):
        now = h["ask"] <= ASK_BAR + 1e-9 and h["spread"] <= SPREAD_BAR + 1e-9
        nxt = h["ask_next"] is not None and h["ask_next"] <= ASK_BAR + 1e-9 and h["spread_next"] <= SPREAD_BAR + 1e-9
        return now or nxt
    def buyable(h):
        """Head of R&D's ruling of Nov 13, 00:09Z: ONE price, the minute after detection, one chance: the SAME contract that was
        the cheaper side at the detection minute, at its ask one minute later, with that minute's spread."""
        return (h["same_ask_next"] is not None and h["same_ask_next"] <= ASK_BAR + 1e-9 and h["same_spread_next"] <= SPREAD_BAR + 1e-9)
    share = sum(1 for h in hits if buyable(h)) / n
    print(f"detections where the cheaper side's own contract was at {ASK_BAR:.2f} or lower (spread {SPREAD_BAR:.2f} or less) ONE MINUTE AFTER the detection minute, one price, one chance: {share:.0%}  [the registered verdict]")
    print(f"  optimistic, best of the detection minute or the next, as first written: {sum(1 for h in hits if optimistic(h)) / n:.0%}  [information only]")
    print("VERDICT: " + ("CARD CLOSED (the market already prices overtime as close to even)" if share < SHARE_BAR - 1e-9 else "SURVIVES the price measurement (nothing beyond it is approved)"))


if __name__ == "__main__":
    main()
