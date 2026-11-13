"""POLAPPR1 second build (History Miner, Nov 13, 2026). Written from Refinement's registration text only
(kalshi-scalper/refine_tools/POLITICS_APPROVAL_CAL_REGISTRATION.md at 99a52f44 on claude/refine-live, with clarifications 1 and 2)
and the made-up input layout (d5a89e1a). polappr1_convert.py, polappr1_score.py, test_polappr1.py and every output were NOT read.

Input: the converted table (cand_all.jsonl, one market a line) and the two cut files. HELD-OUT rows are dropped at load, before any
price is touched, and only counted. Labels follow Amendment 3: a cell under 100 pooled TRAIN plus VALIDATE events prints no PF, mean
or z unless --compare is given (made-up data only, for comparing two builds).

Usage: python3 -I polappr1b.py <cand_all.jsonl> <POL_APPR1_CUTS.json> <POL_APPR1_CUTS_A3.json> <out.json> [--compare]"""
import json, math, random, sys

EPS = 1e-9
FAMILY = {
    "KXTRUMPAPPROVE": "APPR_DAILY", "KXAPRPOTUS": "APPR_RCP", "KX538APPROVE": "APPR_538",
    "KXVOTEHUBTRUMPUPDOWN": "APPR_OTHER", "KXTRUMPVH": "APPR_OTHER", "KXTRUMPAPPROVALBELOW": "APPR_OTHER",
    "KXNYTTRUMPAPPROVAL": "APPR_OTHER", "KXVOTEHUBVANCEAPPROVE": "APPR_OTHER", "KXVHAPRPOTUS": "APPR_OTHER",
    "KXTRUMPAPPROVALYEAR": "APPR_OTHER",
    "KXVHGCB": "GCB", "KXGENERICBALLOTVOTEHUB": "GCB", "KXGENERICBALLOT": "GCB",
}
APPROVAL = ("APPR_DAILY", "APPR_RCP", "APPR_538", "APPR_OTHER")
FAMILIES = APPROVAL + ("GCB", "ALL_APPR")
LOOKS = [("7d", 7 * 86400, 6 * 3600), ("3d", 3 * 86400, 6 * 3600), ("1d", 86400, 3 * 3600), ("6h", 6 * 3600, 3 * 3600)]
BUCKETS = [(0.10, 0.25), (0.25, 0.40), (0.40, 0.60), (0.60, 0.75), (0.75, 0.90)]
B, SEED = 2000, 1
READINGS = [
    "A6 (Amendment 6, ff415eb7): G1 a YES mid exists only when 0 < bid < ask < 1, a market without one makes no observation either side and is not a candidate, events with no valid-mid market per look are printed, calibration only over valid-mid markets; G2 cap of 10 open, fills offered by entry quote time then ticker, the 11th skipped and counted, net, streak and kill over accepted fills in close order; G3 an event held out in any family is in no cell of any family and not in calibration",
    "R1 family by the row's series s; KXGENERICBALLOT (named under GCB, one event) is GCB; a series outside the list (e.g. KXAPRPOTUSD, pulled by Amendment 3 but in no family) is counted and left out",
    "R2 event close = latest ct among its markets in the file; third = the listed third if the event is in the family's cut-file list, else by its close against the family's cut constants",
    "R3 ALL_APPR = the four approval families pooled; its third uses ALL_APPR's own cuts (and its own list)",
    "R4 quote = the last candle with end_ts <= close - look and end_ts >= close - look - tolerance (6h for 7d and 3d, 3h for 1d and 6h); close is the market's own ct; no candle in that range = not open = no observation",
    "R5 a YES quote needs 0 < yes_ask < 1, a NO quote needs 0 < yes_bid < 1 (0.00 bid and 1.00 ask are no side, clarification 2); a null or empty string is no quote",
    "R6 bought price p: YES = yes_ask, NO = 1 - yes_bid; kept if 0.10 <= p <= 0.90 (1e-9); bucket half-open except the last, closed at 0.90",
    "R7 one observation per event per cell: the market whose yes mid (yes_ask + yes_bid)/2 at the quote is nearest 0.50; mid needs both strings present; ties by ticker",
    "R8 per contract: win = (1 - p) - fee - slip, loss = -p - fee - slip, fee = 0.07 p (1 - p) unrounded, slip 0.01 (+1c) or 0 (+0c); PF = gross gain / gross loss (no loss: 'inf'); mean in cents",
    "R9 bootstrap: VALIDATE, +1c mean cents, B 2000, random.Random(1), resample observations with replacement, limits = sorted means at int(0.05B) and int(0.95B); week-block form by ISO week of the event close, as many blocks as distinct, first-seen order",
    "R10 as if live: TRAIN+VALIDATE fills ordered by market close then ticker, 3 contracts, p as R6, slip 0.01 a contract, fee per order ceil to the cent of 0.07*3*p*(1-p); kill = net under -15 dollars at any fill from the 20th on, or 5 losses in a row; open interval = quote end_ts to market close; max simultaneously open counted; net_after_20_dollars is the net over ALL fills once there are 20 or more, net_at_fill_20_dollars the net at the 20th; kill_first_fill is the fill at which the kill first fires",
    "R11 calibration: approval families, TRAIN and VALIDATE events, every market with a valid YES ask in 0.10..0.90 at the look, bucket of the YES ask; realized YES share, mean ask, mean mid (where both sides present), n",
    "R12 pooled n = TRAIN events + VALIDATE events in the cell; under 100: 'no evidence at n = x (TRAIN a, VALID b)' and no PF, mean or z",
]


def f(x):
    if x is None or x == "":
        return None
    return float(x)


def third_of(fam, ev, close, cuts, lists):
    if ev in lists.get(fam, {}):
        return lists[fam][ev]
    c1, c2 = cuts[fam]
    return "TRAIN" if close < c1 else ("VALIDATE" if close < c2 else "HELD-OUT")


def quote(c, ct, look, tol):
    hi, lo = ct - look, ct - look - tol
    best = None
    for row in c:
        if lo <= row[0] <= hi and (best is None or row[0] > best[0]):
            best = row
    return best


def pnl(p, won, slip):
    fee = 0.07 * p * (1 - p)
    return ((1 - p) if won else -p) - fee - slip


def pf(xs):
    g = sum(x for x in xs if x > 0)
    l = -sum(x for x in xs if x < 0)
    return "inf" if l == 0 else round(g / l, 6)


def boot(xs, blocks=None):
    if not xs:
        return None
    r = random.Random(SEED)
    means = []
    if blocks is None:
        n = len(xs)
        for _ in range(B):
            s = [xs[r.randrange(n)] for _ in range(n)]
            means.append(sum(s) / n)
    else:
        order, by = [], {}
        for x, b in zip(xs, blocks):
            if b not in by:
                order.append(b)
                by[b] = []
            by[b].append(x)
        k = len(order)
        for _ in range(B):
            s = []
            for _ in range(k):
                s.extend(by[order[r.randrange(k)]])
            means.append(sum(s) / len(s))
    means.sort()
    return [round(means[int(0.05 * B)] * 100, 6), round(means[int(0.95 * B)] * 100, 6)]


def isoweek(ts):
    import datetime
    y, w, _ = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).isocalendar()
    return "%d-W%02d" % (y, w)


def run(cand, cutf, cutf3, compare):
    cj, c3 = json.load(open(cutf)), json.load(open(cutf3))
    cuts = dict(cj["cuts"]); cuts.update(c3["cuts"])
    lists = {}
    for d in (cj, c3):
        for fam, evs in d["events"].items():
            lists.setdefault(fam, {}).update({x["event"]: x["third"] for x in evs})
    rows = [json.loads(l) for l in open(cand) if l.strip()]
    no_family = sorted({r["s"] for r in rows if r["s"] not in FAMILY})
    by_ev = {}
    for r in rows:
        if r["s"] in FAMILY:
            by_ev.setdefault(r["e"], []).append(r)
    counts = {"rows": len(rows), "rows_no_family": sum(1 for r in rows if r["s"] not in FAMILY), "series_no_family": no_family,
              "unlisted_not_scored_events": {s: len({r["e"] for r in rows if r["s"] == s}) for s in no_family}}
    # thirds per (family incl. ALL_APPR, event); held-out events are dropped here, before any price is read
    evinfo = {}
    held_any = 0
    no_valid_mid = {lk: 0 for lk, _, _ in LOOKS}
    third_counts = {fm: {"TRAIN": 0, "VALIDATE": 0, "HELD-OUT": 0} for fm in FAMILIES}
    for ev, mks in by_ev.items():
        fam = FAMILY[mks[0]["s"]]
        if any(FAMILY[m["s"]] != fam for m in mks):
            raise SystemExit("event %s spans families" % ev)
        close = max(m["ct"] for m in mks)
        fams = [fam] + (["ALL_APPR"] if fam in APPROVAL else [])
        ths = {fm: third_of(fm, ev, close, cuts, lists) for fm in fams}
        for fm, th in ths.items():
            third_counts[fm][th] += 1
        if any(th == "HELD-OUT" for th in ths.values()):
            held_any += 1                     # Amendment 6 G3: held out in ANY family it belongs to = in no cell of any family
            continue
        evinfo[ev] = {fm: (th, close) for fm, th in ths.items()}
    cells = {}
    calib = {}
    live_fills = {}
    for ev, fmth in sorted(evinfo.items()):
        mks = sorted(by_ev[ev], key=lambda m: m["t"])
        for lk, look, tol in LOOKS:
            cand_obs = {}
            any_valid = False
            for m in mks:
                q = quote(m["c"], m["ct"], look, tol)
                if q is None:
                    continue
                ask, bid = f(q[1]), f(q[2])
                if ask is None or bid is None or not (0 < bid < ask < 1):
                    continue                      # Amendment 6 G1: no valid YES mid, so no observation either side and not a candidate
                any_valid = True
                mid = (ask + bid) / 2
                for side in ("YES", "NO"):
                    if side == "YES":
                        if ask is None or not (0 < ask < 1):
                            continue
                        p = ask
                    else:
                        if bid is None or not (0 < bid < 1):
                            continue
                        p = 1 - bid
                    if not (0.10 - EPS <= p <= 0.90 + EPS):
                        continue
                    bi = next(i for i, (a, b) in enumerate(BUCKETS) if (a - EPS <= p < b - EPS) or (i == 4 and p <= b + EPS))
                    won = (m["res"] == "yes") if side == "YES" else (m["res"] == "no")
                    key = (bi, side)
                    dist = abs(mid - 0.5)
                    cur = cand_obs.get(key)
                    if cur is None or dist < cur[0] - EPS:
                        cand_obs[key] = (dist, m["t"], p, won, q[0], m["ct"])
                if FAMILY[m["s"]] in APPROVAL and ask is not None and 0 < ask < 1 and 0.10 - EPS <= ask <= 0.90 + EPS:
                    bi = next(i for i, (a, b) in enumerate(BUCKETS) if (a - EPS <= ask < b - EPS) or (i == 4 and ask <= b + EPS))
                    cb = calib.setdefault("%s|%s" % (lk, bi), {"n": 0, "yes": 0, "ask": 0.0, "mid_n": 0, "mid": 0.0})
                    cb["n"] += 1; cb["yes"] += m["res"] == "yes"; cb["ask"] += ask
                    cb["mid_n"] += 1; cb["mid"] += mid
            if not any_valid:
                no_valid_mid[lk] += 1
            for (bi, side), (_, t, p, won, qts, ct) in cand_obs.items():
                for fm, (th, close) in fmth.items():
                    k = (fm, lk, bi, side)
                    c = cells.setdefault(k, {"TRAIN": [], "VALIDATE": []})
                    c[th].append({"t": t, "p": p, "won": won, "q": qts, "ct": ct, "wk": isoweek(close)})
    out = []
    for (fm, lk, bi, side), c in sorted(cells.items(), key=lambda kv: (FAMILIES.index(kv[0][0]), kv[0][1:])):
        nt, nv = len(c["TRAIN"]), len(c["VALIDATE"])
        row = {"family": fm, "look": lk, "bucket": "%.2f-%.2f" % BUCKETS[bi], "side": side, "n_train": nt, "n_validate": nv}
        pooled = nt + nv
        if pooled < 100:
            row["label"] = "no evidence at n = %d (TRAIN %d, VALID %d)" % (pooled, nt, nv)
        show = pooled >= 100 or compare
        if show:
            for th in ("TRAIN", "VALIDATE"):
                for sl, tag in ((0.01, "p1"), (0.0, "p0")):
                    xs = [pnl(o["p"], o["won"], sl) for o in c[th]]
                    row["%s_pf_%s" % (th.lower(), tag)] = pf(xs) if xs else None
                    row["%s_mean_c_%s" % (th.lower(), tag)] = round(100 * sum(xs) / len(xs), 6) if xs else None
            vx = [pnl(o["p"], o["won"], 0.01) for o in c["VALIDATE"]]
            row["validate_boot90_c"] = boot(vx)
            row["validate_weekblock90_c"] = boot(vx, [o["wk"] for o in c["VALIDATE"]])
            # Amendment 6 G2: the cap of 10 open (entry quote time to close), fills offered by entry quote time, ties by ticker
            accepted, skipped = [], 0
            for o in sorted(c["TRAIN"] + c["VALIDATE"], key=lambda o: (o["q"], o["t"])):
                if sum(1 for x in accepted if x["q"] <= o["q"] < x["ct"]) >= 10:
                    skipped += 1
                else:
                    accepted.append(o)
            fills = sorted(accepted, key=lambda o: (o["ct"], o["t"]))
            net, streak, longest, fired, open_max = 0.0, 0, 0, False, 0
            net20, first_kill = None, None
            for i, o in enumerate(fills):
                fee = math.ceil(100 * 0.07 * 3 * o["p"] * (1 - o["p"]) - 1e-9) / 100
                net += 3 * pnl(o["p"], o["won"], 0.01) + 3 * 0.07 * o["p"] * (1 - o["p"]) - fee
                streak = 0 if o["won"] else streak + 1
                longest = max(longest, streak)
                if i == 19:
                    net20 = net
                if ((i >= 19 and net < -15 - EPS) or streak >= 5) and not fired:
                    fired, first_kill = True, i + 1
                open_max = max(open_max, sum(1 for x in fills if x["q"] <= o["q"] < x["ct"]))
            row["as_if_live"] = {"fills": len(fills), "net_after_20_dollars": round(net, 6) if len(fills) >= 20 else None,
                                 "longest_loss_streak": longest, "kill_fired": fired, "kill_first_fill": first_kill,
                                 "net_at_fill_20_dollars": round(net20, 6) if net20 is not None else None, "max_open": open_max, "skipped_by_cap": skipped}
        out.append(row)
    cal = []
    for k, v in sorted(calib.items()):
        lk, bi = k.split("|")
        cal.append({"look": lk, "bucket": "%.2f-%.2f" % BUCKETS[int(bi)], "n": v["n"], "yes_share": round(v["yes"] / v["n"], 6),
                    "mean_ask": round(v["ask"] / v["n"], 6), "mean_mid": round(v["mid"] / v["mid_n"], 6) if v["mid_n"] else None})
    return {"build": "History Miner second build, registration text only", "compare_mode": compare, "counts": counts,
            "event_thirds": third_counts, "events_held_out_in_any_family": held_any, "events_no_valid_mid_by_look": no_valid_mid, "cells": out, "calibration": cal, "readings": READINGS}


if __name__ == "__main__":
    a = sys.argv
    res = run(a[1], a[2], a[3], "--compare" in a)
    with open(a[4], "w") as fo:
        json.dump(res, fo, indent=1, sort_keys=True); fo.write("\n")
    print(json.dumps(res["event_thirds"]), len(res["cells"]))
