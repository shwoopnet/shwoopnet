#!/usr/bin/env python3
"""CPREM1, CLEAD1, CXS1, CSPR1 scorer (registered in workers/CPREM1_REGISTRATION.md etc. BEFORE it was run).
Kalshi crypto perps (origin/perp-data) against public spot (Coinbase, Bitstamp fallback) and Hyperliquid perp 5 minute candles.
Only dates <= CUT are ever opened. Usage: python3 -I cryptoperp.py REPO_DIR CACHE_JSON OUT_JSON"""
import csv, io, json, math, os, statistics as st, subprocess, sys, time, urllib.request
from datetime import datetime as D, timezone as TZ

CUT = "2026-10-31"; D1_END = "2026-10-26"
THRESH = 0.0030
FEES = {"verdict": 0.0005, "stress": 0.0012}
HOLD = (4 * 3600, 12 * 3600); HOLD_B = (1 * 3600, 8 * 3600)
MIN_PRIOR = 8
CB = {"BTC": "BTC", "ETH": "ETH", "SOL": "SOL", "XRP": "XRP", "DOGE": "DOGE", "ADA": "ADA", "LINK": "LINK", "LTC": "LTC", "AAVE": "AAVE",
      "BCH": "BCH", "UNI": "UNI", "SUI": "SUI", "NEAR": "NEAR", "ZEC": "ZEC", "WLD": "WLD", "HYPE": "HYPE", "BNB": "BNB"}
HLNAME = {"KPEPE": "kPEPE", "KSHIB": "kSHIB"}


def git(repo, *a):
    return subprocess.run(["git", "-C", repo] + list(a), capture_output=True, text=True, check=True).stdout


def tsec(s):
    return int(D.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=TZ.utc).timestamp())


def load(repo):
    seen = {}
    for c in git(repo, "log", "origin/perp-data", "--format=%h").split():
        for f in git(repo, "show", c, "--name-only", "--format=").split():
            if f.rsplit("perps-", 1)[-1][:10] > CUT:
                continue
            for r in csv.DictReader(io.StringIO(git(repo, "show", c + ":" + f))):
                if r["ts_utc"][:10] <= CUT and r["asset_class"] == "Crypto":
                    seen[(r["ts_utc"], r["ticker"])] = r
    return seen


def quote(r):
    try:
        if r["status"] != "active":
            return None
        b, a = float(r["bid"]), float(r["ask"])
        if b <= 0 or a <= 0 or a > 2 * b or a < b:
            return None
        return b, a
    except Exception:
        return None


def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "research", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def spot_at(coin, t):
    try:
        j = get("https://api.exchange.coinbase.com/products/%s-USD/candles?granularity=60&start=%s&end=%s" % (
            coin, D.fromtimestamp(t - 240, TZ.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), D.fromtimestamp(t, TZ.utc).strftime("%Y-%m-%dT%H:%M:%SZ")))
        c = [x for x in j if x[0] <= t - 60]
        if c:
            return max(c)[4], "cb"
    except Exception:
        pass
    try:
        j = get("https://www.bitstamp.net/api/v2/ohlc/%susd/?step=60&limit=4&end=%d" % (coin.lower(), t))
        c = [x for x in j["data"]["ohlc"] if int(x["timestamp"]) <= t - 60]
        if c:
            return float(c[-1]["close"]), "bs"
    except Exception:
        pass
    return None, None


def hl_candles(coin, t0, t1):
    try:
        j = get("https://api.hyperliquid.xyz/info", json.dumps({"type": "candleSnapshot", "req": {"coin": coin, "interval": "5m", "startTime": t0 * 1000, "endTime": t1 * 1000}}).encode())
        return {int(c["t"] // 1000): float(c["c"]) for c in j}
    except Exception:
        return {}


def main(repo, cache_p, out_p):
    seen = load(repo)
    times = sorted({k[0] for k in seen})
    tick = sorted({k[1] for k in seen})
    ts = {t: tsec(t) for t in times}
    cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {"spot": {}, "hl": {}}
    coins = {t: t[2:-4] for t in tick}                       # KXBTCPERP -> BTC
    # --- cost universe (spread only, never returns)
    active = {}; spr = {}
    for (t, k), r in seen.items():
        q = quote(r)
        spr.setdefault(k, [])
        active.setdefault(k, [0, 0])[1] += 1
        if q:
            active[k][0] += 1
            spr[k].append((q[1] - q[0]) / ((q[1] + q[0]) / 2))
    cand = [k for k in tick if active[k][1] and active[k][0] / active[k][1] >= 0.8 and coins[k] in CB]
    cand.sort(key=lambda k: st.median(spr[k]))
    # --- spot (fetched only for candidate coins at sample times)
    for k in cand:
        for t in times:
            key = coins[k] + "|" + str(ts[t])
            if key not in cache["spot"] and quote(seen.get((t, k), {"status": "x"})) :
                p, src = spot_at(coins[k], ts[t]); cache["spot"][key] = [p, src]; time.sleep(0.12)
    json.dump(cache, open(cache_p, "w"))
    # --- unit scale per ticker from the ratio (a unit, not a return)
    scale = {}; unit_drop = []
    for k in cand:
        rs = []
        for t in times:
            q = quote(seen.get((t, k), {"status": "x"})); sp = cache["spot"].get(coins[k] + "|" + str(ts[t]), [None])[0]
            if q and sp:
                rs.append((q[0] + q[1]) / 2 / sp)
        if len(rs) < 10:
            unit_drop.append((k, "spot samples %d" % len(rs))); continue
        m = st.median(rs); e = round(math.log10(m))
        if abs(m / 10 ** e - 1) > 0.5:
            unit_drop.append((k, "unit unresolved ratio %.4g" % m)); continue
        scale[k] = 10 ** e
    ok = [k for k in cand if k in scale]
    uni = ok[:10]
    # --- Hyperliquid 5m candles
    t_lo, t_hi = ts[times[0]] - 900, ts[times[-1]] + 300
    for k in uni:
        if coins[k] not in cache["hl"]:
            cache["hl"][coins[k]] = hl_candles(HLNAME.get(coins[k], coins[k]), t_lo, t_hi); time.sleep(0.3)
    json.dump(cache, open(cache_p, "w"))

    def hlp(coin, t):
        c = cache["hl"].get(coin) or {}
        c = {int(a): b for a, b in c.items()}
        ks = [a for a in c if a <= t - 300 and a >= t - 900]
        return c[max(ks)] if ks else None

    def side_fills(q, side, entry):      # entry: long buys at ask, short sells at bid
        return q[1] if (side > 0) == entry else q[0]

    def exit_idx(i, lo, hi):
        for j in range(i + 1, len(times)):
            dt = ts[times[j]] - ts[times[i]]
            if dt > hi:
                return None
            if dt >= lo:
                return j
        return None

    rows = {}   # per (k,i): dev vs spot, dev vs hl
    hist_s = {k: [] for k in uni}; hist_h = {k: [] for k in uni}
    for i, t in enumerate(times):
        for k in uni:
            q = quote(seen.get((t, k), {"status": "x"}))
            if not q:
                continue
            mid = (q[0] + q[1]) / 2 / scale[k]
            sp = cache["spot"].get(coins[k] + "|" + str(ts[t]), [None])[0]
            hp = hlp(coins[k], ts[t])
            rec = {"q": q}
            if sp:
                d = mid / sp - 1
                if len(hist_s[k]) >= MIN_PRIOR:
                    rec["xs"] = d - st.median(hist_s[k])
                hist_s[k].append(d)
            if hp:
                d = mid / hp - 1
                if len(hist_h[k]) >= MIN_PRIOR:
                    rec["xh"] = d - st.median(hist_h[k])
                hist_h[k].append(d)
            rows[(k, i)] = rec

    def summarize(tr, fee_key="verdict"):
        if not tr:
            return {"n": 0}
        byday = {}
        for d, r in tr:
            byday.setdefault(d, []).append(r)
        dm = [sum(v) / len(v) for v in byday.values()]
        z = (st.mean(dm) / (st.stdev(dm) / math.sqrt(len(dm)))) if len(dm) > 2 and st.stdev(dm) > 0 else None
        d1 = [r for d, r in tr if d <= D1_END]; d2 = [r for d, r in tr if d > D1_END]
        mean = lambda x: (st.mean(x) * 1e4) if x else None
        return {"n": len(tr), "days": len(dm), "mean_bp": mean([r for _, r in tr]), "win": sum(r > 0 for _, r in tr) / len(tr), "D1_n": len(d1), "D1_bp": mean(d1), "D2_n": len(d2), "D2_bp": mean(d2), "day_z": z}

    def run_single(key, hold):
        out = {}
        for fname, fee in FEES.items():
            tr = []; conv = []; gross = []
            for (k, i), rec in rows.items():
                x = rec.get(key)
                if x is None or abs(x) <= THRESH:
                    continue
                j = exit_idx(i, *hold)
                e = rows.get((k, j)) if j is not None else None
                if not e:
                    continue
                side = -1 if x > 0 else 1
                a = side_fills(rec["q"], side, True); b = side_fills(e["q"], side, False)
                r = side * (b / a - 1) - 2 * fee
                tr.append((times[i][:10], r))
                if fname == "verdict":
                    mid0 = sum(rec["q"]) / 2; mid1 = sum(e["q"]) / 2
                    gross.append(side * (mid1 / mid0 - 1))
                    if e.get(key) is not None:
                        conv.append(1 - abs(e[key]) / abs(x))
            out[fname] = summarize(tr)
            if fname == "verdict":
                out["gross_mid_bp"] = st.mean(gross) * 1e4 if gross else None
                out["conv_mean"] = st.mean(conv) if conv else None; out["conv_median"] = st.median(conv) if conv else None
        return out

    res = {"universe_by_spread": [(k, round(st.median(spr[k]) * 1e4, 2)) for k in cand], "unit_drop": unit_drop, "uni": uni,
           "scale": {k: scale[k] for k in uni}, "n_samples": len(times), "dates": sorted({t[:10] for t in times})}
    res["CPREM1"] = run_single("xs", HOLD)
    res["CLEAD1"] = run_single("xh", HOLD_B)
    # CXS1
    for fname, fee in FEES.items():
        tr = []
        for i, t in enumerate(times):
            xs = [(rows[(k, i)]["xs"], k) for k in uni if (k, i) in rows and "xs" in rows[(k, i)]]
            if len(xs) < 8:
                continue
            xs.sort()
            j = exit_idx(i, *HOLD)
            if j is None:
                continue
            legs = [(1, k) for _, k in xs[:2]] + [(-1, k) for _, k in xs[-2:]]
            tot = 0; n = 0
            for side, k in legs:
                e = rows.get((k, j))
                if not e:
                    break
                a = side_fills(rows[(k, i)]["q"], side, True); b = side_fills(e["q"], side, False)
                tot += 0.25 * side * (b / a - 1); n += 1
            if n == 4:
                tr.append((t[:10], tot - 2 * fee))
        res.setdefault("CXS1", {})[fname] = summarize(tr)
    # CSPR1
    bins = {}
    for (t, k), r in seen.items():
        if k not in uni:
            continue
        q = quote(r)
        if not q:
            continue
        h = int(t[11:13]) // 4; half = "D1" if t[:10] <= D1_END else "D2"
        bins.setdefault((half, h), []).append((q[1] - q[0]) / ((q[1] + q[0]) / 2))
    cs = {}
    for half in ("D1", "D2"):
        allv = [v for (hh, h), vs in bins.items() if hh == half for v in vs]
        cs[half] = {"overall_bp": st.median(allv) * 1e4 if allv else None,
                    "bins": {h: (len(bins.get((half, h), [])), (st.median(bins[(half, h)]) * 1e4 if bins.get((half, h)) else None)) for h in range(6)}}
    res["CSPR1"] = cs
    json.dump(res, open(out_p, "w"), indent=1, default=str)
    print(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main(*sys.argv[1:4])
