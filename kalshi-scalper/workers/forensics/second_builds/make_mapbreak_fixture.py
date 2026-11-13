#!/usr/bin/env python3
"""A MADE-UP fixture for MAPBREAK step 1: invented matches, markets, candles and results in the pull-run folder shape (manifest.json + NNNN.json.gz).
Nothing here is real. It exists so two independent builds can be run on the same rows and compared figure by figure.
usage: python3 -I make_mapbreak_fixture.py <out dir> [seed]      writes <out>/lists and <out>/candles
The rows follow the registration's ticker shape: <match_series>-<key>-<TEAM>, <map_series>-<key>-<n>-<TEAM>, <total_maps_series>-<key>-<k> with floor_strike 2.5 for a best-of-three;
the key starts with the date and a four-digit US Eastern clock time. Version 2 (2026-11-13, for Amendments 8 to 10; version 1 is at commit db1c0354). Awkward cases are planted on purpose: not best-of-three, a start that cannot be derived, a pre-match minute
that needs stepping back or never fills, a look that needs stepping forward or never fills, wide spreads, a map with no single winner, a match in the held-out window,
a map result not yet visible in the quotes, and missing candles."""
import sys, os, json, gzip, random
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TITLES = {"CS2": ("KXCS2GAME", "KXCS2MAP", "KXCS2TOTALMAPS"), "DOTA2": ("KXDOTA2GAME", "KXDOTA2MAP", "KXDOTA2TOTALMAPS"),
          "VALORANT": ("KXVALORANTGAME", "KXVALORANTMAP", "KXVALORANTTOTALMAPS"), "LOL": ("KXLOLGAME", "KXLOLMAP", "KXLOLTOTALMAPS")}
PER_TITLE = {"CS2": 3000, "DOTA2": 1500, "VALORANT": 90, "LOL": 230}      # version 2: CS2 and Dota 2 are large enough to pass the 150 minimum
NY = ZoneInfo("America/New_York")
F = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(out, seed):
    rng = random.Random(seed); lists = {}; candles = {}
    def mk(t, close, result, **kw): return dict({"ticker": t, "event_ticker": t.rsplit("-", 1)[0], "close_time": F(close), "open_time": F(close - 90000), "result": result, "volume_fp": "5", "title": "made up"}, **kw)
    def cd(ts, bid, ask):
        c = {"end_period_ts": ts, "volume_fp": "1"}
        if bid is not None: c["yes_bid"] = {"close_dollars": "%.4f" % bid}
        if ask is not None: c["yes_ask"] = {"close_dollars": "%.4f" % ask}
        return c
    def quote(mid, spread): return max(0.01, round(mid - spread / 2, 2)), min(0.99, round(mid + spread / 2, 2))
    n = 0
    for cell, (G, M, T) in TITLES.items():
        for g in (G, M, T): lists.setdefault("live_" + g, {"markets": []})
        for i in range(PER_TITLE[cell]):
            n += 1
            local = datetime(2026, rng.choice([9, 10]), 1, tzinfo=NY).replace(day=rng.randint(14, 28) if rng.random() < 0.5 else rng.randint(1, 21), hour=rng.randint(6, 22), minute=rng.choice([0, 15, 30, 45]))
            if local.month == 9 and local.day < 14: local = local.replace(day=14)
            kind = rng.random()
            if kind < 0.03: local = local.replace(month=10, day=rng.randint(24, 30))           # held-out window: must be refused
            S = int(local.timestamp()); a, b = "T%04dA" % n, "T%04dB" % n
            key = local.strftime("%y%b%d%H%M").upper() + a + b
            q_true = rng.uniform(0.30, 0.70); p_pre = q_true * q_true * (3 - 2 * q_true)
            up = a if rng.random() < q_true else b; down = b if up == a else a
            len1 = rng.randint(25, 70) * 60
            if 0.03 <= kind < 0.06: len1 = rng.choice([8, 200]) * 60                          # start not derivable
            c1 = S + len1 + rng.randint(0, 59); c2 = c1 + rng.randint(8, 70) * 60 + rng.randint(0, 59)
            w2 = up if rng.random() < 0.55 else down; three = w2 != up
            cm = (c2 + rng.randint(25, 70) * 60) if three else (c2 + rng.randint(0, 4) * 60)
            winner = up if not three else (up if rng.random() < 0.5 else down)
            bo3 = not (0.06 <= kind < 0.10); no_map2 = 0.10 <= kind < 0.12; void1 = 0.12 <= kind < 0.135
            for t in (a, b):
                lists["live_" + G]["markets"].append(mk("%s-%s-%s" % (G, key, t), cm, "yes" if t == winner else "no"))
                lists["live_" + M]["markets"].append(mk("%s-%s-1-%s" % (M, key, t), c1, "" if void1 else ("yes" if t == up else "no")))
                if not no_map2: lists["live_" + M]["markets"].append(mk("%s-%s-2-%s" % (M, key, t), c2, "yes" if t == w2 else "no"))
                if three: lists["live_" + M]["markets"].append(mk("%s-%s-3-%s" % (M, key, t), cm, "yes" if t == winner else "no"))
            lists["live_" + T]["markets"].append(mk("%s-%s-2" % (T, key), cm, "yes" if three else "no", floor_strike=2.5, strike_type="greater"))
            if not bo3:
                lists["live_" + T]["markets"].append(mk("%s-%s-3" % (T, key), cm, "no", floor_strike=3.5, strike_type="greater"))
                lists["live_" + T]["markets"].append(mk("%s-%s-4" % (T, key), cm, "no", floor_strike=4.5, strike_type="greater"))
            # ---- candles
            tk = lambda series, *p: "-".join((series, key) + p)
            mt = {a: tk(G, a), b: tk(G, b)}; m1 = {a: tk(M, "1", a), b: tk(M, "1", b)}; m2 = {a: tk(M, "2", a), b: tk(M, "2", b)}
            for x in list(mt.values()) + list(m1.values()) + list(m2.values()): candles[x] = {}
            sp = lambda: rng.choice([0.01, 0.01, 0.02, 0.02, 0.03, 0.04, 0.06, 0.09])
            pre_mode = rng.random()                                                             # 0.80 fills at S-10; 0.10 needs stepping back; 0.05 the map contracts never line up; 0.05 nothing
            for back in range(40, 9, -1):
                ts = S - back * 60
                if pre_mode > 0.95: break
                show_match = pre_mode < 0.80 or back >= 14 or 0.90 <= pre_mode
                show_maps = (pre_mode < 0.80 or back >= 14) and not (0.90 <= pre_mode)
                jit = rng.uniform(-0.01, 0.01)
                for t in (a, b):
                    pm = (p_pre if t == up else 1 - p_pre) + jit * (1 if t == up else -1)
                    if show_match: candles[mt[t]][ts] = quote(min(0.97, max(0.03, pm)), sp())
                    if show_maps:
                        qm = (q_true if t == up else 1 - q_true) + rng.uniform(-0.05, 0.05) - (0.10 if n % 9 == 0 else 0.0)      # version 2: one match in nine has cheap map-1 contracts, so the placebo share is not zero
                        candles[m1[t]][ts] = quote(min(0.97, max(0.03, qm)), sp())
            def map_tail(mp, close, win, visible):
                """the map contracts around their close: the winner's bid shows 0.90 or more before the close only when 'visible'; after the close it does.
                Awkward cases for Amendments 8 to 10 (drawn AFTER the old draws so earlier rows keep their values where they can): the only quotes are 12 to 15 minutes
                old (age limit), both teams show a 0.90 bid, the loser's contract has no quote at all, an empty-book candle (bid 0, ask 1) is the last one."""
                mode = rng.random()
                for k in range(-6, 6):
                    ts = (close // 60) * 60 + k * 60
                    for t in (a, b):
                        if ts <= close and not visible: mid = 0.55 if t == win else 0.45
                        else: mid = 0.95 if t == win else 0.05
                        if rng.random() < 0.06: continue
                        bq = quote(mid, 0.02)
                        candles[mp[t]][ts] = (bq[0], None) if (rng.random() < 0.05) else bq
                c0 = (close // 60) * 60; late = lambda t: [x for x in candles[mp[t]] if x > c0 - 660]      # the pre-match candles are kept in every case
                if mode < 0.05:                                                       # only old quotes: nothing in the last 10 minutes before the close or after it
                    for t in (a, b):
                        for x in late(t): del candles[mp[t]][x]
                        for k in (12, 13, 15): candles[mp[t]][c0 - 60 * k] = quote(0.94 if t == win else 0.06, 0.02)
                elif mode < 0.08:                                                     # both teams' contracts show a bid of 0.90 or more from the close on
                    for t in (a, b):
                        for x in late(t):
                            if x > c0: candles[mp[t]][x] = (0.92, 0.95)
                        candles[mp[t]][c0 + 60] = (0.92, 0.95)
                elif mode < 0.10:                                                     # the loser's contract has no quote near the close or after it
                    lo_ = b if win == a else a
                    for x in late(lo_): del candles[mp[lo_]][x]
                elif mode < 0.15 and mode >= 0.13:                                    # the quotes name the WRONG team after the close (the posted result disagrees): still a bet as observed
                    lo_ = b if win == a else a
                    for x in late(win):
                        if x > c0: candles[mp[win]][x], candles[mp[lo_]][x] = (0.04, 0.07), (0.93, 0.96)
                    candles[mp[win]][c0 + 60], candles[mp[lo_]][c0 + 60] = (0.04, 0.07), (0.93, 0.96)
                elif mode < 0.13:                                                     # empty books (bid 0, ask 1) are the winner's last candles: not quotes, the one before them stands
                    for x in late(win):
                        if x >= c0 + 120: candles[mp[win]][x] = (0.0, 1.0)
            map_tail(m1, c1, up, rng.random() < 0.55)
            if not no_map2: map_tail(m2, c2, w2, rng.random() < 0.55)
            def look(close, value_up, mode):
                first = ((close + 120 + 59) // 60) * 60
                for k in range(0, 6):
                    ts = first + k * 60
                    if mode > 0.93: break
                    if 0.85 <= mode <= 0.93 and k < 2: continue                                # needs stepping forward
                    edge = rng.choice([0.0, 0.0, 0.0, 0.03, 0.06, 0.10, 0.14])
                    for t in (a, b):
                        v = value_up if t == up else 1 - value_up
                        candles[mt[t]][ts] = quote(min(0.97, max(0.03, v - edge * (1 if rng.random() < 0.6 else -0.3))), sp())
                        if ts - 60 in candles[mt[t]] and rng.random() < 0.7: candles[mt[t]][ts] = candles[mt[t]][ts - 60]     # version 2: a quote usually stands for the next minute, so some limits fill
            V = 1 - (1 - q_true) ** 2
            look(c1, V, rng.random())
            if three: look(c2, q_true, rng.random())
    os.makedirs(os.path.join(out, "lists")); os.makedirs(os.path.join(out, "candles"))
    def write(folder, bodies):
        rows = []
        for i, (rid, body) in enumerate(bodies):
            f = "%04d.json.gz" % (i + 1); gzip.open(os.path.join(folder, f), "wt").write(json.dumps(body)); rows.append({"id": rid, "status": 200, "file": f})
        json.dump({"rows": rows, "status": "complete", "note": "MADE-UP DATA"}, open(os.path.join(folder, "manifest.json"), "w"))
    write(os.path.join(out, "lists"), sorted(lists.items()))
    items = sorted(candles.items()); packs = [items[i:i + 400] for i in range(0, len(items), 400)]
    write(os.path.join(out, "candles"), [("c%04d" % i, {"markets": [{"market_ticker": t, "candlesticks": [cd(ts, q[0], q[1]) for ts, q in sorted(c.items())]} for t, c in p]}) for i, p in enumerate(packs)])
    print("made-up fixture written to %s: %d matches, %d candle tickers, seed %d" % (out, n, len(candles), seed))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 7)
