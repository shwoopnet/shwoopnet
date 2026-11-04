"""MLBHR1: unconditional cheap-side pool on KXMLBHR and KXMLBHIT 1+ rungs, with a ladder-sum filter. Research only.
Registration: workers/MLBHR1_REGISTRATION.md.  python -m scalper.mlbhr1 census OUT.json | build | candles MINUTES [STRIDE OFFSET] | score
Census reads listings only (ticker, event, close time, strike, volume): never `result` and never a price.
"""
from __future__ import annotations
import json, re, sqlite3, sys, time, statistics as st
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from . import api
from .candlefield import quote_close
from .nhlg1 import fee, net, cheap_side, valid, cluster_stats, profit_factor, md5, sha, C

CACHE = Path("/home/user/.cache/mlbhr1")
DB = CACHE / "mlbhr1.sqlite"
ROOT = Path(__file__).resolve().parents[2]
CUT = "2026-10-03T16:00:00Z"
SERIES = ("KXMLBHR", "KXMLBHIT")
LEAD, MAXPER, MIN_TRADES = 120, 2, 150
KEEP = ("ticker", "event_ticker", "yes_sub_title", "close_time", "open_time", "expected_expiration_time", "volume_fp", "floor_strike")
SCHEMA = """
CREATE TABLE IF NOT EXISTS gm(event TEXT PRIMARY KEY, series TEXT, start_ts INTEGER, md5 TEXT);
CREATE TABLE IF NOT EXISTS rung(ticker TEXT PRIMARY KEY, event TEXT, series TEXT, volume REAL);
CREATE TABLE IF NOT EXISTS candle(ticker TEXT, end_ts INTEGER, bid REAL, ask REAL, PRIMARY KEY(ticker, end_ts));
CREATE TABLE IF NOT EXISTS cdone(ticker TEXT PRIMARY KEY, n INTEGER);
"""


def conn():
    CACHE.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB, timeout=120)
    c.executescript(SCHEMA)
    return c


# ----------------------------------------------------------------------------- pure functions (tested)

EV = re.compile(r"^KXMLB(?:HR|HIT)-(\d\d)([A-Z]{3})(\d\d)(\d\d)(\d\d)")
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}


def event_start_ts(event: str, utc_offset_hours: int = -4):
    """Start time encoded in the event ticker (YYMONDDHHMM, US Eastern daylight time in this season). None if unparsable."""
    m = EV.match(event)
    if not m or m.group(2) not in MON:
        return None
    y, mo, d, hh, mm = 2000 + int(m.group(1)), MON[m.group(2)], int(m.group(3)), int(m.group(4)), int(m.group(5))
    try:
        dt = datetime(y, mo, d, hh, mm, tzinfo=timezone(timedelta(hours=utc_offset_hours)))
    except ValueError:
        return None
    return int(dt.timestamp())


def look_quote(candles, start_ts: int, lead: int = LEAD):
    ok = [r for r in candles if r[0] <= start_ts - lead and valid(r[1], r[2])]
    if not ok:
        return None
    ok.sort()
    return ok[-1][1], ok[-1][2]


def pick_two(rows):
    return sorted(rows, key=lambda r: sha(r["ticker"]))[:MAXPER]


def terciles(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 3], s[(2 * n) // 3]


def tercile_of(x, cuts):
    return 0 if x < cuts[0] else (1 if x < cuts[1] else 2)


def clustered(trades, key, mult=1.0):
    by = defaultdict(list)
    for t in trades:
        by[t[key]].append(net(t["win"], t["ask"], mult))
    n, m, se, z = cluster_stats(by)
    nets = [x for L in by.values() for x in L]
    return dict(n=n, clusters=len(by), mean_c=100 * m, se_c=100 * se, z=z, lo95_c=100 * (m - 1.96 * se) if se == se else float("nan"),
                pf=profit_factor(nets), win=(sum(1 for t in trades if t["win"]) / n if n else float("nan")),
                price=(sum(t["ask"] for t in trades) / n if n else float("nan")))


def verdict(n, half_means, lo95, pf):
    if n < MIN_TRADES:
        return "NOT_ENOUGH_DATA"
    if all(h > 0 for h in half_means) and lo95 > 0 and pf >= 1.5:
        return "LEAD"
    return "FALSIFIED"


# ----------------------------------------------------------------------------- listing and census

def listing():
    f = CACHE / "listing.json"
    if f.exists():
        return json.load(open(f))
    rows = {}
    for s in SERIES:
        for path, extra in (("/historical/markets", {}), ("/markets", {"status": "settled"})):
            cursor = None
            while True:
                q = dict(series_ticker=s, limit=1000, **extra)
                if cursor:
                    q["cursor"] = cursor
                d = api._get(path, q)
                time.sleep(1.0)
                mine = [m for m in d.get("markets", []) if m["ticker"].startswith(s + "-")]
                for m in mine:  # the cursor leaks into other series, so keep only this series and stop at the first page with none
                    rows[m["ticker"]] = {k: m.get(k) for k in KEEP}
                cursor = d.get("cursor")
                print(s, path, len(rows), len(mine), flush=True)
                if not cursor or not mine:
                    break
    out = list(rows.values())
    json.dump(out, open(f, "w"))
    return out


def build():
    c = conn()
    n = 0
    for r in listing():
        if (r["close_time"] or "9") >= CUT or r["floor_strike"] != 0.5:
            continue
        vol = float(r["volume_fp"] or 0)
        ts = event_start_ts(r["event_ticker"])
        if vol <= 0 or ts is None:
            continue
        sr = r["ticker"].split("-")[0]
        c.execute("INSERT OR IGNORE INTO gm VALUES(?,?,?,?)", (r["event_ticker"], sr, ts, md5(r["event_ticker"])))
        c.execute("INSERT OR IGNORE INTO rung VALUES(?,?,?,?)", (r["ticker"], r["event_ticker"], sr, vol))
        n += 1
    c.commit()
    return n


def census(out):
    rows = listing()
    pre = [r for r in rows if (r["close_time"] or "9") < CUT]
    build()
    c = conn()
    res = dict(total_listed=len(rows), pre_cut_markets=len(pre), post_cut_events=len({r["event_ticker"] for r in rows if (r["close_time"] or "") >= CUT}))
    for s in SERIES:
        per = [r[0] for r in c.execute("SELECT COUNT(*) FROM rung WHERE series=? GROUP BY event", (s,))]
        ev = c.execute("SELECT COUNT(*) FROM gm WHERE series=?", (s,)).fetchone()[0]
        res[s] = dict(pre_cut_events_with_a_volume_1plus=ev, rungs_1plus_with_volume=sum(per),
                      rungs_per_event_median=st.median(per) if per else 0, rungs_per_event_mean=(sum(per) / len(per) if per else 0),
                      first=min((r["close_time"] for r in pre if r["ticker"].startswith(s + "-")), default=None),
                      last=max((r["close_time"] for r in pre if r["ticker"].startswith(s + "-")), default=None))
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))


# ----------------------------------------------------------------------------- candles

def chosen_two(tickers):
    """The 2 rungs of a game fetched for the pooled rule: lowest sha1 of the ticker among ALL its volume-positive 1+ rungs (chosen before any price)."""
    return sorted(tickers, key=sha)[:MAXPER]


def cmd_candles(series, minutes, mode, stride=1, offset=0):
    """mode 'two': the 2 chosen rungs of each game of `series`, games strictly in md5 order of the event ticker.
    mode 'all': every other rung of the games of `series` whose 2 chosen rungs are done, in the same order (ladder subsample)."""
    c = conn()
    t_end = time.time() + 60 * minutes
    byg = defaultdict(list)
    for tk, ev in c.execute("SELECT ticker,event FROM rung WHERE series=?", (series,)):
        byg[ev].append(tk)
    starts = {r[0]: r[1] for r in c.execute("SELECT event,start_ts FROM gm")}
    order = sorted(byg, key=md5)
    print(series, mode, "games", len(order), flush=True)
    ok = fail = 0
    for pas in range(6):
        done = {r[0] for r in c.execute("SELECT ticker FROM cdone")}
        want = {}
        for g in order:
            two = chosen_two(byg[g])
            if mode == "two":
                need = [t for t in two if t not in done]
            else:
                if any(t not in done for t in two):
                    continue  # ladder games: those, in md5 order, whose pooled rungs are done (a failed fetch must not block the rest)
                need = [t for t in byg[g] if t not in done]
            if need:
                want[g] = need
        print("pass", pas, "games with work", len(want), flush=True)
        if not want:
            break
        for gi, (ev, need) in enumerate(want.items()):
            if gi % stride != offset:
                continue
            stt = starts[ev]
            for tk in need:
                if time.time() > t_end:
                    print("time box reached", flush=True)
                    c.commit()
                    return
                cs = None
                for a in range(4):
                    try:
                        cs = api._get(f"/historical/markets/{tk}/candlesticks", {"start_ts": stt - 3600, "end_ts": stt, "period_interval": 1}, retries=1).get("candlesticks", [])
                        break
                    except Exception:  # noqa: BLE001
                        time.sleep(2 + 3 * a)
                time.sleep(0.5)
                if cs is None:
                    fail += 1
                    continue
                ok += 1
                for x in cs:
                    c.execute("INSERT OR REPLACE INTO candle VALUES(?,?,?,?)", (tk, x["end_period_ts"], quote_close(x.get("yes_bid")), quote_close(x.get("yes_ask"))))
                c.execute("INSERT OR REPLACE INTO cdone VALUES(?,?)", (tk, len(cs)))
                c.commit()
            if gi % 10 == 0:
                print("pass", pas, "game", gi, "/", len(want), "ok", ok, "fail", fail, flush=True)
    print("candles done; ok", ok, "fail", fail, flush=True)


# ----------------------------------------------------------------------------- score (results read at score time only)

def results_for(tickers):
    """Results of the fetched rungs only, per event (called at score time, never during census). Cached outside the repo."""
    f = CACHE / "results.json"
    have = json.load(open(f)) if f.exists() else {}
    events = sorted({t.rsplit("-", 2)[0] for t in tickers if t not in have})
    for i, ev in enumerate(events):
        for a in range(5):
            try:
                for m in api._get("/historical/markets", dict(event_ticker=ev, limit=1000)).get("markets", []):
                    have[m["ticker"]] = m.get("result")
                break
            except Exception:  # noqa: BLE001
                time.sleep(3 + 3 * a)
        time.sleep(0.4)
        if i % 20 == 0:
            json.dump(have, open(f, "w"))
    json.dump(have, open(f, "w"))
    return have


def trade_of(c, tk, ev, sr, stt, res):
    q = look_quote(c.execute("SELECT end_ts,bid,ask FROM candle WHERE ticker=?", (tk,)).fetchall(), stt)
    if q is None or res.get(tk) not in ("yes", "no"):
        return None, None
    bid, ask = q
    sd = cheap_side(bid, ask)
    row = None
    if sd:
        side, a = sd
        row = dict(ticker=tk, game=ev, date=ev[len(sr) + 1:len(sr) + 8], side=side, ask=a, win=(res[tk] == "yes") == (side == "yes"), start=stt)
    return ask, row


def games_for(c, sr, res):
    """Pooled games of a series in md5 order (both chosen rungs fetched); ladder fields only when every rung is fetched."""
    done = {r[0] for r in c.execute("SELECT ticker FROM cdone")}
    byg = defaultdict(list)
    for tk, ev in c.execute("SELECT ticker,event FROM rung WHERE series=?", (sr,)):
        byg[ev].append(tk)
    starts = {r[0]: r[1] for r in c.execute("SELECT event,start_ts FROM gm")}
    G = []
    for ev in sorted(byg, key=md5):
        two = chosen_two(byg[ev])
        if any(t not in done for t in two):
            continue
        trades = [r for r in (trade_of(c, t, ev, sr, starts[ev], res)[1] for t in two) if r]
        g = dict(event=ev, series=sr, start=starts[ev], cheap=trades, ladder=False)
        if all(t in done for t in byg[ev]):
            asks, ev_n = [], 0
            for t in byg[ev]:
                a, _ = trade_of(c, t, ev, sr, starts[ev], res)
                if a is not None:
                    asks.append(a)
                    ev_n += res[t] == "yes"
            if len(asks) >= 8:
                g.update(ladder=True, lsum=sum(asks), events=ev_n, nl=len(asks))
        G.append(g)
    return G


def fmt(d):
    return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in d.items()}


def block(o, name, T, med):
    for t in T:
        t["half"] = "H1" if t["start"] < med else "H2"
    d = dict(game=clustered(T, "game"), date=clustered(T, "date"), x12=clustered(T, "game", 1.2))
    for h in ("H1", "H2"):
        d[h] = clustered([t for t in T if t["half"] == h], "game")
    d["verdict"] = verdict(d["game"]["n"], [d["H1"]["mean_c"], d["H2"]["mean_c"]], d["game"]["lo95_c"], d["game"]["pf"])
    o[name] = d


def score():
    c = conn()
    done = [r[0] for r in c.execute("SELECT ticker FROM cdone")]
    res = results_for(done)
    out = {}
    for sr in SERIES:
        G = games_for(c, sr, res)
        if not G:
            continue
        med = st.median([g["start"] for g in G])
        trades = [t for g in G for t in g["cheap"]]
        o = dict(games=len(G), cheap_trades=len(trades))
        block(o, "pool_2_per_game", trades, med)
        o["by_ask_bucket_information"] = {nm: clustered([t for t in trades if lo <= t["ask"] < hi], "game")
                                          for lo, hi, nm in ((0.03, 0.08, "3-8c"), (0.08, 0.15, "8-15c"), (0.15, 0.30001, "15-30c"))}
        o["side_counts"] = {s_: sum(1 for t in trades if t["side"] == s_) for s_ in ("yes", "no")}
        L = [g for g in G if g["ladder"]]
        o["ladder_games"] = len(L)
        if len(L) >= 3:
            third = L[: max(1, len(L) // 3)]
            cuts = terciles([g["lsum"] for g in third])
            for g in L:
                g["tc"] = tercile_of(g["lsum"], cuts)
            o["tercile_cuts_from_first_third"] = cuts
            o["by_tercile_games"] = {i: sum(1 for g in L if g["tc"] == i) for i in range(3)}
            o["by_tercile_trades"] = {i: clustered([t for g in L if g["tc"] == i for t in g["cheap"]], "game") for i in range(3)}
            block(o, "low_tercile", [t for g in L if g["tc"] == 0 for t in g["cheap"]], med)
            o["ladder"] = dict(mean_sum_ask=sum(g["lsum"] for g in L) / len(L), mean_events=sum(g["events"] for g in L) / len(L),
                               mean_rungs=sum(g["nl"] for g in L) / len(L))
        out[sr] = o
    json.dump(out, open(ROOT / "workers" / "MLBHR1_RESULT.json", "w"), indent=1, default=str)
    for sr, o in out.items():
        print("==", sr)
        for k, v in o.items():
            print(k, v if not isinstance(v, dict) else {a: (fmt(b) if isinstance(b, dict) else b) for a, b in v.items()})


if __name__ == "__main__":
    if sys.argv[1] == "census":
        census(sys.argv[2])
    elif sys.argv[1] == "build":
        print(build())
    elif sys.argv[1] == "candles":
        cmd_candles(sys.argv[2], float(sys.argv[3]), sys.argv[4], int(sys.argv[5]) if len(sys.argv) > 5 else 1, int(sys.argv[6]) if len(sys.argv) > 6 else 0)
    elif sys.argv[1] == "score":
        score()
