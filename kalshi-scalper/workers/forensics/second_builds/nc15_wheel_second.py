#!/usr/bin/env python3
"""NC15 depth-cell wheel replay, an INDEPENDENT SECOND SCORER (Forensics desk, 2026-11-13, on the Head of R&D's order of 01:49Z). Built from Desk A's frozen definition
sheet v4 ALONE (claude/idea-desk-a at 8679f760, kalshi-scalper/workers/DESK_A_FROZEN_WHEEL_DEFINITIONS_NOV13.md, sha256 c53d2b9f...; sections 0, 2 and 3) and, for the block,
ROTATION_LANE.md v1.2 section 4 on rnd-queue. Desk A's nc15_wheel_replay.py was not read. Nothing here is a read of the registered NC15DEPTH1 cell.

DEFAULT CLOSED: it runs only on a folder that holds the marker file MADE_UP_DATA (invented rows), or with --block-read, which is for a block read the Head has ordered.
Any path in or resolving into a HELDOUT_ folder is refused.

usage: python3 -I nc15_wheel_second.py <NC15 root> --now <ISO time of the read> [--start <ISO start time, default 2026-11-13T02:40:00Z>] [--records <out.csv>] [--block-read]
  <NC15 root> is the recorder's shape: <root>/<date>/<HHMM>/{book,coverage}.csv.gz (scripts/record_nc_book.py on main).

Places where the sheet or the lane leaves a choice (READINGS, printed with the output):
 a. A poll is one book row of a ticker. A row with no readable Date header can still be a poll if earlier header-readable rows of its run give it an offset (item (u)). Rows of a run are ordered by t_recv_ms, then file order. The offset of a poll uses the last 120 header-readable rows of its own run folder UP TO AND INCLUDING THE POLL'S OWN ROW in that order (the Head's ruling, lane item (u): row by row, the frozen scorer's reading; so two rows received at the same instant can have slightly different offsets; this build first gave every row of an instant the same offset; that reading is not used); the median of an even number is the mean of the two middle values. No such row: "no clock", no signal.
 b. A ticker's polls are pooled over every run folder that holds it, each with its own run's offset. The signal poll is the one with the greatest exchange time at or before D and at most 10 s before it (1e-9 tolerance on both edges); on an exact tie, the later by receive time (Desk A's choice 1 says "ties by run path"). The close time is the close_time of the ticker's first row that has a readable one (choice 2).
 c. A level is present if its price and its size both parse as numbers and the size is above zero. A side with no readable top-level price (yes_bid_px_1, no_bid_px_1), or with no level at all, is "a missing side": no signal. The band test's ask is 1 minus the met side's top-level price (Desk A's choices 4 and 5).
 d. "In the cell" is |imb5| at or above 0.50 with the 1e-9 tolerance; imb5 above zero buys YES, below zero buys NO.
 e. The second poll is the ticker's next poll by receive time IN THE SAME RUN FOLDER as the signal poll (Desk A's choice 1; this build first took the next poll over all run folders). Its distance from the signal poll is measured on EXCHANGE time, each poll with its own offset (item (f); this build first used the recorder's clock, t_recv_ms), at most 6 s with the 1e-9 tolerance; later, or no later poll in that run: "not fill-checked".
 f. The ladder is the met side's present levels as asks (1 minus the bid price), cheapest first. "Offers 10" is the sizes at or under limit + 1e-9 summing to 10 - 1e-9 or more. The walked price takes the first 10 contracts of the levels at or under the limit.
 g. A decision instant before the sheet's commit time (2026-11-13T00:23:49Z) does not count; a close after 2026-12-31T23:59:59Z is past the log's stop. Both are counted and left out.
 h. Result: a coverage row's result of yes or no, from any run folder that holds the ticker (two runs that disagree stop this build's run; Desk A's choice 6 takes the first found). Any other non-empty value is a void. An empty result is OPEN until 7 days after the close (by --now), then a void. A void is a fee-only loss, counted.
 i. BLOCKS follow ROTATION_LANE.md section 4, v1.3, items (a) to (u) with (h) removed, at rnd-queue b25284ef. Counted signals: fillable, signal poll time at or after the start time (l), limit in whole cents under 88 (i); misses, not fill-checked and skipped signals are in no count (m). Order (p): signal poll time, then ticker, then side. A day is the US Central date of the signal poll's exchange time (d).
 j. A block grows in order and ends, to be read once, at the first signal where it holds 60 signals, 7 days, 10 wins and 10 losses (a, c, i); a void is in n and its fee in the losses, but it is neither a win nor a loss for that count (n). An open result stops the search (r): the block WAITS, "expiry not yet decided" (q). A block whose counted signals up to its first signal's time plus 21 x 24 hours are all final and still do not hold the counts is EXPIRED, unread, once the stated read time is past that expiry time (b, k, q); the next block starts at the first counted signal after the expiry time (t).
 k. Money in whole cents (g): a cash result that is not a whole cent is rounded DOWN, floor(100 x cash + 1e-6); 1.3 or better is 10 x W >= 13 x L, 1.0 or better is W >= L, L = 0 with W > 0 passes, W = 0 fails. There is NO single-day limit: item (h) was removed by the owner on Nov 13, 2026 ("Drop the line"); the top day's share is printed for reading only. Halves: the first n // 2 signals and the rest (e).
 l. Confirmation (j): the next 30 counted signals, complete within 21 x 24 hours of the cleared block's last signal; W >= L is QUALIFIED, and then no further block is read (t); else failed, and the next block starts after its 30 signals. Fewer than 30 within its 21 days, all of them final, and the read time past that limit: EXPIRED, unread, and the next block starts at the first counted signal after the expiry time. Its signals belong to no block.
 m. The profit factors printed are W / L from the whole cents, for reading only; every bar is tested on the integers.
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
START = iso("2026-11-13T02:40:00Z")      # the start time of the seven NC15 places' forward count, written in WHEEL_ADMIT_LIST.md and WHEEL_LEDGER.md at rnd-queue e28bcef2 (item (l)); --start overrides it for a fixture
# Three readings that were once switches are FIXED here, each by a ruling in ROTATION_LANE.md section 4 (rnd-queue b25284ef); they are constants, not choices:
SECOND_CLOCK = "exchange"       # item (f): the 6 s to the second poll are measured on estimated exchange time, each poll with its own offset
OFFSET_WINDOW = "row"           # item (u): a poll's offset uses the last 120 header-readable rows up to and including the poll's OWN ROW in the run's order (book.csv.gz row order, stable sort by receive time)
HEADERLESS_POLL = True          # item (u): a row with an unreadable Date header can be a poll; it takes the median of the earlier readable rows and adds none of its own
SIZE = 10; SLIP = 0.01; CELL = 0.50; BAND = (0.10, 0.90); LOOK = 600.0; EARLY = 10.0; SECOND_MAX = 6.0; OFFSET_ROWS = 120; VOID_DAYS = 7
FAV_CENTS = 88; BLOCK = 60; RARE = 10; SPAN_DAYS = 21; MIN_DAYS = 7; DAY_SHARE = 0.30; PF_BLOCK = 1.3; PF_HALF = 1.0; CONFIRM = 30; PF_CONFIRM = 1.0
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
                except (TypeError, ValueError, IndexError): r["_hpos"] = len(hr); continue
                r["_hdr"] = True; hr.append(r["_recv"]); hv.append(h + 0.5 - r["_recv"] / 1000.0); r["_hpos"] = len(hr)
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


def offset_of(run, recv, row=None):
    i = row["_hpos"] if (OFFSET_WINDOW == "row" and row is not None) else bisect.bisect_right(run["hr"], recv); v = run["hv"][max(0, i - OFFSET_ROWS):i]
    return statistics.median(v) if v else None


def measure(root, now, made_up=False, block_read=False, start=None):
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
            off = offset_of(runs[ri], recv, r)
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
                off2 = offset_of(runs[ps[j2][1]], ps[j2][0], ps[j2][2]); gap = None if off2 is None else gap + off2 - off
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
        out["places"][s] = blocks([r for r in recs if r["series"] == s and r["status"].startswith("fillable")], now, START if start is None else start)
    out["start"] = START if start is None else start
    return out, recs


def pf(v):
    w = sum(x for x in v if x > EPS); l = -sum(x for x in v if x < -EPS)
    return None if (w == 0 and l == 0) else (float("inf") if l == 0 else w / l)


def cents(x): return int(math.floor(100 * x + 1e-6))               # (g), as ruled 02:15Z: cash that is not a whole cent is rounded DOWN, toward the worse result: floor(100 x cash + 1e-6)


def WL(c): return sum(x for x in c if x > 0), -sum(x for x in c if x < 0)
def holds_13(c): W, L = WL(c); return W > 0 and 10 * W >= 13 * L     # (g): '1.3 or better' is 10 x W >= 13 x L; L = 0 with W > 0 passes; W = 0 fails
def holds_10(c): W, L = WL(c); return W > 0 and W >= L
def ratio(c): W, L = WL(c); return None if (W == 0 and L == 0) else (float("inf") if L == 0 else W / L)


def blocks(sig, now, start=None):
    """ROTATION_LANE.md v1.3 section 4, items (a) to (u) with (h) removed, as it stands at rnd-queue b25284ef (the Head of R&D's rulings of Nov 13, 2026, and the owner's decision to drop the single-day limit).
    sig: a place's fillable signals. Counted signals are those at or after the start time (l) whose limit in whole cents is under 88 (i), in order of signal poll time, then ticker."""
    start = START if start is None else start; span = SPAN_DAYS * 86400
    sig = sorted(sig, key=lambda r: (r["signal_exchange"], r["ticker"], 0 if r["side"] == "yes" else 1))       # (p): decision time, then ticker, then side (yes before no)
    cnt = [r for r in sig if r["signal_exchange"] >= start - EPS and int(round(r["limit"] * 100)) < FAV_CENTS]
    res = {"fillable": len(sig), "before_the_start_time": sum(1 for r in sig if r["signal_exchange"] < start - EPS),
           "skipped_limit_88c_or_above": sum(1 for r in sig if r["signal_exchange"] >= start - EPS and int(round(r["limit"] * 100)) >= FAV_CENTS), "counted": len(cnt),
           "cash_not_whole_cents_rounded": sum(1 for r in cnt if r["cash"] is not None and abs(100 * r["cash"] - round(100 * r["cash"])) > 1e-6),
           "cash_not_whole_cents_all_final_fillable": sum(1 for r in sig if r["cash"] is not None and abs(100 * r["cash"] - round(100 * r["cash"])) > 1e-6), "blocks": [], "state": None, "qualified": False}
    T = lambda r: r["signal_exchange"]; day = lambda r: datetime.fromtimestamp(T(r), CT).date().isoformat(); i = 0
    while i < len(cnt):
        t0 = T(cnt[i]); exp = t0 + span; j = i; wins = losses = 0; days = set(); end = None
        while j < len(cnt) and T(cnt[j]) <= exp + EPS:
            r = cnt[j]
            if r["cash"] is None: end = "WAITS"; break                                     # (q), (r): an open result stops the search; EXPIRED is written only when every counted signal up to the expiry time is final
            wins += r["win"] is True; losses += r["win"] is False; days.add(day(r)); j += 1    # (n): a void is in n, neither a win nor a loss
            if j - i >= BLOCK and len(days) >= MIN_DAYS and wins >= RARE and losses >= RARE: end = "COMPLETE"; break
        if end is None: end = "EXPIRED" if (now > exp + EPS or j < len(cnt)) else "IN PROGRESS"
        if end == "WAITS": res["state"] = "WAITS: waiting for results, expiry not yet decided (block holds %d before the open result)" % (j - i); break
        if end == "IN PROGRESS": res["state"] = "block in progress: %d signals, %d days, %d wins, %d losses" % (j - i, len(days), wins, losses); break
        if end == "EXPIRED":
            nxt = next((k for k in range(i, len(cnt)) if T(cnt[k]) > exp + EPS), len(cnt)); b = cnt[i:nxt]      # (k): the next block starts at the first counted signal after the expiry time
            res["blocks"].append({"verdict": "EXPIRED", "n": len(b), "first": b[0]["ticker"], "last": b[-1]["ticker"], "span_days": (T(b[-1]) - t0) / 86400.0, "fails": []}); i = nxt; continue
        b = cnt[i:j]; n = len(b); c = [cents(r["cash"]) for r in b]; net = sum(c); h = n // 2; dn = collections.defaultdict(int)
        for r, x in zip(b, c): dn[day(r)] += x
        top = max(dn.values()); fails = []
        # item (h), the single-day limit, was REMOVED by the owner on Nov 13, 2026 (lane v1.3, rnd-queue 5225eff1): no day-concentration test is applied. The top day's share is printed for reading only.
        if not holds_13(c): fails.append("profit factor under 1.3")
        if not holds_10(c[:h]) or not holds_10(c[h:]): fails.append("a half under 1.0")
        W, L = WL(c)
        blk = {"first": b[0]["ticker"], "last": b[-1]["ticker"], "n": n, "wins": wins, "losses": losses, "voids": n - wins - losses, "net_cents": net, "wins_cents": W, "losses_cents": L,
               "pf": ratio(c), "pf_first_half": ratio(c[:h]), "pf_second_half": ratio(c[h:]), "days": len(dn), "span_days": (T(b[-1]) - t0) / 86400.0,
               "top_day_share_of_net": (top / net) if net > 0 else None, "verdict": "CLEARED" if not fails else "FAILED", "fails": fails}
        i = j; res["blocks"].append(blk)
        if fails: continue
        cexp = T(b[-1]) + span; cf = [r for r in cnt[i:i + CONFIRM] if T(r) <= cexp + EPS]      # (j): the next 30 counted signals, complete within 21 x 24 hours of the cleared block's last signal
        past = now > cexp + EPS or i + len(cf) < len(cnt)
        if len(cf) < CONFIRM and past and any(r["cash"] is None for r in cf):               # (q) holds for a confirmation too: no EXPIRED while a counted signal up to its expiry time is open
            blk["confirmation"] = "WAITS: waiting for results, expiry not yet decided (%d of 30)" % len(cf); res["state"] = "cleared block, confirmation waits on an open result"; break
        if len(cf) < CONFIRM:
            if past:
                blk["confirmation"] = "EXPIRED (unread; %d of 30 within 21 days)" % len(cf); i = next((k for k in range(i, len(cnt)) if T(cnt[k]) > cexp + EPS), len(cnt)); continue
            k = next((x for x, r in enumerate(cf) if r["cash"] is None), None)
            blk["confirmation"] = "in progress: %d of 30" % len(cf); res["state"] = "cleared block, confirmation in progress: %d of 30" % len(cf); break
        if any(r["cash"] is None for r in cf): blk["confirmation"] = "WAITS: a result is still open"; res["state"] = "cleared block, confirmation waits on an open result"; break
        cc = [cents(r["cash"]) for r in cf]; blk["confirmation_pf"] = ratio(cc); i += CONFIRM
        if holds_10(cc): blk["confirmation"] = "QUALIFIED"; res["qualified"] = True; res["state"] = "QUALIFIED: the place takes a seat; no further block is read"; break
        blk["confirmation"] = "confirmation failed"
    if res["state"] is None: res["state"] = "block in progress: 0 signals, 0 days, 0 wins, 0 losses"
    return res


REC_COLS = ["series", "ticker", "close", "D", "status", "signal_recv_ms", "signal_exchange", "offset", "imb5", "side", "ask", "limit", "second_recv_ms", "second_gap_s", "offered_signal", "offered_second", "miss_at",
            "walk_signal", "walk_second", "fill", "fee", "result", "win", "cash"]


def lines(out):
    f = lambda x, d=2: "n/a" if x is None else ("inf" if x == float("inf") else ("%." + str(d) + "f") % x)
    z = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    L = ["NC15 depth-cell wheel replay, second scorer | sheet v4 (8679f760), lane v1.3 section 4 at rnd-queue b25284ef | read at %s | blocks count signals from %s" % (z(out["now"]), z(out["start"]))]
    order = ["windows", "decision before the sheet's commit time, not counted", "close after the log's stop, not counted", "no signal: no poll in the window", "no signal: no clock", "no signal: a missing side of the book",
             "not in the cell", "in the cell", "in the cell, ask outside 0.10 to 0.90", "entering", "not fill-checked", "miss", "fillable", "fillable, booked as a void", "fillable, result still open"]
    for s in PLACES:
        c = out["counts"][s]; L.append("%s COUNTS: " % s + "; ".join("%s %d" % (k, c.get(k, 0)) for k in order))
        p = out["places"][s]
        for k, b in enumerate(p["blocks"], 1):
            if b["verdict"] == "EXPIRED":
                L.append("%s BLOCK %d: EXPIRED (unread; not complete within 21 days) | n %d span %s days | %s to %s" % (s, k, b["n"], f(b["span_days"], 1), b["first"], b["last"])); continue
            L.append("%s BLOCK %d: %s | n %d (%s to %s) wins %d losses %d voids %d | net %.2f PF %s halves %s / %s | days %d span %s top day %s%s%s | whole cents: wins %d, losses %d" % (
                s, k, b["verdict"], b["n"], b["first"], b["last"], b["wins"], b["losses"], b["voids"], b["net_cents"] / 100.0, f(b["pf"]), f(b["pf_first_half"]), f(b["pf_second_half"]), b["days"], f(b["span_days"], 1),
                "n/a" if b["top_day_share_of_net"] is None else "%.0f%%" % (100 * b["top_day_share_of_net"]), (" | fails: " + "; ".join(b["fails"])) if b["fails"] else "",
                (" | confirmation: %s%s" % (b["confirmation"], "" if "confirmation_pf" not in b else " (PF %s)" % f(b["confirmation_pf"]))) if "confirmation" in b else "", b["wins_cents"], b["losses_cents"]))
        L.append("%s STATE: %s (fillable signals %d: counted %d, skipped at a limit of 88c or above %d, before the start time %d; cash rounded to the cent on %d counted signals, %d of all final fillable signals; blocks %d)" % (
            s, p["state"], p["fillable"], p["counted"], p["skipped_limit_88c_or_above"], p["before_the_start_time"], p["cash_not_whole_cents_rounded"], p["cash_not_whole_cents_all_final_fillable"], len(p["blocks"])))
    for s in WITHDRAWN: L.append("%s: withdrawn, %d windows counted and not scored" % (s, out["counts"][s].get("windows", 0)))
    return L


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 3 or "--now" not in a: raise SystemExit(__doc__)
    import json
    root = a[0]; now = iso(a[a.index("--now") + 1])
    out, recs = measure(root, now, made_up=True, block_read="--block-read" in a, start=iso(a[a.index("--start") + 1]) if "--start" in a else None)
    if "--records" in a:
        with open(a[a.index("--records") + 1], "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(REC_COLS)
            for r in recs: w.writerow([("" if r.get(k) is None else (("%.6f" % r[k]) if isinstance(r.get(k), float) else r[k])) for k in REC_COLS])
    print("\n".join(lines(out))); print(json.dumps(out, indent=1, default=str))
