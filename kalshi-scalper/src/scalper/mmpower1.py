"""MMPOWER1 (workers/MMPOWER1_PROTOCOL.md). Development events only; loads only book dirs dated <= 2026-11-07 and drops events at/after the cutoff. Held-out file counts from the listing only."""
import sys, collections, math, datetime as dt, re
import numpy as np
sys.path.insert(0, "/home/user/shwoopnet/kalshi-scalper/src/scalper")
from mmsim1 import git, pf, parse_ms
from mmsim2 import rd, sim
from mmhour1 import strikes
NDEV = 171
rng = np.random.default_rng(20261111)
def load():
    names = [f for f in git("ls-tree", "-r", "--name-only", "origin/quote-data").decode().split("\n") if f.startswith("book/") and f.endswith("book.csv.gz")]
    files = [f for f in names if f.split("/")[1] <= "2026-11-07"]
    raw = {f: list(rd(f)) for f in files}
    ev = sorted({r["close_time"] for rows in raw.values() for r in rows}); cutoff = ev[NDEV]; dev = set(ev[:NDEV])
    books = collections.defaultdict(list); trades = collections.defaultdict(dict)
    for f, rows in raw.items():
        keep = [r for r in rows if r["close_time"] in dev]
        for r in keep: books[(r["close_time"], r["ticker"])].append(r)
        if keep:
            for r in rd(f.replace("book.csv.gz", "trades.csv.gz")): trades[r["ticker"]][r["trade_id"]] = r
    return books, trades, cutoff, sorted(dev), names
def pfa(a): 
    w = a[a > 0].sum(); l = -a[a < 0].sum(); return w / l if l > 0 else 99.0
def draw_cluster(days, N, r):
    # days: list of np arrays of per-event P&L; whole days until N events, truncate
    out = []; n = 0
    while n < N:
        d = days[r.integers(len(days))]; out.append(d); n += len(d)
    return np.concatenate(out)[:N]
def power_tab(evs, daysl, Ns, B, r, mean_shift=0.0):
    res = {}
    dl = [d + mean_shift for d in daysl]; e = evs + mean_shift
    for N in Ns:
        pc = np.array([pfa(draw_cluster(dl, N, r)) for _ in range(B)])
        pi = np.array([pfa(e[r.integers(len(e), size=N)]) for _ in range(B)])
        res[N] = (round((pc >= 1.3).mean(), 3), round((pc >= 1.5).mean(), 3), round((pi >= 1.3).mean(), 3), round((pi >= 1.5).mean(), 3), round(float(np.median(pc)), 2))
    return res
def split_days(ct, x):
    d = collections.defaultdict(list)
    for c, v in zip(ct, x): d[c[:10]].append(v)
    keys = sorted(d); return keys, [np.array(d[k]) for k in keys]
def fisher(r, n, c=1.6449):
    z = math.atanh(r); s = 1 / math.sqrt(n - 3); return math.tanh(z - c * s), math.tanh(z + c * s)
def zday(cellev):  # dict ct->pnl, day-clustered z of the mean daily sum
    d = collections.defaultdict(float)
    for c, v in cellev.items(): d[c[:10]] += v
    a = np.array(list(d.values())); return a.mean() / (a.std(ddof=1) / math.sqrt(len(a)))
if __name__ == "__main__":
    books, trades, cutoff, dev, names = load()
    print("cutoff", cutoff, "dev events", len({c for c, _ in books}))
    Ns = (100, 200, 300, 500); B = 5000
    base = {}
    print("== Q1")
    for coef in (0.0, 0.0175):
        res = sim(books, trades, coef, "BASE"); ct = [r[0] for r in res]; x = np.array([r[1] for r in res])
        base[coef] = (ct, x)
        keys, days = split_days(ct, x)
        bs = []
        for _ in range(10000):
            idx = rng.integers(len(days), size=len(days)); bs.append(pfa(np.concatenate([days[i] for i in idx])))
        lo, med, hi = np.percentile(bs, [5, 50, 95])
        print("coef %.4f n=%d days=%d PF=%.2f boot90=[%.2f,%.2f] med %.2f mean/event %+.2fc sd %.1fc P(boot PF>=1)=%.3f" % (coef, len(x), len(days), pfa(x), lo, hi, med, 100 * x.mean(), 100 * x.std(ddof=1), np.mean(np.array(bs) >= 1)))
        print(" N: (D P>=1.3, D P>=1.5, I P>=1.3, I P>=1.5, D median PF)")
        for N, v in power_tab(x, days, Ns, B, rng).items(): print("  as-is  N=%d" % N, v)
        for N, v in power_tab(x, days, Ns, B, rng, mean_shift=-x.mean()).items(): print("  NULL   N=%d" % N, v)
    print("== Q2")
    dailies = {}
    for coef in (0.0, 0.0175):
        ct, x = base[coef]; keys, days = split_days(ct, x); d = np.array([a.sum() for a in days]); dailies[coef] = (keys, d)
        ac = np.corrcoef(d[:-1], d[1:])[0, 1]
        print("coef %.4f days=%d mean $%+.3f/day sd $%.3f lag1 autocorr %+.2f events/day %s" % (coef, len(d), d.mean(), d.std(ddof=1), ac, [len(a) for a in days]))
    for n in (20, 30):
        for r0 in (0.0, 0.3): print("n=%d observed r=%.1f 90%% interval [%.2f, %.2f]" % ((n, r0) + fisher(r0, n)))
    n = 4
    while fisher(0.0, n)[1] >= 0.3: n += 1
    print("smallest n with 90%% upper bound < 0.3 at observed r 0: %d" % n)
    n = 4
    while fisher(0.15, n)[1] >= 0.3: n += 1
    print("... at observed r 0.15: %d" % n)
    d0 = dt.date(2026, 10, 29); print("20th day:", d0 + dt.timedelta(days=19), "30th:", d0 + dt.timedelta(days=29), "32nd:", d0 + dt.timedelta(days=31))
    print("== Q3")
    zmax = np.mean(np.max(np.random.default_rng(1).standard_normal((200000, 92)), axis=1)); print("zmax(92) = %.3f" % zmax)
    for coef in (0.0175, 0.0):
        R = strikes(books, trades, coef); ds = sorted(r[3] for r in R); c2 = ds[2 * len(ds) // 3]
        ctb, xb = base[coef]; mbase = xb.mean()
        cells = {"block12-18": lambda r: r[1] == 2, "highD": lambda r: r[3] >= c2, "both": lambda r: r[1] == 2 and r[3] >= c2}
        for name, f in cells.items():
            ev = collections.defaultdict(float)
            for r in R:
                if f(r): ev[r[0]] += r[4]
            cts = sorted(ev); x = np.array([ev[c] for c in cts]); keys, days = split_days(cts, x)
            z = zday(ev); m = x.mean(); ksel = max(0.0, (z - zmax) / z)
            print("coef %.4f %s: n=%d PF=%.2f mean %+.2fc (base %+.2fc) day z %.2f k_sel %.2f" % (coef, name, len(x), pfa(x), 100 * m, 100 * mbase, z, ksel))
            for lab, k in (("k=1", 1.0), ("k=0.5", 0.5), ("k_sel", ksel)):
                mt = mbase + k * (m - mbase); sh = mt - m
                grid = [25, 50, 75, 100, 150, 200, 300, 400, 500, 700, 1000, 1500, 2000]
                pw = power_tab(x, days, grid, 2000, rng, mean_shift=sh)
                need = next((N for N in grid if pw[N][1] >= 0.8), None)
                print("   %s true mean %+.2fc  shifted PF %.2f  power(PF>=1.5, D) %s  N for 80%%: %s" % (lab, 100 * mt, pfa(x + sh), {N: pw[N][1] for N in (100, 200, 300, 500, 1000, 2000)}, need if need else "not reachable by 2000"))
    print("== Q4")
    t0 = parse_ms(dev[0]); t1 = parse_ms(cutoff); hours = (t1 - t0) / 3.6e6
    cov = NDEV / hours; quot = 168 / 171
    print("first dev event %s cutoff %s span %.1f h, dev events 171 -> coverage %.3f, quotable share %.3f" % (dev[0], cutoff, hours, cov, quot))
    dirs = collections.Counter(f.split("/")[1] for f in names); print("book dirs by date (listing):", dict(sorted(dirs.items())))
    cut = dt.datetime(2026, 11, 7, 15, tzinfo=dt.timezone.utc)
    for tgt in ("2026-11-17", "2026-11-24", "2026-12-01"):
        T = dt.datetime.fromisoformat(tgt).replace(tzinfo=dt.timezone.utc); h = (T - cut).total_seconds() / 3600
        print("closing before %s 00:00Z: grid hours %.0f; at coverage %.2f: %.0f events (quotable %.0f); at full coverage %.0f; 12-18 CT block (1/4) %.0f covered / %.0f full" % (tgt, h, cov, h * cov, h * cov * quot, h, h * cov * quot / 4, h / 4))
    for lab, rate in (("full coverage", 1.0), ("dev coverage", cov)):
        hrs = 300 / (rate * quot); print("n=300 quotable events reached at %s: %s" % (lab, cut + dt.timedelta(hours=hrs)))
        hrs = 300 / (rate * quot / 4); print("n=300 in 12-18 CT block at %s: %s" % (lab, cut + dt.timedelta(hours=hrs)))
