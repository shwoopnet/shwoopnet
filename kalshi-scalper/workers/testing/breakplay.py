#!/usr/bin/env python3
"""breakplay: the GENERIC break-in-play engine (Testing Desk, Nov 12, 2026; Head's 18:24Z request). A new venue of the break-in-play family is a series file plus a small `discover` function and config, not a new program.
Family: a state change read from a sibling market's OWN close and result while play is stopped; a model value from the PRE-MATCH price; a look a fixed time after the state market closes; a placebo at the pre-match instant;
cost and share kill lines; the held-out never requested. Research only: reads files, sends nothing.

A venue supplies RECORDS (one per match), each a dict:
  cell, key, S (scheduled start, epoch), state_close (epoch: when the state market closed), up, down (team ids: `up` is ahead after the state change), 
  match {team: ticker} (the contracts bought and sold), placebo {team: ticker} (contracts that price the SAME single-state number at the pre-match instant),
  and OPTIONALLY `result_up` (True if `up` won the match) added ONLY by the venue's scoring path, never by the measurement path.
and a CONFIG (VenueConfig): model name, pre-match offsets, look offsets, thresholds. Models in MODELS map the pre-match mid of the `up` team's match contract to (value_up, value_down, placebo_up, placebo_down).

Engine pieces:  pre_match_minute | look_minute | measure (zero-try gap measurement, no result) | candle_job (packs by start) | score_rule (a registered RULE: development read only; cash PF with n by window, event-clustered z, the haircut line)
Conditions enforced here: two-sided minute-end candles only (0 < bid < ask < 1), nothing filled from another minute; the look moves FORWARD only; the pre-match search moves BACK only; held-out records are refused by a date constant;
the measurement path never touches `result_up`; score_rule refuses a record whose state_close is on or after the venue's held-out constant unless `heldout_go` is True (the Head's go, default False).
"""
import statistics as st, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k
import tie3

EDGE, SPREAD_MAX, COST_MAX, EDGE_SHARE, MIN_FILLED = 0.08, 0.04, 0.05, 0.10, 150


class VenueConfig:
    def __init__(self, name, model, pre_back=600, pre_max_back=2400, look_after=120, look_max=300, heldout_from=None, freshness="candle freshness measured on Bitcoin 15 minute only, not on this venue",
                 edge=EDGE, spread_max=SPREAD_MAX, cost_max=COST_MAX, edge_share=EDGE_SHARE, min_filled=MIN_FILLED, pack_limit=9000, max_tickers=100):
        self.__dict__.update(locals()); del self.__dict__["self"]


def solve_q(p, f):
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if f(mid) < p: lo = mid
        else: hi = mid
    return (lo + hi) / 2


def model_bo3(p):
    """Best of three: the pre-match match price p of the team that went on to win map 1 gives the single-map chance q (p = q*q*(3-2q)); one map up is worth V = 1-(1-q)^2. Placebo: q and 1-q."""
    q = solve_q(p, lambda x: x * x * (3 - 2 * x)); V = 1 - (1 - q) ** 2
    return V, 1 - V, q, 1 - q


def model_bo5_after_map1(p):
    """Best of five, one map up (first to three): single-map chance q from p = P(win >= 3 of 5 maps at q); one map up is worth P(win >= 2 of the remaining 4 maps at q)."""
    from math import comb
    f = lambda x: sum(comb(5, j) * x ** j * (1 - x) ** (5 - j) for j in range(3, 6))
    q = solve_q(p, f); V = sum(comb(4, j) * q ** j * (1 - q) ** (4 - j) for j in range(2, 5))
    return V, 1 - V, q, 1 - q


MODELS = {"bo3": model_bo3, "bo5_after_map1": model_bo5_after_map1}


def two(idx, t, ts):
    c = idx.get(t, {}).get(ts)
    if not c or c["bid"] is None or c["ask"] is None or not (0 < c["bid"] < c["ask"] < 1): return None
    return c["bid"], c["ask"]


def rt(b, a):
    mid = (a + b) / 2
    return (a - b) + 2 * 0.07 * mid * (1 - mid)


def pre_match_minute(idx, rec, cfg):
    """The candle ending at S - pre_back, stepping BACK a minute at a time to S - pre_max_back, first minute at which the match contract of `up` and BOTH placebo contracts are two-sided. None if none."""
    need = [rec["match"][rec["up"]], rec["placebo"][rec["up"]], rec["placebo"][rec["down"]]]
    for back in range(cfg.pre_back, cfg.pre_max_back + 1, 60):
        if all(two(idx, t, rec["S"] - back) for t in need): return rec["S"] - back
    return None


def pre_match_dropped_match_ok(idx, rec, cfg):
    """Desk B's added count: dropped although the match contract of `up` was two-sided at some minute of the window."""
    return any(two(idx, rec["match"][rec["up"]], rec["S"] - b) for b in range(cfg.pre_back, cfg.pre_max_back + 1, 60))


def look_minute(idx, rec, cfg, state_close=None):
    """The candle ending at the first whole minute at or after state_close + look_after, stepping FORWARD to state_close + look_max until both match contracts are two-sided."""
    sc = rec["state_close"] if state_close is None else state_close
    t0 = -(-(sc + cfg.look_after) // 60) * 60
    for ts in range(t0, sc + cfg.look_max + 1, 60):
        if all(two(idx, rec["match"][x], ts) for x in (rec["up"], rec["down"])): return ts
    return None


def prepare(idx, rec, cfg, look_no=1):
    """-> dict(pre, look, V, placebo gaps, per-side candidate gaps) or a reason string. No result is touched.
    look_no 1: the state is `up` one map ahead (value V / 1-V). look_no 2 (a record with state_close2): one map each, value q for `up` (the map-1 winner), 1-q for `down`; the look follows state_close2."""
    pre = pre_match_minute(idx, rec, cfg)
    if pre is None: return "no_pre"
    pm = sum(two(idx, rec["match"][rec["up"]], pre)) / 2
    Vu, Vd, qu, qd = MODELS[cfg.model](pm)
    plc = {}
    for side, team, val in (("up", rec["up"], qu), ("down", rec["down"], qd)):
        b, a = two(idx, rec["placebo"][team], pre); plc[side] = {"gap": val - a, "spread": a - b, "side": side}
    best_p = max(plc, key=lambda s: plc[s]["gap"])
    look = look_minute(idx, rec, cfg, rec["state_close2"] if look_no == 2 else None)
    out = {"pre": pre, "placebo": plc[best_p], "look": None}
    if look is None: return dict(out, reason="no_look")
    cand = {}
    v1, v2 = (Vu, Vd) if look_no == 1 else (qu, qd)
    for side, team, val in (("up", rec["up"], v1), ("down", rec["down"], v2)):
        b, a = two(idx, rec["match"][team], look)
        cand[side] = {"gap": val - a, "spread": a - b, "side": side, "ask": a, "team": team, "rt": rt(b, a)}
    return dict(out, look=look, cand=cand, best=max(cand, key=lambda s: cand[s]["gap"]))


def stat(rows):
    if not rows: return None
    g = [r["gap"] for r in rows]; q = st.quantiles(g, n=4, method="inclusive") if len(g) > 2 else None; d = st.quantiles(g, n=10, method="inclusive") if len(g) > 2 else None
    fire = [r for r in rows if r["gap"] >= EDGE and r["spread"] <= SPREAD_MAX]
    return {"n": len(rows), "gap_median": round(st.median(g), 4), "gap_quartiles": None if not q else [round(q[0], 4), round(q[2], 4)], "gap_p90": None if not d else round(d[8], 4),
            "share_gap_ge_8c_spread_le_4c": round(len(fire) / len(rows), 3), "share_when_team_up": round(sum(1 for r in fire if r.get("side") == "up") / len(rows), 3), "share_when_team_down": round(sum(1 for r in fire if r.get("side") == "down") / len(rows), 3)}


SECOND = "|second_look"


def measure(records, candle_folders, cfg):
    """The zero-try gap measurement (step 1 of the registered read). Touches no result. A record with state_close2 also gets a second look, kept per title under the key cell + SECOND (its own kill lines; the pre-match placebo is the title's, from all its records)."""
    idx = {t: {c["ts"]: c for c in v} for t, v in k.candles(candle_folders).items()}
    per = {}; plc_all = {}
    new = lambda: {"sampled": 0, "pre": 0, "look": [], "placebo": [], "minutes": [], "rts": [], "spreads": [], "pre_dropped_match_ok": 0, "look_filled": 0}
    for rec in records:
        assert "result_up" not in rec, "the measurement path must not carry a result"
        P = per.setdefault(rec["cell"], new()); P["sampled"] += 1
        r = prepare(idx, rec, cfg)
        if r == "no_pre":
            if pre_match_dropped_match_ok(idx, rec, cfg): P["pre_dropped_match_ok"] += 1
            if rec.get("state_close2"): per.setdefault(rec["cell"] + SECOND, new())["sampled"] += 1
            continue
        P["pre"] += 1; P["placebo"].append(r["placebo"]); plc_all.setdefault(rec["cell"], []).append(r["placebo"])
        if r["look"] is not None:
            P["look_filled"] += 1; P["minutes"].append((r["look"] - rec["state_close"]) / 60)
            for s in ("up", "down"): P["rts"].append(r["cand"][s]["rt"]); P["spreads"].append(r["cand"][s]["spread"])
            P["look"].append(r["cand"][r["best"]])
        if rec.get("state_close2"):
            P2 = per.setdefault(rec["cell"] + SECOND, new()); P2["sampled"] += 1; P2["pre"] += 1
            r2 = prepare(idx, rec, cfg, 2)
            if r2["look"] is not None:
                P2["look_filled"] += 1; P2["minutes"].append((r2["look"] - rec["state_close2"]) / 60)
                for s in ("up", "down"): P2["rts"].append(r2["cand"][s]["rt"]); P2["spreads"].append(r2["cand"][s]["spread"])
                P2["look"].append(r2["cand"][r2["best"]])
    for cell in list(per):
        if cell.endswith(SECOND): per[cell]["placebo"] = plc_all.get(cell[:-len(SECOND)], [])
    titles, verdicts = {}, []
    for cell, P in sorted(per.items()):
        s_l, s_p = stat(P["look"]), stat(P["placebo"]); n = P["look_filled"]; medrt = None if not P["rts"] else round(st.median(P["rts"]), 4)
        if n < cfg.min_filled: v = "no evidence at n = %d filled at the look" % n
        elif medrt > cfg.cost_max: v = "CLOSED on cost: median round trip %.1fc at the look is above 5c" % (100 * medrt)
        elif s_l["share_gap_ge_8c_spread_le_4c"] >= cfg.edge_share and s_l["share_gap_ge_8c_spread_le_4c"] >= 2 * (s_p["share_gap_ge_8c_spread_le_4c"] if s_p else 0): v = "SURVIVES the measurement (share at least 10 percent and at least twice the placebo's): a separate registration and the Head's go"
        else: v = "CLOSED: efficient, move on. The one number: the 90th percentile gap %s" % s_l["gap_p90"]
        verdicts.append(v)
        titles[cell] = {"sampled": P["sampled"], "filled_pre_match": P["pre"], "dropped_pre_match_with_match_contract_ok_but_placebo_contracts_not_in_the_same_minute": P["pre_dropped_match_ok"], "filled_at_the_look": n,
                        "median_minutes_state_close_to_look": None if not P["minutes"] else round(st.median(P["minutes"]), 2), "median_spread_at_look": None if not P["spreads"] else round(st.median(P["spreads"]), 4),
                        "median_round_trip_at_look": medrt, "look": s_l, "placebo": s_p, "verdict": v}
    return {"titles": titles, "tries_added": 0, "rule_scored": False, "result_read": False, "freshness": cfg.freshness,
            "card": "CLOSED: every cell is closed or has no evidence" if verdicts and all(not v.startswith("SURVIVES") for v in verdicts) else ("a cell survives the measurement" if verdicts else "no cell measured")}


def rule_trades(records, candle_folders, cfg, heldout_go=False):
    """REGISTERED RULE (development read): at the look buy 1 contract of the cheaper side's own match contract at its ask when its gap is 8c or more and its spread 4c or less; hold to the end of the match.
    `records` here MAY carry result_up (added by the venue's scoring path). Held-out records (state_close at or after cfg.heldout_from) are refused unless heldout_go. Returns (trades, counts)."""
    idx = {t: {c["ts"]: c for c in v} for t, v in k.candles(candle_folders).items()}
    trades, counts = [], {"records": 0, "held_out_refused": 0, "no_pre": 0, "no_look": 0, "no_signal": 0, "traded": 0, "no_result": 0}
    for rec in records:
        counts["records"] += 1
        if cfg.heldout_from is not None and rec["state_close"] >= cfg.heldout_from and not heldout_go:
            counts["held_out_refused"] += 1; continue
        r = prepare(idx, rec, cfg)
        if r == "no_pre": counts["no_pre"] += 1; continue
        if r["look"] is None: counts["no_look"] += 1; continue
        c = r["cand"][r["best"]]
        if not (c["gap"] >= cfg.edge and c["spread"] <= cfg.spread_max): counts["no_signal"] += 1; continue
        if "result_up" not in rec: counts["no_result"] += 1; continue
        win = rec["result_up"] if r["best"] == "up" else (not rec["result_up"])
        trades.append({"event": rec["key"], "cluster": rec["key"], "day": rec["S"] // 86400, "ts": r["look"], "price": c["ask"], "win": bool(win), "side": r["best"], "gap": c["gap"], "cell": rec["cell"]}); counts["traded"] += 1
    return trades, counts


def score_rule(records, candle_folders, cfg, heldout_go=False, name="break-in-play rule"):
    """Cash PF with n by window (three chronological windows), event-clustered z (one trade per match), day-clustered z beside it, the haircut line; labels per the standing rules. Development read only unless heldout_go."""
    trades, counts = rule_trades(records, candle_folders, cfg, heldout_go)
    out = k.score(trades, {"name": name, "price_source": "1 minute candle ask close at the look (a minute-end candle, two-sided, not a list quote)", "freshness": cfg.freshness,
                           "book_replay": "NOT PROVIDED: no order book exists for these markets; the haircut table stands in (an ask two minutes into a break may be one contract deep)"}) if trades else {"n": 0, "label": "no evidence at n = 0"}
    if trades:
        out["day_clustered_z"] = k.cluster_z([dict(t, cluster=str(t["day"])) for t in trades])
        out["by_side"] = {s: {"n": sum(1 for t in trades if t["side"] == s)} for s in ("up", "down")}
    return {"counts": counts, "result": out, "development_read_only": not heldout_go, "tries": "the one registered try of the card (the measurement stage itself is zero tries)"}


# ---------- THE REGISTERED RULE, MAPBREAK amendments 1 to 3 (Desk B, Nov 12): price = ask + 1c, fee rounded UP to the cent, two looks, order of the read fixed ----------
import math

PRICE_THROUGH = 0.01


def fee_up(p):
    """0.07 x p x (1 - p), rounded UP to the next whole cent (one contract pays it). The float is rounded to 6 places first so that an exact cent is not pushed up by noise."""
    return math.ceil(round(0.07 * p * (1 - p) * 100, 6)) / 100


def amend_trade(rec, r, look_no, won):
    c = r["cand"][r["best"]]; p = round(c["ask"] + PRICE_THROUGH, 4); f = fee_up(p)
    return {"event": rec["key"] + "#%d" % look_no, "match": rec["key"], "cluster": rec["key"], "day": rec["S"] // 86400, "ts": r["look"], "price": p, "fee": f, "win": bool(won),
            "net": (1 - p - f) if won else (-p - f), "side": r["best"], "gap": c["gap"], "cell": rec["cell"], "look": look_no}


def verdict_amended(n, pf_all, halves):
    """Fixed by the registration: under 100 bets NOT_ENOUGH_DATA; PF under 1.0 overall or in either half FALSIFIED (100 or more bets); PF 1.5+ with both halves above 1.0 'development bar met'; else 'bar not met'."""
    if n < 100: return "NOT_ENOUGH_DATA at n = %d" % n
    big = lambda x: x is None or x > 1.0
    if (pf_all is not None and pf_all < 1.0) or any(h is not None and h < 1.0 for h in halves): return "FALSIFIED"
    if (pf_all is None or pf_all >= 1.5) and all(big(h) for h in halves): return "development bar met"
    return "bar not met"


def _pfs(rows):
    from scorekit import net_of, pf
    nets = [net_of(t) for t in rows]
    return None if not rows else pf(nets)


def _sum(rows):
    nets = [t["net"] for t in rows]; n = len(rows); w = sum(1 for t in rows if t["win"])
    p = _pfs(rows)
    return {"bets": n, "wins": w, "mean_price_paid": None if not n else round(sum(t["price"] for t in rows) / n, 4), "cash_pf": None if p is None else (round(p, 3) if p != float("inf") else "inf"),
            "net_cents_per_contract": None if not n else round(100 * sum(nets) / n, 3)}


def score_rule2(records, candle_folders, cfg, result_fn, heldout_go=False, name="rule"):
    """Order of the read (fixed): step 1 per title and look with NO match result read; step 2 a title/look is OUT on a kill line, and if every one is out the card is closed and result_fn is never called;
    step 3 the rule is scored on the titles/looks that are in. result_fn(rec) -> True if `up` won the match, called ONLY for a bet the rule fires. Development only unless heldout_go."""
    recs = [dict(r) for r in records if heldout_go or cfg.heldout_from is None or r["state_close"] < cfg.heldout_from]
    refused = len(records) - len(recs)
    for r in recs: assert "result_up" not in r
    step1 = measure(recs, candle_folders, cfg)
    inn = {c for c, t in step1["titles"].items() if t["verdict"].startswith("SURVIVES")}
    out = {"held_out_refused": refused, "step1": step1["titles"], "in": sorted(inn), "result_fn_calls": 0, "tries": "2 (one for each look) per Amendment 2 and 3", "freshness": cfg.freshness}
    if not inn:
        out["verdict"] = "CLOSED: every title and look is out on its kill lines; no match result was read"; out["bets"] = 0; return out
    idx = {t: {c["ts"]: c for c in v} for t, v in k.candles(candle_folders).items()}
    trades, cnt = [], {"fired": 0, "no_result": 0, "no_pre": 0, "no_look": 0, "no_signal": 0}
    for rec in recs:
        r = prepare(idx, rec, cfg)
        if r == "no_pre": cnt["no_pre"] += 1; continue
        looks = [(1, rec["cell"], r)] + ([(2, rec["cell"] + SECOND, prepare(idx, rec, cfg, 2))] if rec.get("state_close2") else [])
        for no, key, rr in looks:
            if key not in inn: continue
            if rr["look"] is None: cnt["no_look"] += 1; continue
            c = rr["cand"][rr["best"]]
            if not (c["gap"] >= cfg.edge and c["spread"] <= cfg.spread_max): cnt["no_signal"] += 1; continue
            res = result_fn(rec); out["result_fn_calls"] += 1; cnt["fired"] += 1
            if res is None: cnt["no_result"] += 1; continue
            trades.append(amend_trade(rec, rr, no, res if rr["best"] == "up" else (not res)))
    trades.sort(key=lambda t: (t["ts"], t["event"]))
    out["counts"] = cnt; out["bets"] = len(trades)
    if not trades: out["verdict"] = "NOT_ENOUGH_DATA at n = 0"; return out
    halves = k.windows(trades, 2)
    out["all"] = _sum(trades); out["halves_by_date"] = [_sum(h) for h in halves]
    out["by_look"] = {str(n): _sum([t for t in trades if t["look"] == n]) for n in (1, 2) if any(t["look"] == n for t in trades)}
    out["by_title"] = {c: _sum([t for t in trades if t["cell"] == c]) for c in sorted({t["cell"] for t in trades})}
    byday = {}
    for t in trades: byday[t["day"]] = byday.get(t["day"], 0) + t["net"]
    tot = sum(byday.values()); out["largest_day_share_of_net"] = None if tot <= 0 else round(max(byday.values()) / tot, 3)
    zm = k.cluster_z(trades); zd = k.cluster_z([dict(t, cluster=str(t["day"])) for t in trades])
    zs = [x["z"] for x in (zm, zd) if x["z"] is not None]
    out["z_match_cluster"] = zm; out["z_day_cluster"] = zd; out["z_smaller_used"] = None if len(zs) < 2 else round(min(zs), 3)
    out["z_note"] = "one-sided z (positive = profit), the verdict side uses the smaller of the match-clustered and the day-clustered z; the research bar is z 5.46 on development AND held-out together, which this development read cannot meet alone"
    pfa = _pfs(trades); hp = [_pfs(h) for h in halves]
    out["verdict"] = verdict_amended(len(trades), pfa, hp)
    out["haircut_line"] = {"drop": k.HAIRCUT_DROP, "bets_after_drop": round(len(trades) * (1 - k.HAIRCUT_DROP), 1), "note": "no order book for these markets; price is ask + 1c booked as filled; the haircut table (scorekit) stands in"}
    out["price_source"] = "1 minute candle ask close at the look, two-sided, plus 1c; not a list quote"
    return out


def candle_job(records, cfg, series, job_id, registration, window_start_back=2400, window_end_after=300):
    """Pack records by scheduled start: per record the match and placebo contracts from S - window_start_back to state_close + window_end_after; matches in one request share its window; minutes x tickers <= pack_limit, tickers <= max_tickers."""
    ms = sorted(records, key=lambda m: (m["S"], m["key"])); packs, cur = [], []
    tk = lambda m: list(m["match"].values()) + list(m["placebo"].values())
    def win(g): return (max(max(m["state_close"], m.get("state_close2") or 0) for m in g) + window_end_after) - (min(m["S"] for m in g) - window_start_back)
    for m in ms:
        trial = cur + [m]
        if cur and (win(trial) / 60 * sum(len(tk(x)) for x in trial) > cfg.pack_limit or sum(len(tk(x)) for x in trial) > cfg.max_tickers): packs.append(cur); cur = [m]
        else: cur = trial
    if cur: packs.append(cur)
    reqs = [{"id": "c%04d" % i, "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(t for m in g for t in tk(m)), "start_ts": min(m["S"] for m in g) - window_start_back - 60,
             "end_ts": max(max(m["state_close"], m.get("state_close2") or 0) for m in g) + window_end_after, "period_interval": 1}} for i, g in enumerate(packs)]
    eps = [{"name": "batch_candles", "method": "GET", "path_pattern": "/markets/candlesticks", "params_allowed": ["market_tickers", "start_ts", "end_ts", "period_interval"]}]
    j = tie3.job(job_id, "break-in-play measurement stage 2: one minute candles of the match and placebo contracts of the sampled matches.", eps, reqs, series, [t for m in ms for t in tk(m)])
    j["notes"] = "break-in-play zero-try gap measurement stage 2 (%s)" % job_id
    j["registration"] = registration; return j
