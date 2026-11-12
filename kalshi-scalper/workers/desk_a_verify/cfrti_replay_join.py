import runpy, sys, csv, datetime, io, contextlib
sys.argv = ["x", "dev", sys.argv[1]]
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    g = runpy.run_path("/home/user/shwoopnet/kalshi-scalper/workers/desk_a_verify/cfrti_heldout.py")
fee = lambda p: 0.07 * p * (1 - p)
def key(r): return datetime.datetime.fromtimestamp(r[7] / 1000, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") + r[1]
rows = {"three": {key(r): r for r in g["sel3"]}, "kraken": {key(r): r for r in g["selK"]}}
F = list(csv.DictReader(open(sys.argv[2] if False else "/tmp/claude-0/-home-user-shwoopnet/a8996206-4897-57fa-99d1-43a2ddf289e4/scratchpad/fz.csv")))
def pf(pnl):
    a = sum(x for x in pnl if x > 0); b = -sum(x for x in pnl if x < 0); return a / b if b else float("inf")
for form in ("three", "kraken"):
    fr = [f for f in F if f["form"] == form and f["status"] != "no_book"]
    allr = [f for f in F if f["form"] == form]
    print("==", form, "rows", len(allr), "with R6 book", len(fr))
    base, f2, f6, mine2, mine6, mine_base = [], [], [], [], [], []
    for f in fr:
        r = rows[form][f["t0_utc"] + f["ticker"]]
        win = 1 if r[5] else 0
        base.append(win - r[3] - fee(r[3]))
        if f["fill1_2s"] in ("True","1","1.0"):
            p = float(f["px1_2s"]); f2.append(win - p - fee(p))
        if f["fill1_6s"] in ("True","1","1.0"):
            p = float(f["px1_6s"]); f6.append(win - p - fee(p))
        if r[8] is not None: mine2.append(win - r[8] - fee(r[8]))
        if r[9] is not None: mine6.append(win - r[9] - fee(r[9]))
    def line(n, v): print("  %-34s n %2d  cash PF %5.2f  mean %+6.2fc  wins %s" % (n, len(v), pf(v) if v else 0, 100 * sum(v) / len(v) if v else 0, sum(1 for x in v if x > 0)))
    line("registered, same %d rows" % len(fr), base)
    line("Forensics R6 replay +2 s", f2); line("Forensics R6 replay +6 s", f6)
    line("my quote-recorder replay +2 s (same rows)", mine2); line("my quote-recorder replay +6 s (same rows)", mine6)
    # misses: outcome of rows Forensics could not fill
    miss2 = [rows[form][f["t0_utc"] + f["ticker"]] for f in fr if f["fill1_2s"] not in ("True", "1", "1.0")]
    miss6 = [rows[form][f["t0_utc"] + f["ticker"]] for f in fr if f["fill1_6s"] not in ("True", "1", "1.0")]
    print("  missed at +2 s: %d rows, %d winners (registered pnl of those %+.2fc total per contract)" % (len(miss2), sum(1 for r in miss2 if r[5]), 100 * sum((1 if r[5] else 0) - r[3] - fee(r[3]) for r in miss2)))
    print("  missed at +6 s: %d rows, %d winners" % (len(miss6), sum(1 for r in miss6 if r[5])))
    # row by row comparison of fill status
    agree = dis = 0
    for f in fr:
        r = rows[form][f["t0_utc"] + f["ticker"]]
        a = f["fill1_2s"] in ("True", "1", "1.0"); b = r[8] is not None
        agree += a == b; dis += a != b
    print("  fill status +2 s: Forensics vs my quote replay agree on", agree, "disagree", dis)
