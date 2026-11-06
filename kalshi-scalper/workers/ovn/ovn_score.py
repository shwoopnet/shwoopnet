"""OVN1 to OVN4 scorer (registered in workers/OVN*_REGISTRATION.md, commit a840354). Reads only rows before the cut."""
import csv, io, json, math, statistics as st, subprocess, sys, urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
ET = ZoneInfo("America/New_York"); CUT = "2026-11-01T00:00:00Z"
REPO = "/home/user/shwoopnet/kalshi-scalper"
FEE = 0.0012
def git(*a): return subprocess.run(["git", "-C", REPO] + list(a), capture_output=True, text=True).stdout
def load():
    rows = {}
    for c in git("log", "origin/perp-data", "--format=%h").split():
        f = git("show", c, "--format=", "--name-only").split()[0]
        for x in csv.DictReader(io.StringIO(git("show", "%s:%s" % (c, f)))):
            if x["ts_utc"] < CUT: rows[(x["ts_utc"], x["ticker"])] = x
    return rows
def et(ts): return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(ET)
def fl(x):
    try: return float(x)
    except: return 0.0
rows = load(); print("rows before cut", len(rows))
tick_rows = {}
for (ts, tk), x in rows.items():
    if x["asset_class"] in ("Equities", "Indices"): tick_rows.setdefault(tk, []).append(x)
# universe by dev spread
uni = []
for tk, L in sorted(tick_rows.items()):
    sp = [(fl(x["ask"]) - fl(x["bid"])) / ((fl(x["ask"]) + fl(x["bid"])) / 2) * 1e4 for x in L if fl(x["bid"]) > 0 and fl(x["ask"]) > 0]
    if sp:
        med = st.median(sp); print("spread", tk, len(sp), round(med, 2))
        if med <= 5: uni.append(tk)
print("universe", uni)
def stats(label, rets, dates):
    n = len(rets)
    if n == 0: print(label, "n=0"); return
    m = sum(rets) / n; cl = len(set(dates))
    gp = sum(r for r in rets if r > 0); gl = -sum(r for r in rets if r < 0)
    d1 = [r for r, d in zip(rets, dates) if d < "2026-10-27"]; d2 = [r for r, d in zip(rets, dates) if d >= "2026-10-27"]
    print(label, "n=%d clusters=%d mean=%.1fbps PF=%s D1 n=%d mean=%s D2 n=%d mean=%s" % (n, cl, m * 1e4, ("%.2f" % (gp / gl)) if gl else "inf", len(d1), ("%.1f" % (sum(d1) / len(d1) * 1e4)) if d1 else "-", len(d2), ("%.1f" % (sum(d2) / len(d2) * 1e4)) if d2 else "-"))
    # day clustered z
    byd = {}
    for r, d in zip(rets, dates): byd.setdefault(d, []).append(r)
    dm = [sum(v) / len(v) for v in byd.values()]
    if len(dm) > 1 and st.pstdev(dm) > 0: print("   day-clustered z=%.2f" % (st.mean(dm) / (st.stdev(dm) / math.sqrt(len(dm)))))
def pick(L, d, lo, hi):
    out = [x for x in L if et(x["ts_utc"]).date() == d and lo <= et(x["ts_utc"]).hour * 60 + et(x["ts_utc"]).minute <= hi and fl(x["bid"]) > 0 and fl(x["ask"]) > 0]
    return sorted(out, key=lambda x: x["ts_utc"])
from datetime import timedelta, date
res = {k: [] for k in ("OVN1", "OVN2", "OVN3F", "OVN3L")}; skip = {k: {} for k in res}
def bump(k, why): skip[k][why] = skip[k].get(why, 0) + 1
dev_dates = sorted({et(x["ts_utc"]).date() for L in tick_rows.values() for x in L})
for tk in uni:
    L = sorted(tick_rows[tk], key=lambda x: x["ts_utc"])
    for d in [date(2026, 10, 22) + timedelta(days=i) for i in range(0, 11)]:
        if d.weekday() > 4 or d >= date(2026, 11, 1): continue
        pre = pick(L, d, 300, 565); ex = pick(L, d, 590, 690)
        prev = d - timedelta(days=1)
        while prev.weekday() > 4: prev -= timedelta(days=1)
        cl = pick(L, prev, 970, 1319)
        weekend = (d - prev).days > 1
        if not pre or not ex: bump("OVN1", "no t0 or t1"); continue
        t0, t1 = pre[-1], ex[0]
        if t1["ts_utc"] <= t0["ts_utc"]: bump("OVN1", "t1<=t0"); continue
        m0 = (fl(t0["bid"]) + fl(t0["ask"])) / 2; m1 = (fl(t1["bid"]) + fl(t1["ask"])) / 2
        ref0 = fl(t0["reference_price"])
        if not cl: bump("OVN1", "no close sample"); bump("OVN2", "no close sample"); 
        refc = fl(cl[0]["reference_price"]) if cl else None
        if cl and abs(refc - ref0) > 1e-9: bump("OVN1", "ref moved overnight"); continue
        if not cl: continue
        q = m0 / ref0 - 1
        if abs(q) < 5e-4: bump("OVN1", "|q|<5bps"); 
        else:
            s = -1 if q > 0 else 1
            gross = (fl(t1["bid"]) / fl(t0["ask"]) - 1) if s > 0 else (fl(t0["bid"]) / fl(t1["ask"]) * 0 + (fl(t0["bid"]) - fl(t1["ask"])) / fl(t0["bid"]))
            res["OVN1"].append((str(d), gross - 2 * FEE, tk, q))
        mc = (fl(cl[0]["bid"]) + fl(cl[0]["ask"])) / 2; dd = m0 / mc - 1
        if abs(dd) < 5e-4: bump("OVN2", "|d|<5bps")
        else:
            s = 1 if dd > 0 else -1
            gross = (fl(t1["bid"]) / fl(t0["ask"]) - 1) if s > 0 else ((fl(t0["bid"]) - fl(t1["ask"])) / fl(t0["bid"]))
            res["OVN2"].append((str(d), gross - 2 * FEE, tk, dd))
        if weekend:
            if abs(q) < 1e-3: bump("OVN3", "|q_w|<10bps")
            else:
                for nm, s in (("OVN3F", -1 if q > 0 else 1), ("OVN3L", 1 if q > 0 else -1)):
                    gross = (fl(t1["bid"]) / fl(t0["ask"]) - 1) if s > 0 else ((fl(t0["bid"]) - fl(t1["ask"])) / fl(t0["bid"]))
                    res[nm].append((str(d), gross - 2 * FEE, tk, q))
for k, v in res.items():
    print("==", k, "skips", skip.get(k, skip.get(k[:4], {})))
    for r in v: print("  ", r[0], r[2], "net %.1f bps" % (r[1] * 1e4), "signal %.1f bps" % (r[3] * 1e4))
    stats(k, [r[1] for r in v], [r[0] for r in v])
print("skips", skip)
# OVN4 spreads from candles + rows
def bucket(dt):
    wd = dt.weekday(); mins = dt.hour * 60 + dt.minute
    if wd == 5 or wd == 6 or (wd == 4 and mins >= 1200) or (wd == 0 and mins < 570): return "WEEKEND"
    if wd < 5 and 570 <= mins < 960: return "CASH"
    if 960 <= mins < 1200: return "AFTER"
    return "NIGHT"
end = int(datetime.strptime(CUT, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp())
print("== OVN4")
for tk in uni:
    url = "https://external-api.kalshi.com/trade-api/v2/margin/markets/%s/candlesticks?period_interval=60&start_ts=%d&end_ts=%d" % (tk, end - 86400 * 200, end)
    c = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "shwoopnet-research"}), timeout=60))["candlesticks"]
    B = {}; days = {}
    for x in c:
        b, a = fl(x["bid"]["close"]), fl(x["ask"]["close"])
        if b > 0 and a > b and x["end_period_ts"] <= end:
            dt = datetime.fromtimestamp(x["end_period_ts"] - 1800, ET)  # candle midpoint
            h1 = dt.date() < date(2026, 10, 27)
            B.setdefault(bucket(dt), []).append((a - b) / ((a + b) / 2) * 1e4); B.setdefault(bucket(dt) + ("_D1" if h1 else "_D2"), []).append((a - b) / ((a + b) / 2) * 1e4)
            days.setdefault(bucket(dt), set()).add(dt.date())
    print(tk, "candles", len(c), {k: (len(v), round(st.median(v), 2)) for k, v in sorted(B.items())}, "days", {k: len(v) for k, v in days.items()})
