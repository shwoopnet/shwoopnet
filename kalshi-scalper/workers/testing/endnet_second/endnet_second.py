#!/usr/bin/env python3
"""ENDNET independent SECOND build (Testing Desk, Nov 13, 2026), from the card text alone (LIVEDATA_CARDS_NOV13.md, claude/idea-desk-b aca441ae: card 1 and the "three readings pinned" lines); endnet.py was NOT read.
Usage: python3 -I endnet_second.py <stage1|stage2> <input json>. Invented rows only so far; no Kalshi request, no data. Stage 1 never touches a result; stage 2 is development only.
STRUCTURE: map_input() is the ONLY function that knows the input layout (the real feed layout is not known yet); everything below it works on the internal form
Game(game_id, close_ts, minutes=[Minute(end_ts, period, left_s, home, away)], strikes={ticker: floor}, quotes={ticker: {end_ts: (bid, ask) cents}}, results={ticker: str} or None). A later remap touches map_input() only.
Readings of the text where it leaves a choice are NOT chosen silently: they are in AMBIGUITIES, and where they change a printed line both are printed."""
import calendar, json, math, os, sys, statistics as st
from datetime import datetime, timezone
from fractions import Fraction
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
import scorekit as k

DEV_FROM = calendar.timegm((2026, 11, 17, 0, 0, 0)); DEV_TO = calendar.timegm((2026, 12, 14, 23, 59, 59)); HELD_FROM = calendar.timegm((2026, 12, 15, 0, 0, 0))
LEFT_MAX, BAND_LO, BAND_HI, SPREAD_MAX, SLIP = 180, 15, 45, 4, 1
MIN_WEEK, MIN_FILLED, PF_BAR, ASK_CLOSE, Z_BAR = 6, 150, 1.5, 45, 5.46
HALF_FROM = calendar.timegm((2026, 12, 1, 0, 0, 0)); CENTRAL = ZoneInfo("America/Chicago")
TOL = 1e-9
AMBIGUITIES = [
    "RULED Nov 13, 15:32Z (Head; Desk B amendment cards file e917a3cb): 1 entries made; 2 the stage 1 kill reads the median ask over every state with a strike and a two-sided quote before the filters (entries: information); 3 the mean over the 4-week window decides; 4 US Central date and Monday-to-Sunday Central weeks; 5 left_s <= 180; 6 |home - away| = 1; 7 two matching strikes: none, counted; 8 inclusive on the ask before the +1c; 9 fee per order of 10 contracts, rounded up to the cent, divided by 10; 10 filled at ask + 1c; 11 explicit void = fee-only loss counted, missing or null = unsettled, excluded, counted, flagged; 12 halves by the date constant 2026-12-01T00:00Z, a half fails only below 1.0, z day-clustered by Central game day, one-sided, bar 5.46; 13 before 2026-11-17 outside, from 2026-12-15 refused; 14 as built. The remaining text of this list is the original, now superseded where the line above rules.",
    "1. 'qualifying entries' (stage 1): entries actually made (state, strike, two-sided quote, band and spread all pass), taken here; a state that is reached but fails a filter is counted separately. The text does not say whether the band and spread are part of 'qualifying'.",
    "2. 'median ask' (stage 1): the 15c to 45c band makes the median of ENTRIES at most 45c by construction; so the median is printed twice: over the entries made (ask before the +1c) and over every state with a strike and a two-sided quote at the entry minute (before the band and spread filters).",
    "3. 'fewer than 6 qualifying entries a week': read three ways and all printed: every calendar week (Monday to Sunday of the UTC close date) with an entry under 6; the mean over those weeks; the mean over the whole development window (4 weeks). The verdict says so where they differ.",
    "4. 'game night' and week: by the UTC date of the game's close time (a game closing at 03:30Z belongs to the previous US evening); not decided by the text.",
    "5. 'the clock reads 3:00 or less': left_s <= 180 inclusive; the minute's left_s is the clock at the END of the minute (the candle's end time), an assumption about the real feed.",
    "6. 'one goal apart': |home - away| == 1 at that minute; the total is home + away at that minute.",
    "7. The strike rule 0 <= f - total < 1 can match two strikes if a ladder has lines closer than 1 apart: this build then takes NO strike and counts the game (ambiguous strike) rather than choosing; the real ladder is 1 apart so it should not occur.",
    "8. 'ask 15c to 45c' and 'spread 4c or less': inclusive on both ends, tested on the ask BEFORE the +1c; the price paid is ask + 1c.",
    "9. Fee: 0.07 x p x (1 - p) of the price paid, rounded up to the next cent (the standing hold-to-settlement template); the text does not name it.",
    "10. 'one entry a game' and 'filled': every entry is counted FILLED at ask + 1c (a taker); stage 2's '150 filled entries' is read as 150 entries.",
    "11. A result that is not yes or no (void, missing): price refunded, fee kept, a fee-only loss counted in n and PF (the Head's one void rule for hold-to-settlement cards; the card does not repeat it).",
    "12. Halves: the entries sorted by (close time, game id), the first n // 2 and the rest; 'halves at 1.0' is printed under both readings (above 1.0, and 1.0 or above); the deflated z is NOT computed ('at the then-current bar' is not stated).",
    "13. Games closing before 2026-11-17T00:00Z are counted as outside the development window and not used; any game closing on or after 2026-12-15T00:00Z refuses the whole run before a state is read.",
    "14. A game with no third-period minute at or under 180 s with a one-goal score has no state and is counted; a game whose feed is missing a minute is not repaired.",
]


class Minute:
    def __init__(self, end_ts, period, left_s, home, away): self.end_ts, self.period, self.left_s, self.home, self.away = end_ts, period, left_s, home, away
class Game:
    def __init__(self, game_id, close_ts, minutes, strikes, quotes, results): self.game_id, self.close_ts, self.minutes, self.strikes, self.quotes, self.results = game_id, close_ts, minutes, strikes, quotes, results

# ---------- the ONLY functions that know an input layout ----------
def map_input(raw, with_results):
    """The INVENTED layout: {"games": [{"game_id","close_ts","minutes":[{"end_ts","period","left_s","home","away"}],"strikes":{ticker: floor},"candles":{ticker:[{"end_ts","bid","ask"}]},"results":{ticker:str}}]} -> [Game]. Results are mapped only for stage 2."""
    out = []
    for g in raw["games"]:
        mins = [Minute(m["end_ts"], m["period"], m["left_s"], m["home"], m["away"]) for m in g["minutes"]]
        quotes = {tk: {c["end_ts"]: (c["bid"], c["ask"]) for c in cs} for tk, cs in g["candles"].items()}
        out.append(Game(g["game_id"], g["close_ts"], mins, dict(g["strikes"]), quotes, dict(g["results"]) if with_results else None))
    return out

def map_input_deskb(raw, with_results):
    """Desk B's invented layout (a list of games: {"game","close_ts","minutes":[{"end_ts","period","secs_left","home","away"}],"strikes":[{"ticker","floor_strike","result","candles":[{"end_ts","bid","ask"}]}]}) mapped WITHOUT changing a value."""
    out = []
    for g in raw:
        mins = [Minute(m["end_ts"], m["period"], m["secs_left"], m["home"], m["away"]) for m in g["minutes"]]
        strikes = {x["ticker"]: x["floor_strike"] for x in g["strikes"]}
        quotes = {x["ticker"]: {c["end_ts"]: (c["bid"], c["ask"]) for c in x["candles"]} for x in g["strikes"]}
        res = {x["ticker"]: x.get("result") for x in g["strikes"]}
        out.append(Game(g["game"], g["close_ts"], mins, strikes, quotes, res if with_results else None))
    return out


def map_any(raw, with_results): return map_input(raw, with_results) if isinstance(raw, dict) else map_input_deskb(raw, with_results)


# ---------- decision logic (internal form only) ----------
def fee_order_up(p): return -(-7 * p * (100 - p) // 1000)          # cents for an ORDER of 10 contracts at p cents: 0.07 x 10 x p x (1 - p), rounded up to the cent, exact in integers
def fee_per_contract(p): return Fraction(fee_order_up(p), 10)


def entry_minute(g):
    """The FIRST third-period minute with left_s <= 180 and the score exactly one goal apart; None if there is none. No later minute is tried."""
    for m in g.minutes:
        if m.period == 3 and m.left_s <= LEFT_MAX and abs(m.home - m.away) == 1: return m
    return None


def decide(g):
    """-> dict(status, ...). status: no_state | no_strike | ambiguous_strike | no_usable_quote | not_two_sided | ask_outside_band | spread_too_wide | entered."""
    m = entry_minute(g)
    if m is None: return {"status": "no_state"}
    total = m.home + m.away
    fit = [tk for tk, f in g.strikes.items() if 0 <= f - total < 1]
    if not fit: return {"status": "no_strike", "total": total}
    if len(fit) > 1: return {"status": "ambiguous_strike", "total": total}
    tk = fit[0]; q = g.quotes.get(tk, {}).get(m.end_ts)
    if q is None: return {"status": "no_usable_quote", "ticker": tk}
    bid, ask = q
    if not (0 < bid < ask < 100): return {"status": "not_two_sided", "ticker": tk}
    if not (BAND_LO <= ask <= BAND_HI): return {"status": "ask_outside_band", "ticker": tk, "ask": ask, "bid": bid}
    if ask - bid > SPREAD_MAX: return {"status": "spread_too_wide", "ticker": tk, "ask": ask, "bid": bid}
    return {"status": "entered", "ticker": tk, "ask": ask, "bid": bid, "price": ask + SLIP, "end_ts": m.end_ts}


def net_of(price, result):
    """Cents per contract, exact. 'void' (explicit): price refunded, fee kept. Anything else but yes/no is unsettled (the caller excludes it)."""
    f = fee_per_contract(price)
    if result == "yes": return 100 - price - f
    if result == "no": return -price - f
    return -f


def settled(result): return result in ("yes", "no", "void")
def central_day(ts): return datetime.fromtimestamp(ts, CENTRAL).date()
def central_week(ts): d = central_day(ts); return d.toordinal() - d.weekday()          # the Monday of the US Central date, as an ordinal
def fl(x): return float(x)


def pf(nets):
    w = sum(x for x in nets if x > 0); l = -sum(x for x in nets if x < 0)
    return None if l == 0 else float(w / l)


def z_day_clustered(rows):
    """One-sided z of the mean net per entry, clustered by US Central game day, equal-weight clusters: mean of cluster means over stdev / sqrt(k). None under 2 clusters or no spread."""
    by = {}
    for day, net in rows: by.setdefault(day, []).append(net)
    cm = [float(sum(v) / len(v)) for v in by.values()]
    if len(cm) < 2: return None, len(cm)
    sd = st.stdev(cm)
    return ((sum(cm) / len(cm)) / (sd / math.sqrt(len(cm))) if sd > 0 else None), len(cm)


def run(stage, games):
    for g in games:
        if g.close_ts >= HELD_FROM: raise SystemExit("REFUSED: game %s closes on or after the held-out start 2026-12-15T00:00Z; nothing is read" % g.game_id)
    dev = [g for g in games if DEV_FROM <= g.close_ts <= DEV_TO]; outside = len(games) - len(dev)
    dec = [(g, decide(g)) for g in dev]
    by = {}
    for g, d in dec: by[d["status"]] = by.get(d["status"], 0) + 1
    entries = [(g, d) for g, d in dec if d["status"] == "entered"]
    states = [(g, d) for g, d in dec if d["status"] != "no_state"]
    L = []
    L.append("COUNTS: games %d (outside the development window %d); games with a qualifying state %d; entries made %d; states not entered %d: %s" % (
        len(dev), outside, len(states), len(entries), len(states) - len(entries), {k_: v for k_, v in sorted(by.items()) if k_ not in ("entered", "no_state")}))
    asks_e = [d["ask"] for g, d in entries]
    asks_q = [d["ask"] for g, d in dec if d["status"] in ("entered", "ask_outside_band", "spread_too_wide")]
    med = lambda v: None if not v else st.median(v)
    L.append("MEDIAN ASK (stage 1 KILL: every state with a strike and a two-sided quote, before the filters) %s (asks %s); entries made (information) %s (asks %s)" % (med(asks_q), sorted(asks_q), med(asks_e), sorted(asks_e)))
    nights = {}; weeks = {}
    for g, d in entries: nights[central_day(g.close_ts)] = nights.get(central_day(g.close_ts), 0) + 1; weeks[central_week(g.close_ts)] = weeks.get(central_week(g.close_ts), 0) + 1
    L.append("ENTRIES BY US CENTRAL CLOSE DATE: %s" % {str(k_): v for k_, v in sorted(nights.items())})
    L.append("ENTRIES BY US CENTRAL WEEK (Monday): %s" % {datetime.fromordinal(k_).date().isoformat(): v for k_, v in sorted(weeks.items())})
    dev_weeks = (DEV_TO - DEV_FROM + 1) // (7 * 86400)          # the development window is exactly 4 weeks
    mean_window = len(entries) / dev_weeks; every_week = bool(weeks) and all(v < MIN_WEEK for v in weeks.values()); mean_weeks = (len(entries) / len(weeks)) if weeks else 0
    L.append("WEEK TESTS: mean over the %d weeks of the development window %s (DECIDES: under 6 is %s); information: every week with an entry under 6 is %s; mean over the weeks with entries %s" % (dev_weeks, round(mean_window, 4), mean_window < MIN_WEEK, every_week, round(mean_weeks, 4)))
    if med(asks_q) is not None and med(asks_q) > ASK_CLOSE + TOL: v1 = "CLOSED: the median ask is above 45c"
    elif mean_window < MIN_WEEK: v1 = "CLOSED: fewer than 6 qualifying entries a week (the mean over the 4-week window)"
    else: v1 = "NOT CLOSED at stage 1"
    L.append("STAGE 1 VERDICT: %s" % v1)
    if stage == "stage2":
        ent = sorted(((g.close_ts, g.game_id, g, d) for g, d in entries), key=lambda x: (x[0], x[1]))
        uns = [e for e in ent if not settled(e[2].results.get(e[3]["ticker"]))]
        sett = [e for e in ent if settled(e[2].results.get(e[3]["ticker"]))]
        rows = [(t, net_of(d["price"], g.results.get(d["ticker"]))) for t, gid, g, d in sett]
        nets = [n_ for _, n_ in rows]; n = len(nets)
        h1 = [n_ for t, n_ in rows if t < HALF_FROM]; h2 = [n_ for t, n_ in rows if t >= HALF_FROM]
        if uns: L.append("FLAG: %d entries with a missing or null result are UNSETTLED, excluded from n and PF, counted: %s" % (len(uns), [e[1] for e in uns]))
        P, P1, P2 = pf(nets), pf(h1), pf(h2)
        L.append("STAGE 2 (development only): n = %d settled (unsettled %d); wins %d, losses %d (a void is a fee-only loss counted); net %+.1f c, %+.2f c a contract; cash PF %s; halves by 2026-12-01T00:00Z: first n %d PF %s, second n %d PF %s" % (
            n, len(uns), sum(1 for x in nets if x > 0), sum(1 for x in nets if x <= 0), fl(sum(nets)), fl(sum(nets) / n) if n else 0, None if P is None else round(P, 4), len(h1), None if P1 is None else round(P1, 4), len(h2), None if P2 is None else round(P2, 4)))
        z, kk = z_day_clustered([(central_day(t), n_) for t, n_ in rows])
        L.append("Z (one-sided, day-clustered by US Central game day, %d clusters): %s against the bar %s" % (kk, None if z is None else round(z, 2), Z_BAR))
        if n < MIN_FILLED: L.append("STAGE 2 VERDICT: NOT_ENOUGH_DATA at n = %d" % n)
        else:
            half_ok = all(x is None or x >= 1 - TOL for x in (P1, P2))          # a half fails only below 1.0 (an empty half cannot fail)
            L.append("STAGE 2 VERDICT: %s" % ("pass: cash PF %.2f >= 1.5, halves not below 1.0, z %.2f >= %.2f" % (P, z, Z_BAR) if (P is not None and P >= PF_BAR - TOL and half_ok and z is not None and z >= Z_BAR - TOL) else "bar not met (cash PF %s, halves ok %s, z %s)" % (P, half_ok, z)))
    L.append("label: provisional, one build; invented rows")
    return L


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 2 or a[0] not in ("stage1", "stage2"): print(__doc__); print("\n".join(AMBIGUITIES)); raise SystemExit
    k.guard(os.path.dirname(os.path.abspath(a[1])))
    print("\n".join(run(a[0], map_any(json.load(open(a[1])), a[0] == "stage2"))))
