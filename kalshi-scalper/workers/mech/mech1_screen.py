"""MECH1 screen, Desk A's build (Nov 17, 2026), built to MECH1_SCREEN_SPEC_NOV17.md sections 1 to 12 (section 12 wins). The PURE part: classify, the screens, BH and the section 9 print, on a record file written by the generator.
  python3 -I mech1_screen.py <records.jsonl[.gz]> <MECH_REGISTRY.json> <m_carried> [--schema-dir DIR] [--holds-sha SHA] [--holds-excluded N] > print.txt
No I/O except reading the files named and writing the print to stdout."""
import sys, os, json, gzip, math, hashlib, collections, importlib
here = os.path.dirname(os.path.abspath(__file__))
PF_MIN = 1.0
W = {"search": ("2026-09-02", "2026-10-06"), "validate": ("2026-10-07", "2026-10-26")}; HALF1_TO, HALF2_FROM = "2026-09-28", "2026-09-29"       # 12.6 constants (perps minute candles); a header may carry its own
def days_between(a, b):
    import datetime
    d0 = datetime.date.fromisoformat(a); d1 = datetime.date.fromisoformat(b); return (d1 - d0).days + 1
def add_days(a, n):
    import datetime
    return (datetime.date.fromisoformat(a) + datetime.timedelta(days=n)).isoformat()
def pf(xs):
    if not xs: return None
    w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    if l == 0: return "inf" if w > 0 else None
    return w / l
def day_z(recs):
    by = collections.defaultdict(float)
    for r in recs: by[r["day"]] += r["net"]
    v = list(by.values()); k = len(v)
    if k < 2: return None
    m = sum(v) / k; sd = math.sqrt(sum((x - m) ** 2 for x in v) / (k - 1))
    return None if sd == 0 else m / (sd / math.sqrt(k))
def pval(z): return None if z is None else 0.5 * math.erfc(z / math.sqrt(2))
def block(recs, units, primary, cal_days, lo, hi, scale):
    """statistics of one window's TRADED records. cal_days: the window's calendar days for trades a day; lo, hi: its date range for its own halves."""
    tr = sorted([r for r in recs if r["traded"]], key=lambda r: (r["entry_end"], r["market_id"]))
    n = len(tr); nets = [r["net"] for r in tr]
    out = {"n": n, "trade_days": len({r["day"] for r in tr}), "calendar_days": cal_days, "trades_per_day": (n / cal_days) if cal_days else None}
    out["gross_edge_c"] = (sum(r["gross"] for r in tr) / n * scale) if n else None
    out["net_edge_c"] = (sum(nets) / n * scale) if n else None
    if units == "bp": out["pf_1c"] = pf(nets); out["pf_2c"] = None
    else:
        out["pf_1c"] = pf([r["net_1c"] for r in tr]); out["pf_2c"] = pf([r["net_2c"] for r in tr])
    D = days_between(lo, hi); b = add_days(lo, D // 2 - 1)
    h1 = [r["net"] for r in tr if r["day"] <= b]; h2 = [r["net"] for r in tr if r["day"] > b]
    out["pf_half1"] = pf(h1); out["pf_half2"] = pf(h2)
    z = day_z(tr); out["day_z"] = z; out["p"] = pval(z)
    return out
def fnum(x):
    if x == "inf": return '"inf"'
    s = "%.17g" % x
    if s in ("inf", "-inf", "nan"): raise SystemExit("non-finite float in the print")
    return s
def dumps(o):
    if o is None: return "null"
    if o is True: return "true"
    if o is False: return "false"
    if isinstance(o, int): return str(o)
    if isinstance(o, float): return fnum(o)
    if isinstance(o, str): return json.dumps(o)
    if isinstance(o, (list, tuple)): return "[" + ",".join(dumps(x) for x in o) + "]"
    if isinstance(o, dict): return "{" + ",".join(json.dumps(k) + ":" + dumps(o[k]) for k in sorted(o)) + "}"
    raise TypeError(type(o))
def sig_id(s): return hashlib.sha256("|".join(s[k] for k in ("market", "signal", "clock", "entry", "exit", "side")).encode()).hexdigest()[:16]
def main(rec_path, reg_path, m_carried, schema_dir=None, holds_sha=None, holds_excluded=0):
    sd = schema_dir or here; sys.path.insert(0, sd); S = importlib.import_module("mech_schema")
    reg = json.load(open(reg_path))["entries"]
    op = gzip.open if rec_path.endswith(".gz") else open
    heads, recs = {}, collections.defaultdict(list)
    for line in op(rec_path, "rt"):
        o = json.loads(line)
        if "sig" in o: heads[sig_id(o["sig"])] = o
        else:
            for k in ("sig_id", "window", "day", "entry_end", "market_id", "traded", "gross", "cost", "net"):
                if o.get(k) is None: raise SystemExit("record with a missing %s" % k)
            recs[o["sig_id"]].append(o)
    lines = []
    for sid in sorted(heads):
        h = heads[sid]; s = h["sig"]
        cand = dict(s); 
        if h.get("tickers"): cand["tickers"] = h["tickers"]
        if h.get("idea"): cand["idea"] = h["idea"]
        r = S.classify(cand, reg); verdict, ref, extra = r[0], r[1], (r[3] if len(r) > 3 else {})
        scored = verdict in ("NEW", "VERSION_NEW_MARKET", "UNVERIFIED_MATCH") and h.get("threshold_value") is not None
        L = {"sig_id": sid, "class": verdict, "class_ref": ref, "scored": scored, "heldout_read": False, "provisional": bool(extra.get("provisional")), "excluded_tickers": extra.get("excluded_tickers", [])}
        L.update(s)
        L["data"] = h["data"] if isinstance(h.get("data"), str) else None
        if not scored:
            L.update({"setting": None, "search": None, "validate": None, "screen1": False, "screen2": False, "screen2_pf_half1": None, "screen2_pf_half2": None, "bh_survivor": False, "p_union": None})
            lines.append(L); continue
        units = h["units"]; primary = h["primary"]; scale = 10.0 if units == "usd10" else 1.0
        sf, st = h.get("search_from", W["search"][0]), h.get("search_to", W["search"][1]); vf, vt = h.get("validate_from", W["validate"][0]), h.get("validate_to", W["validate"][1])
        cds = h.get("calendar_days_search"); cdv = h.get("calendar_days_validate", days_between(vf, vt))
        rs = [x for x in recs.get(sid, []) if x["window"] == "search"]; rv = [x for x in recs.get(sid, []) if x["window"] == "validate"]
        bs = block(rs, units, primary, cds, sf, st, scale); bv = block(rv, units, primary, cdv, vf, vt, scale)
        L["setting"] = {"threshold_value": h["threshold_value"], "tail": h.get("tail"), "hold_s": h.get("hold_s"), "tp_mult": h.get("tp_mult"), "stop_mult": h.get("stop_mult")}
        L["search"] = bs; L["validate"] = bv
        s1 = bs["trades_per_day"] is not None and bs["trades_per_day"] >= 3 and bs["net_edge_c"] is not None and bs["net_edge_c"] > 0
        L["screen1"] = bool(s1)
        union = sorted([x for x in rs + rv if x["traded"]], key=lambda r: (r["entry_end"], r["market_id"]))
        h1t = h.get("half1_to", HALF1_TO); 
        n1 = [x["net"] for x in union if x["day"] <= h1t]; n2 = [x["net"] for x in union if x["day"] > h1t]
        p1, p2 = pf(n1), pf(n2); L["screen2_pf_half1"] = p1; L["screen2_pf_half2"] = p2
        z = day_z(union); L["p_union"] = pval(z)
        def okpf(v): return v is not None and (v == "inf" or v >= PF_MIN)
        mean_net = (sum(x["net"] for x in union) / len(union)) if union else None
        L["screen2"] = bool(s1 and len(union) >= 100 and len({x["day"] for x in union}) >= 10 and okpf(p1) and okpf(p2) and mean_net is not None and mean_net > 0)
        L["bh_survivor"] = False
        lines.append(L)
    scored_lines = [L for L in lines if L["scored"]]
    m_total = m_carried + len(scored_lines)
    rank = sorted(scored_lines, key=lambda L: (1.0 if L["p_union"] is None else L["p_union"], L["sig_id"]))
    k = 0
    for i, L in enumerate(rank, 1):
        p = 1.0 if L["p_union"] is None else L["p_union"]
        if p <= i * 0.05 / m_total: k = i
    for i, L in enumerate(rank, 1):
        if i <= k and L["screen2"]: L["bh_survivor"] = True
    cum = 0
    for L in lines:
        if L["scored"]: cum += 1
        L["m"] = m_carried + cum
    out = [dumps(L) for L in lines]
    summ = {"tried": len(scored_lines), "settings_counted": len(scored_lines), "m_carried": m_carried, "m_total": m_total, "PF_MIN": PF_MIN, "screen1_pass": sum(1 for L in scored_lines if L["screen1"]), "screen2_pass": sum(1 for L in scored_lines if L["screen2"]),
            "bh_survivors": sum(1 for L in lines if L["bh_survivor"]), "windows": {"search": list(W["search"]), "validate": list(W["validate"]), "half1_to": HALF1_TO, "half2_from": HALF2_FROM},
            "classes": dict(collections.Counter(L["class"] for L in lines)), "holds_file_sha256": holds_sha, "holds_excluded": holds_excluded,
            "rule_hashes": {"mech1_screen.py": hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest(), "mech_schema.py": hashlib.sha256(open(os.path.join(sd, "mech_schema.py"), "rb").read()).hexdigest()},
            "data_file_shas": {os.path.basename(rec_path): hashlib.sha256(open(rec_path, "rb").read()).hexdigest(), os.path.basename(reg_path): hashlib.sha256(open(reg_path, "rb").read()).hexdigest()}}
    out.append('{"summary":' + dumps(summ) + "}")
    sys.stdout.write("\n".join(out) + "\n")
if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 3: sys.exit(__doc__)
    kw = {}; i = 3
    while i < len(a):
        if a[i] == "--schema-dir": kw["schema_dir"] = a[i + 1]
        elif a[i] == "--holds-sha": kw["holds_sha"] = a[i + 1]
        elif a[i] == "--holds-excluded": kw["holds_excluded"] = int(a[i + 1])
        i += 2
    main(a[0], a[1], int(a[2]), **kw)
