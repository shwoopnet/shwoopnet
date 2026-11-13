"""W-POL-APPR1 scorer (registration: POLITICS_APPROVAL_CAL_REGISTRATION.md, Amendments 2 and 3).

One command, run once, after the pull is complete and polappr1_convert.py has written its output folder:
  python3 -I kalshi-scalper/refine_tools/polappr1_score.py OUT_DIR

OUT_DIR must hold cand_all.jsonl (one JSON object per market, the format of the first pull's cand.jsonl)
and POLAPPR1_PULL_COMPLETE (written by the converter only when every request of every part is answered).
  {"t": ticker, "e": event, "s": series, "ct": market close ts, "res": "yes"/"no", "src": ..., "c": [[end_ts, yes_ask, yes_bid, price, volume], ...]}

Before the marker exists this prints one line and nothing else. After a successful read it writes
POLAPPR1_READ_DONE and refuses to run again. Local files only: no network, no Kalshi key, no trading code.

Thirds are constants (POL_APPR1_CUTS.json for five families, POL_APPR1_CUTS_A3.json for APPR_538). An event
is classified by the latest close among its markets in the file. HELD-OUT events are never scored, counted in
a cell, bootstrapped or put in the calibration table. The grid is 6 families x 4 looks x 5 buckets x 2 sides = 240 cells.
"""
import collections
import json
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
MARKER = "POLAPPR1_PULL_COMPLETE"
READ_DONE = "POLAPPR1_READ_DONE"
CANDLES = "cand_all.jsonl"
CUT_FILES = ("POL_APPR1_CUTS.json", "POL_APPR1_CUTS_A3.json")
GCB = {"KXVHGCB", "KXGENERICBALLOTVOTEHUB", "KXGENERICBALLOT"}
LOOKS = [("7d", 7 * 86400, 6 * 3600), ("3d", 3 * 86400, 6 * 3600), ("1d", 86400, 3 * 3600), ("6h", 6 * 3600, 3 * 3600)]
PB = [(0.10, 0.25), (0.25, 0.40), (0.40, 0.60), (0.60, 0.75), (0.75, 0.9001)]
FAMILIES = ["ALL_APPR", "APPR_538", "APPR_DAILY", "APPR_OTHER", "APPR_RCP", "GCB"]
RESEARCH_Z = 5.46      # the research bar: DEFLATION_LEDGER.md (branch rnd-queue), N about 2,113,000
INFO_Z = 4.55          # the retired small ledger (N about 9,459), printed for information only
NO_EVIDENCE_N = 100    # Amendment 3: under this many pooled TRAIN+VALIDATE events a cell gets only the label
NO_SURVIVOR_MIN_CELLS = 3  # Amendment 3: cells with n >= 100 needed before a family reads NO SURVIVOR


class Refuse(Exception):
    pass


APPR_OTHER_SERIES = {"KXVOTEHUBTRUMPUPDOWN", "KXTRUMPVH", "KXTRUMPAPPROVALBELOW", "KXNYTTRUMPAPPROVAL",
                     "KXVOTEHUBVANCEAPPROVE", "KXVHAPRPOTUS", "KXTRUMPAPPROVALYEAR"}


def grp(s):
    """Amendment 5 (1): a family is exactly its registered list of series; any other series is in no family (None)."""
    if s in GCB:
        return "GCB"
    if s == "KXTRUMPAPPROVE":
        return "APPR_DAILY"
    if s == "KXAPRPOTUS":
        return "APPR_RCP"
    if s == "KX538APPROVE":
        return "APPR_538"
    if s in APPR_OTHER_SERIES:
        return "APPR_OTHER"
    return None


def fams_of(series):
    g = grp(series)
    if g is None:
        return []
    return [g] if g == "GCB" else [g, "ALL_APPR"]


def load_cuts(folder=HERE):
    cuts = {}
    for fn in CUT_FILES:
        with open(os.path.join(folder, fn)) as f:
            for fam, v in json.load(f)["cuts"].items():
                cuts[fam] = (int(v[0]), int(v[1]))
    return cuts


def third(cuts, fam, ect):
    a, b = cuts[fam]
    return "TRAIN" if ect < a else ("VALID" if ect < b else "HELD")


def event_closes(rows):
    """{event: latest market close in the rows} (rows are dicts with e and ct)."""
    out = {}
    for j in rows:
        if j["e"] not in out or j["ct"] > out[j["e"]]:
            out[j["e"]] = j["ct"]
    return out


def is_heldout(cuts, series, ect):
    return any(third(cuts, f, ect) == "HELD" for f in fams_of(series))


def valid_mid(ask, bid):
    """Amendment 6 (G1): the YES mid exists only when 0 < bid < ask < 1."""
    if ask is None or bid is None or not (0 < bid < ask < 1):
        return None
    return (ask + bid) / 2


def no_mid_counts(rows, cuts):
    """Events (listed family, not held-out) with no market holding a valid mid at a look, per look (printed)."""
    ec = event_closes(rows)
    seen = {}
    for j in rows:
        if grp(j["s"]) is None or is_heldout(cuts, j["s"], ec[j["e"]]):
            continue
        for ln, L, tol in LOOKS:
            ok = False
            if j["c"]:
                q = look_quote(sorted(j["c"]), j["ct"], L, tol)
                if q and valid_mid(fl(q[1]), fl(q[2])) is not None:
                    ok = True
            seen[(j["e"], ln)] = seen.get((j["e"], ln), False) or ok
    out = collections.Counter()
    for (e, ln), ok in seen.items():
        if not ok:
            out[ln] += 1
    return out


def fl(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def pbk(p):
    for i, (a, b) in enumerate(PB):
        if a <= p < b:
            return i
    return None


def look_quote(cs, ct, L, tol):
    r = ct - L
    q = None
    for c in cs:
        if c[0] <= r and c[0] >= r - tol:
            q = c
    return q


def load_obs(rows, cuts):
    """One observation per (event, look, bucket, side): the market whose YES mid is nearest 0.5. HELD-OUT events are skipped."""
    ec = event_closes(rows)
    obs = {}
    for j in rows:
        if not j["c"]:
            continue
        ect = ec[j["e"]]
        if grp(j["s"]) is None or is_heldout(cuts, j["s"], ect):
            continue
        ct = j["ct"]
        cs = sorted(j["c"])
        for ln, L, tol in LOOKS:
            q = look_quote(cs, ct, L, tol)
            if not q:
                continue
            ask = fl(q[1])
            bid = fl(q[2])
            # Amendment 6 (G1): a mid exists only when 0 < bid < ask < 1; a market without one is not a candidate.
            mid = valid_mid(ask, bid)
            if mid is None:
                continue
            for side in ("Y", "N"):
                if side == "Y":
                    if ask is None or not 0 < ask < 1:
                        continue
                    p = ask
                    win = j["res"] == "yes"
                else:
                    if bid is None or not 0 < bid < 1:
                        continue
                    p = 1 - bid
                    win = j["res"] == "no"
                b = pbk(round(p, 4))
                if b is None:
                    continue
                d = abs(mid - 0.5)
                o = dict(s=j["s"], e=j["e"], t=j["t"], ct=ct, ect=ect, look=ln, pb=b, side=side, p=p, win=win, qt=q[0], dist=d)
                k = (j["e"], ln, b, side)
                # Amendment 4 (Nov 13): exact ties (within 1e-9) go to the lower ticker, not to file order.
                if k not in obs or d < obs[k]["dist"] - 1e-9 or (abs(d - obs[k]["dist"]) <= 1e-9 and o["t"] < obs[k]["t"]):
                    obs[k] = o
    return list(obs.values())


def net(o, slip=0.01):
    p = o["p"]
    return (1.0 if o["win"] else 0.0) - p - slip - 0.07 * p * (1 - p)


def stats(xs):
    n = len(xs)
    if not n:
        return None
    m = sum(xs) / n
    gp = sum(x for x in xs if x > 0)
    gl = -sum(x for x in xs if x < 0)
    sd = (sum((x - m) ** 2 for x in xs) / (n - 1)) ** .5 if n > 1 else 0
    return n, m, (gp / gl if gl > 0 else float("inf")), (m / (sd / n ** .5) if sd > 0 else 0)


def boot(xs, B=2000, seed=1, blocks=None):
    r = random.Random(seed)
    n = len(xs)
    if blocks is None:
        ms = sorted(sum(xs[r.randrange(n)] for _ in range(n)) / n for _ in range(B))
    else:
        bl = collections.defaultdict(list)
        for x, b in zip(xs, blocks):
            bl[b].append(x)
        ks = list(bl)
        ms = []
        for _ in range(B):
            tot = 0
            cnt = 0
            for _ in ks:
                v = bl[ks[r.randrange(len(ks))]]
                tot += sum(v)
                cnt += len(v)
            ms.append(tot / cnt)
        ms.sort()
    return ms[int(.05 * B)], ms[int(.95 * B)]


def live(os_):
    """As if live: 3 contracts, +1c slip, fee rounded up to the cent per order, fills ordered by close time.
    Amendment 5 (2): the net rule (net under -15 dollars after 20 fills) is tested at EVERY fill from the 20th on, in
    fill order; the 5 loss streak at any fill. Amendment 6 (G2): at most 10 positions open at once (entry quote time to
    close); fills are offered in entry-quote-time order (ties by ticker) and a fill that would be the 11th open is skipped
    and counted; the replay then runs over the accepted fills ordered by close time.
    Returns n, net at fill 20 (net so far if under 20 fills), longest streak, fired, max open, net over all fills,
    first fill at which a kill fires (None if none), fills skipped by the cap."""
    offered = sorted(os_, key=lambda o: (o["qt"], o["t"]))
    openct = []
    acc = []
    skipped = 0
    for o in offered:
        openct = [c for c in openct if c > o["qt"]]
        if len(openct) >= 10:
            skipped += 1
            continue
        openct.append(o["ct"])
        acc.append(o)
    os_ = sorted(acc, key=lambda o: (o["ct"], o["t"]))
    tot = 0
    streak = 0
    ml = 0
    first = None
    n = 0
    net20 = 0
    for o in os_:
        p = o["p"] + 0.01
        fee = math.ceil(0.07 * 3 * o["p"] * (1 - o["p"]) * 100 - 1e-9) / 100
        pnl = 3 * ((1.0 if o["win"] else 0) - p) - fee
        n += 1
        tot += pnl
        streak = streak + 1 if pnl < 0 else 0
        ml = max(ml, streak)
        if streak >= 5 and first is None:
            first = n
        if n == 20:
            net20 = tot
        if n >= 20 and tot < -15 - 1e-9 and first is None:
            first = n
    if n < 20:
        net20 = tot
    ev = [(o["qt"], 1) for o in os_] + [(o["ct"], -1) for o in os_]
    ev.sort(key=lambda x: (x[0], x[1]))
    cur = mx = 0
    for _, d in ev:
        cur += d
        mx = max(mx, cur)
    return n, net20, ml, first is not None, mx, tot, first, skipped


def week(o):
    return o["ect"] // (7 * 86400)


def cells(obs, cuts):
    out = []
    for f in FAMILIES:
        for ln, _, _ in LOOKS:
            for pb in range(5):
                for sd in ("Y", "N"):
                    cell = [o for o in obs if f in fams_of(o["s"]) and o["look"] == ln and o["pb"] == pb and o["side"] == sd]
                    tr = [o for o in cell if third(cuts, f, o["ect"]) == "TRAIN"]
                    va = [o for o in cell if third(cuts, f, o["ect"]) == "VALID"]
                    out.append((f, ln, pb, sd, tr, va))
    return out


def p0txt(tr, va):
    """Amendment 6 (G2): PF and mean at +0c slip, shown beside the +1c figures of every reported cell."""
    a = stats([net(o, 0) for o in tr])
    b = stats([net(o, 0) for o in va])
    return "+0c: PF %.2f/%.2f mean(tr)%+.1f mean(va)%+.1f" % (a[2], b[2], 100 * a[1], 100 * b[1])


def calibration_rows(rows, cuts):
    """Amendment 5 (3): by look and the five registered price buckets of the YES ASK, per market, pooled over the approval
    families (ALL_APPR, TRAIN and VALID events only); realized YES frequency against the mean YES ask and mean mid; n always shown."""
    ec = event_closes(rows)
    pts = []
    for j in rows:
        if not j["c"] or "ALL_APPR" not in fams_of(j["s"]):
            continue
        if is_heldout(cuts, j["s"], ec[j["e"]]) or third(cuts, "ALL_APPR", ec[j["e"]]) not in ("TRAIN", "VALID"):
            continue
        cs_ = sorted(j["c"])
        for ln, L, tol in LOOKS:
            q = look_quote(cs_, j["ct"], L, tol)
            if not q:
                continue
            a = fl(q[1])
            b = fl(q[2])
            mid = valid_mid(a, b)
            if mid is None:
                continue
            pts.append((ln, a, mid, 1.0 if j["res"] == "yes" else 0.0))
    out = []
    for ln, _, _ in LOOKS:
        for lo, hi in PB:
            x = [r for r in pts if r[0] == ln and lo <= r[1] < hi]
            if x:
                out.append((ln, "%.2f-%.2f" % (lo, min(hi, 0.9)), len(x), sum(r[1] for r in x) / len(x), sum(r[2] for r in x) / len(x), sum(r[3] for r in x) / len(x)))
    return out


def calibration(rows, cuts):
    return ["%s | %s n%d meanAsk%.3f meanMid%.3f realizedYES%.3f" % r for r in calibration_rows(rows, cuts)]


def family_label(n_big, best_pf, supporting, max_n):
    """Printed family read. n_big = cells with pooled n >= 100; best_pf = cash PF (+1c, after fees) of the best populated cell; supporting = list of cell texts.
    FALSIFIED is the charter's meaning only: the best populated cell has PF under 1.0. NO SURVIVOR is the weaker outcome."""
    parts = []
    if n_big and best_pf is not None and best_pf < 1.0:
        parts.append("FALSIFIED (the best populated cell, pooled n >= %d, has cash PF %.2f after fees, under 1.0)" % (NO_EVIDENCE_N, best_pf))
    if supporting:
        parts.append("SUPPORTING CELLS (exploratory, not an advance): " + "; ".join(supporting))
    elif n_big >= NO_SURVIVOR_MIN_CELLS:
        parts.append("NO SURVIVOR at this grid (an edge of about 10c or more ruled out in the populated cells; %d cells with n >= %d; closes the family for new work)" % (n_big, NO_EVIDENCE_N))
    if not parts:
        if n_big:
            parts.append("neither support nor failure (best populated cell PF %.2f; %d cells with n >= %d)" % (best_pf, n_big, NO_EVIDENCE_N))
        else:
            parts.append("no evidence at n = %d (largest cell; 0 cells with n >= %d)" % (max_n, NO_EVIDENCE_N))
    return "; ".join(parts)


def report(rows, cuts):
    out = []
    ec = event_closes(rows)
    obs = load_obs(rows, cuts)
    scored = collections.defaultdict(lambda: collections.Counter())
    for e, ect in ec.items():
        s = next(j["s"] for j in rows if j["e"] == e)
        for f in fams_of(s):
            scored[f][third(cuts, f, ect)] += 1
    out.append("EVENTS IN FILE BY THIRD (HELD counts are events only; no held-out candle is read or scored)")
    for f in FAMILIES:
        out.append("  %s %s" % (f, dict(scored[f])))
    unl = collections.Counter()
    for e in ec:
        s = next(j["s"] for j in rows if j["e"] == e)
        if grp(s) is None:
            unl[s] += 1
    for s, c in sorted(unl.items()):
        out.append("  %s: unlisted, not scored (%d events)" % (s, c))
    nm = no_mid_counts(rows, cuts)
    out.append("EVENTS WITH NO VALID MID (0 < bid < ask < 1) AT A LOOK, no observation there: " + (", ".join("%s %d" % (ln, nm[ln]) for ln, _, _ in LOOKS) if nm else "none"))
    out.append("OBS %d" % len(obs))
    out.append("")
    out.append("CALIBRATION (Amendment 5: YES ask buckets, per market, approval families pooled, TRAIN and VALID events only; descriptive only): look | bucket n meanAsk meanMid realizedYES")
    out.extend(calibration(rows, cuts))
    out.append("")
    allc = []
    for f, ln, pb, sd, tr, va in cells(obs, cuts):
        if not tr and not va:
            continue
        allc.append((f, ln, pb, sd, tr, va))
    out.append("GRID 240 cells; non-empty %d; with observations in both TRAIN and VALID %d; with n >= 30 in both %d; with pooled n >= %d: %d" % (
        len(allc), sum(1 for c in allc if c[4] and c[5]), sum(1 for c in allc if len(c[4]) >= 30 and len(c[5]) >= 30),
        NO_EVIDENCE_N, sum(1 for c in allc if len(c[4]) + len(c[5]) >= NO_EVIDENCE_N)))
    out.append("")
    # registered pass bar
    adv = []
    ranked = []
    for f, ln, pb, sd, tr, va in allc:
        if not tr or not va:
            continue
        s1 = stats([net(o) for o in tr])
        s2 = stats([net(o) for o in va])
        lo, hi = boot([net(o) for o in va])
        ok = len(tr) >= 30 and len(va) >= 30 and s1[2] >= 1.3 and s2[2] >= 1.3 and lo > 0
        ranked.append((lo, f, ln, pb, sd, tr, va, s1, s2, lo, hi, ok))
    ranked.sort(key=lambda r: -r[0])
    out.append("CELLS with TRAIN and VALID observations, best validation lower bound first ('PASS' = the registered bar; at most two advance)")
    for lo, f, ln, pb, sd, tr, va, s1, s2, lo_, hi, ok in ranked:
        n = len(tr) + len(va)
        tag = "%s %s %.2f-%.2f %s" % (f, ln, PB[pb][0], PB[pb][1], sd)
        if ok and len(adv) < 2:
            adv.append((f, ln, pb, sd, tr, va, s1, s2, lo_, hi))
            L = live(tr + va)
            sa = stats([net(o) for o in tr + va])
            wl, wh = boot([net(o) for o in va], blocks=[week(o) for o in va])
            wide = wl if wl < lo_ else lo_
            killed = L[3] or s2[1] <= 0 or wide <= 0
            out.append("PASS %s n%d/%d PF %.2f/%.2f mean(tr)%+.1f mean(va)%+.1f va90[%+.1f,%+.1f] week-block[%+.1f,%+.1f] z%.2f %s | " % (
                tag, len(tr), len(va), s1[2], s2[2], 100 * s1[1], 100 * s2[1], 100 * lo_, 100 * hi, 100 * wl, 100 * wh, sa[3],
                ("PASSES the research bar z %.2f (4.55 info)" % RESEARCH_Z) if sa[3] >= RESEARCH_Z else "exploratory (below the research bar z %.2f; 4.55 of the retired ledger is information only)" % RESEARCH_Z) + p0txt(tr, va) + " | live3: n%d net@20 $%.2f net(all) $%.2f streak%d kill%s first-kill-fill %s maxopen%d cap-skipped%d | %s" % (
                L[0], L[1], L[5], L[2], "Y" if L[3] else "N", L[6] if L[6] else "none", L[4], L[7],
                "KILLED" if killed else "survives the kill bar") + ("" if n >= NO_EVIDENCE_N else " | no evidence at n = %d" % n))
        elif n < NO_EVIDENCE_N:
            out.append("     %s no evidence at n = %d (TRAIN %d, VALID %d)" % (tag, n, len(tr), len(va)))
        else:
            sa = stats([net(o) for o in tr + va])
            out.append("     %s n%d/%d PF %.2f/%.2f mean(tr)%+.1f mean(va)%+.1f va90[%+.1f,%+.1f] z%.2f | %s" % (
                tag, len(tr), len(va), s1[2], s2[2], 100 * s1[1], 100 * s2[1], 100 * lo_, 100 * hi, sa[3], p0txt(tr, va)))
    out.append("")
    out.append("FAMILY READ (pooled TRAIN+VALID, +1c; a cell 'supports' only if pooled n >= %d, PF >= 1.3 and the event-clustered 90 percent lower bound of the mean is above 0; report only, never an advance)" % NO_EVIDENCE_N)
    for f in FAMILIES:
        cs_ = [c for c in allc if c[0] == f]
        big = [c for c in cs_ if len(c[4]) + len(c[5]) >= NO_EVIDENCE_N]
        sup = []
        for _, ln, pb, sd, tr, va in big:
            xs = [net(o) for o in tr + va]
            st = stats(xs)
            lo, _ = boot(xs)
            if st[2] >= 1.3 and lo > 0:
                sup.append("%s %.2f-%.2f %s n%d PF %.2f lo%+.1f" % (ln, PB[pb][0], PB[pb][1], sd, st[0], st[2], 100 * lo))
        mx = max([len(c[4]) + len(c[5]) for c in cs_] or [0])
        bestpf = max([stats([net(o) for o in tr + va])[2] for _, _, _, _, tr, va in big] or [None], key=lambda x: -1 if x is None else x)
        v = family_label(len(big), bestpf, sup, mx)
        out.append("  %s: %s" % (f, v))
    out.append("")
    out.append("ADVANCING CELLS: %d (HELD-OUT is not read here; frozen survivors go to the session lead)" % len(adv))
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: polappr1_score.py OUT_DIR")
        return 64
    d = argv[0]
    mp = os.path.join(d, MARKER)
    if not os.path.isfile(mp):
        print("POLAPPR1: pull not complete (no %s); nothing is read" % MARKER)
        return 0
    if os.path.exists(os.path.join(d, READ_DONE)):
        print("refused: %s exists; the result was read once" % READ_DONE)
        return 2
    try:
        if int(open(mp).read().strip()) <= 0:
            raise ValueError
        cuts = load_cuts()
        with open(os.path.join(d, CANDLES)) as f:
            rows = [json.loads(l) for l in f if l.strip()]
        lines = report(rows, cuts)
    except (OSError, ValueError, KeyError) as e:
        print("refused: cannot read the inputs (%s); nothing was marked read" % type(e).__name__)
        return 2
    print("\n".join(lines))
    with open(os.path.join(d, READ_DONE), "w") as f:
        f.write(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
