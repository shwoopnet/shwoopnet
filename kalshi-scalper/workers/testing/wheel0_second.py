#!/usr/bin/env python3
"""WHEEL0 independent second scorer (Testing Desk, Nov 12, 2026). Built FROM THE REGISTRATION TEXT ALONE (WHEEL0_REGISTRATION.md with Amendment 1, sha256 66f7e83b...); Forensics' wheel0.py was NOT read.
Research only: reads files, sends nothing. The hard precondition is in code: the READ (read_all) refuses before 2026-11-14T00:00Z and until WHEEL0_PRECONDITION.md has a line starting 'DEPTH1 READ MADE:'; refuses HELDOUT_ folders (typed, nested, relative or through a link: scorekit.guard);
keeps no Bitcoin or Ethereum market closing on or after 2026-10-29T00:00Z (dropped at the reader, on the close time, before anything else); joins no outcome before the read; writes one result file and refuses a second.
The pure functions below (orders, blocks, stats, bootstrap, null calibration, verdict) take in-memory data so they can be tested and cross-checked on a synthetic fixture without any file.
Ambiguities in the text, each resolved the way printed in AMBIGUITIES (the Head rules before the read).
"""
import bisect, hashlib, json, math, os, random, statistics as st, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k

SEED = 20261112
LOOKS = (600, 360, 180)
NOT_BEFORE = 1794614400            # 2026-11-14T00:00:00Z
BTC_ETH_CUT = 1793232000           # 2026-10-29T00:00:00Z
BANDS = {"cheap": (("05-20", 500, 2000, "lo"), ("20-35", 2000, 3500, "lo"), ("35-50", 3500, 5000, "both")),          # in basis points of a dollar; "lo": [a, b); "both": [a, b]
         "fav": (("50-65", 5000, 6500, "hi"), ("65-80", 6500, 8000, "hi"), ("80-88", 8000, 8800, "open"))}          # "hi": (a, b]; "open": (a, b)
THIRD = ("88-97", 8800, 9700)                                                                                       # favourite ask 88c to 97c, both ends in (my reading)
AMBIGUITIES = [
    "A. 'a one-sided quote is no signal': I require bid and ask both present with 0 < bid < ask < 1 (an ask of 1.00 or a bid of 0 is one-sided).",
    "B. Third line '88c to 97c': I take 88.00c <= ask <= 97.00c (80-88 is open at 88, so 88 belongs here); 97 inclusive.",
    "C. The drop's hash is 'a hash of the seed 20261112, the ticker, the look and the side': I use sha256('20261112|ticker|L|side'), first 8 bytes as an integer over 2^64, kept if below the fill share. Another hash gives other draws: bit-for-bit agreement of the random drop needs the exact function.",
    "D. Bootstrap RNG and p: python random.Random(20261112), days resampled with replacement, 10,000 draws; p = share of draws with D <= 0 (one-sided for D > 0). Null calibration RNG: random.Random(20261112) (seed 'fixed' but not stated), 500 runs, p = share with D >= observed.",
    "E. A signal's time order inside a template and market is its market's close time (then ticker). A block's 'day' for the bootstrap is the UTC date of the close of the ORDER (each order in a next-block carries its own day).",
    "F. 'Latest look' of a market (null calibration chance): the smallest L with a two-sided candle; the chance is that candle's YES mid.",
    "G. Sister templates 'HOT at the same moment': a sister template (mirror side same look; same side other look; other band; same market) counts if its most recent COMPLETED block as of the end time of the HOT block (the close time of the block's last order) is HOT. The plain HOT share is HOT blocks over blocks of that market.",
    "H. Secondary (wheel's real rule): after a HOT block the next 30 signals of the same template and market; confirmed if their PF >= 1.0 (no losses = confirmed); then the 60 after those pooled; needs 90 signals after the block.",
    "I. PF with no losses is infinite (printed as 'inf'); PF with no orders is None. Void result: net = minus the fee (price refunded, fee kept), counted as a loss in the block's rarer-outcome count and in PF.",
    "J. Look candle: the 1 minute candle whose end_period_ts equals close minus L exactly.",
]


def cents(x): return round(x * 10000)                      # basis points of a dollar: exact comparisons


def band_of(side, ask_bp):
    for name, a, b, kind in BANDS[side]:
        if (kind == "lo" and a <= ask_bp < b) or (kind == "both" and a <= ask_bp <= b) or (kind == "hi" and a < ask_bp <= b) or (kind == "open" and a < ask_bp < b): return name
    return None


def third_of(ask_bp): return THIRD[0] if THIRD[1] <= ask_bp <= THIRD[2] else None


def fee10(p): return math.ceil(round(0.07 * p * (1 - p) * 10 * 100, 6)) / 100         # 10 contracts, rounded up to the cent


def drop_hash(ticker, L, side):
    h = hashlib.sha256(("%d|%s|%d|%s" % (SEED, ticker, L, side)).encode()).digest()
    return int.from_bytes(h[:8], "big") / 2.0 ** 64


def fill_share(drop_table, series, L, side, band):
    grp = "gold_xrp_doge" if series in ("KXGOLD15M", "KXXRP15M", "KXDOGE15M") else "xrp_doge"
    for r in drop_table[grp]:
        if r["L"] == L and r["side"] == side and r["band"] == band: return r["fill_share"]
    raise KeyError((grp, L, side, band))


def signals(markets, idx):
    """Candle read, BEFORE the drop and WITHOUT any outcome. markets: [{series, ticker, close}] (no result); idx {ticker: {ts: candle}}. Returns the list of signals (one per market, look and side that has one)."""
    out = []
    for m in markets:
        for L in LOOKS:
            c = idx.get(m["ticker"], {}).get(m["close"] - L)
            if not c or c.get("bid") is None or c.get("ask") is None: continue
            b, a = cents(c["bid"]), cents(c["ask"])
            if not (0 < b < a < 10000) or a - b > 400: continue
            ya, na = a, 10000 - b
            if ya == na: continue
            for side, ask, yes in (("cheap" if ya < na else "fav", ya, True), ("fav" if ya < na else "cheap", na, False)):
                band = band_of(side, ask); third = third_of(ask) if side == "fav" else None
                if band is None and third is None: continue
                out.append({"series": m["series"], "ticker": m["ticker"], "close": m["close"], "L": L, "side": side, "band": band or third, "third": band is None, "yes": yes, "ask_bp": ask})
    return out


def settle(sig, result):
    """Add the outcome of ONE signal: the order of 10 at the ask seen. void (neither yes nor no): price refunded, fee kept, a loss."""
    p = sig.get("paid", sig["ask_bp"] / 10000.0); f = fee10(p)
    if result not in ("yes", "no"): return dict(sig, win=False, net=-f, void=True)
    win = (result == "yes") == sig["yes"]
    return dict(sig, win=win, net=(10 * (1 - p) - f) if win else (-10 * p - f), void=False)


def pf(nets):
    w = sum(x for x in nets if x > 0); l = -sum(x for x in nets if x < 0)
    return None if not nets else (float("inf") if l <= 0 and w > 0 else (None if l <= 0 else w / l))


def blocks(seq, third=False):
    """seq: orders of ONE template and market, time order. A block: at least 60 filled signals (150 for the third line) and on until it holds at least 10 of the rarer outcome (wins for cheap, losses for favourite; third line: its 10th loss). -> list of dicts(start, end index, orders, hot)."""
    min_n = 150 if third else 60; rare_is_win = (seq[0]["side"] == "cheap") if seq and not third else False
    out, start, n, rare = [], 0, 0, 0
    for i, o in enumerate(seq):
        n += 1; rare += (1 if o["win"] else 0) if rare_is_win else (0 if o["win"] else 1)
        if n >= min_n and rare >= 10:
            orders = seq[start:i + 1]; nets = [x["net"] for x in orders]; h = len(orders) // 2
            p, p1, p2 = pf(nets), pf(nets[:h]), pf(nets[h:])
            hot = p is not None and p >= 1.3 and p1 is not None and p1 >= 1.0 and p2 is not None and p2 >= 1.0
            out.append({"start": start, "end": i, "orders": orders, "hot": hot, "end_close": orders[-1]["close"]})
            start, n, rare = i + 1, 0, 0
    return out


def group_templates(orders, third=False):
    g = {}
    for o in orders:
        if o["third"] != third: continue
        g.setdefault((o["series"], o["L"], o["side"], o["band"]), []).append(o)
    for v in g.values(): v.sort(key=lambda o: (o["close"], o["ticker"]))
    return g


def pairs(orders, third=False):
    """-> list of (hot_block, next_block, key) for every consecutive pair of blocks of one template and market."""
    res = []
    for key, seq in group_templates(orders, third).items():
        bl = blocks(seq, third)
        for a, b in zip(bl, bl[1:]): res.append((a, b, key))
    return res


def day_of(o): return o["close"] // 86400


def d_stat(prs):
    h = [o["net"] for a, b, _ in prs if a["hot"] for o in b["orders"]]; n = [o["net"] for a, b, _ in prs if not a["hot"] for o in b["orders"]]
    if not h or not n: return None, h, n
    return sum(h) / len(h) - sum(n) / len(n), h, n


def bootstrap_p(prs, draws=10000, seed=SEED):
    """Resample UTC days (with replacement); p = share of draws with D <= 0."""
    days = {}
    for a, b, _ in prs:
        for o in b["orders"]:
            r = days.setdefault(day_of(o), [0.0, 0, 0.0, 0]); i = 0 if a["hot"] else 2; r[i] += o["net"]; r[i + 1] += 1
    keys = sorted(days); rng = random.Random(seed); le = valid = 0
    for _ in range(draws):
        sh = nh = sn = nn = 0
        for _ in keys:
            r = days[keys[rng.randrange(len(keys))]]; sh += r[0]; nh += r[1]; sn += r[2]; nn += r[3]
        if nh and nn:
            valid += 1; le += (sh / nh - sn / nn) <= 0
    return None if not valid else le / valid


def null_calibrated_p(orders, chance, observed_d, runs=500, seed=SEED, third=False):
    """Every order is kept; every market's result is redrawn with P(yes) = chance[ticker]; blocks and labels rebuilt; p = share of runs with D >= observed."""
    rng = random.Random(seed); ge = 0; tickers = sorted({o["ticker"] for o in orders})
    for _ in range(runs):
        res = {t: ("yes" if rng.random() < chance[t] else "no") for t in tickers}
        sim = [settle(o, res[o["ticker"]]) for o in orders]
        d = d_stat(pairs(sim, third))[0]
        ge += (d is not None and observed_d is not None and d >= observed_d)
    return ge / runs


def stats_after(prs):
    d, h, n = d_stat(prs)
    hp = sum(1 for a, _, _ in prs if a["hot"])
    return {"pairs": len(prs), "hot_pairs": hp, "pf_after_hot": pf(h), "orders_after_hot": len(h), "orders_after_not_hot": len(n), "mean_after_hot": None if not h else sum(h) / len(h), "mean_after_not_hot": None if not n else sum(n) / len(n), "D": d}


def verdict(pf_hot, d, hot_pairs, p_boot, p_null):
    if hot_pairs >= 30 and pf_hot is not None and pf_hot >= 1.15 and d is not None and d > 0 and p_boot is not None and p_boot <= 0.05 and p_null is not None and p_null <= 0.05: return "PREMISE SUPPORTED"
    if hot_pairs >= 30 and ((pf_hot is not None and pf_hot < 1.0) or d is None or d <= 0): return "PREMISE NOT SUPPORTED"
    return "no evidence at n = %d HOT pairs" % hot_pairs


def luck_table(orders, luck):
    """HOT blocks per band against the luck share (WHEEL0_NULL_SIM.json hot_share_by_luck)."""
    out = {}
    for third in (False, True):
        for key, seq in group_templates(orders, third).items():
            for b in blocks(seq, third):
                r = out.setdefault(key[3], {"blocks": 0, "hot": 0}); r["blocks"] += 1; r["hot"] += b["hot"]
    for band, r in out.items(): r["hot_share"] = r["hot"] / r["blocks"] if r["blocks"] else None; r["luck_share"] = luck.get(band)
    return out


def sister_lines(orders):
    """For every HOT block, whether a sister template of the same market has a HOT most-recent-completed block at the block's end time; against the market's plain HOT share. (ambiguity G)"""
    g = group_templates(orders); bl = {key: blocks(seq) for key, seq in g.items()}; res = {}
    for key, blist in bl.items():
        ser, L, side, band = key
        for b in blist:
            if not b["hot"]: continue
            for kind in ("mirror_side_same_look", "same_side_other_look", "other_band"):
                tot = hit = 0
                for k2, bl2 in bl.items():
                    if k2 == key or k2[0] != ser: continue
                    ok = {"mirror_side_same_look": k2[1] == L and k2[2] != side, "same_side_other_look": k2[2] == side and k2[1] != L and k2[3] == band, "other_band": k2[3] != band and k2[1] == L and k2[2] == side}[kind]
                    if not ok: continue
                    done = [x for x in bl2 if x["end_close"] <= b["end_close"]]
                    if not done: continue
                    tot += 1; hit += done[-1]["hot"]
                r = res.setdefault((ser, kind), {"hot_blocks_checked": 0, "sister_checks": 0, "sister_hot": 0}); r["hot_blocks_checked"] += 1; r["sister_checks"] += tot; r["sister_hot"] += hit
    plain = {}
    for key, blist in bl.items():
        r = plain.setdefault(key[0], [0, 0]); r[0] += len(blist); r[1] += sum(1 for b in blist if b["hot"])
    return {"%s|%s" % kk: dict(v, sister_hot_share=None if not v["sister_checks"] else v["sister_hot"] / v["sister_checks"], market_plain_hot_share=None if not plain[kk[0]][0] else plain[kk[0]][1] / plain[kk[0]][0]) for kk, v in res.items()}


def secondary(orders):
    """The wheel's real rule (ambiguity H): a HOT block, the next 30 signals at PF >= 1.0 (confirmed), then the 60 after those: pooled PF for confirmed and not confirmed."""
    conf, notc = [], []
    for key, seq in group_templates(orders).items():
        for b in blocks(seq):
            if not b["hot"]: continue
            nxt = seq[b["end"] + 1:b["end"] + 91]
            if len(nxt) < 90: continue
            p30 = pf([o["net"] for o in nxt[:30]]); ok = p30 is None or p30 >= 1.0
            (conf if ok else notc).extend(o["net"] for o in nxt[30:])
    return {"confirmed": {"orders": len(conf), "pf": pf(conf)}, "not_confirmed": {"orders": len(notc), "pf": pf(notc)}}


def full_read(markets_with_results, idx, drop_table, luck, boot_draws=10000, null_runs=500):
    """The whole candle read on in-memory data (this is what the guarded reader calls AFTER the preconditions). markets_with_results: [{series, ticker, close, result}]."""
    mk = [m for m in markets_with_results if not (m["series"] in ("KXBTC15M", "KXETH15M") and m["close"] >= BTC_ETH_CUT)]          # rule (h), at the reader, on the close time
    sig = signals(mk, idx); res = {m["ticker"]: m["result"] for m in mk}; kept = []
    for s in sig:
        if drop_hash(s["ticker"], s["L"], s["side"]) < fill_share(drop_table, s["series"], s["L"], s["side"], s["band"]): kept.append(settle(s, res[s["ticker"]]))
    # the null-calibration chance: YES mid at the market's latest look
    chance = {}
    for m in mk:
        for L in (180, 360, 600):
            c = idx.get(m["ticker"], {}).get(m["close"] - L)
            if c and c.get("bid") is not None and c.get("ask") is not None and 0 < c["bid"] < c["ask"] < 1: chance[m["ticker"]] = (c["bid"] + c["ask"]) / 2; break
    prs = pairs(kept); S = stats_after(prs); counts = {"markets": len(mk), "signals": len(sig), "kept_after_drop": len(kept), "blocks": sum(len(blocks(s)) for s in group_templates(kept).values()), "pairs": S["pairs"], "hot_pairs": S["hot_pairs"]}
    pb = bootstrap_p(prs, boot_draws); pn = null_calibrated_p([o for o in kept if o["ticker"] in chance], chance, S["D"], null_runs)
    out = {"counts_first": counts, "primary": dict(S, p_bootstrap=pb, p_null_calibrated=pn), "verdict": verdict(S["pf_after_hot"], S["D"], S["hot_pairs"], pb, pn), "luck": luck_table(kept, luck), "sister": sister_lines(kept), "secondary": secondary(kept),
           "per_market": {}, "caveat": "Real misses lean toward winners: the candle read overstates the LEVEL of every profit factor; D carries the verdict. Candle freshness measured on the Bitcoin 15 minute series only. A PF after HOT near 0.9 is what 'nothing there' looks like (fee drag)."}
    for ser in sorted({o["series"] for o in kept}):
        sub = [o for o in kept if o["series"] == ser]; ps = pairs(sub); s2 = stats_after(ps)
        out["per_market"][ser] = dict(s2, label=verdict(s2["pf_after_hot"], s2["D"], s2["hot_pairs"], None, None), label_note="comparison only; without the two p values only NOT SUPPORTED or no evidence can show")
    t_orders = [settle(s, res[s["ticker"]]) for s in sig if s["third"] and drop_hash(s["ticker"], s["L"], s["side"]) < fill_share(drop_table, s["series"], s["L"], s["side"], s["band"])]
    pt = pairs(t_orders, True); st3 = stats_after(pt); out["third_line_88_97_apart"] = st3
    return out


# ---------- the book read (the cross-check; gold, XRP, Dogecoin only; never changes the verdict) ----------
def book_signal(poll):
    """-> (yes_bid_bp, yes_ask_bp, yes_levels_for_buying_yes, no_levels) from one R6 poll {t, yes_bids [(px, sz)], no_bids [(px, sz)]}; None if either side of the book is empty."""
    if not poll["yes_bids"] or not poll["no_bids"]: return None
    return cents(max(px for px, _ in poll["yes_bids"])), 10000 - cents(max(px for px, _ in poll["no_bids"]))


def walk_price(levels_asks, limit_bp, size=10):
    """Average price (dollars) of buying `size` contracts walking asks (sorted cheapest first, each (ask_dollars, size)) at or under limit_bp; None if not enough size."""
    need, cost = float(size), 0.0
    for a, sz in sorted(levels_asks):
        if cents(a) > limit_bp: break
        t = min(need, sz); cost += t * a; need -= t
        if need <= 1e-12: return cost / size
    return None


def book_orders(markets, polls_by_ticker):
    """Book read. Look poll: the first poll at or after close - L, arriving within 10 s, else no look. Fill check: the FIRST LATER poll, within 4 s of the look poll, must still offer 10 contracts at or under the limit (ask seen + 1c); price paid = the average walked; else no trade. The result is joined later (settle with the walked price)."""
    out = []
    for m in markets:
        if m["series"] not in ("KXGOLD15M", "KXXRP15M", "KXDOGE15M"): continue
        polls = polls_by_ticker.get(m["ticker"], []); times = [p["t"] for p in polls]
        for L in LOOKS:
            j = bisect.bisect_left(times, m["close"] - L)
            if j >= len(polls) or times[j] - (m["close"] - L) > 10: continue
            sg = book_signal(polls[j])
            if sg is None: continue
            b, a = sg
            if not (0 < b < a < 10000) or a - b > 400: continue
            ya, na = a, 10000 - b
            if ya == na: continue
            nxt = polls[j + 1] if j + 1 < len(polls) else None
            for side, ask, yes in (("cheap" if ya < na else "fav", ya, True), ("fav" if ya < na else "cheap", na, False)):
                band = band_of(side, ask); third = third_of(ask) if side == "fav" else None
                if band is None and third is None: continue
                if nxt is None or nxt["t"] - polls[j]["t"] > 4: continue
                lv = [(1 - px, sz) for px, sz in nxt["no_bids"]] if yes else [(1 - px, sz) for px, sz in nxt["yes_bids"]]
                paid = walk_price(lv, ask + 100)
                if paid is None: continue
                out.append({"series": m["series"], "ticker": m["ticker"], "close": m["close"], "L": L, "side": side, "band": band or third, "third": band is None, "yes": yes, "ask_bp": round(paid * 10000), "paid": paid})
    return out


def count_read(lists, candles, drop_table_path):
    """The count path: signals and orders per series and template AFTER the random drop; NO result is read or joined (the loader keeps no result: markets carry ticker, series and close only)."""
    for f in list(lists) + list(candles): k.guard(f)
    mk = [{"series": v["series"], "ticker": t, "close": v["close"]} for t, v in k.markets(lists).items() if v["close"] and v["series"] in ("KXBTC15M", "KXETH15M", "KXXRP15M", "KXDOGE15M", "KXGOLD15M")]
    dropped_h = sum(1 for m in mk if m["series"] in ("KXBTC15M", "KXETH15M") and m["close"] >= BTC_ETH_CUT)
    mk = [m for m in mk if not (m["series"] in ("KXBTC15M", "KXETH15M") and m["close"] >= BTC_ETH_CUT)]
    idx = {t: {c["ts"]: c for c in v} for t, v in k.candles(candles).items()}
    table = json.load(open(drop_table_path)); sig = signals(mk, idx)
    kept = [s for s in sig if drop_hash(s["ticker"], s["L"], s["side"]) < fill_share(table, s["series"], s["L"], s["side"], s["band"])]
    by = {}
    for s in kept: by[(s["series"], s["L"], s["side"], s["band"])] = by.get((s["series"], s["L"], s["side"], s["band"]), 0) + 1
    return {"markets": len(mk), "rule_h_dropped": dropped_h, "signals_before_drop": len(sig), "orders_after_drop": len(kept), "orders_by_series": {x: sum(1 for s in kept if s["series"] == x) for x in sorted({s["series"] for s in kept})},
            "orders_by_template": {"|".join(map(str, k_)): v for k_, v in sorted(by.items())}}


# ---------- the guarded reader ----------
def precondition(path, now=None):
    now = time.time() if now is None else now
    if now < NOT_BEFORE: raise SystemExit("refused: WHEEL0 is not read before 2026-11-14T00:00Z")
    if not any(line.startswith("DEPTH1 READ MADE:") for line in open(path).read().splitlines()): raise SystemExit("refused: WHEEL0_PRECONDITION.md has no line 'DEPTH1 READ MADE:'")


def read_all(lists, candles, precondition_path, drop_table_path, luck_path, out_path, now=None):
    """THE READ: one result file; a second call refuses. Order: precondition, HELDOUT_ guards (scorekit), then loading; no outcome is joined before this call."""
    precondition(precondition_path, now)
    if os.path.exists(out_path): raise SystemExit("refused: a result already exists; WHEEL0 is read once")
    for f in list(lists) + list(candles): k.guard(f)
    mk = [{"series": v["series"], "ticker": t, "close": v["close"], "result": v["result"]} for t, v in k.markets(lists).items() if v["close"] and v["series"] in ("KXBTC15M", "KXETH15M", "KXXRP15M", "KXDOGE15M", "KXGOLD15M")]
    idx = {t: {c["ts"]: c for c in v} for t, v in k.candles(candles).items()}
    res = full_read(mk, idx, json.load(open(drop_table_path)), json.load(open(luck_path))["hot_share_by_luck"])
    json.dump(res, open(out_path, "w"), indent=1, default=str); return res


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "count":
        i = a.index("--candles"); j = a.index("--drop")
        print(json.dumps(count_read(a[1:i], a[i + 1:j], a[j + 1]), indent=1))
    else: print(__doc__); print("\n".join(AMBIGUITIES))
