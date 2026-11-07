"""Binance Vision BTC/ETH ingest: spot 1m klines, USD-M perp 1m klines, perp funding.

Resumable fetch plus clean. Underlying path only, no strategy statistic here.
Host: data.binance.vision bulk zips (the Binance main API answers 451; never used).
Stops a source on 403/429/451 and records it; never works around a block.

Usage:  python3 -I src/scalper/histbinance.py fetch [--start 2019-01] [--symbols BTCUSDT,ETHUSDT]
        python3 -I src/scalper/histbinance.py report
Output: data/hist_binance/<symbol>_<stream>/<YYYY-MM>.csv.gz  (git-ignored) + manifest.json
Load:   load(symbol, stream) -> list of rows (ts_s first column).
"""
import csv, gzip, hashlib, io, json, os, subprocess, sys, time, zipfile, datetime as dt

HOST = "https://data.binance.vision/data"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "hist_binance")
ROOT = os.path.normpath(ROOT)
STREAMS = {  # stream -> (url path template, kind)
    "spot_1m": ("spot/{p}/klines/{s}/1m/{s}-1m-{d}", "kline"),
    "perp_1m": ("futures/um/{p}/klines/{s}/1m/{s}-1m-{d}", "kline"),
    "funding": ("futures/um/monthly/fundingRate/{s}/{s}-fundingRate-{d}", "funding"),
}
BLOCKED = (403, 429, 451)
SLEEP = 0.3

def norm_ts(v):
    """Return unix MILLISECONDS from ms or us (Binance Vision spot switched to
    microseconds from 2025-01-01). 1e15 ms is year 33658, 1e15 us is 2001, so the
    magnitude is unambiguous for any date after 2001."""
    v = int(v)
    return v // 1000 if v >= 10**15 else v

def curl(url, out=None):
    cmd = ["curl", "-sS", "-m", "120", "-w", "%{http_code}", "-o", out or "-", url]
    r = subprocess.run(cmd, capture_output=True)
    body = r.stdout
    code = int(body[-3:] or 0)
    return code, (b"" if out else body[:-3])

def sha256(b): return hashlib.sha256(b).hexdigest()

def parse_kline(raw):
    rows, dup, bad, nonmono, zerovol, unit_us = {}, 0, 0, 0, 0, 0
    last = -1
    for rec in csv.reader(io.StringIO(raw.decode())):
        if not rec or not rec[0].strip().lstrip("-").isdigit():
            continue  # header row (futures files carry one)
        try:
            t0 = int(rec[0]); t = norm_ts(t0)
            unit_us += t0 >= 10**15
            o, h, l, c, v = (float(x) for x in rec[1:6])
            n = int(rec[8]); tbv = float(rec[9])
        except Exception:
            bad += 1; continue
        if t % 60000: bad += 1; continue
        if h < l or min(o, c) < l - 1e-9 or max(o, c) > h + 1e-9: bad += 1
        if v == 0: zerovol += 1
        if t in rows: dup += 1
        if t < last: nonmono += 1
        last = max(last, t)
        rows[t] = (t // 1000, o, h, l, c, v, n, tbv)
    return sorted(rows.values()), dict(dup=dup, bad=bad, nonmono=nonmono, zerovol=zerovol, us_rows=unit_us)

def parse_funding(raw):
    rows, dup, bad = {}, 0, 0
    for rec in csv.reader(io.StringIO(raw.decode())):
        if not rec or not rec[0].strip().isdigit(): continue
        try: t = norm_ts(rec[0]); iv = rec[1]; r = float(rec[2])
        except Exception: bad += 1; continue
        if t in rows: dup += 1
        rows[t] = (t // 1000, iv, r)
    return sorted(rows.values()), dict(dup=dup, bad=bad)

def months(start, end):
    y, m = map(int, start.split("-")); ey, em = map(int, end.split("-"))
    while (y, m) <= (ey, em):
        yield f"{y:04d}-{m:02d}"
        m += 1
        if m == 13: y, m = y + 1, 1

def periods(stream, today):
    """Monthly zips up to the last complete month; daily zips for the current month."""
    cur = today.strftime("%Y-%m")
    prev = (today.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
    return prev, cur

def fetch_one(stream, sym, key, period, kind_p, man, log):
    tmpl, kind = STREAMS[stream]
    base = f"{HOST}/{tmpl.format(p=kind_p, s=sym, d=period)}"
    d = os.path.join(ROOT, f"{sym}_{stream}"); os.makedirs(d, exist_ok=True)
    tmp = os.path.join(d, ".tmp.zip")
    time.sleep(SLEEP)
    code, _ = curl(base + ".zip", tmp)
    if code in BLOCKED: return ("blocked", code)
    if code == 404: man[key] = dict(status="absent_404"); return ("absent", 404)
    if code != 200: return ("error", code)
    time.sleep(SLEEP)
    ccode, cbody = curl(base + ".zip.CHECKSUM")
    zb = open(tmp, "rb").read(); os.remove(tmp)
    ck = "no_checksum_file"
    if ccode in BLOCKED: return ("blocked", ccode)
    if ccode == 200:
        want = cbody.decode().split()[0].lower()
        if want != sha256(zb): man[key] = dict(status="checksum_mismatch"); return ("error", "checksum")
        ck = "ok"
    z = zipfile.ZipFile(io.BytesIO(zb)); raw = z.read(z.namelist()[0])
    rows, defects = (parse_kline if kind == "kline" else parse_funding)(raw)
    out = os.path.join(d, f"{period}.csv.gz")
    with gzip.open(out + ".part", "wt", newline="", compresslevel=6) as f:
        csv.writer(f).writerows(rows)
    os.replace(out + ".part", out)
    man[key] = dict(status="ok", checksum=ck, rows=len(rows), first=rows[0][0] if rows else None,
                    last=rows[-1][0] if rows else None, bytes=os.path.getsize(out), **defects)
    return ("ok", 200)

def fetch(start="2019-01", symbols=("BTCUSDT", "ETHUSDT"), today=None):
    today = today or dt.datetime.now(dt.timezone.utc).date()
    os.makedirs(ROOT, exist_ok=True)
    mp = os.path.join(ROOT, "manifest.json")
    man = json.load(open(mp)) if os.path.exists(mp) else {}
    last_full, cur = periods(None, today)
    stopped = set()
    for sym in symbols:
        for stream in STREAMS:
            if stream in stopped: continue
            jobs = [(m, "monthly") for m in months(start, last_full)]
            if stream != "funding":  # funding has no daily files; the partial month is not needed
                n = (today - today.replace(day=1)).days  # complete days of current month
                jobs += [(f"{cur}-{i:02d}", "daily") for i in range(1, n + 1)]
            seen_data = False
            for period, kp in jobs:
                key = f"{sym}/{stream}/{period}"
                outp = os.path.join(ROOT, f"{sym}_{stream}", f"{period}.csv.gz")
                if man.get(key, {}).get("status") in ("ok", "absent_404") and (os.path.exists(outp) or man[key]["status"] != "ok"):
                    continue
                res = fetch_one(stream, sym, key, period, kp, man, None)
                json.dump(man, open(mp, "w"), indent=0)
                if res[0] == "blocked":
                    man["_blocked_" + stream] = dict(code=res[1], at=period); stopped.add(stream)
                    print("BLOCKED", stream, res[1], "stop that source"); break
                if res[0] == "error": print("error", key, res)
    json.dump(man, open(mp, "w"), indent=0)
    return man

def load(symbol, stream):
    d = os.path.join(ROOT, f"{symbol}_{stream}"); rows = []
    for fn in sorted(x for x in os.listdir(d) if x.endswith(".csv.gz")):
        with gzip.open(os.path.join(d, fn), "rt") as f:
            for r in csv.reader(f):
                rows.append((int(r[0]),) + tuple(float(x) for x in r[1:]))
    return rows

def report():
    man = json.load(open(os.path.join(ROOT, "manifest.json")))
    out = {}
    for sym in ("BTCUSDT", "ETHUSDT"):
        for stream in STREAMS:
            rows = load(sym, stream) if os.path.isdir(os.path.join(ROOT, f"{sym}_{stream}")) else []
            if not rows: continue
            ts = [r[0] for r in rows]
            gaps = missing = 0
            step = 60 if stream != "funding" else None
            if step:
                for a, b in zip(ts, ts[1:]):
                    if b - a > step: gaps += 1; missing += (b - a) // step - 1
            else:
                for a, b in zip(ts, ts[1:]):
                    if b - a > 8 * 3600 + 60: gaps += 1
            keys = [k for k in man if k.startswith(f"{sym}/{stream}/") and man[k].get("status") == "ok"]
            sm = lambda f: sum(man[k].get(f, 0) for k in keys)
            mb = sum(man[k]["bytes"] for k in keys) / 1e6
            out[f"{sym}/{stream}"] = dict(first=dt.datetime.fromtimestamp(ts[0], dt.timezone.utc).isoformat(), last=dt.datetime.fromtimestamp(ts[-1], dt.timezone.utc).isoformat(),
                rows=len(rows), gaps=gaps, missing_minutes=missing, zerovol=sm("zerovol"), dup=sm("dup"), bad=sm("bad"),
                nonmono=sm("nonmono"), us_rows=sm("us_rows"), mb=round(mb, 1),
                absent=sum(1 for k in man if k.startswith(f"{sym}/{stream}/") and man[k].get("status") == "absent_404"))
    print(json.dumps(out, indent=1)); return out

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["report"]: report()
    else:
        kw = {}
        if "--start" in a: kw["start"] = a[a.index("--start") + 1]
        if "--symbols" in a: kw["symbols"] = tuple(a[a.index("--symbols") + 1].split(","))
        t = time.time(); fetch(**kw); print("seconds", round(time.time() - t))
