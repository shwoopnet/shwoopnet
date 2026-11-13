"""SOCDERIV second build (History Miner, Nov 13, 2026). Reader and measurement written from Desk B's registration text only
(SOCDERIV_REGISTRATION.md, claude/idea-desk-b, last change ec98d614, with the 19:15Z one-way cost amendment) and the series file
SOCDERIV_SERIES.json (sha256 01b7febc...). The Testing Desk's socderiv.py and its tests were NOT read. Zero tries: no result is read,
the market `result` field is never touched. Every output carries the registered freshness line.

Usage: python3 -I socderiv2.py <series.json> <lists run folder> <candles run folder> <out.json>

Readings this build chose where the text is silent are listed in READINGS and printed in every output."""
import gzip, hashlib, json, math, os, statistics, sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import socderiv2_model as M  # noqa: E402

SERIES_SHA = "01b7febcd1466f880aeac1d567a259e5803d42b0b72e16a72331fd11c6d031d2"
FRESH = "candle freshness measured on Bitcoin 15 minute only, not on sports"
EPS = 1e-9
SAMPLE_N = 60
MIN_FILLED = 150
GAP_LINE, SPREAD_LINE = 0.08, 0.04
COST_KILL = 0.04
READINGS = [
    "R16 (Nov 13, after the lists landed and before any candle): the BTTS leg is the ONE market whose event_ticker is KX<LG>BTTS-<GAMEKEY> (series file: one market an event), whatever its last segment (the real tickers end in -BTTS, the made-up layout used -YES); more than one such market = no BTTS leg, counted (third amendment 707fad73, item 1)",
    "R1 lists proof: every live_<SERIES> request answered 200 on pages 1..k with no cursor left; the three fee-field reads are not used (the fee is the registered formula) and may be unanswered",
    "R2 a game = one GAME event with all three winner markets (two team codes and -TIE); a game missing one is counted 'winner legs incomplete' and is not derivable",
    "R3 sample: GAME events whose latest winner close is inside [2026-09-12, 2026-11-13) UTC, the 60 with the latest such close per league, ties by event ticker; never extended",
    "R4 kickoff: the three winner markets must carry one occurrence_datetime; each of the three must close 100 to 135 minutes (inclusive) after kickoff",
    "R5 the minute at 'kickoff minus m' is the candle whose end_period_ts equals kickoff minus m minutes; m from 30 up to 90",
    "R6 two-sided: 0 < yes bid < yes ask < 1 from close_dollars; 0.00 bid or 1.00 ask is no side; a candle with no close_dollars stops the reader",
    "R7 rate 1 belongs to the lower team code; winner mids are (P(team1 > team2), P(level), P(team2 > team1)); a total strike is used only with a numeric floor_strike and means over floor_strike",
    "R8 targets: the BTTS market and every team-total market with a numeric floor_strike whose last ticker segment starts with exactly one of the two team codes; else 'unreadable'. Each target gets its own instant",
    "R9 cheaper side: the side with the lower ask, YES ask vs NO ask = 1 - YES bid; a tie takes YES. gap = model value of that side minus its ask",
    "R10 placebo: at each (game, instant) of a filled target, the two-sided total strike whose mid is nearest 0.50 (tie: lower line) is left out, the rates refit, its cheaper-side gap taken; one placebo per (game, instant)",
    "R11 residual: per fit, sqrt(SSE / number of fitted legs); the median over fits is reported",
    "R12 one-way cost per target: (ask - mid) + entry fee, fee = ceil to the cent of 0.07 x p x (1 - p) with p = cheaper-side ask + 0.01; the cell's cost is the median; CLOSED on cost above 0.04",
    "R13 n for the minimum = filled games (games with at least one filled target of that type); targets filled are also printed",
    "R14 verdict order (Desk B second dated amendment, e12b26cd, sha256 228e7860...): no evidence at n = x (under 150 filled games), then closed on cost, then not tradable, then efficient or survives; every flag is printed beside the verdict",
    "R15 quantiles: median by statistics.median; quartiles and 90th percentile by linear interpolation between order statistics at (n - 1) x q",
]


class Stop(Exception):
    pass


def iso(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()


def load_run(folder, used):
    """Proof the run is whole for the request ids in `used` (None = every request), and its answers by id."""
    m = json.load(open(os.path.join(folder, "manifest.json")))
    if m.get("status") != "complete":
        raise Stop("run not complete: %s" % folder)
    reqs = m["job"]["requests"]
    by = {}
    root = os.path.realpath(folder)
    for r in m["rows"]:
        if r.get("truncated"):
            raise Stop("truncated row %s" % r.get("id"))
        p = os.path.realpath(os.path.join(folder, r["file"]))
        if os.path.dirname(p) != root:
            raise Stop("file outside run: %s" % r["file"])
        raw = gzip.open(p, "rb").read()
        if "sha256" in r and hashlib.sha256(raw).hexdigest() != r["sha256"]:
            raise Stop("sha mismatch %s" % r["file"])
        if "bytes" in r and len(raw) != r["bytes"]:
            raise Stop("length mismatch %s" % r["file"])
        by.setdefault(r["id"], []).append((r, json.loads(raw)))
    out = {}
    for q in reqs:
        if used is not None and not used(q["id"]):
            continue
        rows = sorted(by.get(q["id"], []), key=lambda x: x[0]["page"])
        if not rows or [x[0]["page"] for x in rows] != list(range(1, len(rows) + 1)):
            raise Stop("request %s not answered on pages 1..k" % q["id"])
        if any(x[0]["status"] != 200 for x in rows):
            raise Stop("request %s has a non-200 page" % q["id"])
        if rows[-1][1].get("cursor"):
            raise Stop("request %s left a cursor" % q["id"])
        out[q["id"]] = (q, [x[1] for x in rows])
    return out


def px(c, side):
    o = c.get(side)
    if not isinstance(o, dict) or "close_dollars" not in o:
        raise Stop("candle without %s.close_dollars" % side)
    return float(o["close_dollars"])


def two_sided(c):
    if c is None:
        return None
    b, a = px(c, "yes_bid"), px(c, "yes_ask")
    if 0 < b < a < 1 and b > EPS and a < 1 - EPS:
        return b, a
    return None


def q_lin(xs, q):
    s = sorted(xs)
    if not s:
        return None
    h = (len(s) - 1) * q
    lo = math.floor(h)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (h - lo)


def fee_cents(p):
    return math.ceil(100 * 0.07 * p * (1 - p) - 1e-9) / 100


def cheaper(bid, ask, model_yes):
    no_ask = 1 - bid
    if no_ask < ask - EPS:
        return "no", no_ask, (1 - model_yes) - no_ask
    return "yes", ask, model_yes - ask


def stats(gaps, spreads):
    if not gaps:
        return {"n": 0}
    hit = sum(1 for g, s in zip(gaps, spreads) if g >= GAP_LINE - EPS and s <= SPREAD_LINE + EPS)
    return {"n": len(gaps), "median": round(statistics.median(gaps), 6), "q1": round(q_lin(gaps, 0.25), 6),
            "q3": round(q_lin(gaps, 0.75), 6), "p90": round(q_lin(gaps, 0.90), 6),
            "share_gap8_spread4": round(hit / len(gaps), 6), "count_gap8_spread4": hit}


def run(series_path, lists_dir, candles_dir):
    raw = open(series_path, "rb").read()
    if hashlib.sha256(raw).hexdigest() != SERIES_SHA:
        raise Stop("series file hash")
    ser = json.loads(raw)
    lo, hi = iso(ser["window"]["closes_from"]), iso(ser["window"]["closes_before"])
    group_of = {lg: g for g, lgs in ser["groups"].items() for lg in lgs}

    lists = load_run(lists_dir, lambda i: i.startswith("live_"))
    markets = {}
    no_such = []
    for rid, (q, pages) in lists.items():
        s = rid[len("live_"):]
        got = [mk for pg in pages for mk in pg.get("markets", [])]
        if not got:
            no_such.append(s)
        for mk in got:
            if mk["ticker"].split("-")[0] != s:
                raise Stop("market %s in the list of %s" % (mk["ticker"], s))
            mk = {k: v for k, v in mk.items() if k != "result"}  # never read
            markets[mk["ticker"]] = mk

    candles = load_run(candles_dir, None)
    cmap = {}
    for rid, (q, pages) in candles.items():
        asked = set(q["params"]["market_tickers"].split(","))
        for pg in pages:
            for e in pg.get("markets", []):
                t = e["market_ticker"]
                if t not in asked:
                    raise Stop("candle ticker %s not asked by %s" % (t, rid))
                d = cmap.setdefault(t, {})
                for c in e.get("candlesticks", []):
                    ts = int(c["end_period_ts"])
                    if ts in d and d[ts] != c:
                        raise Stop("conflicting candle %s %d" % (t, ts))
                    d[ts] = c

    cells = {}
    no_btts = {}
    league_rows = {}
    for lg in sorted(group_of):
        grp = group_of[lg]
        gs = "KX%sGAME" % lg
        events = {}
        for t, mk in markets.items():
            if t.split("-")[0] == gs:
                events.setdefault(mk["event_ticker"], []).append(mk)
        games, incomplete = [], 0
        for ev, mks in events.items():
            codes = sorted(m["ticker"].split("-")[-1] for m in mks if not m["ticker"].endswith("-TIE"))
            ties = [m for m in mks if m["ticker"].endswith("-TIE")]
            if len(codes) != 2 or len(ties) != 1 or len(mks) != 3:
                incomplete += 1
                continue
            cl = max(iso(m["close_time"]) for m in mks)
            if lo <= cl < hi:
                games.append((cl, ev, mks, codes))
        games.sort(key=lambda g: (-g[0], g[1]))
        sample = games[:SAMPLE_N]
        lr = {"group": grp, "games_listed_in_window": len(games), "winner_legs_incomplete": incomplete,
              "games_in_sample": len(sample), "kickoff_derivable": 0}
        league_rows[lg] = lr
        for cl, ev, mks, codes in sample:
            occ = {m.get("occurrence_datetime") for m in mks}
            if len(occ) != 1 or None in occ:
                continue
            ko = iso(occ.pop()) - 180 * 60
            if not all(100 * 60 - EPS <= iso(m["close_time"]) - ko <= 135 * 60 + EPS for m in mks):
                continue
            lr["kickoff_derivable"] += 1
            key = ev.split("-", 1)[1]
            win = {c: "%s-%s" % (ev, c) for c in codes}
            win["TIE"] = "%s-TIE" % ev
            totals = sorted(((float(m["floor_strike"]), t) for t, m in markets.items()
                             if t.startswith("KX%sTOTAL-%s-" % (lg, key)) and isinstance(m.get("floor_strike"), (int, float))))
            targets = []
            bts = sorted(t for t, m in markets.items() if m.get("event_ticker") == "KX%sBTTS-%s" % (lg, key))
            if len(bts) == 1:                  # R16 = third amendment item 1: the ONE market of the BTTS event, whatever its last segment
                targets.append(("BTTS", bts[0], None, None))
            else:                              # none, or more than one: no BTTS leg, counted (third amendment item 1)
                no_btts[grp] = no_btts.get(grp, 0) + 1
            for t, m in sorted(markets.items()):
                if not t.startswith("KX%sTEAMTOTAL-%s-" % (lg, key)):
                    continue
                last = t.split("-")[-1]
                hits = [i for i, c in enumerate(codes) if last.startswith(c)]
                fs = m.get("floor_strike")
                if len(hits) != 1 or not isinstance(fs, (int, float)):
                    targets.append(("TEAMTOTAL", t, "unreadable", None))
                else:
                    targets.append(("TEAMTOTAL", t, hits[0], float(fs)))
            for tt in ("BTTS", "TEAMTOTAL"):
                c = cells.setdefault((grp, tt), {"derivable": 0, "games_with_target": 0, "targets": 0, "unreadable": 0,
                                                 "targets_filled": 0, "games_filled": set(), "gaps": [], "spreads": [],
                                                 "cost": [], "roundtrip": [], "resid": [], "plac": {}})
                c["derivable"] += 1
                mine = [x for x in targets if x[0] == tt]
                if mine:
                    c["games_with_target"] += 1
                for _, tk, team, line in mine:
                    c["targets"] += 1
                    if team == "unreadable":
                        c["unreadable"] += 1
                        continue
                    for m_ in range(30, 91):
                        ts = int(ko - m_ * 60)
                        wq = [two_sided(cmap.get(win[k], {}).get(ts)) for k in (codes[0], "TIE", codes[1])]
                        if any(w is None for w in wq):
                            continue
                        tq = [(ln, tkr, two_sided(cmap.get(tkr, {}).get(ts))) for ln, tkr in totals]
                        tq = [(ln, tkr, q) for ln, tkr, q in tq if q is not None]
                        if len(tq) < 3:
                            continue
                        g = two_sided(cmap.get(tk, {}).get(ts))
                        if g is None:
                            continue
                        wm = [(b + a) / 2 for b, a in wq]
                        tm = [(ln, (q[0] + q[1]) / 2) for ln, _, q in tq]
                        l1, l2, sse = M.fit(wm, tm)
                        c["resid"].append(math.sqrt(sse / (3 + len(tm))))
                        if tt == "BTTS":
                            val = M.p_btts(l1, l2)
                        else:
                            val = M.p_team_over(l1 if team == 0 else l2, line)
                        b, a = g
                        side, sa, gap = cheaper(b, a, val)
                        c["targets_filled"] += 1
                        c["games_filled"].add(ev)
                        c["gaps"].append(gap)
                        c["spreads"].append(a - b)
                        c["cost"].append((a - (a + b) / 2) + fee_cents(sa + 0.01))
                        mid = (a + b) / 2
                        c["roundtrip"].append((a - b) + 2 * 0.07 * mid * (1 - mid))
                        pk = (ev, ts)
                        if pk not in c["plac"]:
                            ln0, _, q0 = min(tq, key=lambda x: (abs((x[2][0] + x[2][1]) / 2 - 0.5), x[0]))
                            rest = [(ln, mm) for ln, mm in tm if ln != ln0]
                            p1, p2, _ = M.fit(wm, rest)
                            _, _, pg = cheaper(q0[0], q0[1], M.p_total_over(p1, p2, ln0))
                            c["plac"][pk] = (pg, q0[1] - q0[0])
                        break

    out_cells = []
    for (grp, tt), c in sorted(cells.items()):
        nf = len(c["games_filled"])
        st = stats(c["gaps"], c["spreads"])
        pl = list(c["plac"].values())
        ps = stats([x[0] for x in pl], [x[1] for x in pl])
        cost = statistics.median(c["cost"]) if c["cost"] else None
        flags = {
            "not_tradable": c["derivable"] > 0 and nf < c["derivable"] / 2 - EPS,
            "closed_on_cost": cost is not None and cost > COST_KILL + EPS,
            "under_minimum": nf < MIN_FILLED,
        }
        share, pshare = st.get("share_gap8_spread4"), ps.get("share_gap8_spread4")
        flags["survives_share_test"] = (share is not None and pshare is not None and share >= 0.10 - EPS
                                        and share >= 2 * pshare - EPS)
        if flags["under_minimum"]:
            v = "no evidence at n = %d" % nf
        elif flags["closed_on_cost"]:
            v = "closed on cost (selected on development)"
        elif flags["not_tradable"]:
            v = "closed: not tradable"
        elif flags["survives_share_test"]:
            v = "survives the measurement"
        else:
            v = "efficient, move on (p90 gap %s)" % st.get("p90")
        out_cells.append({
            "group": grp, "target": tt, "games_kickoff_derivable": c["derivable"], "games_with_target": c["games_with_target"],
            "targets": c["targets"], "targets_unreadable": c["unreadable"], "targets_filled": c["targets_filled"],
            "games_filled": nf, "filled_share": round(nf / c["derivable"], 6) if c["derivable"] else None,
            "median_spread": round(statistics.median(c["spreads"]), 6) if c["spreads"] else None,
            "one_way_cost_median": round(cost, 6) if cost is not None else None,
            "round_trip_median_info_only": round(statistics.median(c["roundtrip"]), 6) if c["roundtrip"] else None,
            "gap": st, "placebo": ps,
            "fit_residual_median": round(statistics.median(c["resid"]), 6) if c["resid"] else None,
            "flags": flags, "verdict": v, "freshness": FRESH})
    return {"build": "History Miner second build, from the registration text only", "freshness": FRESH,
            "no_such_series": sorted(no_such), "no_btts_leg_by_group": no_btts, "leagues": league_rows, "cells": out_cells, "readings": READINGS}


def main(argv):
    try:
        res = run(argv[1], argv[2], argv[3])
    except Stop as e:
        res = {"stopped": str(e), "freshness": FRESH}
    with open(argv[4], "w") as f:
        json.dump(res, f, indent=1, sort_keys=True)
        f.write("\n")
    print(FRESH)
    print(json.dumps(res.get("cells", res), sort_keys=True)[:4000])


if __name__ == "__main__":
    main(sys.argv)
