#!/usr/bin/env python3
"""MECH1 screen, BUILD 2 (Testing Desk, Nov 17, 2026), blind from MECH1_SCREEN_SPEC_NOV17.md at 7068f8f3c (sha256 a58d449c904d450f36fe9572a2149ed5fe096cd28902533b3859c7df23bc8864), section 12 winning over earlier sections, sections 9 and 11, the CURRENT mech_schema.py docstring (f9cf4a9c7, classify rules written here from the text) and my readings M1 to M16, N1 to N14. Pure part: classify, tail cut, screen statistics, screens 1 and 2, BH, the section 9 print."""
import calendar, hashlib, json, math, time

MARKET = ("15m_crypto", "15m_noncrypto", "hourly_ladder", "stock_perp", "index_perp", "metal_perp", "crypto_perp", "combo", "politics", "sports", "weather", "economics", "entertainment", "other")
SIGNAL = ("price_level", "price_change", "spread", "book_depth_imbalance", "open_interest", "volume", "funding_rate", "settlement_mark", "tape_flow", "spot_elsewhere", "event_calendar", "cross_market_residual", "none", "external_model")
CLOCK = ("fixed_time_to_close", "time_of_day", "scheduled_event", "print", "reopen", "any_minute")
ENTRY = ("taker", "maker_touch", "both")
EXIT = ("hold_to_settle", "fixed_time", "take_profit_multiple", "stop", "next_print", "none")
SIDE = ("favourite", "cheap", "follow", "fade", "both", "any")
FIELDS = (("market", MARKET), ("signal", SIGNAL), ("clock", CLOCK), ("entry", ENTRY), ("exit", EXIT), ("side", SIDE))
PF_MIN = 1.0


def sig_id(c): return hashlib.sha256("|".join(c[f] for f, _ in FIELDS).encode()).hexdigest()[:16]
def vals(v): return ["*"] if v == "*" else (list(v) if isinstance(v, (list, tuple)) else [v])
def fm(entry_v, cand_v):
    v = vals(entry_v); return "*" in v or cand_v in v


def classify(cand, registry):
    """-> (verdict, ref, why, extra) per the current schema docstring: DECLINED (pattern match on all six fields, with tickers and exceptions), then SAME MECHANISM on signal, clock and exit (DUPLICATE on the same market family, else VERSION_NEW_MARKET with the first such entry), else NEW (provisional)."""
    for f, vocab in FIELDS:
        if cand.get(f) not in vocab: raise ValueError("candidate %s %r not in vocabulary" % (f, cand.get(f)))
    ctick = list(cand.get("tickers") or []); excluded = set()
    for e in registry:
        if e.get("kind") != "pattern" or not all(fm(e[f], cand[f]) for f, _ in FIELDS): continue
        if cand.get("idea") and cand["idea"] in (e.get("exceptions") or []): continue
        pt = e.get("tickers")
        if pt and pt != "*":
            if not ctick: continue
            hit = [t for t in ctick if t in pt]
            if not hit: continue
            if len(hit) < len(ctick): excluded.update(hit); continue
        return "DECLINED", e["id"], "declined pattern " + e["id"], {"provisional": False, "excluded_tickers": sorted(excluded)}
    ver = None
    for e in registry:
        if e.get("kind") == "pattern": continue
        if fm(e["signal"], cand["signal"]) and fm(e["clock"], cand["clock"]) and fm(e["exit"], cand["exit"]):
            if fm(e["market"], cand["market"]): return "DUPLICATE", e["id"], "duplicate of " + e["id"], {"provisional": False, "excluded_tickers": sorted(excluded)}
            ver = ver or e["id"]
    if ver: return "VERSION_NEW_MARKET", ver, "version of " + ver, {"provisional": False, "excluded_tickers": sorted(excluded)}
    return "NEW", None, "new", {"provisional": True, "excluded_tickers": sorted(excluded)}


def tail_threshold(xs):
    """12.2: ascending |x|, the value at sorted index ceil(0.9 n) - 1; n = 0: None. A signal fires when |x| >= threshold."""
    v = sorted(abs(x) for x in xs); n = len(v)
    return None if n == 0 else v[math.ceil(0.9 * n) - 1]


def date_ord(s): return calendar.timegm(time.strptime(s, "%Y-%m-%d")) // 86400
def days_inclusive(a, b): return date_ord(b) - date_ord(a) + 1


def pf(v):
    if not v: return None
    pos = sum(x for x in v if x > 0); neg = -sum(x for x in v if x < 0)
    if neg == 0: return "inf" if pos > 0 else None
    return pos / neg


def day_z_p(trades, key="net"):
    by = {}
    for t in trades: by[t["day"]] = by.get(t["day"], 0.0) + t[key]
    d = list(by.values()); k = len(d)
    if k < 2: return None, None
    m = sum(d) / k; sd = math.sqrt(sum((x - m) ** 2 for x in d) / (k - 1))
    if sd == 0: return None, None
    z = m / (sd / math.sqrt(k)); return z, 0.5 * math.erfc(z / math.sqrt(2))


def sort_trades(tr): return sorted(tr, key=lambda t: (t["entry_end"], t["market_id"]))


def halves(trades, start, end):
    """calendar split of [start, end]: the first floor(D / 2) days are half 1 (trade belongs to the half of its day)"""
    D = days_inclusive(start, end); cut = date_ord(start) + D // 2          # day ordinals below cut are half 1
    a = [t for t in trades if date_ord(t["day"]) < cut]; b = [t for t in trades if date_ord(t["day"]) >= cut]
    return a, b


def block(trades, header, start, end, cal_days):
    """statistics of one window on its TRADED records"""
    tr = sort_trades([t for t in trades if t["traded"]]); n = len(tr); mult = 10.0 if header["units"] == "usd10" else 1.0
    out = {"n": n, "trade_days": len(set(t["day"] for t in tr)), "calendar_days": cal_days}
    out["trades_per_day"] = n / cal_days if cal_days else None
    out["gross_edge_c"] = (sum(t["gross"] for t in tr) / n * mult) if n else None
    out["net_edge_c"] = (sum(t["net"] for t in tr) / n * mult) if n else None
    if header["units"] == "bp":
        out["pf_1c"] = pf([t["net"] for t in tr]); out["pf_2c"] = None
    else:
        out["pf_1c"] = pf([t["net_1c"] for t in tr]); out["pf_2c"] = pf([t["net_2c"] for t in tr])
    h1, h2 = halves(tr, start, end); out["pf_half1"] = pf([t["net"] for t in h1]); out["pf_half2"] = pf([t["net"] for t in h2])
    z, p = day_z_p(tr); out["day_z"] = z; out["p"] = p
    return out


def pf_ok(x): return x == "inf" or (x is not None and x >= PF_MIN)


def fmt(x):
    """section 12.12 print: floats %.17g (integral prints as 3), ints, true/false/null, strings, keys sorted, separators , and :"""
    if x is None: return "null"
    if x is True: return "true"
    if x is False: return "false"
    if isinstance(x, int): return str(x)
    if isinstance(x, float):
        if math.isnan(x) or math.isinf(x): raise ValueError("non finite float in the print")
        return "%.17g" % x
    if isinstance(x, str): return json.dumps(x)
    if isinstance(x, dict): return "{" + ",".join(json.dumps(k) + ":" + fmt(x[k]) for k in sorted(x)) + "}"
    if isinstance(x, (list, tuple)): return "[" + ",".join(fmt(v) for v in x) + "]"
    raise TypeError(type(x))


TRADE_KEYS = ("sig_id", "window", "day", "entry_end", "market_id", "traded", "gross", "cost", "net", "net_1c", "net_2c")
HEAD_KEYS = ("sig", "settings", "primary", "units", "tail", "threshold_value", "calendar_days_search", "data")


def read_records(lines):
    """JSON lines -> {sig_id: {'header', 'trades'}}; a missing or null required field raises"""
    sigs = {}; order = []
    for ln in lines:
        ln = ln.strip()
        if not ln: continue
        o = json.loads(ln)
        if "sig" in o:
            for k in HEAD_KEYS:
                if k not in o: raise ValueError("header lacks %s" % k)
            for f, _ in FIELDS:
                if f not in o["sig"]: raise ValueError("header sig lacks %s" % f)
            sid = sig_id(o["sig"]); sigs[sid] = {"header": o, "trades": []}; order.append(sid)
        else:
            for k in TRADE_KEYS:
                if k not in o: raise ValueError("trade lacks %s" % k)
            for k in ("sig_id", "window", "day", "entry_end", "market_id", "traded", "gross", "cost", "net"):
                if o[k] is None: raise ValueError("trade has null %s" % k)
            if o["sig_id"] not in sigs: raise ValueError("trade of an unknown signature %s" % o["sig_id"])
            if o["window"] not in ("search", "validate"): raise ValueError("bad window")
            h = sigs[o["sig_id"]]["header"]
            if h["units"] == "usd10" and (o["net_1c"] is None or o["net_2c"] is None): raise ValueError("binary trade lacks net_1c or net_2c")
            sigs[o["sig_id"]]["trades"].append(o)
    return sigs


def run(lines, registry, windows, m_carried, option_a=True, extra_summary=None, data_file_shas=None, rule_hashes=None, holds_file_sha256=None, holds_excluded=0):
    """windows = {'search': [start, end], 'validate': [start, end]} (UTC date strings); -> list of print lines (strings)"""
    sigs = read_records(lines); rows = []; ss, se = windows["search"]; vs, ve = windows["validate"]
    for sid in sorted(sigs):
        h = sigs[sid]["header"]; cand = dict(h["sig"]); verdict, ref, _why, extra = classify(cand, registry)
        scored = verdict in ("NEW", "VERSION_NEW_MARKET") and h["threshold_value"] is not None
        if verdict == "VERSION_NEW_MARKET" and not option_a: scored = False
        rows.append({"sid": sid, "h": h, "verdict": verdict, "ref": ref, "extra": extra, "scored": scored, "trades": sigs[sid]["trades"]})
    for r in rows:
        if not r["scored"]: continue
        h = r["h"]; tr = r["trades"]; S = [t for t in tr if t["window"] == "search"]; V = [t for t in tr if t["window"] == "validate"]
        r["search"] = block(S, h, ss, se, h["calendar_days_search"])
        r["validate"] = block(V, h, vs, ve, h.get("calendar_days_validate", days_inclusive(vs, ve)))
        r["screen1"] = bool(r["search"]["n"] > 0 and r["search"]["trades_per_day"] is not None and r["search"]["trades_per_day"] >= 3 and r["search"]["net_edge_c"] is not None and sum(t["net"] for t in S if t["traded"]) / r["search"]["n"] > 0)
        U = sort_trades([t for t in S + V if t["traded"]]); u1, u2 = halves(U, ss, ve); pf1, pf2 = pf([t["net"] for t in u1]), pf([t["net"] for t in u2])
        r["screen2"] = bool(r["screen1"] and len(U) >= 100 and len(set(t["day"] for t in U)) >= 10 and pf_ok(pf1) and pf_ok(pf2) and sum(t["net"] for t in U) / len(U) > 0)
        z, p = day_z_p(U); r["p_union"] = 1.0 if p is None else p
    scored = [r for r in rows if r["scored"]]; settings_counted = len(scored); m_total = m_carried + settings_counted
    rank = sorted(scored, key=lambda r: (r["p_union"], r["sid"])); k = 0
    for i, r in enumerate(rank, 1):
        if r["p_union"] <= i * 0.05 / m_total: k = i
    surv = set(r["sid"] for r in rank[:k] if r["screen2"])
    out = []; cum = 0
    for r in rows:
        h = r["h"]; c = h["sig"]
        if r["scored"]: cum += 1
        line = {"sig_id": r["sid"], "market": c["market"], "signal": c["signal"], "clock": c["clock"], "entry": c["entry"], "exit": c["exit"], "side": c["side"], "class": r["verdict"], "class_ref": r["ref"], "scored": r["scored"], "heldout_read": False, "provisional": bool(r["extra"]["provisional"]), "excluded_tickers": list(r["extra"]["excluded_tickers"]), "m": m_carried + cum}
        if r["scored"]:
            line.update({"data": h["data"], "setting": {"threshold_value": h["threshold_value"], "tail": h["tail"], "hold_s": h.get("hold_s"), "tp_mult": h.get("tp_mult"), "stop_mult": h.get("stop_mult")}, "search": r["search"], "validate": r["validate"], "screen1": r["screen1"], "screen2": r["screen2"], "bh_survivor": r["sid"] in surv})
        else:
            line.update({"data": h["data"] if isinstance(h.get("data"), str) else None, "setting": None, "search": None, "validate": None, "screen1": False, "screen2": False, "bh_survivor": False})
        out.append(fmt(line))
    summary = {"tried": settings_counted, "settings_counted": settings_counted, "m_carried": m_carried, "m_total": m_total, "screen1_pass": sum(1 for r in scored if r["screen1"]), "screen2_pass": sum(1 for r in scored if r["screen2"]), "bh_survivors": len(surv), "windows": {"search": list(windows["search"]), "validate": list(windows["validate"])}, "PF_MIN": PF_MIN, "rule_hashes": rule_hashes or {}, "data_file_shas": data_file_shas or {}, "holds_file_sha256": holds_file_sha256, "holds_excluded": holds_excluded}
    summary.update(extra_summary or {})
    out.append(fmt({"summary": summary}))
    return out
