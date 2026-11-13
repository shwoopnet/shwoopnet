"""MMSIM1 RULE P PORT (Desk A, Nov 13 2026), a COPY of V2's `src/scalper/mmsim1.py` (sha256 ORIGINAL_SHA below; nothing on V2's branch is edited) with Rule P added beside Rule Q, as MMSIM1_AMENDMENT_3.md section 2 says. Reads the `quote-data` branch book and trade files via git; no network.
  python3 -I mmsim1_rulep.py            DEVELOPMENT reproduction only: events closing BEFORE PINNED_CUTOFF, printed under Rule Q (must equal the registered development figures exactly) and under Rule P.
  python3 -I mmsim1_rulep.py heldout    REFUSED before 2026-11-24 and by the read-once marker (the original's lines, unchanged); this copy does not wire the marker file, so the held-out mode stays refused until the Head says go.
Changes from the original, and only these: (1) load() reads only book files dated on or before 2026-11-07 and keeps ONLY rows of events closing before PINNED_CUTOFF (a later event's rows are dropped as they are parsed; its trades are dropped too), so no held-out event is ever simulated or printed; (2) simulate() takes a `rule` argument, 'Q' (the original code path, byte for byte in behaviour) or 'P' (price priority: a leg also fills at its own price at the earliest of the Rule Q condition, a taker print through our price in [post, T-15], or the first book poll strictly after the post and strictly before T-15 at which our side's best bid is below our price or absent); (3) the main block prints both rules. PINNED_CUTOFF and the refusal before 2026-11-24 are unchanged."""
ORIGINAL_SHA = "b221030109f627a4e0a15f54ccf7d48b0730462cd7da2e070e41457ca5b99a7d"
import csv, gzip, io, subprocess, sys, os, collections, math, datetime as dt
REPO = "/home/user/shwoopnet"
def git(*a): return subprocess.run(["git", "-C", REPO] + list(a), capture_output=True, check=True).stdout
PINNED_CUTOFF = "2026-11-07T15:00:00Z"   # close_time strings compare lexically; events closing at or after this are the held-out set
def pf(x):
    w = sum(v for v in x if v > 0); l = -sum(v for v in x if v < 0); return w / l if l > 0 else 99.0
def parse_ms(s): return int(dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp() * 1000)
def load():
    files = [f for f in git("ls-tree", "-r", "--name-only", "origin/quote-data").decode().split("\n") if f.startswith("book/") and f.endswith("book.csv.gz") and f.split("/")[1] <= "2026-11-07"]      # port change (1): no folder dated after the cutoff day is opened
    books = collections.defaultdict(list); trades = collections.defaultdict(dict); pending = collections.defaultdict(dict)
    for f in files:
        for name, store in ((f, "b"), (f.replace("book.csv.gz", "trades.csv.gz"), "t")):
            try: raw = gzip.decompress(git("show", "origin/quote-data:" + name)).decode()
            except Exception: continue
            for r in csv.DictReader(io.StringIO(raw)):
                if store == "b":
                    if r["close_time"] < PINNED_CUTOFF: books[(r["close_time"], r["ticker"])].append(r)      # port change (1): a held-out event's row is dropped as parsed
                else: pending[r["ticker"]][r["trade_id"]] = r
    for (_ct, tk) in books: trades[tk] = pending.get(tk, {})      # trades of tickers with no development event are never kept
    return books, trades
def fnum(x):
    try: return float(x)
    except Exception: return None
def simulate(books, trades, maker_coef, rule="Q"):
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
                if not filled and rule == "P":      # Rule P (Amendment 3 section 2): the union with the through-print and the book conditions, at OUR price
                    for t, price, cnt, taker in tr:
                        if t < post or t > flat: continue
                        if (side == "yes" and taker == "no" and price < p - 1e-6) or (side == "no" and taker == "yes" and price > (1 - p) + 1e-6): filled = t; break
                    if not filled:
                        for r in rows:
                            ts = int(r["poll_ts_local_ms"])
                            if ts <= post or ts >= flat: continue
                            bp = fnum(r["yes_bid_px_1" if side == "yes" else "no_bid_px_1"])
                            if bp is None or bp < p - 1e-6: filled = ts; break
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
    # PINNED (amendment 1, Nov 12, 2026): the cutoff is a fixed time, NOT two thirds of whatever events are on the branch.
    # Without this a re-run would score held-out events as development. Held-out mode is refused before 2026-11-24.
    cut = PINNED_CUTOFF
    HELD = len(sys.argv) > 1 and sys.argv[1] == "heldout"
    if HELD and dt.datetime.now(dt.timezone.utc) < dt.datetime(2026, 11, 24, tzinfo=dt.timezone.utc):
        raise SystemExit("held-out read refused before 2026-11-24 (single read; see MMSIM1_PROTOCOL.md Amendment 1)")
    if HELD:
        # read-once: the COMMITTED marker line in the protocol must still say "not yet read" (and carry an allowed date that has come)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from readonce import require_unread
        require_unread("workers/MMSIM1_PROTOCOL.md", "MMSIM1")
        print("After this read, replace the marker line in workers/MMSIM1_PROTOCOL.md with 'READ-ONCE MARKER: MMSIM1 READ ON <date>, commit <hash>' and commit it.")
    print("events", len(ev), "dev events", len([c for c in ev if c < cut]), "(held-out third unread)", "tickers", len(books), "trade tickers", len(trades))
    for rule, coef in (("Q", 0.0), ("Q", 0.0175), ("P", 0.0), ("P", 0.0175)):
        print("RULE", rule)
        res = [r for r in simulate(books, trades, coef, rule) if (r[0] >= cut if HELD else r[0] < cut)]
        x = [r[1] for r in res]; n = len(x)
        strikes = sum(r[2] for r in res)
        days = len({r[0][:10] for r in res})
        print("maker coef %.4f: dev events %d days %d | strikes quoted %d | fills yes %d no %d | pairs %d singles %d | PF %.2f | mean per strike %+.2fc | mean per event %+.2fc | net %+.2f$ per contract-set" % (
            coef, n, days, strikes, sum(r[3] for r in res), sum(r[4] for r in res), sum(r[5] for r in res), sum(r[6] for r in res), pf(x), 100 * sum(x) / max(1, strikes), 100 * sum(x) / max(1, n), sum(x)))
