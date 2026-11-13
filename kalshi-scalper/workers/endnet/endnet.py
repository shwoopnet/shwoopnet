#!/usr/bin/env python3
"""ENDNET scorer (the goalie-pull regime). Written Nov 13, 2026 on invented rows only: no real state, price or result of this card exists
or was read. The card: livedata_cards/LIVEDATA_CARDS_NOV13.md, CARD 1. NOT registered; the layout below is INVENTED and will be mapped
to the real feed's layout by a separate reader once probe B2 shows it.

  endnet.py measure <games.json>   stage 1: how often the trigger fires and at what price. Reads NO result (the loader drops it).
  endnet.py score   <games.json>   stage 2 on DEVELOPMENT rows only: cash PF, halves, verdict. There is no held-out mode: a held-out read
                                   is a separate, reviewed change to this file, and any row closing on or after the held-out date stops the run.

games.json: a list of games. Every price is an integer number of CENTS.
  {"game": str, "close_ts": int,
   "minutes": [{"end_ts": int, "period": int, "secs_left": int, "home": int, "away": int}, ...],   # one state per minute, from the feed
   "strikes": [{"ticker": str, "floor_strike": number, "result": "yes"|"no"|null,
                "candles": [{"end_ts": int, "bid": int, "ask": int}, ...]}, ...]}      # the total-goals ladder; YES = final total > floor_strike

The rule, as the card words it, with the readings this file PINS (to be written into the registration as dated lines before it is registered):
  - Entry minute: the FIRST state minute with period 3, secs_left <= 180 and the score exactly one goal apart. One look: if that minute has no usable quote
    the game is counted and not entered; no later minute is tried.
  - The strike: the one whose floor_strike f satisfies 0 <= f - total < 1 (total = home + away), so exactly one more goal makes YES. (The card said
    "floor_strike is the current total"; a half line such as 5.5 against a total of 5 is the usual case and an integer line equal to the total also qualifies.)
  - Quote: the candle whose end_ts equals the entry minute's end_ts, two-sided (0 < bid < ask < 100), nothing carried from another minute.
  - Buy YES at ask + 1 cent (at most 99) if the ask is 15 to 45 cents inclusive and ask - bid is at most 4 cents. One contract. Held to settlement.
  - Fee per contract: 7% x p x (1 - p) on 10 contracts, rounded UP to the cent on the order, divided by 10 (the standing convention).
Amended Nov 13, 2026 on the Head of R&D's rulings of the 14 ambiguities (items 2, 7, 11, 13 and the z line). Standard library only. Exact arithmetic (integers and fractions); no float comparison against a registered line.
"""
import json
import math
import os
import sys
from datetime import datetime, timezone
from fractions import Fraction
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from deskb_guard import refuse_all, refuse_heldout  # noqa: E402

DEV_FROM = "2026-11-17T00:00:00Z"
DEV_TO = "2026-12-14T23:59:59Z"            # closes after this are held out (from 2026-12-15T00:00:00Z) and stop the run
HALF_FROM = "2026-12-01T00:00:00Z"         # second half of development
HELD_FROM = "2026-12-15T00:00:00Z"
WEEKS = 4                                  # the development window is 28 days
SECS = 180
ASK_LO, ASK_HI, SPREAD_MAX, SLIP, MAX_PAY = 15, 45, 4, 1, 99
C = 10
MIN_ENTRIES, PF_LINE, HALF_LINE = 150, Fraction(3, 2), Fraction(1)
MEDIAN_ASK_LINE, MIN_PER_WEEK = 45, 6
Z_BAR = 5.46                               # the research ledger's line at registration (N about 2.11 million), ENDNET adding 1; one-sided, day-clustered
CT = ZoneInfo("America/Chicago")
TAG = " [invented rows only, not a result]"


def ts(iso):
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())


def load(path, drop_result):
    """Returns (games in the development window, the number of games that closed BEFORE it). A game closing on or after the held-out date stops the
    whole run before any state is read; a game closing before the development window is counted and not used (Nov 13 ruling, item 13)."""
    refuse_heldout(path)
    games = json.load(open(path))
    for g in games:
        if g["close_ts"] > ts(DEV_TO):
            sys.exit("REFUSED: game %s closes on or after the held-out date %s" % (g.get("game"), HELD_FROM))
    early = [g for g in games if g["close_ts"] < ts(DEV_FROM)]
    games = [g for g in games if g["close_ts"] >= ts(DEV_FROM)]
    if drop_result:
        for g in games:
            for s in g["strikes"]:
                s.pop("result", None)          # stage 1 never holds a result
    return games, len(early)


def fee_per_contract(pay):
    p = Fraction(pay, 100)
    cents_on_order = -((-(Fraction(7, 100) * C * p * (1 - p) * 100)).__floor__())      # ceiling, exact
    return Fraction(cents_on_order, C * 100)


def entry(g):
    """Returns (reason, row). reason is None for an entry; otherwise the counted skip reason."""
    ms = sorted(g["minutes"], key=lambda m: m["end_ts"])
    st = next((m for m in ms if m["period"] == 3 and m["secs_left"] <= SECS and abs(m["home"] - m["away"]) == 1), None)
    if st is None:
        return "no state minute", None
    total = st["home"] + st["away"]
    cand = [s for s in g["strikes"] if 0 <= Fraction(str(s["floor_strike"])) - total < 1]
    if not cand:
        return "no strike one goal away", None
    if len(cand) > 1:
        return "ambiguous strike", None                 # item 7: the rule cannot choose, so it takes none
    s = cand[0]
    c = next((c for c in s["candles"] if c["end_ts"] == st["end_ts"]), None)
    if c is None:
        return "no candle at the entry minute", None
    if not (0 < c["bid"] < c["ask"] < 100):
        return "not two-sided", None
    seen = {"seen_ask": c["ask"]}                       # item 2: a state with a strike and a two-sided quote, before the band and spread
    if not ASK_LO <= c["ask"] <= ASK_HI:
        return "ask out of band", seen
    if c["ask"] - c["bid"] > SPREAD_MAX:
        return "spread too wide", seen
    pay = min(MAX_PAY, c["ask"] + SLIP)
    return None, {"game": g["game"], "close_ts": g["close_ts"], "ask": c["ask"], "pay": pay, "ticker": s["ticker"], "result": s.get("result"), "seen_ask": c["ask"]}


def run(games):
    rows, skips, seen = [], {}, []
    for g in games:
        why, r = entry(g)
        if why:
            skips[why] = skips.get(why, 0) + 1
        else:
            rows.append(r)
        if r and "seen_ask" in r:
            seen.append(r["seen_ask"])
    return rows, skips, seen


def pct(x):
    return "%.1f%%" % (float(x) * 100 + 1e-9)


def money(x):
    return "%+.4f" % (float(x) + (1e-9 if x >= 0 else -1e-9))


def median(v):
    v = sorted(v)
    n = len(v)
    return None if not n else (Fraction(v[n // 2]) if n % 2 else Fraction(v[n // 2 - 1] + v[n // 2], 2))


def cmd_measure(path):
    games, early = load(path, True)
    rows, skips, seen = run(games)
    print("ENDNET stage 1: how often the trigger fires and at what price; NO result read%s" % TAG)
    print("games %d (and %d closed before the development window, not used) | entries %d | skipped %s%s" % (len(games), early, len(rows), ", ".join("%s %d" % kv for kv in sorted(skips.items())) or "none", TAG))
    ms, me = median(seen), median([r["ask"] for r in rows])
    if seen:
        print("ask over every state with a strike and a two-sided quote (before the band and spread; THE KILL LINE READS THIS): median %s cents over %d states | lowest %d | highest %d%s" % ("%.1f" % (float(ms) + 1e-9), len(seen), min(seen), max(seen), TAG))
    if rows:
        print("ask over the entries made (information only): median %s cents | lowest %d | highest %d%s" % ("%.1f" % (float(me) + 1e-9), min(r["ask"] for r in rows), max(r["ask"] for r in rows), TAG))
    per_week = Fraction(len(rows), WEEKS)
    print("entries a week over the %d week development window: %s%s" % (WEEKS, ("%.2f" % (float(per_week) + 1e-9)), TAG))
    if not seen:
        print("STAGE 1: NOT_ENOUGH_DATA (no state with a quote)%s" % TAG)
    elif ms > MEDIAN_ASK_LINE or per_week < MIN_PER_WEEK:
        print("STAGE 1: CLOSED (median ask over every quoted state above %d cents: %s | fewer than %d entries a week: %s)%s" % (MEDIAN_ASK_LINE, ms > MEDIAN_ASK_LINE, MIN_PER_WEEK, per_week < MIN_PER_WEEK, TAG))
    else:
        print("STAGE 1: NOT CLOSED (a stage 2 registration may be written)%s" % TAG)


def one_pnl(r):
    fee = fee_per_contract(r["pay"])
    if r["result"] == "void":
        return -fee                                      # item 11: the price is refunded and the fee kept
    return (Fraction(1) if r["result"] == "yes" else Fraction(0)) - Fraction(r["pay"], 100) - fee


def stats(rs):
    pnl = [one_pnl(r) for r in rs]
    win = sum(p for p in pnl if p > 0)
    loss = -sum(p for p in pnl if p < 0)
    pf = None if loss == 0 else win / loss
    return len(pnl), sum(1 for r in rs if r["result"] == "yes"), sum(pnl), pf, pnl


def fmt(name, rs):
    n, w, net, pf, _ = stats(rs)
    if not n:
        return "%s: no entry" % name
    return "%s: n %d | wins %d | net %s | mean %s | cash PF %s" % (name, n, w, money(net), money(net / n), "no losses" if pf is None else "%.2f" % (float(pf) + 1e-9))


def day_z(rs):
    """Day-clustered z of the mean net per entry, one-sided; the cluster is the US Central calendar date of the close. Information beside the bar."""
    pnl = [float(one_pnl(r)) for r in rs]
    n = len(pnl)
    if n < 2:
        return None
    mean = sum(pnl) / n
    clusters = {}
    for r, p in zip(rs, pnl):
        d = datetime.fromtimestamp(r["close_ts"], CT).date()
        c = clusters.setdefault(d, [0, 0.0])
        c[0] += 1
        c[1] += p - mean
    se = math.sqrt(sum(v * v for _, v in clusters.values())) / n
    return None if se == 0 else mean / se


def cmd_score(path):
    games, early = load(path, False)
    rows, skips, _ = run(games)
    settled = [r for r in rows if r["result"] in ("yes", "no", "void")]
    unsettled = len(rows) - len(settled)
    print("ENDNET stage 2 on DEVELOPMENT rows only%s" % TAG)
    print("games %d (and %d closed before the development window, not used) | entries %d | settled %d (a void counts: fee-only loss) | unsettled %d | skipped %s%s" % (len(games), early, len(rows), len(settled), unsettled, ", ".join("%s %d" % kv for kv in sorted(skips.items())) or "none", TAG))
    if unsettled:
        print("FLAG: %d entries have no result and every one closed before the end of the development window%s" % (unsettled, TAG))
    h1 = [r for r in settled if r["close_ts"] < ts(HALF_FROM)]
    h2 = [r for r in settled if r["close_ts"] >= ts(HALF_FROM)]
    for name, rs in (("development", settled), ("first half", h1), ("second half", h2)):
        print(fmt(name, rs) + TAG)
    n, _, net, pf, _ = stats(settled)
    p1, p2 = stats(h1)[3], stats(h2)[3]
    good = lambda x: x is None or x >= HALF_LINE                      # no losses counts as above the line
    if n < MIN_ENTRIES:
        v = "NOT_ENOUGH_DATA (%d settled entries, need %d)" % (n, MIN_ENTRIES)
    elif net <= 0 or (pf is not None and pf < PF_LINE) or not (good(p1) and good(p2)):
        v = "FALSIFIED (cash PF line %.1f, both halves at %.1f, net above 0)" % (float(PF_LINE), float(HALF_LINE))
    else:
        v = "SURVIVES DEVELOPMENT (the held-out is a later, reviewed read; nothing here is approved)"
    z = day_z(settled)
    print("day-clustered z (US Central game day, one-sided, mean net per entry): %s against the ledger bar %.2f%s" % ("n/a" if z is None else "%.2f" % (z + 1e-9 if z >= 0 else z - 1e-9), Z_BAR, TAG))
    print("VERDICT: %s%s" % (v, TAG))


def main():
    refuse_all()
    cmds = {"measure": cmd_measure, "score": cmd_score}
    if len(sys.argv) != 3 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    cmds[sys.argv[1]](sys.argv[2])


if __name__ == "__main__":
    main()
