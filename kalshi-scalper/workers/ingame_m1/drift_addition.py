#!/usr/bin/env python3
"""In-game lag card: POST-READ ADDITION, NOT IN THE REGISTRATION. Zero tries.

Defined in section 11 of workers/IDEA_DESK_B_INGAME_CARD.md before it was computed and
allowed by the Head of R&D on Nov 12, 2026 with these conditions: it can CLOSE the card, it
cannot count as evidence for the card, and nothing else is computed from these candles.

For every trigger event of measure.py (same trigger, same in-play guard, NO condition on
where the spread ends) and every spread market of that game with a usable quote at both
minutes: drift = the spread's mid at minute 10 minus its mid at minute 1 after the signal
minute, signed the way the moneyline jumped. Averaged over the game's spread markets (no
picking), then over events. Per sport: events, games, mean in cents, standard error with
games as the cluster. For comparison, and stated before computing: the same drift from
minute 0 to minute 1.

Rule fixed before computing: the card is CLOSED if the mean drift from minute 1 to minute 10
is under that sport's round-trip cost in every sport (4.5c NBA and NFL, 6.4c NHL; the
Forensics desk's figures).

Usage: python3 drift_addition.py <games.json> <folder of pull run A> [<run B> ...]
"""
import glob, gzip, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # measure.py sits beside this file
import measure as M

COST = {"NBA": 0.045, "NFL": 0.045, "NHL": 0.064}


def cluster(xs):
    """xs: list of (game, value). Returns n events, n games, mean, cluster standard error."""
    n = len(xs)
    if not n:
        return 0, 0, None, None
    mean = sum(v for _, v in xs) / n
    by = {}
    for g, v in xs:
        by[g] = by.get(g, 0.0) + (v - mean)
    G = len(by)
    se = math.sqrt((G / (G - 1)) * sum(s * s for s in by.values())) / n if G > 1 else None
    return n, G, mean, se


def main():
    games = json.load(open(sys.argv[1]))
    cand = {}
    for run in sys.argv[2:]:
        for f in sorted(glob.glob(os.path.join(run, "[0-9]*.json.gz"))):
            try:
                M.walk(json.load(gzip.open(f, "rt")), cand)
            except (ValueError, OSError):
                continue
    late, first, triggers, no_quote = {}, {}, 0, 0
    for g in games:
        a, b = g["ml"]
        ml = M.minute_mids(cand.get(a, []))
        span = M.in_play(ml, g["sport"]) if ml else None
        if span is None:
            continue
        keep = lambda series: {m: v for m, v in series.items() if span[0] <= m <= span[1]}
        ml = keep(ml)
        spreads = {t: keep(M.minute_mids(cand.get(t, []))) for t in g["spread"]}
        if len(ml) < 30 or not any(len(v) >= 30 for v in spreads.values()):
            continue
        last = None
        for t in sorted(ml):                               # the trigger loop of measure.py, unchanged
            if t - M.LOOKBACK_MIN not in ml or (last is not None and t - last < M.GAP_MIN):
                continue
            if t + M.HORIZON_MIN > span[1]:
                continue
            before, move = ml[t - M.LOOKBACK_MIN], ml[t] - ml[t - M.LOOKBACK_MIN]
            if abs(move) < M.JUMP or not (M.BAND[0] <= before <= M.BAND[1]):
                continue
            last = t
            triggers += 1
            mover = M.team(a) if move > 0 else M.team(b)
            d_late, d_first = [], []
            for tk, s in spreads.items():
                sign = 1.0 if M.team(tk) == mover else -1.0
                if t + 1 in s and t + M.HORIZON_MIN in s:
                    d_late.append(sign * (s[t + M.HORIZON_MIN] - s[t + 1]))
                if t in s and t + 1 in s:
                    d_first.append(sign * (s[t + 1] - s[t]))
            if d_late:
                late.setdefault(g["sport"], []).append((g["game"], sum(d_late) / len(d_late)))
            else:
                no_quote += 1
            if d_first:
                first.setdefault(g["sport"], []).append((g["game"], sum(d_first) / len(d_first)))
    print("POST-READ ADDITION, NOT IN THE REGISTRATION. It can close the card; it is not evidence for it. Zero tries.")
    print("candle freshness measured on Bitcoin 15 minute only, not on sports; one-minute resolution, no seconds-level claim")
    print(f"trigger events {triggers} | with no spread market quoted at minute 1 and minute 10 {no_quote}")
    closed = True
    for sp in ("NBA", "NFL", "NHL"):
        n, G, m, se = cluster(late.get(sp, []))
        n0, G0, m0, se0 = cluster(first.get(sp, []))
        if not n:
            print(f"{sp}: no events")
            continue
        f = lambda v: "n/a" if v is None else f"{100 * v:+.2f}c"
        print(f"{sp}: events {n} | games {G} | mean drift minute 1 to 10: {f(m)} (cluster standard error {f(se).lstrip('+')}) | round-trip cost {100 * COST[sp]:.1f}c"
              f" | comparison, minute 0 to 1: events {n0}, games {G0}, mean {f(m0)} (standard error {f(se0).lstrip('+')})")
        if m >= COST[sp]:
            closed = False
    print("RESULT: " + ("CARD CLOSED: no lag at one minute resolution; whatever catching up exists is inside the first minute" if closed
                        else "at least one sport's mean drift is at or above its round-trip cost: that sport alone goes to the Head for a ruling on step 2"))


if __name__ == "__main__":
    main()
