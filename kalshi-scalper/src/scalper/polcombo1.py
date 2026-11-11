"""POLCOMBO1 census (workers/POLCOMBO1_PROTOCOL.md). Read-only, public GET, 2s spacing, stops at first 429."""
import sys, json, math, time, urllib.request, urllib.parse, urllib.error, collections, datetime
BASE = "https://api.elections.kalshi.com/trade-api/v2"
last = [0.0]; reads = [0]
class Stop(Exception): pass
halted=[None]
def get(path, params=None):
    if halted[0]: return None
    w = 2.0 - (time.time() - last[0])
    if w > 0: time.sleep(w)
    last[0] = time.time(); reads[0] += 1
    q = ("?" + urllib.parse.urlencode(params)) if params else ""
    try:
        with urllib.request.urlopen(BASE + path + q, timeout=30) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 429:
            halted[0] = "429 at " + path; return None
        return None
    except Exception: return None
def fee(p): return math.ceil(0.07 * 10 * p * (1 - p) * 100 - 1e-9) / 10 / 100
PFX = ["KXPRES","KXSEN","KXHOUSE","KXGOV","KXELECT","KXTRUMP","KXCONGRESS","KXBILL","KXSHUTDOWN","KXFED","KXLEAVE","KXSCOTUS","KXCABINET","KXPOLL","KXAPPROVAL"]
out = {}
try:
    ser = get("/series", {"category": "Exotics"}) or {}
    names = sorted({s["ticker"] for s in ser.get("series", []) if s["ticker"].startswith("KXMVE")})
    out["mve_series_found"] = names
    SERIES = names or ["KXMVECROSSCATEGORY"]
    combos = []; tot = collections.Counter()
    for s in SERIES:
        cur = None
        for page in range(3):
            p = {"status": "open", "limit": 100, "series_ticker": s}
            if cur: p["cursor"] = cur
            d = get("/markets", p)
            if not d: break
            for m in d.get("markets", []):
                cs = m.get("custom_strike") or {}
                ml = [x for x in (cs.get("Associated Markets") or "").split(",") if x]
                sd = [x for x in (cs.get("Associated Market Sides") or "").split(",") if x]
                if ml and len(ml) == len(sd):
                    tot[(s, len(ml))] += 1
                    combos.append(dict(t=m["ticker"], s=s, legs=ml, sides=sd, bid=float(m.get("yes_bid_dollars") or 0), ask=float(m.get("yes_ask_dollars") or 0), fee_fields={k: m[k] for k in m if "fee" in k}))
            cur = d.get("cursor")
            if not cur: break
    out["open_combos_read"] = len(combos)
    out["by_series_legcount"] = {"%s|%d" % k: v for k, v in sorted(tot.items())}
    # cheap pre-filter: leg series prefix on the list (event category read only for survivors)
    def evt(l): return l.rsplit("-", 1)[0] if l.count("-") >= 2 else l
    def prefix_ok(l): return any(l.startswith(p) for p in PFX)
    cand = [c for c in combos if 2 <= len(c["legs"]) <= 5 and all(prefix_ok(l) for l in c["legs"])]
    anyp = [c for c in combos if any(prefix_ok(l) for l in c["legs"])]
    out["combos_any_leg_on_politics_prefix"] = len(anyp)
    out["combos_2to5_all_legs_politics_prefix"] = len(cand)
    out["leg_prefix_sample_of_all_combos"] = collections.Counter(l.split("-")[0] for c in combos for l in c["legs"]).most_common(25)
    # category check of leg events for a sample of distinct leg events (<=60 reads)
    evs = collections.Counter(evt(l) for c in combos for l in c["legs"])
    cat = {}
    for e, _ in evs.most_common(60):
        d = get("/events/" + e)
        if d and d.get("event"): cat[e] = d["event"].get("category")
    out["event_category_counts_top60_leg_events"] = collections.Counter(cat.values()).most_common()
    pol = lambda l: cat.get(evt(l)) in ("Politics", "Elections") or (evt(l) not in cat and prefix_ok(l))
    inscope = [c for c in combos if 2 <= len(c["legs"]) <= 5 and all(pol(l) for l in c["legs"])]
    out["politics_only_2to5_legs_by_n"] = dict(collections.Counter(len(c["legs"]) for c in inscope))
    out["politics_only_6plus"] = sum(1 for c in combos if len(c["legs"]) > 5 and all(pol(l) for l in c["legs"]))
    # price in-scope
    need = sorted({l for c in inscope for l in c["legs"]})[:200]
    q = {}; close = {}
    for i in range(0, len(need), 100):
        d = get("/markets", {"tickers": ",".join(need[i:i+100]), "limit": 100})
        for m in (d or {}).get("markets", []):
            b, a = float(m.get("yes_bid_dollars") or 0), float(m.get("yes_ask_dollars") or 0)
            close[m["ticker"]] = m.get("close_time")
            if a > 0 and b > 0: q[m["ticker"]] = (b + a) / 2
    now = datetime.datetime.now(datetime.timezone.utc)
    def within14(l):
        t = close.get(l)
        if not t: return False
        return (datetime.datetime.fromisoformat(t.replace("Z", "+00:00")) - now).days <= 14
    rows = []
    for c in inscope:
        if not all(within14(l) for l in c["legs"]): continue
        out.setdefault("inscope_14d_by_n", collections.Counter())[len(c["legs"])] += 1
        if not all(l in q for l in c["legs"]): continue
        ps = [q[l] if sd == "yes" else 1 - q[l] for l, sd in zip(c["legs"], c["sides"])]
        pi = math.prod(ps); lo = max(0, sum(ps) - (len(ps) - 1)); hi = min(ps)
        rows.append(dict(t=c["t"], n=len(ps), ask=c["ask"], bid=c["bid"], p_ind=round(pi, 4), frechet=[round(lo, 4), round(hi, 4)], fee=fee(c["ask"]) if c["ask"] else None, edge_if_indep=round(pi - c["ask"] - fee(c["ask"]), 4) if c["ask"] else None, haircut=round(c["ask"] / pi, 2) if pi and c["ask"] else None))
    out["inscope_14d_by_n"] = dict(out.get("inscope_14d_by_n", {}))
    out["priced_rows"] = rows
    # settled history
    sett = collections.Counter(); 
    for s in SERIES[:6]:
        d = get("/markets", {"status": "settled", "limit": 100, "series_ticker": s})
        if not d: continue
        for m in d.get("markets", []):
            cs = m.get("custom_strike") or {}
            ml = [x for x in (cs.get("Associated Markets") or "").split(",") if x]
            sett[(s, len(ml), all(prefix_ok(l) for l in ml))] += 1
    out["settled_first_page_by_series_legs_politicsprefix"] = {"%s|%d|%s" % k: v for k, v in sett.items()}
except Stop as e:
    out["STOPPED"] = str(e)
out["STOPPED"] = halted[0]
out["reads"] = reads[0]
json.dump(out, open("workers/POLCOMBO1_CENSUS.json", "w"), indent=1, default=str)
print(json.dumps(out, indent=1, default=str)[:6000])
