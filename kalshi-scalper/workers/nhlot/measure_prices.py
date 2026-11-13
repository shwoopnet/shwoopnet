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
import glob
import gzip
import json
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
LAST_MIN = 45               # only the last 45 minutes before the game market closed are searched
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
    """minute -> (yes bid, yes ask); a missing side is None."""
    out = {}
    for c in candles:
        out[int(c["end_period_ts"]) // 60] = (price(c.get("yes_bid")), price(c.get("yes_ask")))
    return out


def detect(g, cand):
    ml = [quotes(cand.get(t, [])) for t in g["ml"]]
    tot = [quotes(cand.get(t, [])) for t in g["total"]]
    if len(ml) != 2 or not ml[0] or not ml[1]:
        return None, False
    last = int(g["close_ts"]) // 60
    for m in range(last - LAST_MIN, last + 1):
        sides = []
        for q in ml:
            b, a = q.get(m, (None, None))
            if b is None or a is None or b <= 0 or a > 1 or a < b:
                sides = None
                break
            sides.append((b, a))
        if not sides or not all(ML_BAND[0] <= (b + a) / 2 <= ML_BAND[1] for b, a in sides):
            continue
        known = hi = lo = open_ = 0
        for q in tot:
            b, a = q.get(m, (None, None))
            if b is None and a is None:
                continue
            known += 1
            if b is not None and b >= HIGH:
                hi += 1
            elif a is not None and a <= LOW:
                lo += 1
            else:
                open_ += 1
        if known >= MIN_STRIKES and open_ == 0 and hi >= 1 and lo >= 1:
            k = min(range(2), key=lambda i: sides[i][1])       # the cheaper side at the detection minute
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
                    "same_ask_next": same_next[1] if same_next else None, "window_edge": (m - (last - LAST_MIN)) < 5,
                    "ask_next": cheap_next[1] if cheap_next else None, "spread_next": (cheap_next[1] - cheap_next[0]) if cheap_next else None}, True
    return None, True


def ot_state(g, cand, minutes):
    """Cross-check only (added Nov 12 before any NHL pull): what the 'game goes to overtime' market showed in those minutes.
    'yes' = its YES bid was 0.90 or more in one of them, 'no' = its YES ask was 0.10 or less in all quoted ones, 'open' = neither, 'none' = no quote."""
    q = quotes(cand.get(g.get("ot", ""), []))
    seen = [q[m] for m in minutes if m in q and (q[m][0] is not None or q[m][1] is not None)]
    if not seen:
        return "none"
    if any(b is not None and b >= 0.90 for b, a in seen):
        return "yes"
    if all(a is not None and a <= 0.10 for b, a in seen):
        return "no"
    return "open"


def main():
    run, games = sys.argv[1], json.load(open(sys.argv[2]))
    cand = {}
    for f in sorted(glob.glob(os.path.join(run, "[0-9]*.json.gz"))):
        try:
            walk(json.load(gzip.open(f, "rt")), cand)
        except (ValueError, OSError):
            continue
    usable, hits = 0, []
    cross = {"detected": {"yes": 0, "no": 0, "open": 0, "none": 0}, "not detected": {"yes": 0, "no": 0, "open": 0, "none": 0}}
    for g in games:
        d, ok = detect(g, cand)
        usable += 1 if ok else 0
        if d:
            hits.append(d)
            cross["detected"][ot_state(g, cand, [d["minute"], d["minute"] + 1])] += 1
        elif ok:
            last = int(g["close_ts"]) // 60
            cross["not detected"][ot_state(g, cand, range(last - LAST_MIN, last + 1))] += 1
    n = len(hits)
    print("candle freshness measured on Bitcoin 15 minute only, not on sports; one-minute resolution, no seconds-level claim")
    print(f"games in the list {len(games)} | with moneyline candles {usable} | detections {n}" + (f" ({n / usable:.1%} of usable games)" if usable else ""))
    for k in ("detected", "not detected"):
        c = cross[k]
        print(f"cross-check, the game-goes-to-overtime market in games {k} by the rule: says overtime {c['yes']} | says no overtime {c['no']} | undecided {c['open']} | no quote {c['none']}")
    if n:
        asks = sorted(h["ask"] for h in hits)
        print(f"cheaper side's ask at the detection minute: median {asks[n // 2]:.2f} | quartiles {asks[n // 4]:.2f} to {asks[(3 * n) // 4]:.2f} | lowest {asks[0]:.2f}")
        for cut in (0.40, 0.43, 0.45, 0.47):
            print(f"  at {cut:.2f} or lower: {sum(1 for a in asks if a <= cut + 1e-9)} of {n}")
        mins = sorted(h["minutes_before_close"] for h in hits)
        print(f"detection minute, minutes before the game market closed: median {mins[n // 2]} | range {mins[0]} to {mins[-1]}")
    print("HINDSIGHT LABEL: the search is bounded to the last 45 minutes before the game market closed, a time known only afterwards. "
          "Inside that window the scan runs forward and takes the FIRST qualifying minute. This is a price measurement with no bet and no outcome; "
          "a rule would need candles anchored on the scheduled start.")
    print(f"detections in the first 5 minutes of the window (the state may have begun before the window): {sum(1 for h in hits if h['window_edge'])} of {n}")
    if n < MIN_DETECTIONS:
        print(f"VERDICT: NOT_ENOUGH_DATA ({n} detections, need {MIN_DETECTIONS})")
        return
    fire = n / usable
    if not (FIRE_RANGE[0] <= fire <= FIRE_RANGE[1]):
        print(f"VERDICT: CARD CLOSED (the rule fires in {fire:.0%} of games; overtime is about 20% to 23%, so it is not detecting overtime)")
        return
    def optimistic(h):
        now = h["ask"] <= ASK_BAR + 1e-9 and h["spread"] <= SPREAD_BAR + 1e-9
        nxt = h["ask_next"] is not None and h["ask_next"] <= ASK_BAR + 1e-9 and h["spread_next"] <= SPREAD_BAR + 1e-9
        return now or nxt
    def buyable(h):
        """Amendment of Nov 13 (Auditor B): decide on the detection minute (ask at the bar or lower, spread at the bar or less);
        a limit at that ask plus 1c is filled only if the SAME contract's ask one minute later is at or under the limit."""
        decided = h["ask"] <= ASK_BAR + 1e-9 and h["spread"] <= SPREAD_BAR + 1e-9
        return decided and h["same_ask_next"] is not None and h["same_ask_next"] <= h["ask"] + 0.01 + 1e-9
    share = sum(1 for h in hits if buyable(h)) / n
    print(f"detections where the cheaper side was at {ASK_BAR:.2f} or lower (spread {SPREAD_BAR:.2f} or less) at the detection minute AND a limit one cent higher was filled the next minute: {share:.0%}  [the registered verdict]")
    print(f"  optimistic, best of the detection minute or the next, as first written: {sum(1 for h in hits if optimistic(h)) / n:.0%}  [information only]")
    print("VERDICT: " + ("CARD CLOSED (the market already prices overtime as close to even)" if share < SHARE_BAR else "SURVIVES the price measurement (nothing beyond it is approved)"))


if __name__ == "__main__":
    main()
