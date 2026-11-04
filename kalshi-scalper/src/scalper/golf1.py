"""GOLF1 (workers/GOLF1_REGISTRATION.md): the CHEAP side (ask 3c to 30c) of Kalshi PGA tournament-winner, top 10 and top 20 markets against a stroke model
built only from ESPN per-round scores, read after round 2 and after round 3. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA,
NOT_RUNNABLE. Nothing here means trade; no promote verb. Cheap side only: no favourite-side result is computed or printed anywhere in this file.

    python -m scalper.golf1 census   (listings and ESPN names only; no price, no Kalshi result)
    python -m scalper.golf1 fetch    (resumable, time boxed; candles of the registered universe, md5-ordered tournaments, before the frozen cut)
    python -m scalper.golf1 project  (counts treated rows from prices only; no Kalshi result is read; decides whether a scored read is allowed)
    python -m scalper.golf1 run      (the one scored read; refused a second time; refused if project said NOT_ENOUGH_DATA)
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
import time
import unicodedata
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

CUT = datetime(2026, 10, 3, 16, 0, tzinfo=timezone.utc)   # frozen last third: tournaments closing from here are never fetched or joined
SERIES = ("KXPGATOUR", "KXPGATOP10", "KXPGATOP20")
TOPN = {"KXPGATOP10": 10, "KXPGATOP20": 20}
LOOK_ROUNDS = (2, 3)
LOOK_HOUR = 10          # UTC, on the day after round r was played (event date + r days); before any US round-r+1 tee time
K_GRID = (5, 10, 20, 40, 80)
MIN_P, MAX_P = 0.09, 0.91      # a model probability outside this can never be a treated trade on either side (p >= 3 x ask, ask >= 0.03), so no candle is fetched
ASK_LO, ASK_HI, RATIO, HARD_LIMIT = 0.03, 0.30, 3.0, 0.30
C, MAX_PER_LOOK = 10, 3
SIMS = 4000
BAR_PF, MIN_TRADES, MIN_TOURNAMENTS = 1.5, 150, 40
Z_BAR = 5.27
BOX_S = 90 * 60         # time box for the candle fetch (registered)

D = Path(os.environ.get("GOLF1_DIR", "/tmp/g1"))        # caches live outside the repo
ESPN_DIR = D / "espn_golf"
OUT = D / "golf1"
RESULT = OUT / "golf1_result.txt"


def norm(name: str) -> str:
    n = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode().lower()
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    return " ".join(w for w in n.split() if w not in ("jr", "sr", "ii", "iii"))


# ---------- ESPN parsing and ratings ----------
def parse_event(e):
    """ESPN scoreboard event -> dict(id, date, name, players={norm: {r: strokes}}) with only COMPLETE (18 hole) rounds; None for a team event."""
    comp = (e.get("competitions") or [{}])[0]
    cs = comp.get("competitors")
    if not cs:
        return None
    players = {}
    for c in cs:
        nm = norm((c.get("athlete") or {}).get("displayName", ""))
        if not nm:
            continue
        rd = {}
        for ls in c.get("linescores", []):
            inner = ls.get("linescores") or []
            if len(inner) >= 18 and ls.get("value"):
                rd[int(ls["period"])] = float(ls["value"])
            elif ls.get("value") and not inner:
                pass
        # round r+1 presence as an alive marker is read separately: any linescore entry with a value
        started = {int(ls["period"]) for ls in c.get("linescores", []) if ls.get("value")}
        players[nm] = dict(rd=rd, started=started)
    if not players or max((len(p["rd"]) for p in players.values()), default=0) < 4:
        return None
    return dict(id=e["id"], date=e["date"][:10], name=e.get("name"), players=players)


def field_means(ev):
    out = {}
    for r in (1, 2, 3, 4):
        xs = [p["rd"][r] for p in ev["players"].values() if r in p["rd"]]
        if xs:
            out[r] = sum(xs) / len(xs)
    return out


def walk_forward(events):
    """events sorted by date. Returns {event_id: {name: (sum_x, n)}} = each player's sum of (strokes - field round mean) and rounds BEFORE that event."""
    tot = defaultdict(lambda: [0.0, 0])
    pre = {}
    for ev in events:
        pre[ev["id"]] = {nm: tuple(tot[nm]) for nm in ev["players"]}
        fm = field_means(ev)
        for nm, p in ev["players"].items():
            for r, s in p["rd"].items():
                tot[nm][0] += s - fm[r]
                tot[nm][1] += 1
    return pre


def rating(sn, k):
    s, n = sn
    return s / (n + k)


def fit(events, pre):
    """Choose shrink k by walk-forward MSE of round deviation over the TRAIN events (first two thirds), and sigma = rmse at that k."""
    best = None
    for k in K_GRID:
        se, n = 0.0, 0
        for ev in events:
            fm = field_means(ev)
            for nm, p in ev["players"].items():
                for r, s in p["rd"].items():
                    e = (s - fm[r]) - rating(pre[ev["id"]][nm], k)
                    se += e * e
                    n += 1
        mse = se / n if n else float("inf")
        if best is None or mse < best[1]:
            best = (k, mse, n)
    return dict(k=best[0], sigma=math.sqrt(best[1]), rounds=best[2])


# ---------- model ----------
def simulate(done, rat, rounds_left, sigma, seed):
    """done: totals so far (strokes), rat: expected per-round deviation, for the alive players (aligned lists). Returns win share, P(top10), P(top20)
    (ties included, as Kalshi's rule says) from SIMS simulated finishes; future rounds are integer strokes mean rat + N(0, sigma)."""
    import numpy as np
    n = len(done)
    rng = np.random.default_rng(seed)
    base = np.array(done, float)
    r = np.array(rat, float)
    fut = np.rint(r[None, :] * rounds_left + rng.standard_normal((SIMS, n)) * sigma * math.sqrt(rounds_left)) if rounds_left else np.zeros((SIMS, n))
    tot = base[None, :] + fut
    # rank count of players strictly better
    srt = np.sort(tot, axis=1)
    better = np.empty((SIMS, n))
    for j in range(n):
        better[:, j] = (srt < tot[:, [j]]).sum(axis=1)
    mn = srt[:, [0]]
    tied = (tot == mn)
    win = (tied / tied.sum(axis=1, keepdims=True)).mean(axis=0)
    return win, (better < 10).mean(axis=0), (better < 20).mean(axis=0)


def fee(price, contracts=C):
    return math.ceil(round(0.07 * contracts * price * (1 - price) * 100, 6)) / 100


def cheap_side(yes_bid, yes_ask):
    if yes_bid is None or yes_ask is None or not (0 < yes_bid < yes_ask < 1):
        return None
    if ASK_LO <= yes_ask <= ASK_HI:
        return "yes", yes_ask
    no_ask = 1 - yes_bid
    if ASK_LO <= no_ask <= ASK_HI:
        return "no", no_ask
    return None


def net_cents(ask, won, contracts=C):
    gross = (1.0 - ask) if won else -ask
    return (gross * contracts - fee(ask, contracts)) / contracts * 100


def treated(p_side, ask):
    return ask <= HARD_LIMIT and p_side >= RATIO * ask - 1e-9


def pick(rows):
    """rows of one (tournament, look, series): dicts with ratio; keep the MAX_PER_LOOK highest model-to-ask ratios among treated rows."""
    t = sorted((r for r in rows if r["treated"]), key=lambda r: (-r["p_side"] / r["ask"], r["ticker"]))
    return t[:MAX_PER_LOOK]


def profit_factor(xs):
    g = sum(x for x in xs if x > 0)
    l = -sum(x for x in xs if x < 0)
    return g / l if l > 0 else float("inf") if g > 0 else 0.0


def verdict(rows, midpoint, tournaments):
    """rows: (cluster, net_cents, start_key). FALSIFIED unless mean net > 0 in BOTH halves (split at midpoint) and PF >= 1.5; NOT_ENOUGH_DATA under 150 trades."""
    if len(rows) < MIN_TRADES:
        return "NOT_ENOUGH_DATA"
    h1 = [r[1] for r in rows if r[2] < midpoint]
    h2 = [r[1] for r in rows if r[2] >= midpoint]
    m1 = sum(h1) / len(h1) if h1 else 0.0
    m2 = sum(h2) / len(h2) if h2 else 0.0
    pf = profit_factor([r[1] for r in rows])
    return "NOT_YET_FALSIFIED" if (m1 > 0 and m2 > 0 and pf >= BAR_PF) else "FALSIFIED"


def look_ts(date_iso, r):
    d = datetime.strptime(date_iso, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=r, hours=LOOK_HOUR)
    return int(d.timestamp())


def look_quote(candles, ts):
    """Last candle ending at or before ts (within 6 hours) with a valid two-sided quote: (yes_bid, yes_ask) or None. candles: (end, bid, ask)."""
    best = None
    for end, b, a in candles:
        if ts - 6 * 3600 <= end <= ts and b is not None and a is not None and 0 < b < a < 1:
            if best is None or end > best[0]:
                best = (end, b, a)
    return (best[1], best[2]) if best else None


def md5_key(s):
    return hashlib.md5(s.encode()).hexdigest()


# ---------- universe ----------
def load_events():
    evs = []
    for f in sorted(ESPN_DIR.glob("ev*.json")):
        e = json.loads(f.read_text())
        if e:
            pe = parse_event(e)
            if pe:
                evs.append(pe)
    evs.sort(key=lambda e: (e["date"], e["id"]))
    return evs


def match_events(markets, evs):
    """Kalshi event ticker -> ESPN event: window of the earliest market close against the ESPN end date (-5..+4 days) and at least 30 shared names."""
    byev = defaultdict(list)
    for m in markets.values():
        byev[(m["series"], m["event_ticker"])].append(m)
    out = {}
    for key, ms in byev.items():
        close = min(x["close_time"] for x in ms)[:10]
        kn = {norm(x["yes_sub_title"]) for x in ms}
        best = None
        for ev in evs:
            end = (datetime.strptime(ev["date"], "%Y-%m-%d") + timedelta(days=3)).strftime("%Y-%m-%d")   # ESPN endDate is the Sunday 05:00Z (date + 3)
            d = (datetime.fromisoformat(close) - datetime.fromisoformat(end)).days
            if -5 <= d <= 4:
                ov = len(kn & set(ev["players"]))
                if ov >= 30 and (best is None or ov > best[0]):
                    best = (ov, ev["id"])
        if best:
            out[key] = best[1]
    return out


def model_for_look(ev, pre, par, r, seed):
    """Alive players after round r (a round r+1 entry exists, all rounds <= r complete). Returns {name: (p_win, p_top10, p_top20)}."""
    names = [nm for nm, p in ev["players"].items() if (r + 1) in p["started"] and all(q in p["rd"] for q in range(1, r + 1))]
    if len(names) < 20:
        return {}
    done = [sum(ev["players"][nm]["rd"][q] for q in range(1, r + 1)) for nm in names]
    rat = [rating(pre[ev["id"]][nm], par["k"]) for nm in names]
    w, t10, t20 = simulate(done, rat, 4 - r, par["sigma"], seed)
    return {nm: (float(w[i]), float(t10[i]), float(t20[i])) for i, nm in enumerate(names)}


def p_for(series, probs):
    return probs[0] if series == "KXPGATOUR" else probs[1] if series == "KXPGATOP10" else probs[2]


def list_markets(with_result):
    from . import api
    cut = CUT.strftime("%Y-%m-%dT%H:%M")
    fields = ("ticker", "event_ticker", "close_time", "open_time", "yes_sub_title")
    out = {}
    for s in SERIES:
        for path, live in (("/historical/markets", False), ("/markets", True)):
            cur = None
            while True:
                p = {"series_ticker": s, "limit": 1000}
                if live:
                    p["status"] = "settled"
                if cur:
                    p["cursor"] = cur
                d = api._get(path, p)
                for m in d.get("markets", []):
                    if (m.get("close_time") or "") < cut and m.get("result") in ("yes", "no"):
                        row = {k: m.get(k) for k in fields} | {"series": s, "src": "live" if live else "hist"}
                        if with_result:
                            row["result"] = m["result"]
                        out[m["ticker"]] = row
                cur = d.get("cursor")
                if not cur or not d.get("markets"):
                    break
    return out


def universe():
    """[(kalshi_event_key, espn_event, look_round, series, [(ticker, src, p_yes, name)])] using prices of nothing: model and listings only."""
    evs = load_events()
    pre = walk_forward(evs)
    order = [e["id"] for e in evs]
    tr = {}
    # the train third: first two thirds of the tournaments that have a Kalshi match, by ESPN date
    markets = {t: m for t, m in json.loads((OUT / "markets.json").read_text()).items() if m["series"] in SERIES}
    match = match_events(markets, evs)
    used = sorted({ev_id for ev_id in match.values()}, key=lambda i: order.index(i))
    ntrain = (2 * len(used)) // 3
    train_ids = set(used[:ntrain])
    par = fit([e for e in evs if e["id"] in train_ids], pre)
    byid = {e["id"]: e for e in evs}
    byev = defaultdict(list)
    for m in markets.values():
        byev[(m["series"], m["event_ticker"])].append(m)
    uni = []
    cache = {}
    for key, ms in byev.items():
        if key not in match:
            continue
        ev = byid[match[key]]
        for r in LOOK_ROUNDS:
            if (ev["id"], r) not in cache:
                cache[(ev["id"], r)] = model_for_look(ev, pre, par, r, int(md5_key(ev["id"] + str(r))[:8], 16))
            probs = cache[(ev["id"], r)]
            lt = look_ts(ev["date"], r)
            rows = []
            for m in ms:
                nm = norm(m["yes_sub_title"])
                if nm not in probs or (m["close_time"] or "") <= datetime.fromtimestamp(lt, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"):
                    continue
                py = p_for(key[0], probs[nm])
                if MIN_P <= py <= MAX_P:
                    rows.append((m["ticker"], m["src"], py, nm))
            if rows:
                uni.append(dict(key=f"{key[0]}|{key[1]}", espn=ev["id"], date=ev["date"], r=r, series=key[0], look=lt, mk=rows))
    return uni, par, train_ids


def census():
    OUT.mkdir(parents=True, exist_ok=True)
    mp = OUT / "markets.json"
    if not mp.exists():
        mp.write_text(json.dumps(list_markets(False)))
    uni, par, train = universe()
    tours = {u["espn"] for u in uni}
    by = defaultdict(set)
    n_mk = defaultdict(int)
    for u in uni:
        by[u["series"]].add(u["espn"])
        n_mk[u["series"]] += len(u["mk"])
    print("fit", par, "train tournaments", len(train))
    print("tournaments with candidates", len(tours), {s: len(v) for s, v in by.items()}, "candidate markets (model p in [0.09, 0.91])", dict(n_mk))
    print("looks", len(uni), "batched requests at 8 markets", sum(math.ceil(len(u["mk"]) / 8) for u in uni))


def fetch():
    from . import api
    from .candlefield import quote_close
    OUT.mkdir(parents=True, exist_ok=True)
    uni, par, train = universe()
    cp = OUT / "candles.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}
    tourn = sorted({u["espn"] for u in uni}, key=md5_key)
    t0 = time.time()
    for tid in tourn:
        for u in [x for x in uni if x["espn"] == tid]:
            todo = [m for m in u["mk"] if m[0] not in have]
            live = [m for m in todo if m[1] == "live"]
            hist = [m for m in todo if m[1] == "hist"]
            for i in range(0, len(live), 8):
                if time.time() - t0 > BOX_S:
                    cp.write_text(json.dumps(have)); print("time box reached"); return
                ch = live[i:i + 8]
                time.sleep(3.3)
                try:
                    got = api.batch_candlesticks([m[0] for m in ch], u["look"] - 6 * 3600, u["look"])
                except Exception:
                    continue
                for m in ch:
                    have[m[0] + f"@{u['look']}"] = [(c["end_period_ts"], quote_close(c.get("yes_bid")), quote_close(c.get("yes_ask"))) for c in got.get(m[0], [])]
            for m in hist:
                if time.time() - t0 > BOX_S:
                    cp.write_text(json.dumps(have)); print("time box reached"); return
                time.sleep(3.3)
                try:
                    d = api._get(f"/historical/markets/{m[0]}/candlesticks", {"start_ts": u["look"] - 6 * 3600, "end_ts": u["look"], "period_interval": 1})
                except Exception:
                    continue
                have[m[0] + f"@{u['look']}"] = [(c["end_period_ts"], quote_close(c.get("yes_bid")), quote_close(c.get("yes_ask"))) for c in d.get("candlesticks", [])]
        cp.write_text(json.dumps(have))
        print("tournament done", tid, len(have), flush=True)
    cp.write_text(json.dumps(have))
    print("done", len(have))


def build_rows(uni, candles, results):
    """Cheap-side rows per look. results is ticker -> 'yes'|'no' or None (project). Returns rows dicts."""
    rows = []
    for u in uni:
        for tk, src, py, nm in u["mk"]:
            ck = f"{tk}@{u['look']}"
            if ck not in candles:
                continue
            q = look_quote(candles[ck], u["look"])
            if q is None:
                continue
            cs = cheap_side(*q)
            if cs is None:
                continue
            side, ask = cs
            p_side = py if side == "yes" else 1 - py
            row = dict(ticker=tk, key=u["key"], espn=u["espn"], date=u["date"], r=u["r"], series=u["series"], side=side, ask=ask, p_side=p_side,
                       treated=treated(p_side, ask), net=None, won=None)
            if results is not None:
                won = (results[tk] == "yes") if side == "yes" else (results[tk] == "no")
                row["won"], row["net"] = won, net_cents(ask, won)
            rows.append(row)
    return rows


def select(rows):
    g = defaultdict(list)
    for r in rows:
        g[(r["key"], r["r"])].append(r)
    return [x for v in g.values() for x in pick(v)]


def project():
    uni, par, train = universe()
    candles = json.loads((OUT / "candles.json").read_text())
    done_t = {k.split("@")[0] for k in candles}
    covered = [u for u in uni if all(m[0] + f"@{u['look']}" in candles for m in u["mk"])]
    rows = build_rows(covered, candles, None)
    tr = select(rows)
    ct = len({u["espn"] for u in covered})
    allt = len({u["espn"] for u in uni})
    proj = len(tr) * allt / max(ct, 1)
    txt = (f"fully fetched looks {len(covered)} of {len(uni)}; tournaments {ct} of {allt}; cheap-side rows {len(rows)}; treated (after max 3 per look) {len(tr)} "
           f"in {len({r['espn'] for r in tr})} tournaments; projected on all {allt} tournaments: {proj:.0f} (bar {MIN_TRADES} trades, {MIN_TOURNAMENTS} tournaments)")
    ok = proj >= MIN_TRADES and allt >= MIN_TOURNAMENTS
    txt += "\nPROJECT " + ("RUNNABLE" if ok else "NOT_ENOUGH_DATA")
    (OUT / "golf1_project.txt").write_text(txt + "\n")
    print(txt)


def cluster_z(obs):
    from .calibration import cluster_mean_z
    return cluster_mean_z(obs)


def run():
    if RESULT.exists():
        print("refused: the scored read was already run"); return
    pj = (OUT / "golf1_project.txt")
    if not pj.exists() or "NOT_ENOUGH_DATA" in pj.read_text():
        print("refused: project says NOT_ENOUGH_DATA or was not run"); return
    uni, par, train = universe()
    candles = json.loads((OUT / "candles.json").read_text())
    markets = list_markets(True)
    results = {tk: m["result"] for tk, m in markets.items()}
    covered = [u for u in uni if all(m[0] + f"@{u['look']}" in candles for m in u["mk"])]
    rows = [r for r in build_rows(covered, candles, results)]
    tr = select(rows)
    lines = [f"cheap-side rows {len(rows)}, treated {len(tr)}, tournaments {len({r['espn'] for r in tr})}, model k {par['k']} sigma {par['sigma']:.2f}"]
    for tag, rs in (("treated", tr), ("control", rows)):
        if not rs:
            continue
        n = len(rs)
        m, se, z = cluster_z([(r["espn"], r["net"]) for r in rs])
        lines.append(f"{tag}: n {n} mean {m:+.2f}c win {sum(r['won'] for r in rs)/n:.3f} vs mean ask {sum(r['ask'] for r in rs)/n:.3f} "
                     f"PF {profit_factor([r['net'] for r in rs]):.2f} tournament-cluster z {z:+.2f}")
    if tr:
        dates = sorted(r["date"] for r in tr)
        mid = dates[len(dates) // 2]
        h1 = [r["net"] for r in tr if r["date"] < mid]
        h2 = [r["net"] for r in tr if r["date"] >= mid]
        lines.append(f"halves {len(h1)}/{sum(h1)/max(len(h1),1):+.2f}c, {len(h2)}/{sum(h2)/max(len(h2),1):+.2f}c")
        v = verdict([(r["espn"], r["net"], r["date"]) for r in tr], mid, len({r["espn"] for r in tr}))
        m, se, z = cluster_z([(r["espn"], r["net"]) for r in tr])
        cm = sum(r["net"] for r in rows) / len(rows)
        if v == "NOT_YET_FALSIFIED" and not (z >= Z_BAR and m >= 2.0 and m > cm):
            v = "FALSIFIED"
        lines.append("VERDICT " + v)
    else:
        lines.append("VERDICT NOT_ENOUGH_DATA")
    RESULT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"census": census, "fetch": fetch, "project": project, "run": run}.get(cmd, lambda: print(__doc__))()
