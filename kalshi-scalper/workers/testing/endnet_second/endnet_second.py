#!/usr/bin/env python3
"""ENDNET independent SECOND build (Testing Desk, Nov 13, 2026), from the card text alone (LIVEDATA_CARDS_NOV13.md, claude/idea-desk-b aca441ae: card 1 and the "three readings pinned" lines); endnet.py was NOT read.
Usage: python3 -I endnet_second.py <stage1|stage2> <input json>. Invented rows only so far; no Kalshi request, no data. Stage 1 never touches a result; stage 2 is development only.
STRUCTURE: map_input() is the ONLY function that knows the input layout (the real feed layout is not known yet); everything below it works on the internal form
Game(game_id, close_ts, minutes=[Minute(end_ts, period, left_s, home, away)], strikes={ticker: floor}, quotes={ticker: {end_ts: (bid, ask) cents}}, results={ticker: str} or None). A later remap touches map_input() only.
Readings of the text where it leaves a choice are NOT chosen silently: they are in AMBIGUITIES, and where they change a printed line both are printed."""
import calendar, json, os, sys, statistics as st
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
import scorekit as k

DEV_FROM = calendar.timegm((2026, 11, 17, 0, 0, 0)); DEV_TO = calendar.timegm((2026, 12, 14, 23, 59, 59)); HELD_FROM = calendar.timegm((2026, 12, 15, 0, 0, 0))
LEFT_MAX, BAND_LO, BAND_HI, SPREAD_MAX, SLIP = 180, 15, 45, 4, 1
MIN_WEEK, MIN_FILLED, PF_BAR, ASK_CLOSE = 6, 150, 1.5, 45
TOL = 1e-9
AMBIGUITIES = [
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


# ---------- the ONLY function that knows the input layout ----------
def map_input(raw, with_results):
    """The INVENTED layout: {"games": [{"game_id","close_ts","minutes":[{"end_ts","period","left_s","home","away"}],"strikes":{ticker: floor},"candles":{ticker:[{"end_ts","bid","ask"}]},"results":{ticker:str}}]} -> [Game]. Results are mapped only for stage 2."""
    out = []
    for g in raw["games"]:
        mins = [Minute(m["end_ts"], m["period"], m["left_s"], m["home"], m["away"]) for m in g["minutes"]]
        quotes = {tk: {c["end_ts"]: (c["bid"], c["ask"]) for c in cs} for tk, cs in g["candles"].items()}
        out.append(Game(g["game_id"], g["close_ts"], mins, dict(g["strikes"]), quotes, dict(g["results"]) if with_results else None))
    return out


# ---------- decision logic (internal form only) ----------
def fee_up(p): return -(-7 * p * (100 - p) // 10000)          # cents, 0.07 x p x (1 - p) rounded up, exact in integers


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
    f = fee_up(price)
    if result == "yes": return 100 - price - f
    if result == "no": return -price - f
    return -f          # void or missing: price refunded, fee kept


def day_of(ts): return datetime.fromtimestamp(ts, timezone.utc).date()
def week_of(ts): d = day_of(ts); return d.toordinal() - d.weekday()          # the Monday of the UTC close date, as an ordinal


def pf(nets):
    w = sum(x for x in nets if x > 0); l = -sum(x for x in nets if x < 0)
    return None if l == 0 else w / l


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
    L.append("MEDIAN ASK: entries made %s (asks %s); every state with a strike and a two-sided quote %s (asks %s)" % (med(asks_e), sorted(asks_e), med(asks_q), sorted(asks_q)))
    nights = {}; weeks = {}
    for g, d in entries: nights[day_of(g.close_ts)] = nights.get(day_of(g.close_ts), 0) + 1; weeks[week_of(g.close_ts)] = weeks.get(week_of(g.close_ts), 0) + 1
    L.append("ENTRIES BY CLOSE DATE (UTC): %s" % {str(k_): v for k_, v in sorted(nights.items())})
    wk = {datetime.fromordinal(k_).date().isoformat(): v for k_, v in sorted(weeks.items())}
    dev_weeks = (DEV_TO - DEV_FROM) // (7 * 86400) + (1 if (DEV_TO - DEV_FROM) % (7 * 86400) else 0)
    L.append("ENTRIES BY WEEK (Monday of the UTC close date): %s" % wk)
    closed_ask = (med(asks_e) is not None and med(asks_e) > ASK_CLOSE + TOL) or (med(asks_q) is not None and med(asks_q) > ASK_CLOSE + TOL)
    every_week = bool(weeks) and all(v < MIN_WEEK for v in weeks.values()); mean_weeks = (len(entries) / len(weeks) < MIN_WEEK) if weeks else True; mean_window = len(entries) / dev_weeks < MIN_WEEK
    L.append("WEEK TESTS (fewer than 6 a week): every week under 6: %s; mean over the weeks with entries under 6: %s; mean over the %d weeks of the development window under 6: %s" % (every_week, mean_weeks, dev_weeks, mean_window))
    if closed_ask: v1 = "CLOSED: the median ask is above 45c"
    elif every_week and mean_weeks and mean_window: v1 = "CLOSED: fewer than 6 qualifying entries a week (all three readings)"
    elif every_week or mean_weeks or mean_window: v1 = "depends on the reading of 'a week': not decided"
    else: v1 = "NOT CLOSED at stage 1"
    L.append("STAGE 1 VERDICT: %s" % v1)
    if stage == "stage2":
        ent = sorted(((g.close_ts, g.game_id, g, d) for g, d in entries), key=lambda x: (x[0], x[1]))
        nets = [net_of(d["price"], g.results.get(d["ticker"])) for _, _, g, d in ent]
        n = len(nets); h1, h2 = nets[: n // 2], nets[n // 2:]
        L.append("STAGE 2 (development only): n = %d filled; wins %d, losses %d (a void is a fee-only loss counted); net %+d c, %.1f c a contract; cash PF %s; halves PF %s / %s" % (
            n, sum(1 for x in nets if x > 0), sum(1 for x in nets if x <= 0), sum(nets), (sum(nets) / n if n else 0), None if pf(nets) is None else round(pf(nets), 4), None if pf(h1) is None else round(pf(h1), 4), None if pf(h2) is None else round(pf(h2), 4)))
        if n < MIN_FILLED: L.append("STAGE 2 VERDICT: NOT_ENOUGH_DATA at n = %d" % n)
        else:
            p, a, b = pf(nets), pf(h1), pf(h2)
            ok_pf = p is not None and p >= PF_BAR - TOL
            L.append("STAGE 2 VERDICT: cash PF >= 1.5: %s; halves above 1.0: %s; halves 1.0 or above: %s; deflated z: not computed (bar not stated)" % (ok_pf, bool(a and b and a > 1 + TOL and b > 1 + TOL), bool(a and b and a >= 1 - TOL and b >= 1 - TOL)))
    L.append("label: provisional, one build; invented rows; every reading in AMBIGUITIES is unruled")
    return L


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 2 or a[0] not in ("stage1", "stage2"): print(__doc__); print("\n".join(AMBIGUITIES)); raise SystemExit
    k.guard(os.path.dirname(os.path.abspath(a[1])))
    print("\n".join(run(a[0], map_input(json.load(open(a[1])), a[0] == "stage2"))))
