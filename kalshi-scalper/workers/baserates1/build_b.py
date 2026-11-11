"""BASERATES1 table set B: mention base rates from data/ment1.sqlite (settled history already held). Descriptive only."""
import sqlite3, csv, math, collections, statistics as st, re
db = sqlite3.connect("../../data/ment1.sqlite")
Z90 = 1.645
def wil(k, n):
    if n == 0: return ("", "")
    p = k / n; z = Z90; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0, c - h), 3), round(min(1, c + h), 3))
def wr(f, rows):
    keys = []
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    w = csv.DictWriter(open(f, "w", newline=""), keys); w.writeheader(); w.writerows(rows)
EARN_SECTOR = {}
for s, tks in {
 "Tech": "AMD MSFT AAPL NFLX ORCL CRWD PANW ADBE ADOBE EA ROKU PYPL DELL TSMC MU PSKY CRWV SPCX MSTR RKLB",
 "Autos_Transport": "LUCID CVNA AAL NIO",
 "Retail_Consumer": "KR SFM HD TGT AS ARITZIA CHWY LULU ANF VSCO DOLLARGENERAL URBN BB",
 "Restaurants_Leisure": "YUM DPZ HLT AMC MTN CELH TOST",
 "Finance": "JPM MA ALLY HOOD TFC",
 "Industrials_Defense": "BA LMT TOL ACI KMX",
}.items():
    for t in tks.split(): EARN_SECTOR[t] = s
def family(series):
    if series.startswith("KXEARNINGSMENTION"): return "EARNINGS"
    if series.startswith("KXMENTIONEARN"): return "EARNINGS"
    return "NONEARN"
NONEARN_SECTOR = {}
for s, tks in {
 "Trump_speeches": "TRUMP TRUMPB DJTNATO DJTJUSTICE",
 "Other_US_politics": "VANCE LEAVITT LEAVITTSMF RUBIO JOHNSON GOVERNOR RFK NBIS CARNEY LAMMY STARMER STARMERB",
 "News_TV": "WORLDNEWS FOXNEWS CARLSON INGRAHAM MAHER BANNON ZAKARIA CANDACE SNL COOPER CAT",
 "Sports": "NCAA ATHLETE LEBRON SNF TNF FTN GAMEDAY SB DOGSHOW DWTS INFANTINO",
 "Entertainment": "SURVIVOR AWARD KARDASHIAN CENA ZIWE",
 "Business_Tech_Fed": "JENSEN ALTMAN AMODEI ECB TSLA ABNB MSFT SPANBERGER",
}.items():
    for t in tks.split(): NONEARN_SECTOR[t] = s
rows = db.execute("select ticker,series,close_ts,result from mk").fetchall()
mk = []
for tk, ser, c, res in rows:
    p = tk.split("-"); 
    if len(p) < 3: continue
    ev = "-".join(p[:-1]); word = p[-1]
    mk.append(dict(tk=tk, ser=ser, ev=ev, word=word, c=c, y=1 if res == "yes" else 0))
# sector label
def sector(ser):
    if family(ser) == "EARNINGS":
        t = ser.replace("KXEARNINGSMENTION", "").replace("KXMENTIONEARN", "")
        return "Earnings:" + EARN_SECTOR.get(t, "Unmapped")
    t = ser.replace("KX", "").replace("MENTION", "")
    return NONEARN_SECTOR.get(t, "Other")
for m in mk: m["sec"] = sector(m["ser"])
evc = {}
for m in mk: evc.setdefault(m["ev"], []).append(m["c"])
for m in mk: m["ec"] = st.median(evc[m["ev"]])
# B1 per series
by = collections.defaultdict(list)
for m in mk: by[m["ser"]].append(m)
out = []
for ser, L in sorted(by.items(), key=lambda x: -len(x[1])):
    n = len(L); k = sum(m["y"] for m in L); evs = {m["ev"] for m in L}
    lo, hi = wil(k, n)
    out.append({"series": ser, "sector": L[0]["sec"], "markets": n, "calls": len(evs), "words": len({m["word"] for m in L}), "yes_rate": round(k / n, 3), "ci90_lo": lo, "ci90_hi": hi, "words_per_call": round(n / len(evs), 1), "note": "n<30" if n < 30 else ""})
wr("B1_yes_rate_by_series.csv", out)
# B1b by sector and family
out = []
for key in ("sec",):
    g = collections.defaultdict(list)
    for m in mk: g[m[key]].append(m)
    for s, L in sorted(g.items()):
        n = len(L); k = sum(m["y"] for m in L); lo, hi = wil(k, n)
        out.append({"sector": s, "series": len({m["ser"] for m in L}), "calls": len({m["ev"] for m in L}), "markets": n, "yes_rate": round(k / n, 3), "ci90_lo": lo, "ci90_hi": hi})
n = len(mk); k = sum(m["y"] for m in mk); lo, hi = wil(k, n)
out.append({"sector": "ALL", "series": len(by), "calls": len(evc), "markets": n, "yes_rate": round(k / n, 3), "ci90_lo": lo, "ci90_hi": hi})
wr("B1b_yes_rate_by_sector.csv", out)
# B2 per series-word
g = collections.defaultdict(list)
for m in mk: g[(m["ser"], m["word"])].append(m)
out = []
for (ser, w), L in g.items():
    if len(L) < 8: continue
    n = len(L); k = sum(m["y"] for m in L); lo, hi = wil(k, n)
    out.append({"series": ser, "word_code": w, "sector": L[0]["sec"], "calls": n, "yes": k, "yes_rate": round(k / n, 3), "ci90_lo": lo, "ci90_hi": hi, "first_call_utc": min(m["c"] for m in L), "last_call_utc": max(m["c"] for m in L)})
out.sort(key=lambda r: (-r["calls"], r["series"]))
wr("B2_yes_rate_by_series_word_n8plus.csv", out)
# B3 call-level
out = []
for ser, L in sorted(by.items(), key=lambda x: -len(x[1])):
    e = collections.defaultdict(list)
    for m in L: e[m["ev"]].append(m["y"])
    sh = [sum(v) / len(v) for v in e.values() if len(v) >= 3]
    if len(sh) < 5: continue
    p = sum(m["y"] for m in L) / len(L); nb = st.mean(len(v) for v in e.values() if len(v) >= 3)
    out.append({"series": ser, "calls_with_3plus_words": len(sh), "mean_share_yes": round(st.mean(sh), 3), "sd_share_yes": round(st.pstdev(sh), 3),
                "sd_if_independent_binomial": round(math.sqrt(p * (1 - p) / nb), 3), "p10": round(sorted(sh)[int(0.1 * (len(sh) - 1))], 3), "p50": round(st.median(sh), 3), "p90": round(sorted(sh)[int(0.9 * (len(sh) - 1))], 3)})
wr("B3_call_level_share_yes.csv", out)
# B4 persistence: same series+word, ordered by call time; condition on previous appearance
def persist(groupkey):
    cnt = collections.defaultdict(lambda: [0, 0, 0, 0])  # [n_prev_yes, yes_after_yes, n_prev_no, yes_after_no]
    for (ser, w), L in g.items():
        L = sorted(L, key=lambda m: m["ec"])
        for a, b in zip(L, L[1:]):
            if b["ec"] - a["ec"] < 3600: continue
            c = cnt[groupkey(a)]
            if a["y"]: c[0] += 1; c[1] += b["y"]
            else: c[2] += 1; c[3] += b["y"]
    return cnt
def prow(name, c):
    n1, k1, n0, k0 = c; l1, h1 = wil(k1, n1); l0, h0 = wil(k0, n0)
    return {"group": name, "pairs_prev_yes": n1, "next_yes_given_prev_yes": round(k1 / n1, 3) if n1 else "", "ci90_a": l1, "ci90_b": h1,
            "pairs_prev_no": n0, "next_yes_given_prev_no": round(k0 / n0, 3) if n0 else "", "ci90_c": l0, "ci90_d": h0,
            "diff_yes_minus_no": round(k1 / n1 - k0 / n0, 3) if n1 and n0 else "", "note": "n<30 in a cell" if min(n1, n0) < 30 else ""}
out = []
allc = [0, 0, 0, 0]
for ser, c in persist(lambda m: m["ser"]).items():
    for i in range(4): allc[i] += c[i]
out.append(prow("ALL", allc))
for lab, fn in (("sector", lambda m: m["sec"]),):
    for s, c in sorted(persist(fn).items()): out.append(prow("sector:" + s, c))
for s, c in sorted(persist(lambda m: m["ser"]).items(), key=lambda x: -(x[1][0] + x[1][2])):
    if c[0] + c[2] >= 30: out.append(prow("series:" + s, c))
wr("B4_word_persistence.csv", out)
# B4b persistence by previous-call word yes-count in a run (streak)
run = collections.defaultdict(lambda: [0, 0])
for (ser, w), L in g.items():
    L = sorted(L, key=lambda m: m["ec"]); s = 0
    for i in range(1, len(L)):
        s = s + 1 if L[i - 1]["y"] else 0
        # streak of consecutive YES ending at previous call
        key = min(s, 4) if L[i - 1]["y"] else -min(sum(1 for _ in iter(()) ), 0)
        if not L[i - 1]["y"]:
            j = i - 1; z = 0
            while j >= 0 and not L[j]["y"]: z += 1; j -= 1
            key = -min(z, 4)
        run[key][0] += 1; run[key][1] += L[i]["y"]
out = []
for k in sorted(run):
    n, y = run[k]; lo, hi = wil(y, n)
    out.append({"streak_ending_at_previous_call": ("YES x%d%s" % (k, "+" if k == 4 else "")) if k > 0 else ("NO x%d%s" % (-k, "+" if k == -4 else "")), "pairs": n, "next_yes_rate": round(y / n, 3), "ci90_lo": lo, "ci90_hi": hi})
wr("B4b_word_streaks.csv", out)
# B4c the null: predicted by prior rate. expanding prior of the word (>=3 prior calls) vs next outcome, decile table
rows2 = []
for (ser, w), L in g.items():
    L = sorted(L, key=lambda m: m["ec"]); ys = 0
    for i, m in enumerate(L):
        if i >= 3: rows2.append((ys / i, m["y"], m["sec"]))
        ys += m["y"]
bins = [0, .1, .25, .5, .75, .9, 1.0001]
out = []
for a, b in zip(bins, bins[1:]):
    s = [r for r in rows2 if a <= r[0] < b]
    if s:
        k = sum(r[1] for r in s); lo, hi = wil(k, len(s))
        out.append({"word_prior_yes_rate_bin": f"[{a},{min(b,1)})", "n": len(s), "mean_prior": round(st.mean(r[0] for r in s), 3), "next_yes_rate": round(k / len(s), 3), "ci90_lo": lo, "ci90_hi": hi})
wr("B4c_prior_rate_vs_next_call.csv", out)
# B5 price vs base-rate gap (description only): decision quote = last candle ending >=1h before close, both sides quoted, spread<=0.05
cand = collections.defaultdict(list)
for tk, e, b, a in db.execute("select ticker,end_ts,bid_c,ask_c from candle"):
    cand[tk].append((e, b, a))
idx = {m["tk"]: m for m in mk}
hist = {key: sorted(L, key=lambda m: m["ec"]) for key, L in g.items()}
sh = {ser: sorted(L, key=lambda m: m["ec"]) for ser, L in by.items()}
def prior(m, minn=3):
    L = [x for x in hist[(m["ser"], m["word"])] if x["ec"] < m["ec"] - 3600]
    if len(L) >= minn: return sum(x["y"] for x in L) / len(L), "word", len(L)
    L = [x for x in sh[m["ser"]] if x["ec"] < m["ec"] - 3600]
    if len(L) >= 20: return sum(x["y"] for x in L) / len(L), "series", len(L)
    return None
res = []
for tk, cs in cand.items():
    m = idx.get(tk)
    if not m: continue
    ok = [c for c in cs if c[0] <= m["c"] - 3600 and c[1] is not None and c[2] is not None and c[2] - c[1] <= 0.05]
    if not ok: continue
    e, b, a = max(ok)
    pr = prior(m)
    if pr: res.append(dict(tk=tk, ser=m["ser"], sec=m["sec"], price=(a + b) / 2, base=pr[0], src=pr[1], np=pr[2]))
fine = []
for r in res: fine.append({"ticker": r["tk"], "series": r["ser"], "quote_mid": round(r["price"], 3), "prior_yes_rate": round(r["base"], 3), "prior_source": r["src"], "prior_n": r["np"], "gap_mid_minus_prior": round(r["price"] - r["base"], 3)})
wr("B5a_price_vs_base_rate_markets.csv", fine)
out = []
for a, b in zip([0, .1, .2, .3, .5, .7, .9], [.1, .2, .3, .5, .7, .9, 1.0001]):
    s = [r for r in res if a <= r["price"] < b]
    if s: out.append({"quote_mid_bin": f"[{a},{min(b,1)})", "n": len(s), "mean_quote_mid": round(st.mean(r["price"] for r in s), 3), "mean_prior_yes_rate": round(st.mean(r["base"] for r in s), 3), "mean_gap": round(st.mean(r["price"] - r["base"] for r in s), 3), "share_quote_above_prior": round(sum(r["price"] > r["base"] for r in s) / len(s), 3)})
wr("B5b_gap_by_quote_bin.csv", out)
out = []
g2 = collections.defaultdict(list)
for r in res: g2[r["sec"]].append(r)
for s, L in sorted(g2.items()):
    out.append({"sector": s, "n": len(L), "mean_quote_mid": round(st.mean(r["price"] for r in L), 3), "mean_prior_yes_rate": round(st.mean(r["base"] for r in L), 3), "mean_gap": round(st.mean(r["price"] - r["base"] for r in L), 3)})
wr("B5c_gap_by_sector.csv", out)
print(len(mk), len(evc), len(by), len(res), "unmapped earnings:", sorted({m["ser"] for m in mk if m["sec"].endswith("Unmapped")}), "other:", sorted({m["ser"] for m in mk if m["sec"]=="Other"}))
