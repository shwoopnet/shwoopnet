"""FLOWX1: taker flow on the cheap side of non-15-minute, non-Bitcoin markets (public tape; research only, no orders).
    python3 -I -m scalper.flowx1 census OUT.sqlite      (market list and volumes only; the result field is never stored)
Registration: workers/FLOWX1_REGISTRATION.md. Cheap side only (ask 3c to 30c).
"""
from __future__ import annotations
import json, sqlite3, sys, time, datetime
import urllib.request, urllib.parse, urllib.error
from . import api

BASE = "https://api.elections.kalshi.com/trade-api/v2"   # api.BASES[0] (external-api) was refused 2026-11-06 while this host answered


def get(path, params=None, tries=6):
    url = BASE + path + ("?" + urllib.parse.urlencode(params) if params else "")
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=25) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 429:
                time.sleep(4.0 * (i + 1))
            else:
                time.sleep(2.0)
        except Exception as e:  # noqa
            last = e
            time.sleep(3.0)
    raise RuntimeError("GET %s failed: %s" % (path, last))

CUT = int(datetime.datetime(2026, 10, 3, 16, tzinfo=datetime.timezone.utc).timestamp())   # frozen last third starts here: never fetched
START = int(datetime.datetime(2026, 9, 6, tzinfo=datetime.timezone.utc).timestamp())   # live /markets and /markets/trades tier only (the historical endpoints were rate limited 2026-11-06)
CATS = ("Financials", "Crypto", "Commodities")
FREQS = ("hourly", "daily", "weekly")
EXCLUDE_WORDS = ("TEST",)


def universe(series_list):
    """Series chosen from the public series catalogue only (category, frequency, title). No price or outcome."""
    out = []
    for s in series_list:
        t, title = s["ticker"], (s.get("title") or "")
        if s.get("category") not in CATS or s.get("frequency") not in FREQS:
            continue
        if "15M" in t or any(w in t for w in EXCLUDE_WORDS):
            continue
        if "Bitcoin" in title or t.startswith("KXBTC") or t in ("BTC", "BTCD", "BTCD-B"):   # BTC hourly is FLOWHR1's lane
            continue
        out.append(t)
    return sorted(set(out))


def census(out):
    ser = get("/series", {})["series"]
    U = universe(ser)
    db = sqlite3.connect(out)
    db.execute("create table if not exists mk(ticker text primary key, series text, event text, open_ts integer, close_ts integer, volume real, src text)")
    db.execute("create table if not exists sdone(series text primary key, n integer)")
    done = {r[0] for r in db.execute("select series from sdone")}
    print("universe", len(U), "done", len(done), flush=True)
    for k, s in enumerate(U):
        if s in done:
            continue
        rows = []
        for path, extra in (("/markets", {"status": "settled", "min_close_ts": START, "max_close_ts": CUT - 1}),):
            cur = None
            while True:
                p = {"series_ticker": s, "limit": 1000, **extra}
                if cur:
                    p["cursor"] = cur
                try:
                    d = get(path, p)
                except Exception as e:  # noqa
                    print("fail", path, s, e, flush=True)
                    break
                for m in d.get("markets", []):
                    ct = int(datetime.datetime.fromisoformat(m["close_time"].replace("Z", "+00:00")).timestamp())
                    if not (START <= ct < CUT) or m.get("result") not in ("yes", "no"):
                        continue
                    ot = int(datetime.datetime.fromisoformat(m["open_time"].replace("Z", "+00:00")).timestamp())
                    rows.append((m["ticker"], s, m.get("event_ticker"), ot, ct, float(m.get("volume_fp") or m.get("volume") or 0), path))
                cur = d.get("cursor")
                time.sleep(1.2)
                if not cur or not d.get("markets"):
                    break
        db.executemany("insert or ignore into mk values(?,?,?,?,?,?,?)", rows)
        db.execute("insert or replace into sdone values(?,?)", (s, len(rows)))
        db.commit()
        print(k, len(U), s, len(rows), flush=True)


# ---------------------------------------------------------------- list / fetch / score (registration of 2026-11-06)
import hashlib, math, random
from collections import defaultdict

LO_ASK, HI_ASK, LIMIT = 0.03, 0.30, 0.30
FLOW_HI, FLOW_LO = 0.30, -0.30
MIN_VOL, PER_SERIES, PER_EVENT, MIN_FLOW_N = 100, 40, 3, 10
D1_END = int(datetime.datetime(2026, 9, 20, tzinfo=datetime.timezone.utc).timestamp())
BOX_MIN = 150
FAM = [("crypto", ("KXETH", "KXSOL", "KXHYPE", "KXXRP", "KXBNB", "KXDOGE", "KXSHIBA")), ("indices", ("KXINX", "KXNASDAQ", "KXDJI", "KXNKY")),
       ("rates", ("KXUST",)), ("fx", ("KXEUR", "KXGBP", "KXAUD", "KXNZD", "KXUSD")), ("commodities", ("KXGOLD", "KXSILVER", "KXPLAT", "KXPALL", "KXWTI", "KXBRENT", "KXNATGAS", "KXCOPPER"))]


def family(s):
    for n, pre in FAM:
        if s.startswith(pre):
            return n
    return "other"


def fee(p, c=10, k=1.0):
    return math.ceil(round(k * 0.07 * c * p * (1 - p) * 100, 9)) / 100


def md5(t):
    return hashlib.md5(t.encode()).hexdigest()


def make_list(cdb):
    db = sqlite3.connect(cdb)
    rows = db.execute("select ticker, series, event, open_ts, close_ts from mk where src='/markets' and volume>=? and close_ts>=? and close_ts<?",
                      (MIN_VOL, START, CUT)).fetchall()
    rows.sort(key=lambda r: md5(r[0]))
    per_s, per_e, out = defaultdict(int), defaultdict(int), []
    for r in rows:
        if per_s[r[1]] >= PER_SERIES or per_e[r[2]] >= PER_EVENT:
            continue
        per_s[r[1]] += 1
        per_e[r[2]] += 1
        out.append(r)
    out.sort(key=lambda r: md5(r[0]))
    return out


def iso_ts(x):
    return datetime.datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp()


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def cdl(s, tk, lo, hi):
    d = get("/series/%s/markets/%s/candlesticks" % (s, tk), {"start_ts": lo, "end_ts": hi, "period_interval": 1})
    out = {}
    for c in d.get("candlesticks", []):
        a, b = fnum(c["yes_ask"]["close_dollars"]), fnum(c["yes_bid"]["close_dollars"])
        out[int(c["end_period_ts"])] = (b, a)
    return out


def entry(cs, L):
    """(side, signal ask, fill ask) or (None, reason). Cheap side = lower ask at the candle ending L; fill at the candle ending L+60."""
    q, nq = cs.get(L), cs.get(L + 60)
    if q is None or q[0] is None or q[1] is None:
        return None, "no_signal_candle"
    ay, an = q[1], round(1 - q[0], 4)
    if abs(ay - an) < 1e-9:
        return None, "tie"
    side = "yes" if ay < an else "no"
    a = min(ay, an)
    if not (LO_ASK - 1e-9 <= a <= HI_ASK + 1e-9):
        return None, "out_of_band"
    if nq is None or nq[0] is None or nq[1] is None:
        return None, "no_fill_candle"
    f = nq[1] if side == "yes" else round(1 - nq[0], 4)
    if f > LIMIT + 1e-9 or f < LO_ASK - 1e-9:
        return None, "over_limit"
    return (side, a, f), "ok"


def trades(tk, lo, hi):
    cur, rows = None, []
    while True:
        p = {"ticker": tk, "limit": 1000, "min_ts": int(lo), "max_ts": int(hi)}
        if cur:
            p["cursor"] = cur
        d = get("/markets/trades", p)
        for t in d.get("trades", []):
            ts = iso_ts(t["created_time"])
            if lo < ts <= hi:
                rows.append((ts, float(t["count_fp"]), t.get("taker_side") or "?"))
        cur = d.get("cursor")
        time.sleep(1.2)
        if not cur or not d.get("trades"):
            return rows


def fetch(cdb, out, box=BOX_MIN):
    L_ = make_list(cdb)
    db = sqlite3.connect(out)
    db.execute("create table if not exists ent(ticker primary key, series, event, close_ts, side, sig real, fill real, nflow real, flow real, why)")
    done = {r[0] for r in db.execute("select ticker from ent")}
    print("list", len(L_), "done", len(done), flush=True)
    t0 = time.time()
    for i, (tk, s, ev, ot, ct) in enumerate(L_):
        if tk in done:
            continue
        if time.time() - t0 > box * 60:
            print("time box reached at", i, flush=True)
            break
        L = ct - 3600
        if ot > L - 1200:
            db.execute("insert into ent values(?,?,?,?,?,?,?,?,?,?)", (tk, s, ev, ct, None, None, None, None, None, "no_flow_window"))
            continue
        try:
            e, why = entry(cdl(s, tk, L - 120, L + 120), L)
            row = (tk, s, ev, ct, None, None, None, None, None, why)
            time.sleep(1.2)
            if e is not None:
                side, a, f = e
                lo = max(ot, L - 3600)
                tr = trades(tk, lo, L)
                tot = sum(n for _, n, _ in tr)
                if tot < MIN_FLOW_N:
                    row = (tk, s, ev, ct, side, a, f, tot, None, "no_flow")
                else:
                    fl = sum((n if sd == side else -n) for _, n, sd in tr if sd in ("yes", "no")) / tot
                    row = (tk, s, ev, ct, side, a, f, tot, fl, "ok")
        except Exception as ex:  # noqa
            row = (tk, s, ev, ct, None, None, None, None, None, "err")
        db.execute("insert or replace into ent values(?,?,?,?,?,?,?,?,?,?)", row)
        db.commit()
        time.sleep(1.2)
        if i % 25 == 0:
            print(i, len(L_), tk, row[-1], round(time.time() - t0), flush=True)


def stats(rows):
    n = len(rows)
    if not n:
        return None
    net = [r["net"] for r in rows]
    w = sum(1 for r in rows if r["win"])
    gp = sum(x for x in net if x > 0)
    gl = -sum(x for x in net if x < 0)
    days = defaultdict(float)
    for r in rows:
        days[r["day"]] += r["net"]
    d = list(days.values())
    m = sum(d) / len(d)
    sd = (sum((x - m) ** 2 for x in d) / max(1, len(d) - 1)) ** 0.5
    z = m / (sd / len(d) ** 0.5) if sd > 0 else 0.0
    return {"n": n, "events": len({r["ev"] for r in rows}), "days": len(d), "win": round(w / n, 4), "paid": round(sum(r["fill"] for r in rows) / n * 100, 2),
            "net_c10": round(sum(net) / n * 100, 2), "net_c1": round(sum(r["net1"] for r in rows) / n * 100, 2),
            "pf": round(gp / gl, 2) if gl else None, "pf12": None, "z_day": round(z, 2)}


def pf12(rows):
    gp = sum(r["net12"] for r in rows if r["net12"] > 0)
    gl = -sum(r["net12"] for r in rows if r["net12"] < 0)
    return round(gp / gl, 2) if gl else None


def score(out, marker):
    import os
    if os.path.exists(marker):
        print("REFUSED: FLOWX1 already scored (marker exists)")
        return
    open(marker, "w").write(str(time.time()))
    db = sqlite3.connect(out)
    ents = db.execute("select ticker, series, event, close_ts, side, sig, fill, nflow, flow from ent where why='ok'").fetchall()
    cnt = defaultdict(int)
    for r in db.execute("select why, count(*) from ent group by why"):
        cnt[r[0]] = r[1]
    rows = []
    for i, (tk, s, ev, ct, side, a, f, nf, fl) in enumerate(ents):
        for k in range(8):
            try:
                m = get("/markets/" + tk)["market"]
                break
            except Exception:
                m = None
                time.sleep(10)
        time.sleep(1.2)
        res = (m or {}).get("result")
        if res not in ("yes", "no"):
            cnt["no_result"] += 1
            continue
        win = 1.0 if res == side else 0.0
        day = datetime.datetime.fromtimestamp(ct, datetime.timezone.utc).strftime("%Y-%m-%d")
        rows.append({"tk": tk, "s": s, "ev": ev, "ct": ct, "day": day, "fam": family(s), "side": side, "fill": f, "flow": fl, "win": win,
                     "net": win - f - fee(f, 10), "net1": win - f - fee(f, 1), "net12": win - f - fee(f, 10, 1.2)})
    json.dump(rows, open(out + ".scored.json", "w"))
    print("counts", dict(cnt))
    arms = {"CONTROL all": rows, "HIGH flow>=+0.30 (primary)": [r for r in rows if r["flow"] >= FLOW_HI],
            "COMPLEMENT <+0.30": [r for r in rows if r["flow"] < FLOW_HI], "LOW flow<=-0.30 (secondary)": [r for r in rows if r["flow"] <= FLOW_LO]}
    for name, rr in arms.items():
        st = stats(rr)
        print(name, st, "pf12", pf12(rr) if rr else None)
        for h, hh in (("D1", [r for r in rr if r["ct"] < D1_END]), ("D2", [r for r in rr if r["ct"] >= D1_END])):
            print("   ", h, stats(hh))
        fams = defaultdict(list)
        for r in rr:
            fams[r["fam"]].append(r)
        for k, v in sorted(fams.items()):
            print("    fam", k, stats(v))
    hi, lo_ = arms["HIGH flow>=+0.30 (primary)"], arms["COMPLEMENT <+0.30"]
    if hi and lo_:
        obs = sum(r["net"] for r in hi) / len(hi) - sum(r["net"] for r in lo_) / len(lo_)
        evs = defaultdict(list)
        for r in rows:
            evs[r["ev"]].append(r)
        keys = list(evs)
        rnd = random.Random(7)
        ge = 0
        flows = {k: [r["flow"] >= FLOW_HI for r in evs[k]] for k in keys}
        allflags = [f for k in keys for f in flows[k]]
        for _ in range(2000):
            rnd.shuffle(allflags)
            idx, a, b = 0, [], []
            for k in keys:
                for r in evs[k]:
                    (a if allflags[idx] else b).append(r["net"])
                    idx += 1
            if a and b and sum(a) / len(a) - sum(b) / len(b) >= obs:
                ge += 1
        print("treated minus complement (c per contract, C=10):", round(obs * 100, 2), "permutation one sided p (event-level shuffle of flags):", round(ge / 2000, 3))


if __name__ == "__main__":
    if sys.argv[1] == "census":
        census(sys.argv[2])
    elif sys.argv[1] == "list":
        L_ = make_list(sys.argv[2])
        print(len(L_), "candidates;", len({r[1] for r in L_}), "series")
    elif sys.argv[1] == "fetch":
        fetch(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "score":
        score(sys.argv[2], sys.argv[2] + ".scored.marker")
