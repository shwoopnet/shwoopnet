"""MMSIM1 RULE P PORT (Desk A, Nov 13 2026), a COPY of V2's `src/scalper/mmsim1.py` (sha256 ORIGINAL_SHA below; nothing on V2's branch is edited) with Rule P added beside Rule Q, as MMSIM1_AMENDMENT_3.md section 2 says. Reads the `quote-data` branch book and trade files via git; no network.
  python3 -I mmsim1_rulep.py            DEVELOPMENT reproduction only: events closing BEFORE PINNED_CUTOFF, printed under Rule Q (must equal the registered development figures exactly) and under Rule P.
  python3 -I mmsim1_rulep.py heldout    REFUSED before 2026-11-24 and by the read-once marker (the original's lines, unchanged); this copy does not wire the marker file, so the held-out mode stays refused until the Head says go.
Changes from the original, and only these: (1) load() reads only book files dated on or before 2026-11-07 and keeps ONLY rows of events closing before PINNED_CUTOFF (a later event's rows are dropped as they are parsed; its trades are dropped too), so no held-out event is ever simulated or printed; (2) simulate() takes a `rule` argument and the order size (the Rule Q queue condition at N contracts needs cum >= ahead + N; Rule P's through-print and book conditions fill the whole order), 'Q' (the original code path, byte for byte in behaviour) or 'P' (price priority: a leg also fills at its own price at the earliest of the Rule Q condition, a taker print through our price in [post, T-15], or the first book poll strictly after the post and strictly before T-15 at which our side's best bid is below our price or absent); (3) the main block prints both rules. PINNED_CUTOFF and the refusal before 2026-11-24 are unchanged."""
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
def fee_leg(coef, p, size=1, rounded=False):
    """per-contract fee of one order of `size` contracts: coef x size x p x (1 - p), rounded UP to the cent per order when `rounded` (Amendment 1 item 4), divided back to one contract"""
    raw = coef * size * p * (1 - p)
    return (math.ceil(raw * 100 - 1e-9) / 100 if rounded else raw) / size
def pts(r):
    try: return int(r["poll_ts_local_ms"])
    except Exception: return None
def simulate(books, trades, maker_coef, rule="Q", size=1, rounded=False, stats=None, dev_only=True):
    events = collections.defaultdict(list)          # close_time -> [ticker]
    for (ct, tk) in books: events[ct].append(tk)
    out = []                                         # per event: (close_time, pnl, strikes, fills_yes, fills_no, pairs, singles)
    for ct in sorted(events):
        if dev_only and ct >= PINNED_CUTOFF: continue      # a held-out event is never simulated here (F2)
        T = parse_ms(ct); start, end, flat = T - 50 * 60000, T - 15 * 60000, T - 15 * 60000
        ev_pnl = 0.0; fy = fn = pairs = singles = quoted = 0
        for tk in events[ct]:
            rows = sorted([r for r in books[(ct, tk)] if pts(r) is not None], key=pts)      # F5: a blank or unparseable poll time drops that row
            rows = [r for r in rows if start <= int(r["poll_ts_local_ms"]) <= end]
            if not rows: continue
            tr = sorted(trades.get(tk, {}).values(), key=lambda r: r["created_time"])
            tr2 = []
            for r in tr:      # F5: a trade with an unparseable time, price or count is skipped, never a crash
                try: tm = parse_ms(r["created_time"])
                except Exception: continue
                pr_, ct_ = fnum(r["yes_price_dollars"]), fnum(r["count_fp"])
                if pr_ is None or ct_ is None: continue
                tr2.append((tm, pr_, ct_, r["taker_outcome_side"]))
            tr = tr2
            first = rows[0]; post = int(first["poll_ts_local_ms"])
            legs = {}
            yb, ys = fnum(first["yes_bid_px_1"]), fnum(first["yes_bid_sz_1"]); nb, ns = fnum(first["no_bid_px_1"]), fnum(first["no_bid_sz_1"])
            if None in (yb, ys, nb, ns) or yb <= 0 or nb <= 0: continue
            quoted += 1
            for side, p, ahead in (("yes", yb, ys), ("no", nb, ns)):
                cum = 0.0; filled = None; fkind = None; ffrac = None
                for t, price, cnt, taker in tr:
                    if t < post or t > flat: continue
                    if side == "yes" and abs(price - p) < 1e-6 and taker == "no": cum += cnt
                    elif side == "no" and abs(price - (1 - p)) < 1e-6 and taker == "yes": cum += cnt
                    if cum >= ahead + size: filled = t; fkind = "q"; ffrac = abs(cnt - round(cnt)) > 0.001; break
                if not filled and rule == "P":      # Rule P (Amendment 3 section 2): the union with the through-print and the book conditions, at OUR price
                    for t, price, cnt, taker in tr:
                        if t < post or t > flat: continue
                        if (side == "yes" and taker == "no" and price < p - 1e-6) or (side == "no" and taker == "yes" and price > (1 - p) + 1e-6): filled = t; fkind = "x"; ffrac = abs(cnt - round(cnt)) > 0.001; break
                    if not filled:
                        for r in rows:
                            ts = int(r["poll_ts_local_ms"])
                            if ts <= post or ts >= flat: continue
                            bp = fnum(r["yes_bid_px_1" if side == "yes" else "no_bid_px_1"])
                            if bp is None or bp < p - 1e-6: filled = ts; fkind = "b"; ffrac = None; break
                if filled:
                    legs[side] = (p, filled)
                    if stats is not None: stats.append({"kind": fkind, "frac": ffrac})
            fy += "yes" in legs; fn += "no" in legs
            mf = lambda p: fee_leg(maker_coef, p, size, rounded)
            if "yes" in legs and "no" in legs:
                p, q = legs["yes"][0], legs["no"][0]; pnl = 1 - p - q - mf(p) - mf(q); pairs += 1
            elif legs:
                side, (p, _) = next(iter(legs.items()))
                fl = [r for r in rows if int(r["poll_ts_local_ms"]) <= flat]
                last = fl[-1] if fl else first
                bid = fnum(last["yes_bid_px_1" if side == "yes" else "no_bid_px_1"]) or 0.0
                pnl = bid - p - mf(p) - fee_leg(0.07, bid, size, rounded); singles += 1
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
    registered = {}
    for rule in ("Q", "P"):
        print("RULE", rule)
        for (size, rounded, name) in ((1, False, "1 contract, fee unrounded (registered basis)"), (1, True, "1 contract, fee rounded up"), (10, True, "10 contracts, fee rounded up"), (10, False, "10 contracts, fee unrounded (reference: the Nov 12 note read 1.48 and 1.35 under Rule Q)")):
            for coef in (0.0, 0.0175):
                res = [r for r in simulate(books, trades, coef, rule, size, rounded, dev_only=not HELD) if (r[0] >= cut if HELD else r[0] < cut)]
                x = [r[1] for r in res]; n = len(x)
                strikes = sum(r[2] for r in res)
                days = len({r[0][:10] for r in res})
                if size == 1 and not rounded: registered[(rule, coef)] = pf(x)
                print("%s | maker coef %.4f: dev events %d days %d | strikes quoted %d | fills yes %d no %d | pairs %d singles %d | PF %.2f | mean per strike %+.2fc | mean per event %+.2fc | net %+.2f$ per contract-set" % (
                    name, coef, n, days, strikes, sum(r[3] for r in res), sum(r[4] for r in res), sum(r[5] for r in res), sum(r[6] for r in res), pf(x), 100 * sum(x) / max(1, strikes), 100 * sum(x) / max(1, n), sum(x)))
        st = []; simulate(books, trades, 0.0175, rule, 1, False, st, dev_only=not HELD)
        tape = [f for f in st if f["kind"] in ("q", "x")]; book_fills = sum(1 for f in st if f["kind"] == "b")
        print("fractional-size share of the fills behind the P&L (Amendment 2; fills triggered by a trade print, fractional = a non-integer contract count): %d of %d (%.1f%%) | fills triggered by the book alone (no trade): %d | all fills %d" % (
            sum(1 for f in tape if f["frac"]), len(tape), 100 * sum(1 for f in tape if f["frac"]) / max(1, len(tape)), book_fills, len(st)))
    pp = registered[("P", 0.0175)]
    print("DEVELOPMENT LABEL INPUT (unrounded figures, the registered basis: 1 contract, fee unrounded, maker bound 0.0175): Rule Q PF %.4f, Rule P PF %.4f; Rule P PF below 1.0: %s (168 development events, under the 300 the original bar needs; the Amendment 3 verdict applies to the held-out read, and the Head rules what a development PF below 1.0 means)" % (registered[("Q", 0.0175)], pp, "YES" if pp < 1.0 else "NO"))
