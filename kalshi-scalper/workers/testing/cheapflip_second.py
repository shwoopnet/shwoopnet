#!/usr/bin/env python3
"""CHEAPFLIP descriptive read, BUILD 2 (Testing Desk, Nov 17, 2026), blind from Desk C's card CHEAPFLIP_CARD.md at aa822bc85 (sha256 8a070a17...) with Amendments 1 and 2 and my readings Q1 to Q24. Pure functions on in-memory polls.
poll = (recv_ms, ticker, close_epoch, yes_bids, no_bids), bids = [(price dollars or None, size or None) x 5]; results {ticker: 'yes'|'no'|'void'}; series {ticker: series}."""
import math, time
BANDS = (3, 5, 10); KS = (2, 3, 5); HS = (1, 2); CONTRACTS = 10
M_CARRIED, M_NEW = 7492484, 9
SERIES = ("KXHYPE15M", "KXBNB15M", "KXNATGAS15M")


def fee(price_cents, n=CONTRACTS):
    p = price_cents / 100.0
    return math.ceil(round(0.07 * n * p * (1 - p) * 100, 9)) / 100


def best_bid(levels):
    """-> (cents, size) of the highest price among the levels with price and size both non-empty, or None"""
    best = None
    for px, sz in levels:
        if px is None or sz is None: continue
        c = round(px * 100)
        if best is None or c > best[0]: best = (c, sz)
    return best


def side_view(poll, side):
    """-> (ask_cents, ask_size, bid_cents, bid_size) of one side; None parts when the quote is missing"""
    own, opp = (poll[3], poll[4]) if side == "yes" else (poll[4], poll[3])
    ob, bb = best_bid(opp), best_bid(own)
    return (100 - ob[0] if ob else None, ob[1] if ob else None, bb[0] if bb else None, bb[1] if bb else None)


def find_entries(polls, close, side, upper):
    """polls of one market ordered by receive time -> (index, a cents, ask size) of the FIRST entry or None"""
    for i, pl in enumerate(polls):
        recv = pl[0] / 1000.0
        if recv >= close: continue
        ask, asz, _b, _s = side_view(pl, side)
        if ask is None or not (1 <= ask <= upper) or close - recv < 120: continue
        return i, ask, asz
    return None


def find_touch(polls, close, side, i0, a, k):
    """first later poll strictly before the close with bid >= k x a (cents) -> (index, bid cents, bid size) or None"""
    for j in range(i0 + 1, len(polls)):
        pl = polls[j]
        if pl[0] / 1000.0 >= close: continue
        _a, _as, bid, bsz = side_view(pl, side)
        if bid is not None and bid >= k * a: return j, bid, bsz
    return None


def trade_net(a, h, touch, result, side):
    """net dollars at 10 contracts, or None (a hold with no result is dropped)"""
    pe = min(a + h, 99)
    if touch is not None:
        ps = max(touch[1] - h, 1)
        return CONTRACTS * (ps - pe) / 100.0 - fee(pe) - fee(ps)
    if result not in ("yes", "no", "void"): return None
    if result == "void": return -fee(pe)
    payoff = 1.0 if result == side else 0.0
    return CONTRACTS * (payoff - pe / 100.0) - fee(pe)


def median(v):
    s = sorted(v); n = len(s)
    if not n: return None
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def pf(v):
    pos = sum(x for x in v if x > 0); neg = -sum(x for x in v if x < 0)
    if not v: return None
    if neg == 0: return math.inf if pos > 0 else None
    return pos / neg


def utc_day(t): return time.strftime("%Y-%m-%d", time.gmtime(t))


def collect(markets, results):
    """markets {ticker: (series, close, polls ordered)} -> entries list of dicts and counts"""
    ents = []; cnt = {"polls_at_or_after_close": 0, "held_entries_without_result": {}, "no_result_by_series": {}, "windows_without_result": 0}
    for tk in sorted(markets):
        series, close, polls = markets[tk]
        cnt["polls_at_or_after_close"] += sum(1 for pl in polls if pl[0] / 1000.0 >= close)
        if results.get(tk) not in ("yes", "no", "void"):
            cnt["windows_without_result"] += 1; cnt["no_result_by_series"][series] = cnt["no_result_by_series"].get(series, 0) + 1
        for side in ("yes", "no"):
            for upper in BANDS:
                e = find_entries(polls, close, side, upper)
                if e is None: continue
                i, a, asz = e; t0 = polls[i][0] / 1000.0; touches = {}
                for k in KS:
                    t = find_touch(polls, close, side, i, a, k)
                    touches[k] = None if t is None else (polls[t[0]][0] / 1000.0 - t0, t[1], t[2])
                ents.append({"ticker": tk, "series": series, "close": close, "side": side, "band": upper, "a": a, "ask_size": asz, "touches": touches, "result": results.get(tk)})
    return ents, cnt


def cell(ents, k, held_missing=None):
    n = len(ents); out = {"n": n, "days": len(set(utc_day(e["close"]) for e in ents)), "windows": len(set(e["ticker"] for e in ents))}
    out["first_day"] = min((utc_day(e["close"]) for e in ents), default=None); out["last_day"] = max((utc_day(e["close"]) for e in ents), default=None)
    tch = [e for e in ents if e["touches"][k] is not None]
    out["reach_share"] = len(tch) / n if n else None; out["median_touch_s"] = median([e["touches"][k][0] for e in tch])
    out["bid_size_5_share_at_touch"] = (sum(1 for e in tch if e["touches"][k][2] is not None and e["touches"][k][2] >= 5) / len(tch)) if tch else None
    out["ask_size_5_share_at_entry"] = (sum(1 for e in ents if e["ask_size"] is not None and e["ask_size"] >= 5) / n) if n else None
    for hi, h in enumerate(HS, 1):
        nets = [x for x in (trade_net(e["a"], h, e["touches"][k], e["result"], e["side"]) for e in ents) if x is not None]
        out["n_scored"] = len(nets); out["pf_h%d" % hi] = pf(nets); out["net_per_trade_h%d" % hi] = (sum(nets) / len(nets)) if nets else None; out["trades_h%d" % hi] = len(nets)
    return out


def table(ents, cnt):
    """-> list of (band, k, {'POOLED': cell, series: cell...}) and the held-without-result counts"""
    rows = []
    for band in BANDS:
        be = [e for e in ents if e["band"] == band]
        for k in KS:
            cells = {"POOLED": cell(be, k)}
            for s in SERIES: cells[s] = cell([e for e in be if e["series"] == s], k)
            rows.append((band, k, cells))
            for s in SERIES:
                m = sum(1 for e in be if e["series"] == s and e["touches"][k] is None and e["result"] not in ("yes", "no", "void"))
                if m: cnt["held_entries_without_result"].setdefault(s, 0); cnt["held_entries_without_result"][s] += m
    return rows
