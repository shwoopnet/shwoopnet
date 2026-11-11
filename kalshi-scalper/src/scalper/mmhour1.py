"""MMHOUR1 (workers/MMHOUR1_PROTOCOL.md). Development events only (mmsim2.load drops later events). No network."""
import sys, collections, itertools
from zoneinfo import ZoneInfo
import datetime as dt
sys.path.insert(0, "/home/user/shwoopnet/kalshi-scalper/src/scalper")
from mmsim1 import pf, parse_ms, fnum
from mmsim2 import load
CT = ZoneInfo("America/Chicago")
def strikes(books, trades, coef):
    mf = lambda p: coef * p * (1 - p)
    out = []  # (close_time, block, spread_label, depth, pnl, fills)
    for (ct, tk), rws in sorted(books.items()):
        T = parse_ms(ct); start, flat = T - 50 * 60000, T - 15 * 60000
        rows = sorted([r for r in rws if start <= int(r["poll_ts_local_ms"]) <= flat], key=lambda r: int(r["poll_ts_local_ms"]))
        if not rows: continue
        f0 = rows[0]
        yb, ys, nb, ns = fnum(f0["yes_bid_px_1"]), fnum(f0["yes_bid_sz_1"]), fnum(f0["no_bid_px_1"]), fnum(f0["no_bid_sz_1"])
        if None in (yb, ys, nb, ns) or yb <= 0 or nb <= 0: continue
        post = int(f0["poll_ts_local_ms"])
        hr = dt.datetime.fromtimestamp(post / 1000, CT).hour
        block = hr // 6
        sp = round(100 * (1 - yb - nb)); sl = "1c" if sp <= 1 else "2c" if sp == 2 else "3c+"
        tr = sorted(trades.get(tk, {}).values(), key=lambda r: r["created_time"])
        tr = [(parse_ms(r["created_time"]), fnum(r["yes_price_dollars"]), fnum(r["count_fp"]), r["taker_outcome_side"]) for r in tr]
        legs = {}
        for side, p, ahead in (("yes", yb, ys), ("no", nb, ns)):
            cum = 0.0
            for t, price, cnt, taker in tr:
                if t < post or t > flat: continue
                if side == "yes" and abs(price - p) < 1e-6 and taker == "no": cum += cnt
                elif side == "no" and abs(price - (1 - p)) < 1e-6 and taker == "yes": cum += cnt
                if cum >= ahead + 1: legs[side] = p; break
        if len(legs) == 2:
            p, q = legs["yes"], legs["no"]; pnl = 1 - p - q - mf(p) - mf(q)
        elif legs:
            side, p = next(iter(legs.items()))[0], next(iter(legs.values()))
            last = rows[-1]
            bid = fnum(last["yes_bid_px_1" if side == "yes" else "no_bid_px_1"]) or 0.0
            pnl = bid - p - mf(p) - 0.07 * bid * (1 - bid)
        else: pnl = 0.0
        out.append((ct, block, sl, ys + ns, pnl, len(legs)))
    return out
def cellstats(recs):
    ev = collections.defaultdict(float); fills = 0
    for r in recs: ev[r[0]] += r[4]; fills += r[5]
    cts = sorted(ev); n = len(cts)
    if n == 0: return None
    x = [ev[c] for c in cts]
    days = collections.defaultdict(float)
    for c in cts: days[c[:10]] += ev[c]
    d = list(days.values()); nd = len(d)
    z = None
    if nd > 1:
        m = sum(d) / nd; sd = (sum((a - m) ** 2 for a in d) / (nd - 1)) ** .5
        z = m / (sd / nd ** .5) if sd else 0
    th = [x[i * n // 3:(i + 1) * n // 3] for i in range(3)]
    return dict(n=n, q=len(recs), fills_day=fills / 10.0, pf=pf(x), mean=100 * sum(x) / n, z=z, thirds=[100 * sum(t) / len(t) if t else 0 for t in th], pos=sum(1 for t in th if t and sum(t) > 0), nd=nd)
if __name__ == "__main__":
    books, trades, cutoff = load()
    print("cutoff", cutoff, "dev events", len({c for c, _ in books}))
    for coef in (0.0175, 0.0):
        R = strikes(books, trades, coef)
        ds = sorted(r[3] for r in R); c1, c2 = ds[len(ds) // 3], ds[2 * len(ds) // 3]
        tc = lambda d: 0 if d < c1 else 1 if d < c2 else 2
        print("== maker coef", coef, "strike-quotes", len(R), "depth cuts", c1, c2, "spreads", collections.Counter(r[2] for r in R))
        names = ["C0-6", "C6-12", "C12-18", "C18-24"]; dn = ["lowD", "midD", "highD"]
        def show(label, recs):
            s = cellstats(recs)
            if not s: print("%-28s empty" % label); return
            print("%-28s n=%3d q=%4d fills/day=%5.1f PF=%5.2f mean=%+6.2fc z=%s thirds=%s pos=%d" % (label, s["n"], s["q"], s["fills_day"], s["pf"], s["mean"], "NA" if s["z"] is None else "%.2f" % s["z"], "/".join("%+.1f" % t for t in s["thirds"]), s["pos"]))
        show("ALL", R)
        for b in range(4): show("block " + names[b], [r for r in R if r[1] == b])
        for sl in ("1c", "2c", "3c+"): show("spread " + sl, [r for r in R if r[2] == sl])
        for t in range(3): show("depth " + dn[t], [r for r in R if tc(r[3]) == t])
        for b, sl, t in itertools.product(range(4), ("1c", "2c", "3c+"), range(3)):
            show("%s|%s|%s" % (names[b], sl, dn[t]), [r for r in R if r[1] == b and r[2] == sl and tc(r[3]) == t])
