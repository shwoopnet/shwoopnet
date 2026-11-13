"""OIVER-DEPTH, BUILD 2 (History Miner, Nov 13, 2026), from Desk A's card 3 only (DESK_A_OICORE_VERSIONS_NOV13.md at 741092a7, sha256 e7b918b0);
Desk A's build was not read. Rules and hand figures in EXPECTED_BY_HAND.md (a0b02753), committed first; the parent is the same as OIVER-SPREAD build 2's;
the input adds yes_bid_size and yes_ask_size at the decision time; the Head's convention of 19:53Z (dated line there) governs: the decision quote is the candle ending close - 180 s (the input's yes_bid and yes_ask), C = 20, the price is the ask seen.
Governing card: Desk A's 23b5bd9b, DESK_A_OICORE_VERSIONS_NOV13.md sha256 ae1f1ee6 (its 19:52Z, 19:54Z, 21:13Z and 21:14Z lines; dated line
of 21:17Z in EXPECTED_BY_HAND.md). Development only: a held-out read is refused in this build. Prints aggregates only.
Usage: python3 -I oiver_depth2.py dev <windows.csv>"""
import csv, json, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hm_guard  # noqa: E402

EPS = 1e-9
HELDOUT_FIRST = 1796083200          # 2026-12-01T00:00:00Z
OI_MIN = 86300                      # (g) inclusive
FLOOR, CEIL = 0.08, 0.50
SLIP = 0.0                          # (c) Head 19:53Z: the ask seen, no +1c (PR 895); filled at that ask, an UPPER BOUND on fills
C = 20                              # (b) Head 19:53Z: OICORE bottom step (PR 901), fee rounded up per order
DEPTH_FACTOR = 2                    # the version's one condition: the touch the order meets holds at least 2 x C contracts (open reading (a))
WEEK = 604800
RANGE_FROM = 1793232000            # 2026-10-29T00:00:00Z: DEPTH's intersection of the candle and R6 ranges
RANGE_TO = 1794182400              # 2026-11-09T00:00:00Z, exclusive
MIN_SIGNALS = 60


class Stop(Exception):
    pass


def touch_size(r, side):
    v = r.get("yes_ask_size" if side == "yes" else "yes_bid_size")
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def fee(p):
    return math.ceil(round(100 * 0.07 * C * p * (1 - p), 6)) / 100 / C


def pf(xs):
    w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return None if not xs else (math.inf if l == 0 else w / l)


def shown(x):
    return None if x is None else ("inf" if x == math.inf else round(x, 6))


def summary(nets, weeks):
    n = len(nets); h = n // 2
    return {"n": n, "pf": shown(pf(nets)), "net": round(sum(nets), 6), "mean": round(sum(nets) / n, 6) if n else None,
            "half1_pf": shown(pf(nets[:h])), "half2_pf": shown(pf(nets[h:])),
            "net_per_contract_week": round(sum(nets) / weeks, 6) if n else None}


def run(mode, path):
    hm_guard.refuse_all([path])
    if mode != "dev":
        raise Stop("only a development read is built; a held-out read is refused")
    counts, parent, version, closes = {}, [], [], []                              # closes: of the parent's trades (the weeks)

    def bump(k):
        counts[k] = counts.get(k, 0) + 1
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            close = int(r["close_ts"])
            if close >= HELDOUT_FIRST:
                bump("held_out_ignored"); continue
            if not (RANGE_FROM <= close < RANGE_TO):
                raise Stop("development row %s closes outside the development range" % r["ticker"])
            if r["result"] not in ("yes", "no", "void"):
                raise Stop("result %r refused (%s)" % (r["result"], r["ticker"]))
            rows.append((close, r))
    for close, r in sorted(rows, key=lambda x: (x[0], x[1]["ticker"])):
        try:
            rise = float(r["oi_180"]) - float(r["oi_360"])
        except (TypeError, ValueError):
            bump("no_oi"); continue
        if not math.isfinite(rise):
            bump("no_oi"); continue
        if rise < OI_MIN - EPS:
            bump("oi_below"); continue
        b, a = float(r["yes_bid"] or 0), float(r["yes_ask"] or 1)
        if not (0 < b < 1 and 0 < a < 1) or b >= a - EPS:
            bump("not_two_sided"); continue
        asks = {"yes": a, "no": 1 - b}
        side = "yes" if asks["yes"] <= asks["no"] + EPS else "no"      # (d) tie to YES
        ask = asks[side]
        if ask < FLOOR - EPS:
            bump("cheap_skipped"); continue
        if ask > CEIL + EPS:
            bump("out_of_band"); continue
        if str(r.get("r6_poll", "")).strip() != "1":                    # replay set: parent trades with an R6 decision poll only
            bump("no_poll"); continue
        price = min(ask + SLIP, CEIL)
        fe = fee(price)
        res = r["result"]
        net = -fe if res == "void" else ((1 - price - fe) if res == side else (-price - fe))
        net = round(net, 9)
        parent.append(net)
        closes.append(close)
        size = touch_size(r, side)                                      # a YES buy meets the YES ask; a NO buy meets the YES bid
        if size is None:
            bump("size_unknown"); continue
        if size < DEPTH_FACTOR * C - EPS:
            bump("depth_thin"); continue
        version.append(net)
    weeks = max((max(closes) - min(closes)) / WEEK, 1.0) if closes else 1.0       # over the parent's (DEPTH: the replay set's) trades, at least 1
    P, V = summary(parent, weeks), summary(version, weeks)
    removed = round(1 - len(version) / len(parent), 6) if parent else None
    take = {"pf_lift_ge_0.10": None if P["pf"] is None or V["pf"] is None else (pf(version) >= pf(parent) + 0.10 - EPS),
            "net_week_not_lower": None if P["net_per_contract_week"] is None else V["net_per_contract_week"] >= P["net_per_contract_week"] - EPS,
            "half2_not_worse": None if pf(parent[len(parent)//2:]) is None or pf(version[len(version)//2:]) is None else pf(version[len(version)//2:]) >= pf(parent[len(parent)//2:]) - EPS,
            "signals_ge_60": len(version) >= MIN_SIGNALS}
    kills = {"removed_more_than_half": removed is not None and removed > 0.5 + EPS,
             "pf_below_parent": pf(version) is not None and pf(parent) is not None and pf(version) < pf(parent) - EPS}
    label = "no evidence at n = %d" % len(version) if len(version) < MIN_SIGNALS else "development (not a verdict)"
    return {"removed_share": removed, "counts": counts, "parent": P, "version": V, "takeover_info": take, "kills_info": kills, "label": label}


if __name__ == "__main__":
    try:
        print(json.dumps(run(sys.argv[1], sys.argv[2])))
    except Stop as e:
        raise SystemExit("STOP: %s" % e)
