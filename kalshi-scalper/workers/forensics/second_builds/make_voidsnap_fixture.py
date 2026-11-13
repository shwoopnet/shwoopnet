#!/usr/bin/env python3
"""A MADE-UP fixture for VOIDSNAP stage 1 in the pull-run folder shape (manifest.json + NNNN.json.gz): <out>/lists and <out>/candles, plus the marker file MADE_UP_DATA.
Nothing here is real: events, results, settlement values, quotes and volumes are invented so two independent builds can be run on the same rows and compared figure by figure.
usage: python3 -I make_voidsnap_fixture.py <out dir> [seed] [variant]
  variant plain (default): the mixed bag below; on seed 5 every detector fails a line under every carry (CLOSED).
  variant mixed: four voids in five (nine in ten in variant worth) are a "standing rumour": one book near the settlement value set 100 to 170 minutes before S and never changed, no trade from S to S plus 60,
    then ONE candle after S plus 60 with a side 10c or more under its settlement, standing. Seen with the registered carry, not with no carry: "depends on the carry".
  variant worth: the same voids with candles exactly at S minus 180, S minus 60 and S and six candles a minute apart for the cheap book, so all three carries see them: "worth a rule".

The lists run holds request live_KXCS2GAME in two pages and one hist_KXCS2GAME answer. The hist_ answer holds events closing before 2026-09-12: a build that opens it shows
outside-window drops or a different base; a correct build never opens it.
Planted on purpose (each can move a printed figure if a build reads the card differently):
  sample: events sharing a start time (ties in the match), team codes that start with digits, an event with one contract, one with three, a contract with no close time, an event
    ticker with no clock, events whose later close is after the window, events that are neither void nor played (yes and yes, no and no, yes and scalar);
  windows: a void closing exactly at S minus 185 minutes (no window) and others closing before it, voids closing before S, a void still open two days later;
    candles a batched request returns outside the event's own window (before S minus 185 and after the window's end), a candle exactly on each edge;
  quotes: standing books set once and never changed, empty-book candles (0.00 and 1.00), candles with one side missing or at 0.00 or 1.00, a candle exactly 60 minutes old at
    the reference minute and one 61 minutes old;
  exact ties in floats: a settlement of 0.30 with an ask of 0.20 (10c under: 0.30 - 0.20 is 0.0999... in floats), a spread of exactly 4c (0.54 - 0.50), a mid exactly 2c from
    the mid at S, a mid exactly 3c and exactly 1c from the settlement value, a 10c fall from S minus 180 to S, exactly 10.00 contracts and 9.99 contracts after the start;
  runs: a buyable run of exactly 5 minutes that starts at S plus 60, one of 5 minutes of which only 4 are at or after S plus 60, a run that changes side half way, a run cut
    by an empty-book candle, a run buyable but outside 15c to 64c, a run of exactly 4."""
import sys, os, json, gzip, random
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York"); MIN = 60; BACK, FWD = 185 * MIN, 480 * MIN
F = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
W1 = int(datetime(2026, 10, 22, 23, 59, 59, tzinfo=timezone.utc).timestamp())


def main(out, seed, variant="plain", n_void=150, n_played=900):
    assert variant in ("plain", "mixed", "worth"), variant
    rng = random.Random(seed); os.makedirs(out); open(os.path.join(out, "MADE_UP_DATA"), "w").write("invented rows for a build comparison; nothing here is real\n")
    markets = []; hist = []; candles = {}; events = []; used = set()
    def code():
        while True:
            c = "".join(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(rng.randint(2, 5)))
            if rng.random() < 0.04: c = rng.choice(["100", "9", "3D", "7"]) + c
            if c not in used: used.add(c); return c
    def start():
        d = datetime(2026, 9, 12, tzinfo=NY) + timedelta(days=rng.randint(0, 39))
        return int(d.replace(hour=rng.choice([4, 6, 7, 9, 10, 12, 13, 15, 17, 19]), minute=rng.choice([0, 0, 0, 30, 15, 45])).timestamp())
    def mk(t, e, close, result, sv): return {"ticker": t, "event_ticker": e, "close_time": F(close), "open_time": F(close - 86400), "result": result, "settlement_value_dollars": sv, "status": "finalized", "title": "made up"}
    def event(S, close, kind, sv_first=None, dest=None):
        a, b = sorted([code(), code()]); key = datetime.fromtimestamp(S, NY).strftime("%y%b%d%H%M").upper() + rng.choice([a + b, b + a])
        e = "KXCS2GAME-" + key; t1, t2 = e + "-" + a, e + "-" + b
        if kind == "void": r1 = r2 = "scalar"; s1, s2 = "%.4f" % sv_first, "%.4f" % (1 - sv_first)
        else:
            w = rng.random() < 0.5; r1, r2 = ("yes", "no") if w else ("no", "yes"); s1, s2 = ("1.0000", "0.0000") if w else ("0.0000", "1.0000")
        rows = [mk(t1, e, close - rng.randint(0, 40), r1, s1), mk(t2, e, close, r2, s2)]
        (markets if dest is None else dest).extend(rows); candles[t1] = {}; candles[t2] = {}
        return {"event": e, "t": (t1, t2), "S": S, "close": close, "kind": kind, "v": sv_first}
    def put(ev, ts, bid, ask, vol=0.0, which=0, both=True, gap=0.0):
        """a candle of contract `which`; with both=True the other contract gets the complementary book (gap widens it)"""
        candles[ev["t"][which]][ts] = (bid, ask, vol)
        if both: candles[ev["t"][1 - which]][ts] = (None if ask is None else round(1 - ask - gap, 2), None if bid is None else round(1 - bid + gap, 2), vol)
    def book(mid, sp): b = round(mid - sp / 2, 2); return max(0.01, b), min(0.99, round(b + sp, 2))
    cent = lambda x: round(min(0.9, max(0.1, x)), 2)

    # ---------------- played events
    for i in range(n_played):
        S = start(); close = min(W1 - 60, S + rng.randint(35, 200) * MIN + rng.randint(0, 59)); ev = event(S, close, "played"); events.append(ev)
        p0 = cent(rng.uniform(0.2, 0.8)); mode = rng.random(); t = S - BACK - rng.choice([0, 0, 3, 9, 20]) * MIN     # some candles before the window: only seen if a batch returns them
        p = p0
        while t < S:
            if mode < 0.08 and t > S - 100 * MIN: break                                         # sparse: nothing in the last 100 minutes before the start
            if 0.08 <= mode < 0.18 and t > S - 120 * MIN: p = cent(p - rng.choice([0.02, 0.03, 0.04]))  # a run before the start (lineup news): D3 can flag a played event
            else: p = cent(p + rng.choice([0, 0, 0, 0.01, -0.01]))
            put(ev, t, *book(p, rng.choice([0.01, 0.02, 0.02, 0.03])), vol=rng.choice([0, 0, 0, 2, 7]), gap=rng.choice([0, 0, 0.01])); t += rng.randint(1, 9) * MIN
        late = rng.randint(62, 95) * MIN if 0.18 <= mode < 0.30 else 0                           # a delayed start: frozen and untraded for the first hour: D1 and D2 can flag it
        t = S + (late or rng.randint(1, 4) * MIN); win0 = ev["close"] and markets[-2]["result"] == "yes"
        while t <= close:
            p = cent(p + (0.02 if win0 else -0.02) * rng.choice([0, 1, 1, 2, -1]))
            put(ev, t, *book(p, rng.choice([0.01, 0.02, 0.03, 0.05])), vol=rng.choice([0, 3, 12, 40]), gap=rng.choice([0, 0.01])); t += rng.randint(1, 3) * MIN
        if rng.random() < 0.3: put(ev, close + rng.randint(1, 5) * MIN, 0.0, 1.0)                 # after the close: outside the window

    # ---------------- void events
    for i in range(n_void):
        S = start(); mode = i % 20; p0 = cent(rng.uniform(0.25, 0.75)); v = cent(p0 + rng.choice([0, 0, 0.01, -0.01, 0.02, -0.03, 0.05, -0.08]))
        if i % 7 == 0: v = 0.50
        if variant != "plain" and i % (10 if variant == "worth" else 5) != 0:                                                     # a standing rumour (variants mixed and worth)
            close = min(W1 - 30, S + rng.randint(90, 600) * MIN + rng.choice([0, 0, 23])); ev = event(S, close, "void", sv_first=v); events.append(ev)
            ref = book(cent(v + rng.choice([0, 0, 0.01, -0.01, 0.02, -0.02, 0.03, -0.03, 0.04, -0.06] if variant == "mixed" else [0, 0, 0, 0.01, -0.01, 0.01, -0.01, 0.02, -0.02, 0.03, -0.03, 0.05])), 0.02)
            if variant == "worth": [put(ev, S + d * MIN, *ref) for d in (-180, -60, 0)]
            else: put(ev, S - rng.randint(100, 170) * MIN, *ref)
            side = i % 2; base = v if side == 0 else 1 - v; a = cent(base - rng.choice([0.10, 0.10, 0.12, 0.20, 0.30, 0.09])); sp = rng.choice([0.02, 0.03, 0.04, 0.04, 0.05]); t = S + rng.randint(61, 120) * MIN
            for k in range(6 if variant == "worth" else 1):
                if t + k * MIN <= min(close, S + FWD): put(ev, t + k * MIN, round(a - sp, 2), a, vol=2.0, which=side, both=False)
            continue
        if mode in (0, 1, 2): close = S - rng.randint(5, 150) * MIN                               # closed before the start
        elif mode == 3: close = S - BACK if i % 40 == 3 else S - rng.randint(186, 400) * MIN      # no window (one exactly on the edge)
        elif mode == 4: close = S + 2 * 86400 + rng.randint(0, 59)                                # still open two days later: the window ends at S plus 480
        else: close = S + rng.randint(40, 600) * MIN + rng.choice([0, 0, 17, 44])
        close = min(close, W1 - 30); ev = event(S, close, "void", sv_first=v); events.append(ev); ws, we = S - BACK, min(close, S + FWD)
        if rng.random() < 0.5: put(ev, ws - rng.randint(1, 30) * MIN, *book(cent(v - 0.15), 0.02))  # before the window: a buyable-looking book that must not be seen
        if rng.random() < 0.3: put(ev, ws, *book(p0, 0.02))                                       # exactly on the window's first edge
        if mode in (5, 6, 7, 8):                                                                  # quiet: a standing book set once, never changed
            put(ev, S - rng.choice([170, 181, 184, 120, 61, 60]) * MIN, *book(cent(v + rng.choice([0, 0.01, -0.01, 0.03, -0.03, 0.04])), rng.choice([0.02, 0.04])))
            if mode == 8: put(ev, S + rng.randint(20, 300) * MIN, 0.0, 1.0)                       # then an empty book
            continue
        t = ws + rng.randint(1, 12) * MIN; p = p0
        while t < min(S - 95 * MIN, we):
            p = cent(p + rng.choice([0, 0, 0.01, -0.01])); put(ev, t, *book(p, rng.choice([0.01, 0.02, 0.03])), vol=rng.choice([0, 0, 4]), gap=rng.choice([0, 0.01])); t += rng.randint(2, 15) * MIN
        side = i % 2; drop = rng.choice([0.06, 0.10, 0.12, 0.18, 0.25, 0.30]); when = rng.choice([-80, -40, -10, 15, 45, 70, 110]) * MIN
        if mode in (9, 10, 11, 12, 13):                                                           # a rumour: one side is sold `drop` under where it stood, then the book stands
            base = v if side == 0 else 1 - v; t = S + when; steps = rng.randint(1, 4)
            for k in range(1, steps + 1):
                if t > we: break
                px = cent(base - drop * k / steps); b, a = book(px, rng.choice([0.02, 0.03, 0.04, 0.05])); put(ev, t, b, a, vol=rng.choice([1, 6, 20]), which=side, gap=rng.choice([0, 0.01, 0.03])); t += rng.randint(1, 6) * MIN
            n_after = rng.choice([0, 0, 1, 3, 8])
            for k in range(n_after):
                t += rng.randint(5, 70) * MIN
                if t > we: break
                r = rng.random()
                if r < 0.25: put(ev, t, 0.0, 1.0)                                                 # an empty book: the carry stops here
                elif r < 0.40: put(ev, t, None, a, which=side, both=False)                        # one side missing on one contract only
                else: b, a = book(cent(base - drop + rng.choice([0, 0.01, -0.01, 0.05])), rng.choice([0.02, 0.04])); put(ev, t, b, a, vol=rng.choice([0, 2]), which=side)
        else:                                                                                     # a traded void: candles nearly every minute through the start
            t = max(t, S - 95 * MIN)
            while t <= min(we, S + rng.randint(70, 200) * MIN):
                p = cent(p + rng.choice([0, 0.01, -0.01, 0.02, -0.02])); put(ev, t, *book(p, rng.choice([0.01, 0.02, 0.04, 0.06])), vol=rng.choice([0, 1, 5, 15]), gap=rng.choice([0, 0.01])); t += rng.randint(1, 3) * MIN
        if rng.random() < 0.3: put(ev, we + rng.randint(1, 20) * MIN, *book(cent(v - 0.2), 0.02))   # after the window's end

    # ---------------- exact cases, each on its own void
    def exact(v, close_after=400):
        S = start(); ev = event(S, min(W1 - 30, S + close_after * MIN), "void", sv_first=v); events.append(ev); return ev, S
    ev, S = exact(0.30); put(ev, S - 30 * MIN, 0.29, 0.31); [put(ev, S + (60 + k) * MIN, 0.16, 0.20, vol=0) for k in range(5)]; put(ev, S + 65 * MIN, 0.28, 0.30)       # 10c under in floats 0.0999..., spread 4c, exactly 5 minutes from S+60; D1 fails (mid moved), D2 flags
    ev, S = exact(0.64); put(ev, S, 0.50, 0.54); [put(ev, S + (57 + k) * MIN, 0.50, 0.54) for k in range(5)]; put(ev, S + 62 * MIN, 0.62, 0.64)                         # spread exactly 4c, 5 minutes of which 2 are before S+60; the run goes on by carry? no: a new candle at S+62 ends it, so 3 at or after S+60 by D1/D2 and 5 over all
    ev, S = exact(0.50); put(ev, S - 10 * MIN, 0.49, 0.51); put(ev, S + 30 * MIN, 0.51, 0.53); put(ev, S + 50 * MIN, 0.47, 0.49)                                        # D1: mids exactly 2c from the mid at S
    ev, S = exact(0.50); put(ev, S - 10 * MIN, 0.49, 0.51); put(ev, S + 30 * MIN, 0.51, 0.54)                                                                           # D1: a mid 2.5c away: not frozen
    ev, S = exact(0.53); put(ev, S - 181 * MIN, 0.49, 0.51); put(ev, S - 60 * MIN, 0.51, 0.53)                                                                          # exactly 3c and exactly 1c from the settlement value; the S-60 candle is exactly 60 minutes old at S
    ev, S = exact(0.53); put(ev, S - 182 * MIN, 0.49, 0.51); put(ev, S - 61 * MIN, 0.51, 0.53)                                                                          # 61 minutes old at S: not seen under the 60 minute carry
    ev, S = exact(0.60); put(ev, S - 180 * MIN, 0.59, 0.61); put(ev, S, 0.49, 0.51)                                                                                      # D3: exactly 10c down from S-180 to S, exact candles (also seen with no carry)
    ev, S = exact(0.60); put(ev, S - 180 * MIN, 0.59, 0.61); put(ev, S - 1 * MIN, 0.50, 0.52)                                                                            # D3: 9c down: not flagged
    ev, S = exact(0.45); put(ev, S - 5 * MIN, 0.44, 0.46); put(ev, S + 10 * MIN, 0.44, 0.46, vol=5.0)                                                                    # D2: exactly 10.00 contracts after the start over both contracts: not under 10
    ev, S = exact(0.45); put(ev, S - 5 * MIN, 0.44, 0.46); put(ev, S + 10 * MIN, 0.44, 0.46, vol=4.995)                                                                  # D2: 9.99 contracts: flagged
    ev, S = exact(0.55); put(ev, S + 70 * MIN, 0.40, 0.43, which=0, both=False); put(ev, S + 70 * MIN, 0.30, 0.33, which=1, both=False); put(ev, S + 73 * MIN, 0.50, 0.56, which=0, both=False); put(ev, S + 76 * MIN, 0.0, 1.0, which=1, both=False)   # a run that changes side: 3 minutes on one contract, then 3 on the other: no run of 5
    ev, S = exact(0.50); put(ev, S + 61 * MIN, 0.36, 0.39); put(ev, S + 65 * MIN, 0.0, 1.0)                                                                              # a run of exactly 4, cut by an empty book
    ev, S = exact(0.90); put(ev, S + 61 * MIN, 0.74, 0.78, both=False); put(ev, S + 90 * MIN, 0.0, 1.0, both=False)                                                      # buyable for 29 minutes but above 64c: counts for line 1, not for the band count
    ev, S = exact(0.24); put(ev, S + 61 * MIN, 0.11, 0.14, both=False); put(ev, S + 70 * MIN, 0.12, 0.15, both=False); put(ev, S + 76 * MIN, 0.20, 0.22, both=False)    # 9 minutes under 15c, then 6 minutes at 15c (not 10c under 0.24? 0.24 - 0.15 = 0.09: not buyable)
    ev, S = exact(0.40, close_after=62); put(ev, S + 58 * MIN, 0.25, 0.28)                                                                                               # closes 2 minutes after S+60: a run of 5 overall, only 3 minutes at or after S+60

    # ---------------- drops and odd rows in the live answer
    S = start(); e = event(S, S + 3600, "played"); markets.pop()                                                                                                         # one contract only
    S = start(); e = event(S, S + 3600, "played"); markets.append(mk(e["event"] + "-ZZZ", e["event"], S + 3600, "no", "0.0000"))                                         # three contracts
    S = start(); e = event(S, S + 3600, "played"); markets[-1]["close_time"] = ""                                                                                        # no close time
    e = event(start(), 0, "played"); [markets.pop() for _ in range(2)]; markets += [mk("KXCS2GAME-FINALAAB-AA", "KXCS2GAME-FINALAAB", W1 - 5000, "yes", "1.0000"), mk("KXCS2GAME-FINALAAB-B", "KXCS2GAME-FINALAAB", W1 - 5000, "no", "0.0000")]   # no clock in the ticker
    for k in range(3):                                                                                                                                                   # the later close is after the window
        S = int(datetime(2026, 10, 22, 17, 0, tzinfo=NY).timestamp()); e = event(S, W1 + 600 + k, "void" if k == 0 else "played", sv_first=0.5)
    for res in (("yes", "yes"), ("no", "no"), ("yes", "scalar")):
        S = start(); e = event(S, S + 3600, "played"); markets[-2]["result"], markets[-1]["result"] = res
    for k in range(40):                                                                                                                                                  # the hist_ answer: closes before 2026-09-12, never to be opened
        S = int(datetime(2026, 9, rng.randint(1, 10), 12, 0, tzinfo=NY).timestamp()); event(S, S + 7200, "void" if k % 4 == 0 else "played", sv_first=0.5, dest=hist)

    # ---------------- write
    def write_run(folder, job, reqs):
        os.makedirs(folder); rows = []
        for n, (rid, params, body) in enumerate(reqs, 1):
            name = "%04d.json.gz" % n
            with gzip.open(os.path.join(folder, name), "wt") as f: json.dump(body, f)
            rows.append({"index": n, "id": rid, "path": "/markets" if "series_ticker" in params else "/markets/candlesticks", "params": params, "page": 1, "status": 200, "file": name, "truncated": False, "body_kind": "object"})
        json.dump({"job": {"job_id": job, "note": "MADE UP"}, "status": "complete", "requests_sent": len(rows), "rows": rows}, open(os.path.join(folder, "manifest.json"), "w"))
    rng.shuffle(markets); half = len(markets) // 2; lp = {"series_ticker": "KXCS2GAME", "status": "settled"}
    write_run(os.path.join(out, "lists"), "MADE_UP_LISTS", [("live_KXCS2GAME", lp, {"markets": markets[:half], "cursor": "x"}), ("live_KXCS2GAME", lp, {"markets": markets[half:], "cursor": ""}),
                                                            ("hist_KXCS2GAME", lp, {"markets": hist, "cursor": ""})])
    def cjson(ts, b, a, v):
        c = {"end_period_ts": ts, "volume_fp": "%.2f" % v if abs(v * 100 - round(v * 100)) < 1e-9 else "%.3f" % v}
        if b is not None: c["yes_bid"] = {"close_dollars": "%.4f" % b}
        if a is not None: c["yes_ask"] = {"close_dollars": "%.4f" % a}
        return c
    events.sort(key=lambda e: (e["S"], e["event"])); reqs = []
    for k in range(0, len(events), 6):                                                              # batched like the real job: one time range for several events, so some candles outside an event's own window come back
        grp = events[k:k + 6]; lo = min(e["S"] for e in grp) - BACK; hi = max(min(e["close"], e["S"] + FWD) for e in grp); tks = [t for e in grp for t in e["t"]]
        body = {"markets": [{"market_ticker": t, "candlesticks": [cjson(ts, *candles[t][ts]) for ts in sorted(candles[t]) if lo <= ts <= hi]} for t in tks]}
        reqs.append(("v%03d" % (k // 6 + 1), {"market_tickers": ",".join(tks), "start_ts": lo, "end_ts": hi, "period_interval": 1}, body))
    write_run(os.path.join(out, "candles"), "MADE_UP_CANDLES", reqs)
    print("made-up VOIDSNAP fixture written to %s: %d sampled-shape events (%d voids), %d list rows in the live answers, %d in the hist_ answer, %d candle requests, seed %d" % (
        out, len(events), sum(1 for e in events if e["kind"] == "void"), len(markets), len(hist), len(reqs), seed) + ", variant " + variant)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 5, sys.argv[3] if len(sys.argv) > 3 else "plain")
