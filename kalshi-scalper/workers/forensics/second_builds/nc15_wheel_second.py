#!/usr/bin/env python3
"""NC15 depth-cell wheel replay, an INDEPENDENT SECOND SCORER (Forensics desk, 2026-11-13, on the Head of R&D's order of 01:49Z). Built from Desk A's frozen definition
sheet v4 ALONE (claude/idea-desk-a at 8679f760, kalshi-scalper/workers/DESK_A_FROZEN_WHEEL_DEFINITIONS_NOV13.md, sha256 c53d2b9f...; sections 0, 2 and 3) and, for the block,
ROTATION_LANE.md v1.2 section 4 on rnd-queue. Desk A's nc15_wheel_replay.py was not read. Nothing here is a read of the registered NC15DEPTH1 cell.

DEFAULT CLOSED: it runs only on a folder that holds the marker file MADE_UP_DATA (invented rows), or with --block-read, which is for a block read the Head has ordered.
Any path in or resolving into a HELDOUT_ folder is refused.

usage: python3 -I nc15_wheel_second.py <NC15 root> --now <ISO time of the read> [--records <out.csv>] [--block-read]
  <NC15 root> is the recorder's shape: <root>/<date>/<HHMM>/{book,coverage}.csv.gz (scripts/record_nc_book.py on main).

Places where the sheet or the lane leaves a choice (READINGS, printed with the output):
 a. A poll is one book row of a ticker. A row with no readable Date header can still be a poll if earlier header-readable rows of its run give it an offset (the sheet's text, and what the first build does; Desk A's note 3 says "never a poll"; set NC15_HEADERLESS_POLL=no for that reading). Rows of a run are ordered by t_recv_ms, then file order. The offset of a poll uses the last 120 header-readable rows of its own run folder with t_recv_ms at or before the poll's (rows of the same instant all count); the median of an even number is the mean of the two middle values. No such row: "no clock", no signal.
 b. A ticker's polls are pooled over every run folder that holds it, each with its own run's offset. The signal poll is the one with the greatest exchange time at or before D and at most 10 s before it (1e-9 tolerance on both edges); on an exact tie, the later by receive time (Desk A's choice 1 says "ties by run path"). The close time is the close_time of the ticker's first row that has a readable one (choice 2).
 c. A level is present if its price and its size both parse as numbers and the size is above zero. A side with no readable top-level price (yes_bid_px_1, no_bid_px_1), or with no level at all, is "a missing side": no signal. The band test's ask is 1 minus the met side's top-level price (Desk A's choices 4 and 5).
 d. "In the cell" is |imb5| at or above 0.50 with the 1e-9 tolerance; imb5 above zero buys YES, below zero buys NO.
 e. The second poll is the ticker's next poll by receive time IN THE SAME RUN FOLDER as the signal poll (Desk A's choice 1; this build first took the next poll over all run folders). Its distance from the signal poll is measured on EXCHANGE time, each poll with its own offset (what the first build does; this build first used the recorder's clock, t_recv_ms; set NC15_SECOND_CLOCK=recorder for that reading), at most 6 s with the 1e-9 tolerance; later, or no later poll in that run: "not fill-checked".
 f. The ladder is the met side's present levels as asks (1 minus the bid price), cheapest first. "Offers 10" is the sizes at or under limit + 1e-9 summing to 10 - 1e-9 or more. The walked price takes the first 10 contracts of the levels at or under the limit.
 g. A decision instant before the sheet's commit time (2026-11-13T00:23:49Z) does not count; a close after 2026-12-31T23:59:59Z is past the log's stop. Both are counted and left out.
 h. Result: a coverage row's result of yes or no, from any run folder that holds the ticker (two runs that disagree stop this build's run; Desk A's choice 6 takes the first found). Any other non-empty value is a void. An empty result is OPEN until 7 days after the close (by --now), then a void. A void is a fee-only loss, counted.
 i. A day is the US Central calendar date of the decision instant.
 j. Blocks, per place, over its fillable signals in order of decision instant: a block is the next 60; while it holds fewer than 10 wins or fewer than 10 losses it grows one signal at a time (a void is neither). It is READ only when every signal in it has a final value; a block holding an open signal WAITS, and so does everything after it.
 k. A block FAILS if its first and last decision are more than 21 days apart, if it has fewer than 7 different days, if one day holds more than 30 percent of a positive block net, if its cash profit factor is under 1.3, or if either half (the first n // 2 signals and the rest) is under 1.0. Otherwise it CLEARS. No sliding and no re-read: the next block starts at the first signal after it.
 l. After a cleared block the next 30 fillable signals are its confirmation (profit factor 1.0 or better: QUALIFIED); they belong to no block. The next block starts after them.
 m. Profit factor: wins over losses in dollars; no losses is infinite and passes; no wins is zero. Every bar is tested with a 1e-9 tolerance on the float figure, and the figure in exact tenths of a cent is printed beside any figure within 0.001 of its bar.
 n. Only the seven series the sheet keeps (copper, WTI, natural gas, HYPE, BNB, silver, USD/CAD) are places; the four withdrawn series are counted and not scored.
"""
import sys, os, csv, gzip, math, bisect, statistics, collections
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

CT = ZoneInfo("America/Chicago")
def iso(s): return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()
PLACES = ["KXCOPPER15M", "KXWTI15M", "KXNATGAS15M", "KXHYPE15M", "KXBNB15M", "KXSILVER15M", "KXUSDCAD15M"]
WITHDRAWN = ["KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXAUDUSD15M"]
COUNT_FROM = iso("2026-11-13T00:23:49Z"); STOP = iso("2026-12-31T23:59:59Z")
SECOND_CLOCK = os.environ.get("NC15_SECOND_CLOCK", "exchange")      # "exchange": the 6 s to the second poll are measured on exchange time (each poll's own offset); "recorder": on t_recv_ms
HEADERLESS_POLL = os.environ.get("NC15_HEADERLESS_POLL", "yes") == "yes"   # "yes": a row with no readable Date header can be a poll if earlier rows of its run give an offset (the sheet's text); "no": it is never a poll
SIZE = 10; SLIP = 0.01; CELL = 0.50; BAND = (0.10, 0.90); LOOK = 600.0; EARLY = 10.0; SECOND_MAX = 6.0; OFFSET_ROWS = 120; VOID_DAYS = 7
BLOCK = 60; RARE = 10; SPAN_DAYS = 21; MIN_DAYS = 7; DAY_SHARE = 0.30; PF_BLOCK = 1.3; PF_HALF = 1.0; CONFIRM = 30; PF_CONFIRM = 1.0
EPS = 1e-9
READINGS = [l.strip() for l in __doc__.split("READINGS, printed with the output):")[1].strip().split("\n")]


def refuse_heldout(path):
    for p in (os.path.abspath(path), os.path.realpath(path)):
        if any(part.upper().startswith("HELDOUT_") for part in p.split(os.sep)):
            raise SystemExit("REFUSED: %s is in or resolves into a HELDOUT_ folder (standing rule (h))" % path)


def num(v):
    try:
        x = float(v)
        return x if x == x else None
    except (TypeError, ValueError): return None


def fee_up_order(p, contracts=SIZE): return math.ceil(0.07 * contracts * p * (1 - p) * 100 - EPS) / 100.0


def levels(row, side):
    out = []
    for i in range(1, 6):
        p, s = num(row.get("%s_bid_px_%d" % (side, i))), num(row.get("%s_bid_sz_%d" % (side, i)))
        if p is not None and s is not None and s > 0: out.append((p, s))
    return out


def ladder(row, side_bought):
    """the asks the order meets, cheapest first: a YES buy meets the NO bids"""
    return sorted((1 - p, s) for p, s in levels(row, "no" if side_bought == "yes" else "yes"))


def offered(lad, limit): return sum(s for a, s in lad if a <= limit + EPS)


def walked(lad, limit):
    left = float(SIZE); cost = 0.0
    for a, s in lad:
        if a > limit + EPS or left <= EPS: break
        take = min(s, left); cost += take * a; left -= take
    return cost / SIZE


def read_root(root):
    refuse_heldout(root)
    runs = []; cover = {}
    for date in sorted(os.listdir(root)):
        dd = os.path.join(root, date)
        if not os.path.isdir(dd): continue
        for hhmm in sorted(os.listdir(dd)):
            run = os.path.join(dd, hhmm); refuse_heldout(run)
            if not os.path.isdir(run): continue
            bp, cp = os.path.join(run, "book.csv.gz"), os.path.join(run, "coverage.csv.gz")
            rows = []
            if os.path.exists(bp):
                with gzip.open(bp, "rt", newline="") as f:
                    for k, r in enumerate(csv.DictReader(f)):
                        try: r["_recv"] = int(r["t_recv_ms"])
                        except (TypeError, ValueError, KeyError): continue
                        r["_k"] = k; r["_hdr"] = False; rows.append(r)
            rows.sort(key=lambda r: (r["_recv"], r["_k"]))
            hr, hv = [], []
            for r in rows:
                try: h = parsedate_to_datetime(r.get("server_date_header") or "").timestamp()
                except (TypeError, ValueError, IndexError): continue
                r["_hdr"] = True; hr.append(r["_recv"]); hv.append(h + 0.5 - r["_recv"] / 1000.0)
            runs.append({"path": run, "rows": rows, "hr": hr, "hv": hv})
            if os.path.exists(cp):
                with gzip.open(cp, "rt", newline="") as f:
                    for r in csv.DictReader(f):
                        res = (r.get("result") or "").strip().lower(); tk = r.get("ticker")
                        if not tk: continue
                        old = cover.get(tk)
                        if res in ("yes", "no"):
                            if old in ("yes", "no") and old != res: raise SystemExit("REFUSED: two run folders give %s different results" % tk)
                            cover[tk] = res
                        elif old in (None, ""): cover[tk] = res                 # an empty result, or a final value that is neither yes nor no; a yes or no from another run folder wins over either
    return runs, cover


def offset_of(run, recv):
    i = bisect.bisect_right(run["hr"], recv); v = run["hv"][max(0, i - OFFSET_ROWS):i]
    return statistics.median(v) if v else None


def measure(root, now, made_up=False, block_read=False):
    if not (made_up and os.path.exists(os.path.join(root, "MADE_UP_DATA"))) and not block_read:
        raise SystemExit("REFUSED: this scorer runs on a folder of invented rows (marker file MADE_UP_DATA) or, on real NC15 rows, only at a block read the Head has ordered (--block-read)")
    runs, cover = read_root(root)
    polls = collections.defaultdict(list)                                      # ticker -> [(recv, run index, row)]
    for i, run in enumerate(runs):
        for r in run["rows"]:
            if (r.get("series") in PLACES or r.get("series") in WITHDRAWN) and (r["_hdr"] or HEADERLESS_POLL): polls[r["ticker"]].append((r["_recv"], i, r))
    recs = []; C = {s: collections.Counter() for s in PLACES + WITHDRAWN}
    for tk in sorted(polls):
        ps = sorted(polls[tk], key=lambda x: (x[0], x[1], x[2]["_k"])); series = ps[0][2]["series"]; c = C[series]; T = None
        for _, _, r0 in ps:
            try: T = iso(r0["close_time"]); break
            except (ValueError, TypeError): continue
        if T is None: c["no readable close time"] += 1; continue
        D = T - LOOK; c["windows"] += 1
        rec = {"series": series, "ticker": tk, "close": T, "D": D, "status": None}
        if series in WITHDRAWN: c["withdrawn series, not scored"] += 1; continue
        if D < COUNT_FROM: c["decision before the sheet's commit time, not counted"] += 1; continue
        if T > STOP: c["close after the log's stop, not counted"] += 1; continue
        best = None; no_clock = 0
        for j, (recv, ri, r) in enumerate(ps):
            if abs(recv / 1000.0 - D) > 120: continue
            off = offset_of(runs[ri], recv)
            if off is None: no_clock += 1; continue
            ex = recv / 1000.0 + off
            if D - EARLY - EPS <= ex <= D + EPS and (best is None or (ex, recv) >= (best[0], best[1])): best = (ex, recv, j, off)
        if best is None:
            rec["status"] = "no signal: no clock" if no_clock else "no signal: no poll in the window"; c[rec["status"]] += 1; recs.append(rec); continue
        ex, recv, j, off = best; r = ps[j][2]; rec.update(signal_recv_ms=recv, signal_exchange=ex, offset=off)
        y, n = levels(r, "yes"), levels(r, "no"); top = {"yes": num(r.get("yes_bid_px_1")), "no": num(r.get("no_bid_px_1"))}
        if not y or not n or top["yes"] is None or top["no"] is None: rec["status"] = "no signal: a missing side of the book"; c[rec["status"]] += 1; recs.append(rec); continue
        sy, sn = sum(s for _, s in y), sum(s for _, s in n); imb = (sy - sn) / (sy + sn); rec["imb5"] = imb
        if abs(imb) < CELL - EPS: rec["status"] = "not in the cell"; c[rec["status"]] += 1; recs.append(rec); continue
        c["in the cell"] += 1; side = "yes" if imb > 0 else "no"; ask = 1 - top["no" if side == "yes" else "yes"]; rec.update(side=side, ask=ask)
        if not (BAND[0] - EPS <= ask <= BAND[1] + EPS): rec["status"] = "in the cell, ask outside 0.10 to 0.90"; c[rec["status"]] += 1; recs.append(rec); continue
        c["entering"] += 1; limit = ask + SLIP; rec["limit"] = limit
        j2 = next((k for k in range(j + 1, len(ps)) if ps[k][1] == ps[j][1]), None)       # the next poll of the ticker in the SAME run folder
        gap = None
        if j2 is not None:
            gap = (ps[j2][0] - recv) / 1000.0
            if SECOND_CLOCK == "exchange":
                off2 = offset_of(runs[ps[j2][1]], ps[j2][0]); gap = None if off2 is None else gap + off2 - off
        if gap is None or gap > SECOND_MAX + EPS:
            rec["status"] = "not fill-checked"; rec["second_gap_s"] = gap; c[rec["status"]] += 1; recs.append(rec); continue
        r2 = ps[j2][2]; rec.update(second_recv_ms=ps[j2][0], second_gap_s=gap)
        l1, l2 = ladder(r, side), ladder(r2, side); o1, o2 = offered(l1, limit), offered(l2, limit); rec.update(offered_signal=o1, offered_second=o2)
        if o1 < SIZE - EPS or o2 < SIZE - EPS:
            rec["status"] = "miss"; rec["miss_at"] = "both" if (o1 < SIZE - EPS and o2 < SIZE - EPS) else ("signal poll" if o1 < SIZE - EPS else "second poll"); c["miss"] += 1; recs.append(rec); continue
        w1, w2 = walked(l1, limit), walked(l2, limit); p = max(w1, w2); fee = fee_up_order(p); rec.update(walk_signal=w1, walk_second=w2, fill=p, fee=fee)
        res = cover.get(tk, "") or ""; c["fillable"] += 1
        if res in ("yes", "no"): rec.update(result=res, win=(res == side), cash=SIZE * ((1.0 if res == side else 0.0) - p) - fee, status="fillable, scored")
        elif res != "" or now >= T + VOID_DAYS * 86400: rec.update(result=res or "(none after 7 days)", win=None, cash=-fee, status="fillable, void"); c["fillable, booked as a void"] += 1
        else: rec.update(result="", win=None, cash=None, status="fillable, open")
        if rec["status"] == "fillable, open": c["fillable, result still open"] += 1
        recs.append(rec)
    out = {"build": "Forensics second scorer of the NC15 depth-cell wheel replay", "sheet": "DESK_A_FROZEN_WHEEL_DEFINITIONS_NOV13.md v4 (8679f760, sha256 c53d2b9f...)", "now": now,
           "counts": {s: dict(C[s]) for s in PLACES + WITHDRAWN}, "readings": READINGS, "places": {}}
    for s in PLACES:
        sig = sorted((r for r in recs if r["series"] == s and r["status"].startswith("fillable")), key=lambda r: (r["D"], r["ticker"]))
        out["places"][s] = blocks(sig)
    return out, recs


def pf(v):
    w = sum(x for x in v if x > EPS); l = -sum(x for x in v if x < -EPS)
    return None if (w == 0 and l == 0) else (float("inf") if l == 0 else w / l)


def pf_exact(v):
    """the same in whole tenths of a cent: (wins, losses) as integers"""
    t = [int(round(x * 1000)) for x in v]; return sum(x for x in t if x > 0), -sum(x for x in t if x < 0)


def ge(x, bar): return x is not None and x >= bar - EPS


def blocks(sig):
    res = {"fillable": len(sig), "blocks": [], "state": None}; i = 0
    day = lambda r: datetime.fromtimestamp(r["D"], CT).date().isoformat()
    while True:
        n = BLOCK
        if i + n > len(sig): res["state"] = "block in progress: %d of 60 fillable signals" % (len(sig) - i); break
        def rare(k): b = sig[i:i + k]; return min(sum(1 for r in b if r["win"] is True), sum(1 for r in b if r["win"] is False))
        waiting = False
        while True:
            b = sig[i:i + n]
            if any(r["cash"] is None for r in b): waiting = True; break
            if rare(n) >= RARE: break
            if i + n >= len(sig): break
            n += 1
        b = sig[i:i + n]
        if waiting: res["state"] = "block of %d WAITS: it holds a signal whose result is still open" % n; break
        if rare(n) < RARE: res["state"] = "block in progress: %d signals, still under 10 of the rarer outcome" % n; break
        v = [r["cash"] for r in b]; net = sum(v); h = n // 2; days = collections.defaultdict(float)
        for r in b: days[day(r)] += r["cash"]
        top = max(days.values()); P, P1, P2 = pf(v), pf(v[:h]), pf(v[h:]); span = (b[-1]["D"] - b[0]["D"]) / 86400.0
        fails = []
        if span > SPAN_DAYS + EPS: fails.append("spans %.1f days, over 21" % span)
        if len(days) < MIN_DAYS: fails.append("%d different days, under 7" % len(days))
        if net > EPS and top > DAY_SHARE * net + EPS: fails.append("one day holds %.0f%% of the net, over 30%%" % (100 * top / net))
        if not ge(P, PF_BLOCK): fails.append("profit factor under 1.3")
        if not ge(P1, PF_HALF) or not ge(P2, PF_HALF): fails.append("a half under 1.0")
        blk = {"first": b[0]["ticker"], "last": b[-1]["ticker"], "n": n, "wins": sum(1 for r in b if r["win"] is True), "losses": sum(1 for r in b if r["win"] is False), "voids": sum(1 for r in b if r["win"] is None),
               "net": net, "pf": P, "pf_first_half": P1, "pf_second_half": P2, "pf_exact_tenths_of_a_cent": pf_exact(v), "days": len(days), "span_days": span, "top_day_share_of_net": (top / net) if net > EPS else None,
               "verdict": "CLEARED" if not fails else "FAILED", "fails": fails}
        i += n
        if not fails:
            cf = sig[i:i + CONFIRM]
            if len(cf) < CONFIRM: blk["confirmation"] = "in progress: %d of 30" % len(cf); res["blocks"].append(blk); res["state"] = "cleared block, confirmation in progress"; break
            if any(r["cash"] is None for r in cf): blk["confirmation"] = "WAITS: a result is still open"; res["blocks"].append(blk); res["state"] = "cleared block, confirmation waits"; break
            cp = pf([r["cash"] for r in cf]); blk["confirmation_pf"] = cp; blk["confirmation"] = "QUALIFIED" if ge(cp, PF_CONFIRM) else "confirmation failed"; i += CONFIRM
        res["blocks"].append(blk)
    return res


REC_COLS = ["series", "ticker", "close", "D", "status", "signal_recv_ms", "signal_exchange", "offset", "imb5", "side", "ask", "limit", "second_recv_ms", "second_gap_s", "offered_signal", "offered_second", "miss_at",
            "walk_signal", "walk_second", "fill", "fee", "result", "win", "cash"]


def lines(out):
    f = lambda x, d=2: "n/a" if x is None else ("inf" if x == float("inf") else ("%." + str(d) + "f") % x)
    L = ["NC15 depth-cell wheel replay, second scorer | sheet v4 (8679f760) | read at %s" % datetime.fromtimestamp(out["now"], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")]
    order = ["windows", "decision before the sheet's commit time, not counted", "close after the log's stop, not counted", "no signal: no poll in the window", "no signal: no clock", "no signal: a missing side of the book",
             "not in the cell", "in the cell", "in the cell, ask outside 0.10 to 0.90", "entering", "not fill-checked", "miss", "fillable", "fillable, booked as a void", "fillable, result still open"]
    for s in PLACES:
        c = out["counts"][s]; L.append("%s COUNTS: " % s + "; ".join("%s %d" % (k, c.get(k, 0)) for k in order))
        p = out["places"][s]
        for k, b in enumerate(p["blocks"], 1):
            near = any(x is not None and x != float("inf") and abs(x - bar) < 0.001 for x, bar in ((b["pf"], PF_BLOCK), (b["pf_first_half"], PF_HALF), (b["pf_second_half"], PF_HALF)))
            L.append("%s BLOCK %d: %s | n %d (%s to %s) wins %d losses %d voids %d | net %s PF %s halves %s / %s | days %d span %s top day %s%s%s%s" % (
                s, k, b["verdict"], b["n"], b["first"], b["last"], b["wins"], b["losses"], b["voids"], f(b["net"]), f(b["pf"]), f(b["pf_first_half"]), f(b["pf_second_half"]), b["days"], f(b["span_days"], 1),
                "n/a" if b["top_day_share_of_net"] is None else "%.0f%%" % (100 * b["top_day_share_of_net"]), (" | fails: " + "; ".join(b["fails"])) if b["fails"] else "",
                (" | confirmation: %s%s" % (b["confirmation"], "" if "confirmation_pf" not in b else " (PF %s)" % f(b["confirmation_pf"]))) if "confirmation" in b else "",
                (" | exact tenths of a cent: wins %d, losses %d" % b["pf_exact_tenths_of_a_cent"]) if near else ""))
        L.append("%s STATE: %s (fillable signals %d, blocks read %d)" % (s, p["state"], p["fillable"], len(p["blocks"])))
    for s in WITHDRAWN: L.append("%s: withdrawn, %d windows counted and not scored" % (s, out["counts"][s].get("windows", 0)))
    return L


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 3 or "--now" not in a: raise SystemExit(__doc__)
    import json
    root = a[0]; now = iso(a[a.index("--now") + 1])
    out, recs = measure(root, now, made_up=True, block_read="--block-read" in a)
    if "--records" in a:
        with open(a[a.index("--records") + 1], "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(REC_COLS)
            for r in recs: w.writerow([("" if r.get(k) is None else (("%.6f" % r[k]) if isinstance(r.get(k), float) else r[k])) for k in REC_COLS])
    print("\n".join(lines(out))); print(json.dumps(out, indent=1, default=str))
