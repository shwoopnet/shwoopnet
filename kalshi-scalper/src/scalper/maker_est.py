"""Research estimate: what a resting (maker) entry would add to the cash PF of favourite and cheap-tail rules on hist15 BTC and ETH.
Resting order at the decision candle's touch (YES side: our bid; NO side: the NO bid = 1 - YES ask). Filled if, during the next W seconds, the book trades through it by the candle proxy
(YES: min ask_l <= bid; NO: max bid_h >= YES ask). Unrounded fee (rebate makes the per-fill rounding go away): taker 0.07*p*(1-p); maker 0 or 0.0175*p*(1-p). Proxy only: candles are not the trade tape."""
import sqlite3, collections, sys
def pf(x):
    w = sum(v for v in x if v > 0); l = -sum(v for v in x if v < 0); return w / l if l > 0 else 99.0
RULES = [("FAV6 88-97c @6min", 0.88, 0.97, 330, 390, "fav"), ("FAV10 88-97c @10min", 0.88, 0.97, 570, 640, "fav"), ("TAIL10 4-12c @10min", 0.04, 0.12, 570, 640, "cheap")]
W = 180
for db, ser in (("data/hist15/KXBTC15M.sqlite", "BTC"), ("data/hist15/KXETH15M.sqlite", "ETH")):
    c = sqlite3.connect(db)
    mk = {t: (ct, r) for t, ct, r in c.execute("select ticker,close_ts,result from market where result in ('yes','no') and n_candles>0")}
    by = collections.defaultdict(list)
    for tk, ts, bo, bh, bl, bc, ao, ah, al, ac in c.execute("select ticker,end_ts,bid_o,bid_h,bid_l,bid_c,ask_o,ask_h,ask_l,ask_c from candle"):
        if tk in mk and bc is not None and ac is not None: by[tk].append((ts, bh, bl, bc, ah, al, ac))
    for name, lo, hi, l0, l1, kind in RULES:
        base, filled, missed = [], {"m0": [], "mq": [], "tk": []}, []
        for tk, v in by.items():
            v.sort(); ct, res = mk[tk]
            pick = None
            for x in v:
                if l0 <= ct - x[0] <= l1: pick = x
            if not pick: continue
            ts, bh, bl, b, ah, al, a = pick
            if b <= 0 or a >= 1 or a <= b or a - b > 0.03: continue
            ya, na = a, 1 - b
            side, p = (("yes", ya) if ya >= na else ("no", na)) if kind == "fav" else (("yes", ya) if ya <= na else ("no", na))
            if not (lo <= p < hi + 1e-9): continue
            win = 1.0 if res == side else 0.0
            tk_net = win - p - 0.07 * p * (1 - p); base.append(tk_net)
            # resting order at the touch of the chosen side
            if side == "yes": rest = b; fills = any(x[5] <= b + 1e-9 for x in v if ts < x[0] <= ts + W)
            else: rest = 1 - a; fills = any(x[1] >= a - 1e-9 for x in v if ts < x[0] <= ts + W)
            if fills:
                filled["m0"].append(win - rest); filled["mq"].append(win - rest - 0.0175 * rest * (1 - rest)); filled["tk"].append(win - rest - 0.07 * rest * (1 - rest))
            else: missed.append(tk_net)
        n = len(base)
        if n < 30: print(ser, name, "n", n, "too few"); continue
        f = len(filled["m0"])
        print("%s %-20s signals %4d | taker baseline PF %.2f mean %+.2fc | resting at touch: fill rate %.0f%% (%d) PF maker-fee-0 %.2f / 0.0175 %.2f / taker-fee %.2f, mean %+.2fc / %+.2fc / %+.2fc | missed signals taker PF %.2f (n %d)" % (
            ser, name, n, pf(base), 100 * sum(base) / n, 100 * f / n, f, pf(filled["m0"]), pf(filled["mq"]), pf(filled["tk"]),
            100 * sum(filled["m0"]) / max(1, f), 100 * sum(filled["mq"]) / max(1, f), 100 * sum(filled["tk"]) / max(1, f), pf(missed) if missed else 0, len(missed)))
