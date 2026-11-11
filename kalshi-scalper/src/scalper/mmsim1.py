"""MMSIM1 simulation (workers/MMSIM1_PROTOCOL.md). Reads the `quote-data` branch book and trade files via git; no network. Development = first two thirds of events by close time."""
import csv, gzip, io, subprocess, sys, collections, math, datetime as dt
REPO = "/home/user/shwoopnet"
def git(*a): return subprocess.run(["git", "-C", REPO] + list(a), capture_output=True, check=True).stdout
def pf(x):
    w = sum(v for v in x if v > 0); l = -sum(v for v in x if v < 0); return w / l if l > 0 else 99.0
def parse_ms(s): return int(dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp() * 1000)
def load():
    files = [f for f in git("ls-tree", "-r", "--name-only", "origin/quote-data").decode().split("\n") if f.startswith("book/") and f.endswith("book.csv.gz")]
    books = collections.defaultdict(list); trades = collections.defaultdict(dict)
    for f in files:
        for name, store in ((f, "b"), (f.replace("book.csv.gz", "trades.csv.gz"), "t")):
            try: raw = gzip.decompress(git("show", "origin/quote-data:" + name)).decode()
            except Exception: continue
            for r in csv.DictReader(io.StringIO(raw)):
                if store == "b": books[(r["close_time"], r["ticker"])].append(r)
                else: trades[r["ticker"]][r["trade_id"]] = r
    return books, trades
def fnum(x):
    try: return float(x)
    except Exception: return None
def simulate(books, trades, maker_coef):
    events = collections.defaultdict(list)          # close_time -> [ticker]
    for (ct, tk) in books: events[ct].append(tk)
    out = []                                         # per event: (close_time, pnl, strikes, fills_yes, fills_no, pairs, singles)
    for ct in sorted(events):
        T = parse_ms(ct); start, end, flat = T - 50 * 60000, T - 15 * 60000, T - 15 * 60000
        ev_pnl = 0.0; fy = fn = pairs = singles = quoted = 0
        for tk in events[ct]:
            rows = sorted(books[(ct, tk)], key=lambda r: int(r["poll_ts_local_ms"]))
            rows = [r for r in rows if start <= int(r["poll_ts_local_ms"]) <= end]
            if not rows: continue
            tr = sorted(trades.get(tk, {}).values(), key=lambda r: r["created_time"])
            tr = [(parse_ms(r["created_time"]), fnum(r["yes_price_dollars"]), fnum(r["count_fp"]), r["taker_outcome_side"]) for r in tr]
            first = rows[0]; post = int(first["poll_ts_local_ms"])
            legs = {}
            yb, ys = fnum(first["yes_bid_px_1"]), fnum(first["yes_bid_sz_1"]); nb, ns = fnum(first["no_bid_px_1"]), fnum(first["no_bid_sz_1"])
            if None in (yb, ys, nb, ns) or yb <= 0 or nb <= 0: continue
            quoted += 1
            for side, p, ahead in (("yes", yb, ys), ("no", nb, ns)):
                cum = 0.0; filled = None
                for t, price, cnt, taker in tr:
                    if t < post or t > flat: continue
                    if side == "yes" and abs(price - p) < 1e-6 and taker == "no": cum += cnt
                    elif side == "no" and abs(price - (1 - p)) < 1e-6 and taker == "yes": cum += cnt
                    if cum >= ahead + 1: filled = t; break
                if filled: legs[side] = (p, filled)
            fy += "yes" in legs; fn += "no" in legs
            mf = lambda p: maker_coef * p * (1 - p)
            if "yes" in legs and "no" in legs:
                p, q = legs["yes"][0], legs["no"][0]; pnl = 1 - p - q - mf(p) - mf(q); pairs += 1
            elif legs:
                side, (p, _) = next(iter(legs.items()))
                fl = [r for r in rows if int(r["poll_ts_local_ms"]) <= flat]
                last = fl[-1] if fl else first
                bid = fnum(last["yes_bid_px_1" if side == "yes" else "no_bid_px_1"]) or 0.0
                pnl = bid - p - mf(p) - 0.07 * bid * (1 - bid); singles += 1
            else: pnl = 0.0
            ev_pnl += pnl
        if quoted: out.append((ct, ev_pnl, quoted, fy, fn, pairs, singles))
    return out
if __name__ == "__main__":
    books, trades = load()
    ev = sorted({ct for ct, _ in books})
    cut = ev[2 * len(ev) // 3]
    print("events", len(ev), "dev events", len([c for c in ev if c < cut]), "(held-out third unread)", "tickers", len(books), "trade tickers", len(trades))
    for coef in (0.0, 0.0175):
        res = [r for r in simulate(books, trades, coef) if r[0] < cut]
        x = [r[1] for r in res]; n = len(x)
        strikes = sum(r[2] for r in res)
        days = len({r[0][:10] for r in res})
        print("maker coef %.4f: dev events %d days %d | strikes quoted %d | fills yes %d no %d | pairs %d singles %d | PF %.2f | mean per strike %+.2fc | mean per event %+.2fc | net %+.2f$ per contract-set" % (
            coef, n, days, strikes, sum(r[3] for r in res), sum(r[4] for r in res), sum(r[5] for r in res), sum(r[6] for r in res), pf(x), 100 * sum(x) / max(1, strikes), 100 * sum(x) / max(1, n), sum(x)))
