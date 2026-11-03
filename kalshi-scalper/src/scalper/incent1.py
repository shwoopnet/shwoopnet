"""INCENT1: model of Kalshi liquidity incentive program (LIP) rewards for a small resting lane.
Registration: workers/INCENT1_REGISTRATION.md. Public data only, no key, no order. Discovery only."""
import json, random, subprocess, time, sys

BASE = "https://external-api.kalshi.com/trade-api/v2"
DISC = 0.5
ADV = {"pess": 0.27, "cent": 0.125, "opt": -0.02}      # MAKERTAIL1 bounds, fraction of price, bids <= 15c
ADV_MID = {"pess": 0.03, "cent": 0.015, "opt": 0.0}    # UNMEASURED assumption, dollars per fill, price > 15c
CAP_YEAR = 0.05


def get(path, tries=8):
    for k in range(tries):
        r = subprocess.run(["curl", "-sS", "-m", "40", "-w", "\n%{http_code}", BASE + path],
                           capture_output=True, text=True).stdout
        if "\n" not in r:
            time.sleep(2); continue
        b, c = r.rsplit("\n", 1)
        if c == "200":
            return json.loads(b)
        time.sleep(min(60, 2 * 2 ** k))
    return None


def side_levels(book, key):
    lv = [(float(p), float(s)) for p, s in book.get(key, [])]
    lv = [(p, s) for p, s in lv if s > 0]
    lv.sort(key=lambda x: -x[0])
    return lv


def ref_level(levels, T):
    """First price walking down from best bid where cumulative >= T/5; None if never."""
    c = 0.0
    for p, s in levels:
        c += s
        if c >= T / 5.0:
            return p
    return None


def competing_score(levels, T, ref, tick=0.01, clip=False):
    """Sum of size x multiplier over orders that help reach T (the crossing level in full unless clip)."""
    c = 0.0; tot = 0.0
    for p, s in levels:
        if c >= T:
            break
        take = s
        if clip and c + s > T:
            take = T - c
        ticks = 0 if (ref is None or p >= ref) else round((ref - p) / tick)
        tot += take * (DISC ** ticks)
        c += s
    return tot


def lane_price(levels, T, last, is_yes):
    """Price our order rests at: the reference level if the side has T/5 depth, else best bid, else last-3c."""
    r = ref_level(levels, T)
    if r is not None:
        return r
    if levels:
        return levels[0][0]
    if last is None or last <= 0:
        return None
    base = last if is_yes else 1 - last
    p = round(base - 0.03, 2)
    return p if 0.01 <= p <= 0.99 else None


def score_lane(book, T, last, vol24, pool_day, period_days, lane_cash=100.0, clip=False):
    """One sample of one market. Returns dict or None (no_price)."""
    y = side_levels(book, "yes_dollars"); n = side_levels(book, "no_dollars")
    py = lane_price(y, T, last, True); pn = lane_price(n, T, last, False)
    if py is None or pn is None:
        return None
    q = min(100.0, lane_cash / (py + pn))
    out = {"py": py, "pn": pn, "q": q, "cap": q * (py + pn)}
    shares = []
    for lv, p in ((y, py), (n, pn)):
        above = sum(s for pp, s in lv if pp > p)
        r = ref_level(lv + [(p, q)] if False else sorted(lv + [(p, q)], key=lambda x: -x[0]), T)
        Q = competing_score(lv, T, r, clip=clip)
        qualifies = above < T
        shares.append(q / (Q + q) if qualifies else 0.0)
    out["s"] = shares
    out["counts"] = (sum(s for _, s in y) + q >= T) and (sum(s for _, s in n) + q >= T)
    out["depth"] = (sum(s for _, s in y), sum(s for _, s in n))
    return out


def lane_value(samples, T, pool_day, period_days, vol24, case):
    """samples: list of score_lane dicts (None dropped) for one market under the case's Q convention."""
    ss = [s for s in samples if s]
    if not ss:
        return None
    f = sum(1 for s in ss if s["counts"]) / len(ss)
    sy = sum(s["s"][0] for s in ss) / len(ss); sn = sum(s["s"][1] for s in ss) / len(ss)
    cap = sum(s["cap"] for s in ss) / len(ss)
    reward = pool_day * f * (sy + sn) / 2.0
    if (sy + sn) / 2.0 * pool_day * period_days * f < 1.0:
        reward = 0.0                                    # $1 payout floor
    q = sum(s["q"] for s in ss) / len(ss)
    py = sum(s["py"] for s in ss) / len(ss); pn = sum(s["pn"] for s in ss) / len(ss)
    half = max(vol24, 0.0) / 2.0
    mult = {"pess": 2.0, "cent": 1.0, "opt": 0.5}[case]
    cost = 0.0
    for sh, p in ((sy, py), (sn, pn)):
        fills = min(q, half * sh * mult)
        c = ADV[case] * p if p <= 0.15 else ADV_MID[case]
        cost += fills * c
    capcost = cap * CAP_YEAR / 365.0
    net = reward - cost - capcost
    k = 100.0 / cap if cap > 0 else 0.0
    return {"f": f, "reward100": reward * k, "cost100": cost * k, "net100": net * k, "cap": cap, "fills_day": sum(min(q, half * sh * mult) for sh in (sy, sn))}


def verdict(lanes, scored_min=100):
    """lanes: list of net100 under the verdict case; returns word."""
    if len(lanes) < scored_min:
        return "NOT_ENOUGH_DATA"
    pos = sum(1 for x in lanes if x > 0.10)
    if pos >= 10 and pos >= 0.05 * len(lanes):
        return "VIABLE_SMALL_PROBE"
    return "NOT_VIABLE"
