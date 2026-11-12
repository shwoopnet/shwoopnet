"""NOSIDE1 scorer (W-NO-ARM1, development thirds only).

Run once, after the pull is complete:
  python3 -I kalshi-scalper/refine_tools/noside1_score.py DIR_WITH_cand_no.jsonl [--cuts NO_ARM_CUTS.json]

DIR holds cand_no.jsonl and NOSIDE1_PULL_COMPLETE (content 1034). Without the marker it prints
only 'pull incomplete'. With it, it prints the development verdict ONCE, writes NOSIDE1_READ_DONE
and refuses to run again ('already read').

Thirds come from NO_ARM_CUTS.json (fixed event lists, amendment 2): third 0 TRAIN, 1 VALIDATE.
Third 2 (held-out) and any event not in the list are dropped on load and never scored.
Arms (NO price paid): A [0.75, 0.90), B [0.10, 0.25). Look: last candle at or before close minus
86400 s and no more than 3 h older; one observation per event per arm (YES mid nearest 0.5, ties by
ticker); hold to settlement; fee 0.07 p (1-p) unrounded; slippage +0c and +1c; +1c is the basis.
Label per cell (registration): n >= 30 in TRAIN and in VALIDATE else 'no evidence at n = a/b'
(no PF or mean shown for a third under 30). PASS = PF >= 1.5 at +1c in TRAIN, VALIDATE and pooled,
VALIDATE event-clustered 90 percent lower bound at +1c above 0, pooled t at +1c >= 4.553
(N = 9,465). All of that but the t bar = EXPLORATORY. Otherwise FAIL. A cell where the as-if-live
rule (3 contracts: net under -15 dollars after 20 fills, or 5 losses in a row) fires cannot pass.
"""
import sys, os, json, math, random, collections

MARKER = "NOSIDE1_PULL_COMPLETE"
READ_DONE = "NOSIDE1_READ_DONE"
REQUESTS = 1034
HERE = os.path.dirname(os.path.abspath(__file__))
APPRS = {"KXAPRPOTUS", "KXAPRPOTUSD", "KXTRUMPAPPROVE", "KXVOTEHUBTRUMPUPDOWN"}
ARMS = {"A": (0.75, 0.9001), "B": (0.10, 0.2501)}
MIN_N = 30
BONF_Z = 4.553


def fl(x):
    try:
        return float(x)
    except Exception:
        return None


def thirds(cuts_path):
    c = json.load(open(cuts_path))["series"]
    return {e: t for v in c.values() for e, t in v["events"]}


def load(path, TH):
    ob = {}
    for l in open(path):
        if not l.strip():
            continue
        j = json.loads(l)
        if TH.get(j["e"], 2) >= 2:
            continue  # held-out or unlisted: never scored
        r = j["ct"] - 86400
        q = None
        for c in sorted(j["c"]):
            if r - 3 * 3600 <= c[0] <= r:
                q = c
        if not q:
            continue
        ask, bid = fl(q[1]), fl(q[2])
        if bid is None or not 0 < bid < 1:
            continue
        p = 1 - bid
        mid = (ask + bid) / 2 if ask and 0 < ask < 1 else p
        for arm, (lo, hi) in ARMS.items():
            if lo - 1e-9 <= p < hi:
                o = dict(e=j["e"], t=j["t"], s=j["s"], ct=j["ct"], qt=q[0], p=p,
                         win=j["res"] == "no", d=abs(mid - 0.5))
                k = (j["e"], arm)
                if k not in ob or (o["d"], o["t"]) < (ob[k]["d"], ob[k]["t"]):
                    ob[k] = o
    return ob


def net(o, sl):
    p = o["p"]
    return (1.0 if o["win"] else 0.0) - p - sl - 0.07 * p * (1 - p)


def stats(xs):
    n = len(xs)
    m = sum(xs) / n
    gp = sum(x for x in xs if x > 0)
    gl = -sum(x for x in xs if x < 0)
    sd = (sum((x - m) ** 2 for x in xs) / (n - 1)) ** .5 if n > 1 else 0
    return m, (gp / gl if gl > 0 else float("inf")), (m / (sd / n ** .5) if sd > 0 else 0.0)


def boot(xs, blocks, B=2000, seed=1):
    r = random.Random(seed)
    bl = collections.defaultdict(list)
    for x, b in zip(xs, blocks):
        bl[b].append(x)
    ks = sorted(bl)
    ms = []
    for _ in range(B):
        tot = cnt = 0
        for _ in ks:
            v = bl[ks[r.randrange(len(ks))]]
            tot += sum(v)
            cnt += len(v)
        ms.append(tot / cnt)
    ms.sort()
    return ms[int(.05 * B)], ms[int(.95 * B)]


def live(os_):
    os_ = sorted(os_, key=lambda o: o["ct"])
    tot = st = 0
    fired = False
    for i, o in enumerate(os_, 1):
        p = o["p"] + 0.01
        fee = math.ceil(0.07 * 3 * o["p"] * (1 - o["p"]) * 100 - 1e-9) / 100
        pnl = 3 * ((1.0 if o["win"] else 0) - p) - fee
        tot += pnl
        st = st + 1 if pnl < 0 else 0
        if st >= 5 or (i == 20 and tot < -15):
            fired = True
    return fired


def fam(s):
    return "APPR" if s in APPRS else "GCB"


def inf(x):
    return "inf" if x == float("inf") else "%.2f" % x


def cell_report(arm, f, cell, TH):
    tr = [o for o in cell if TH[o["e"]] == 0]
    va = [o for o in cell if TH[o["e"]] == 1]
    lines = ["ARM %s price paid [%.2f,%.2f) family %s: n TRAIN %d, n VALID %d" % (arm, ARMS[arm][0], ARMS[arm][1], f, len(tr), len(va))]
    if len(tr) < MIN_N or len(va) < MIN_N:
        lines.append("  no evidence at n = %d (TRAIN) / %d (VALID); needs %d in each third" % (len(tr), len(va), MIN_N))
        return lines, "NO EVIDENCE"
    res = {}
    for lab, xs in (("TRAIN", tr), ("VALID", va), ("POOLED", tr + va)):
        for sl in (0, 0.01):
            m, pf, t = stats([net(o, sl) for o in xs])
            res[(lab, sl)] = (m, pf, t)
            lines.append("  %-6s +%dc n%d PF %s mean %+.1fc t %+.2f" % (lab, sl * 100, len(xs), inf(pf), 100 * m, t))
    lo, hi = boot([net(o, 0.01) for o in va], [o["e"] for o in va])
    lines.append("  VALID +1c event-clustered 90%% interval [%+.1f,%+.1f]c" % (100 * lo, 100 * hi))
    fired = live(tr + va)
    lines.append("  as-if-live 3c TRAIN+VALID: stop rule %s" % ("FIRED" if fired else "not fired"))
    pf_ok = all(res[(l, 0.01)][1] >= 1.5 for l in ("TRAIN", "VALID", "POOLED"))
    base = pf_ok and lo > 0 and not fired
    if base and res[("POOLED", 0.01)][2] >= BONF_Z:
        lab = "PASS"
    elif base:
        lab = "EXPLORATORY"
    else:
        lab = "FAIL"
    return lines, lab


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    cuts = os.path.join(HERE, "NO_ARM_CUTS.json")
    if "--cuts" in argv:
        cuts = argv[argv.index("--cuts") + 1]
        args = [a for a in args if a != cuts]
    d = args[0] if os.path.isdir(args[0]) else os.path.dirname(os.path.abspath(args[0]))
    path = os.path.join(d, "cand_no.jsonl")
    mk = os.path.join(d, MARKER)
    try:
        ok = open(mk).read().strip() == str(REQUESTS)
    except OSError:
        ok = False
    if not ok:
        print("pull incomplete")
        return 0
    if os.path.exists(os.path.join(d, READ_DONE)):
        print("already read")
        return 0
    TH = thirds(cuts)
    ob = load(path, TH)
    print("NOSIDE1 development verdict (TRAIN and VALIDATE only; held-out not read). N = 9,465, Bonferroni z %.3f" % BONF_Z)
    for arm in ARMS:
        for f in ("APPR", "GCB", "ALL"):
            cell = [o for (e, a), o in ob.items() if a == arm and (f == "ALL" or fam(o["s"]) == f)]
            lines, lab = cell_report(arm, f, cell, TH)
            print("\n".join(lines))
            print("  VERDICT: %s" % lab)
    open(os.path.join(d, READ_DONE), "w").write("read")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
