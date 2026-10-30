"""SPORTCONS1 (workers/SPORTCONS1_REGISTRATION.md): sports consistency locks. Research only.
Usage: python -m scalper.sportcons1 inventory | t1   (t1 refuses a second run)
Prices only; no settled result is read by inventory or t1."""
from __future__ import annotations
import json, math, sqlite3, statistics as st, sys
from collections import defaultdict
from .paths import DATA_DIR

NO_TIE = ("KXMLBGAME", "KXNBAGAME", "KXNCAAFGAME")  # NFL can tie: YES+YES is not a lock there
C = 10


def fee(p, c=C):
    return math.ceil(0.07 * c * p * (1 - p) * 100 - 1e-9) / 100 / c


def quotes_winner():
    """(event, series) -> {leg: {end_ts: (bid, ask, vol)}} for two-leg winner events (espn1)."""
    db = sqlite3.connect(DATA_DIR / "espn1.sqlite")
    q = defaultdict(dict)
    for t, e, b, a, v in db.execute("select ticker, end_ts, bid, ask, volume from candle"):
        q[t][e] = (b, a, v or 0)
    out = []
    for ev, s, h, a in db.execute("select event, series, home_ticker, away_ticker from match"):
        if h in q and a in q:
            out.append((ev, s, q[h], q[a]))
    close = dict(db.execute("select ticker, close_ts from kmarket"))
    return out, close


def pairs_totals():
    """(game ticker prefix) -> list of (game strike, game quotes, 1H strike, 1H quotes) where K_game <= K_1H."""
    db = sqlite3.connect(DATA_DIR / "sports1.sqlite")
    mk = defaultdict(lambda: {"g": [], "h": []})
    for t, s, k, cl in db.execute("select ticker, series, strike, close_ts from market where strike is not null"):
        sp = s.replace("1HTOTAL", "").replace("TOTAL", "")
        key = (sp, t.split("-")[1])
        mk[key]["h" if "1HTOTAL" in s else "g"].append((k, t, cl))
    q = defaultdict(dict)
    for t, e, b, a, v in db.execute("select ticker, end_ts, bid_c, ask_c, volume from candle where bid_c is not null and ask_c is not null"):
        q[t][e] = (b, a, v or 0)
    return mk, q


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else None


def inventory():
    L = []
    # R1/R2: winner complement
    ev, close = quotes_winner()
    by = defaultdict(lambda: dict(games=0, both=0, sp=[], vh=[], va=[], mins=0))
    for e, s, qh, qa in ev:
        d = by[s]; d["games"] += 1
        common = set(qh) & set(qa)
        if common:
            d["both"] += 1; d["mins"] += len(common)
            for ts in common:
                d["sp"].append(max(qh[ts][1] - qh[ts][0], qa[ts][1] - qa[ts][0])); d["vh"].append(qh[ts][2]); d["va"].append(qa[ts][2])
    L.append("R1/R2 winner complement (home YES + away YES, or both NO), espn1.sqlite candles, same-minute pairs only")
    for s, d in sorted(by.items()):
        L.append(f"  {s}: games {d['games']}, games with >=1 same-minute pair {d['both']}, pair-minutes {d['mins']}, "
                 f"median wider-leg spread {100*st.median(d['sp']):.1f}c, p90 {100*pct(d['sp'],.9):.1f}c, "
                 f"median leg volume/min {st.median(d['vh']+d['va']):.0f} contracts")
    # R3: game total vs 1H total with K_game <= K_1H
    mk, q = pairs_totals()
    agg = defaultdict(lambda: dict(games=0, withpair=0, pairs=0, mins=0, sp=[], vg=[], vh=[], twosided=0))
    for (sp, ev_), d in mk.items():
        a = agg[sp]; a["games"] += 1 if d["g"] and d["h"] else 0
        if not (d["g"] and d["h"]): continue
        got = False
        for kg, tg, _ in d["g"]:
            for kh, th, _ in d["h"]:
                if kg <= kh:
                    a["pairs"] += 1
                    common = set(q[tg]) & set(q[th])
                    if common:
                        got = True; a["mins"] += len(common)
                        for ts in common:
                            a["sp"].append(max(q[tg][ts][1] - q[tg][ts][0], q[th][ts][1] - q[th][ts][0])); a["vg"].append(q[tg][ts][2]); a["vh"].append(q[th][ts][2])
        a["withpair"] += got
    L.append("R3 game total vs first-half total, strikes with K_game <= K_1H (the only strict implication: 1H over K_1H => game over K_game)")
    for s, a in sorted(agg.items()):
        L.append(f"  {s}: games with both a game and a 1H market {a['games']}, strike pairs with K_game<=K_1H {a['pairs']}, "
                 f"games with a same-minute pair {a['withpair']}, pair-minutes {a['mins']}"
                 + (f", median wider-leg spread {100*st.median(a['sp']):.1f}c, median volume game/1H {st.median(a['vg']):.0f}/{st.median(a['vh']):.0f}" if a["sp"] else ""))
    # games where the 1H strike range overlaps game range at all
    L.append("R3b strike ranges (median per game): ")
    for sp in agg:
        gs, hs = [], []
        for (s2, _), d in mk.items():
            if s2 == sp and d["g"] and d["h"]:
                gs.append(min(k for k, *_ in d["g"])); hs.append(max(k for k, *_ in d["h"]))
        if gs: L.append(f"  {sp}: median lowest game strike {st.median(gs):.1f}, median highest 1H strike {st.median(hs):.1f}")
    # relations NOT on file
    db = sqlite3.connect(DATA_DIR / "sports1.sqlite"); s1 = [r[0] for r in db.execute("select distinct series from market")]
    db2 = sqlite3.connect(DATA_DIR / "espn1.sqlite"); s2 = [r[0] for r in db2.execute("select distinct series from kmarket")]
    L.append(f"series on file: sports1 {s1}; espn1 {s2}; sports.sqlite 12 game-winner series (hourly candles, pre-game only)")
    L.append("NOT on file: first-half winner, spread ladders (win by 5+/10+), game winner vs spread, first-half spread: no such series in any local database.")
    txt = "\n".join(L); print(txt); return txt


def t1():
    out = DATA_DIR / "sportcons1_t1_result.txt"
    if out.exists(): print("Refusing to run again"); return
    ev, close = quotes_winner()
    games = []
    for e, s, qh, qa in ev:
        games.append((min(close.get(k, 0) for k in [e + "-x"]) if False else max(max(qh), max(qa)), e, s, qh, qa))
    games.sort(); n = len(games); hold = games[-1][0] - 12 * 86400
    older = [g for g in games if g[0] < hold]; mid = older[len(older) // 2][0]
    win = lambda c: 2 if c >= hold else (0 if c < mid else 1)
    names = ("discovery", "validation", "holdout")
    R = {"yes_both": [dict(g=0, lockg=0, mins=0, m1c=0, best=-9.0, ex=[]) for _ in range(3)], "no_both": [dict(g=0, lockg=0, mins=0, m1c=0, best=-9.0, ex=[]) for _ in range(3)]}
    for last, e, s, qh, qa in games:
        w = win(last)
        for kind in R: R[kind][w]["g"] += 1
        hitY = hitN = False
        for ts in set(qh) & set(qa):
            (bh, ah, vh), (ba, aa, va) = qh[ts], qa[ts]
            if min(vh, va) < C: continue
            if s in NO_TIE and 0 < ah < 1 and 0 < aa < 1:
                lock = 1 - ah - aa - fee(ah) - fee(aa); d = R["yes_both"][w]
                d["best"] = max(d["best"], lock)
                if lock > 0:
                    d["mins"] += 1; d["m1c"] += lock >= 0.01; hitY = True
                    if len(d["ex"]) < 5: d["ex"].append((e, ts, ah, aa, round(100 * lock, 2)))
            if 0 < bh < 1 and 0 < ba < 1:
                lock = bh + ba - 1 - fee(1 - bh) - fee(1 - ba); d = R["no_both"][w]
                d["best"] = max(d["best"], lock)
                if lock > 0:
                    d["mins"] += 1; d["m1c"] += lock >= 0.01; hitN = True
                    if len(d["ex"]) < 5: d["ex"].append((e, ts, bh, ba, round(100 * lock, 2)))
        R["yes_both"][w]["lockg"] += hitY; R["no_both"][w]["lockg"] += hitN
    # R3
    mk, q = pairs_totals()
    gm = []
    for (sp, ev_), d in mk.items():
        if d["g"] and d["h"]: gm.append((min(c for *_, c in d["g"]), sp, ev_, d))
    gm.sort(); hold3 = gm[-1][0] - 12 * 86400
    older3 = [g for g in gm if g[0] < hold3]; mid3 = older3[len(older3) // 2][0]
    w3 = lambda c: 2 if c >= hold3 else (0 if c < mid3 else 1)
    T = [dict(g=0, lockg=0, mins=0, m1c=0, best=-9.0, ex=[]) for _ in range(3)]
    for cl, sp, ev_, d in gm:
        w = w3(cl); T[w]["g"] += 1; hit = False
        for kg, tg, _ in d["g"]:
            for kh, th, _ in d["h"]:
                if kg > kh: continue
                for ts in set(q[tg]) & set(q[th]):
                    (bg, ag, vg), (bh, ah, vh) = q[tg][ts], q[th][ts]
                    if min(vg, vh) < C or not (0 < ag < 1 and 0 < bh < 1): continue
                    lock = bh - ag - fee(ag) - fee(1 - bh)
                    T[w]["best"] = max(T[w]["best"], lock)
                    if lock > 0:
                        T[w]["mins"] += 1; T[w]["m1c"] += lock >= 0.01; hit = True
                        if len(T[w]["ex"]) < 5: T[w]["ex"].append((ev_, kg, kh, ts, ag, bh, round(100 * lock, 2)))
        T[w]["lockg"] += hit
    L = []
    for name, rows in (("R2 winner YES+YES (no-tie sports)", R["yes_both"]), ("R2 winner NO+NO", R["no_both"]), ("R3 game total vs 1H total", T)):
        L.append(name + "  (lock = guaranteed payoff minus ask cost minus rounded fees, 10 contracts, both legs traded that minute)")
        for nm, d in zip(names, rows):
            L.append(f"  {nm}: units {d['g']}, units with a lock > 0 {d['lockg']}, lock-minutes {d['mins']} (>=1c: {d['m1c']}), best {100*d['best']:+.2f}c/contract")
            for x in d["ex"]: L.append(f"     example {x}")
    txt = "\n".join(L); out.write_text(txt + "\n"); print(txt)


if __name__ == "__main__":
    {"inventory": inventory, "t1": t1}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
