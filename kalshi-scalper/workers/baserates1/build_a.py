"""BASERATES1 table set A (offline; reads eo_list.csv, plaw_list.csv). Descriptive only, no scoring."""
import csv, math, datetime as dt, collections, statistics as st
D = dt.date.fromisoformat
eo = [D(r["signed"]) for r in csv.DictReader(open("eo_list.csv"))]
pl = [(int(r["congress"]), D(r["approved"])) for r in csv.DictReader(open("plaw_list.csv"))]
def sunday(d): return d - dt.timedelta(days=(d.weekday() + 1) % 7)
PER = {  # complete weeks / months only; weeks Sunday to Saturday as in the Kalshi rules text
 "TrumpI": (D("2017-01-22"), D("2021-01-16")),     # first full Sun week after Jan 20 to last full week before Jan 20 2021
 "TrumpII": (D("2025-01-26"), D("2026-10-17")),
}
SEG = {"TrumpII_2025H1": (D("2025-01-26"), D("2025-08-30")), "TrumpII_since_2025-09": (D("2025-08-31"), D("2026-10-17"))}
def weeks(a, b):
    w = []; s = a
    while s + dt.timedelta(days=6) <= b: w.append(s); s += dt.timedelta(days=7)
    return w
def pois_gt(m, n):
    return 1 - sum(math.exp(-m) * m ** k / math.factorial(k) for k in range(n + 1))
def wcounts(dates, ws):
    c = collections.Counter(sunday(d) for d in dates)
    return [c.get(w, 0) for w in ws]
def summ(name, xs, ex):
    n = len(xs); m = st.mean(xs); v = st.variance(xs) if n > 1 else float("nan")
    r = {"group": name, "n": n, "mean": round(m, 3), "var": round(v, 3), "dispersion_var_over_mean": round(v / m, 2) if m else "",
         "median": st.median(xs), "min": min(xs), "max": max(xs)}
    for N in ex: r[f"emp_P_gt_{N}"] = round(sum(x > N for x in xs) / n, 3); r[f"pois_P_gt_{N}"] = round(pois_gt(m, N), 3)
    return r
def wr(f, rows):
    keys = []
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    w = csv.DictWriter(open(f, "w", newline=""), keys); w.writeheader(); w.writerows(rows)
EXN = [0, 1, 2, 3, 4, 5, 6, 8, 10]
# A1 weekly EO distributions
rows = []; W = {}
for p, (a, b) in list(PER.items()) + list(SEG.items()):
    ws = weeks(a, b); xs = wcounts(eo, ws); W[p] = (ws, xs)
    rows.append(summ(p, xs, EXN))
    # by calendar quarter
for p in ("TrumpI", "TrumpII"):
    ws, xs = W[p]; byq = collections.defaultdict(list)
    for w, x in zip(ws, xs): byq[f"{p}_{w.year}Q{(w.month - 1)//3 + 1}"].append(x)
    for q in sorted(byq): rows.append(summ(q, byq[q], EXN))
wr("A1_eo_weekly_distribution.csv", rows)
# weekly histogram
h = []
for p in ("TrumpI", "TrumpII", "TrumpII_2025H1", "TrumpII_since_2025-09"):
    c = collections.Counter(W[p][1])
    for k in range(0, max(c) + 1): h.append({"group": p, "count_in_week": k, "weeks": c.get(k, 0), "share": round(c.get(k, 0) / len(W[p][1]), 3)})
wr("A1b_eo_weekly_histogram.csv", h)
# A2 conditional: given k orders signed through weekday d, final weekly count
rows = []
DAYN = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]
for p in ("TrumpI", "TrumpII", "TrumpII_since_2025-09"):
    ws, _ = W[p]
    byd = collections.defaultdict(lambda: [0] * 7)
    wk = collections.defaultdict(list)
    for d in eo: wk[sunday(d)].append((d - sunday(d)).days)
    for w in ws:
        days = wk.get(w, []); fin = len(days)
        for d in range(6):
            k = sum(x <= d for x in days)
            wk_k = min(k, 7)
            rows.append((p, d, wk_k, fin))
    agg = collections.defaultdict(list)
    for r in rows:
        if r[0] == p: agg[(r[1], r[2])].append(r[3])
for p in ("TrumpI", "TrumpII", "TrumpII_since_2025-09"):
    pass
out = []
agg = collections.defaultdict(list)
for p, d, k, fin in rows: agg[(p, d, k)].append(fin)
for (p, d, k), fs in sorted(agg.items()):
    n = len(fs); r = {"period": p, "through_day": DAYN[d], "k_so_far": ("7+" if k == 7 else k), "n_weeks": n, "mean_final": round(st.mean(fs), 2), "median_final": st.median(fs)}
    for N in range(0, 13): r[f"P_final_gt_{N}"] = round(sum(f > N for f in fs) / n, 3)
    r["note"] = "n<5: do not use" if n < 5 else ""
    out.append(r)
wr("A2_eo_conditional_final_count.csv", out)
# A3 bills: weekly and monthly public laws (approved date). Trump I: 115th+116th, ends 2021-01-03 (data end); Trump II: 119th
pld = {"TrumpI": [d for c, d in pl if c in (115, 116) and d >= D("2017-01-20")], "TrumpII": [d for c, d in pl if c == 119]}
plend = {"TrumpI": D("2021-01-03"), "TrumpII": D("2026-10-31")}  # 119th held to the last file pulled
rows = []; MW = {}
def months(a, b):
    out = []; y, m = a
    while (y, m) <= b: out.append((y, m)); y, m = (y, m + 1) if m < 12 else (y + 1, 1)
    return out
M_RANGE = {"TrumpI": ((2017, 2), (2020, 12)), "TrumpII": ((2025, 2), (2026, 10))}
for p in ("TrumpI", "TrumpII"):
    ds = pld[p]; ws = weeks(*{"TrumpI": (D("2017-01-22"), D("2021-01-02")), "TrumpII": (D("2025-01-26"), D("2026-10-31"))}[p])
    xs = wcounts(ds, ws); rows.append({**summ(p + "_week", xs, [0, 1, 2, 3, 5, 8]), "unit": "week"})
    mc = collections.Counter((d.year, d.month) for d in ds)
    ms = months(*M_RANGE[p]); ys = [mc.get(m, 0) for m in ms]; MW[p] = (ms, ys)
    rows.append({**summ(p + "_month", ys, [0, 2, 4, 6, 8, 10, 15, 20]), "unit": "month"})
    for y in sorted({m[0] for m in ms}):
        z = [mc.get(m, 0) for m in ms if m[0] == y]
        rows.append({**summ(f"{p}_{y}_months", z, [0, 2, 4, 6, 8, 10, 15, 20]), "unit": "month"})
wr("A3_bills_distribution.csv", rows)
mr = []
for p in ("TrumpI", "TrumpII"):
    for (y, m), c in zip(*MW[p]): mr.append({"period": p, "month": f"{y}-{m:02d}", "public_laws_by_approved_date": c})
wr("A3b_bills_by_month.csv", mr)
# A4 bills conditional: given k laws by end of day d of the month, final month count
out = []; agg = collections.defaultdict(list)
for p in ("TrumpI", "TrumpII"):
    ds = pld[p]
    for (y, m) in MW[p][0]:
        days = [d.day for d in ds if d.year == y and d.month == m]
        for cut in (1, 8, 15, 22):
            k = sum(x <= cut for x in days); kb = "0" if k == 0 else "1-2" if k <= 2 else "3-5" if k <= 5 else "6+"
            agg[(p, cut, kb)].append(len(days))
for (p, cut, kb), fs in sorted(agg.items()):
    n = len(fs); r = {"period": p, "through_day_of_month": cut, "k_so_far_bucket": kb, "n_months": n, "mean_final": round(st.mean(fs), 2), "median_final": st.median(fs)}
    for N in (0, 1, 2, 3, 4, 5, 6, 8, 10, 15): r[f"P_final_gt_{N}"] = round(sum(f > N for f in fs) / n, 3)
    r["note"] = "n<5: do not use" if n < 5 else ""
    out.append(r)
wr("A4_bills_conditional_final_count.csv", out)
# reconciliation reference
open("A5_reconcile_note.txt", "w").write("EXECSUM (workers/EXECSUM_PROTOCOL.md): EO counts reproduce 96 of 96 Kalshi 'above N' markets; public laws by approved date reproduce 90 of 94 bills markets, misses KXBILLSCOUNT Mar 2026 (Kalshi 4, public laws 2) and Jul 2026 (Kalshi 0, public laws 2).\n")
for r in rows[:6]: print(r)
