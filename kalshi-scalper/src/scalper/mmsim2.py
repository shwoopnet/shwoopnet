"""MMSIM2 (workers/MMSIM2_PROTOCOL.md). Development events only: the script drops every event closing at or after the cutoff (events closing before PINNED_CUTOFF 2026-11-07T15:00:00Z) before simulating. No network."""
import csv, gzip, io, subprocess, collections, math, json, sys
sys.path.insert(0, "/home/user/shwoopnet/kalshi-scalper/src/scalper")
from mmsim1 import git, pf, parse_ms, fnum, REPO, PINNED_CUTOFF
NDEV = 171   # expected development count, a check only; the cut is the timestamp constant
def rd(name):
    try: return csv.DictReader(io.StringIO(gzip.decompress(git("show", "origin/quote-data:" + name)).decode()))
    except Exception: return []
def load():
    files = [f for f in git("ls-tree", "-r", "--name-only", "origin/quote-data").decode().split("\n") if f.startswith("book/") and f.endswith("book.csv.gz")]
    rawb = {}
    cts = set()
    for f in files:
        rows = list(rd(f)); rawb[f] = rows
        cts |= {r["close_time"] for r in rows}
    cutoff = PINNED_CUTOFF; dev = {c for c in cts if c < cutoff}   # timestamp constant, not an event index (Nov 12, 2026)
    books = collections.defaultdict(list); trades = collections.defaultdict(dict)
    for f, rows in rawb.items():
        keep = [r for r in rows if r["close_time"] in dev]
        for r in keep: books[(r["close_time"], r["ticker"])].append(r)
        if keep:
            for r in rd(f.replace("book.csv.gz", "trades.csv.gz")): trades[r["ticker"]][r["trade_id"]] = r
    del rawb
    return books, trades, cutoff
def sim(books, trades, coef, v):
    mf = lambda p: coef * p * (1 - p)
    start_m = 35 if v == "V6" else 50
    flat_m = 20 if v == "V4a" else 10 if v == "V4b" else 15
    events = collections.defaultdict(list)
    for (ct, tk) in books: events[ct].append(tk)
    out = []; dayfills = collections.defaultdict(int)
    for ct in sorted(events):
        T = parse_ms(ct); start, flat = T - start_m * 60000, T - flat_m * 60000
        cand = []
        for tk in sorted(events[ct]):
            rows = sorted(books[(ct, tk)], key=lambda r: int(r["poll_ts_local_ms"]))
            rows = [r for r in rows if start <= int(r["poll_ts_local_ms"]) <= flat]
            if not rows: continue
            f0 = rows[0]
            yb, ys, nb, ns = fnum(f0["yes_bid_px_1"]), fnum(f0["yes_bid_sz_1"]), fnum(f0["no_bid_px_1"]), fnum(f0["no_bid_sz_1"])
            if None in (yb, ys, nb, ns) or yb <= 0 or nb <= 0: continue
            cand.append((tk, rows, yb, ys, nb, ns, (yb + 1 - nb) / 2))
        if v == "V3": cand = [c for c in cand if 0.20 <= c[6] <= 0.80]
        if v == "V5": cand = sorted(cand, key=lambda c: abs(c[6] - 0.5))[:4]
        ranked = sorted(cand, key=lambda c: abs(c[6] - 0.5)); rank = {c[0]: i + 1 for i, c in enumerate(ranked)}
        legs_all = {}   # (tk, side) -> (price, filltime)
        for tk, rows, yb, ys, nb, ns, mid in cand:
            f0 = rows[0]; post = int(f0["poll_ts_local_ms"])
            tr = sorted(trades.get(tk, {}).values(), key=lambda r: r["created_time"])
            tr = [(parse_ms(r["created_time"]), fnum(r["yes_price_dollars"]), fnum(r["count_fp"]), r["taker_outcome_side"]) for r in tr]
            inside = v == "V1" and yb + nb <= 0.97 + 1e-9
            for side, p, ahead in (("yes", yb, ys), ("no", nb, ns)):
                if inside: p = round(p + 0.01, 4); ahead = 0.0
                cancel = None
                if v == "V7":
                    for r in rows:
                        b = fnum(r["yes_bid_px_1" if side == "yes" else "no_bid_px_1"])
                        if b is not None and b <= p - 0.02 - 1e-9: cancel = int(r["poll_ts_local_ms"]); break
                cum = 0.0
                for t, price, cnt, taker in tr:
                    if t < post or t > flat: continue
                    if cancel is not None and t >= cancel: break
                    if side == "yes":
                        hit = taker == "no" and (price <= p + 1e-6 if inside else abs(price - p) < 1e-6)
                    else:
                        hit = taker == "yes" and (price >= 1 - p - 1e-6 if inside else abs(price - (1 - p)) < 1e-6)
                    if hit: cum += cnt
                    if cum >= ahead + 1: legs_all[(tk, side)] = (p, t); break
        if v in ("V2", "V8"):
            order = sorted(legs_all.items(), key=lambda kv: (kv[1][1], kv[0][0]))
            seen = collections.Counter(); keep = {}
            for (tk, side), (p, t) in order:
                if v == "V2":
                    if seen[side] >= 1: continue
                    seen[side] += 1
                else:
                    key = (ct[:10], rank[tk], side)
                    if dayfills[key] >= 3: continue
                    dayfills[key] += 1
                keep[(tk, side)] = (p, t)
            legs_all = keep
        ev_pnl = 0.0; fy = fn = pairs = singles = 0
        for tk, rows, yb, ys, nb, ns, mid in cand:
            legs = {s: legs_all[(tk, s)] for s in ("yes", "no") if (tk, s) in legs_all}
            fy += "yes" in legs; fn += "no" in legs
            if len(legs) == 2:
                p, q = legs["yes"][0], legs["no"][0]; ev_pnl += 1 - p - q - mf(p) - mf(q); pairs += 1
            elif legs:
                side, (p, _) = next(iter(legs.items()))
                fl = [r for r in rows if int(r["poll_ts_local_ms"]) <= flat]; last = fl[-1] if fl else rows[0]
                bid = fnum(last["yes_bid_px_1" if side == "yes" else "no_bid_px_1"]) or 0.0
                ev_pnl += bid - p - mf(p) - 0.07 * bid * (1 - bid); singles += 1
        if cand: out.append((ct, ev_pnl, len(cand), fy, fn, pairs, singles))
    return out
def stats(res):
    x = [r[1] for r in res]; n = len(x)
    days = collections.defaultdict(float)
    for r in res: days[r[0][:10]] += r[1]
    d = list(days.values()); nd = len(d); md = sum(d) / nd
    sd = (sum((a - md) ** 2 for a in d) / (nd - 1)) ** .5
    z = md / (sd / nd ** .5) if sd else 0
    th = [x[i * n // 3:(i + 1) * n // 3] for i in range(3)]
    return dict(n=n, pf=round(pf(x), 2), fills_day=round(sum(r[3] + r[4] for r in res) / nd, 1), mean_c=round(100 * sum(x) / n, 2),
                z=round(z, 2), thirds=[round(100 * sum(t) / len(t), 2) for t in th], pos=sum(1 for t in th if sum(t) > 0), days=nd,
                daily={k: round(v, 4) for k, v in sorted(days.items())})
if __name__ == "__main__":
    books, trades, cutoff = load()
    print("cutoff", cutoff, "events kept", len({c for c, _ in books}))
    allr = {}
    for v in ("BASE", "V1", "V2", "V3", "V4a", "V4b", "V5", "V6", "V7", "V8"):
        for coef in (0.0, 0.0175):
            s = stats(sim(books, trades, coef, v)); allr[(v, coef)] = s
            print(v, coef, {k: s[k] for k in s if k != "daily"})
    json.dump({"%s|%s" % k: v for k, v in allr.items()}, open("/tmp/claude-0/mmsim2.json", "w"))
