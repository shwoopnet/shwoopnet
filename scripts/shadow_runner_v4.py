#!/usr/bin/env python3
"""The forward shadow runner for SHADOW_LIST_V2, V3 and V4 (Nov 17, 2026, the Head of R&D's order, Desk A's packages, Auditor B's pins). LOG ONLY: it places no order, holds no key, writes no Firestore and touches nothing under functions/.
It is a SEPARATE file from shadow_runner.py (V1) on purpose: V1's runner sha, state key and output files are untouched, V1 keeps running beside it, and every list here has its own config, its own state and its own output files (shadow_results_<v>.json, shadow_counts_<v>.json, v in v2, v3, v4).
What these lists add over V1 (Desk A's configs): the filters oiacc (open interest acceleration of the pick's own market), btcmom3, ethmom3 and goldmom3 (the YES mid change of the OTHER series' market with the SAME close: KXBTC15M, KXETH15M or KXGOLD15M) and swid (the change of the entry candle's spread against the candle 180 s earlier), all sign classes by the enumerator's cls,
and vspike (volume of the entry candle against the mean of the 5 earlier minutes, low, mid or high by FROZEN tercile cuts from the archive SEARCH half; a list whose picks need cuts must carry the cuts file, pinned by sha256, or those picks are listed in the config as excluded and are not run).
Features come from Desk A's audited functions pinned by sha256 (engine1_batchc.oiacc and xmom, engine1_batchb.btcmom3, engine1_batchb2.swid and vspike, engine1_enum.cls). A feature with any candle missing is no feature and no entry.
Everything else is V1's code, imported unchanged: the Puller (public GETs only, api.elections.kalshi.com, one request a second, three 429s stop the run, no redirects, no key), the held-out guard (scripts/shadow_holds.py reading HOLDS.json, S1 row), the engine core's scoring
at a 1c and a 2c worse fill, void scored as minus the entry fee, aggregates only (clause S1). The start is a written constant per list (the later of the list's start_utc and this runner's merge); a pick may start later (the Bitcoin picks, H09)."""
import json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shadow_runner as R   # V1's pure helpers and Puller, unchanged

OTHER = {"btcmom3": "KXBTC15M", "ethmom3": "KXETH15M", "goldmom3": "KXGOLD15M"}
OWN = ("oiacc", "swid", "vspike")
LISTS = ("V2", "V3", "V4")


def out_names(v):
    return "shadow_results_%s.json" % v.lower(), "shadow_counts_%s.json" % v.lower()


def candle_rows_v4(body, kept_close):
    """V1's candle mapping with Desk A's open interest rule: open_interest_fp, else open_interest."""
    out = {}
    for mk in (body.get("markets") if isinstance(body, dict) and isinstance(body.get("markets"), list) else []):
        tk = mk.get("market_ticker")
        if tk not in kept_close:
            continue
        for k in mk.get("candlesticks", []):
            try:
                e = int(k["end_period_ts"]); bid = float(k["yes_bid"]["close_dollars"]); ask = float(k["yes_ask"]["close_dollars"])
            except (KeyError, TypeError, ValueError):
                continue
            if e > kept_close[tk]:
                continue
            oi = R.num(k.get("open_interest_fp"))
            if oi is None:
                oi = R.num(k.get("open_interest"))
            out.setdefault(tk, {}).setdefault(e, (e, bid, ask, R.num((k.get("price") or {}).get("close_dollars")), R.num(k.get("volume_fp")), oi))
    return out


def feature_class(mods, name, market, other_idx, e, cuts=None, bucket=None):
    """-> 'up', 'flat', 'down' (or 'low', 'mid', 'high' for vspike) or None (missing). oiacc, swid and vspike read the market's own candles; btcmom3, ethmom3 and goldmom3 read the other series' market with the same close (other_idx = {end: candle} of it)."""
    N, C = mods["engine1_enum"], mods["engine1_batchc"]
    by_end = {c[0]: c for c in market["candles"] if c[0] <= market["close"]}
    if name == "oiacc":
        x = C.oiacc(by_end, e)
    elif name == "swid":
        x = mods["engine1_batchb2"].swid(by_end, e)
    elif name == "vspike":
        v = mods["engine1_batchb2"].vspike(by_end, e)
        c = ((cuts or {}).get("all_series_buckets", {}).get(market["series"], {})).get(str(bucket)) or {}
        c1, c2 = c.get("c1"), c.get("c2")
        if v is None or c1 is None or c2 is None:
            return None
        return "low" if v <= c1 else ("mid" if v <= c2 else "high")
    elif name in OTHER:
        x = None if other_idx is None else C.xmom(other_idx, e)
    else:
        raise R.Refused("feature %s is not one this runner knows" % name)
    return None if x is None else N.cls(x)


def v4_entry(mods, spec, market, other_idx, cuts=None):
    """The enumerator's entry rules (engine1_enum.entries) with one of these filters: -> entry dict or None."""
    N = mods["engine1_enum"]
    e_ = spec["entry"]; name, want = R.parse_filter(e_["filter"]); bucket, band, side_rule = e_["seconds_left"], e_["price_band_5c"], e_["side_rule"]
    by_end = {c[0]: c for c in market["candles"] if c[0] <= market["close"]}
    e = market["close"] - bucket
    c = by_end.get(e)
    if c is None or not (0 < c[1] < c[2] < 1):
        return None
    ya, na = N.asks(c); side = N.side_for(side_rule, ya, na); a = ya if side == "yes" else na
    if not (5 <= a <= 94) or a // 5 != band:
        return None
    k = feature_class(mods, name, market, other_idx, e, cuts, bucket)
    if k is None or k != want:
        return None
    ra = N.raw_ask(c, side)
    return {"side": side, "ask": ra, "entry_end": e, "whole_cent": abs(ra * 100 - round(ra * 100)) < 1e-6}


def spec_start(spec, cfg_start):
    t = R.iso_epoch(spec.get("start_utc"))
    return max(cfg_start, t) if t is not None else cfg_start


def score_spec_v4(mods, spec, markets, other_by_close, cfg_start, guard, guard_series, sha256, cuts=None):
    """-> (new trades, refused count). Same trade shape and scoring as V1's score_spec; a market is skipped unless the guard clears it for this spec."""
    K, D = mods["engine1_core"], mods["engine1_driver"]
    start = spec_start(spec, cfg_start); bucket = spec["entry"]["seconds_left"]
    name = R.parse_filter(spec["entry"]["filter"])[0]
    info = {"sha256": sha256, "series": guard_series, "start_utc": start}
    trades, refused = [], 0
    for m in markets:
        if m["close"] < start or m["close"] - bucket < start:
            continue
        ok, _why = guard(info, m["ticker"], m["close"])
        if not ok:
            refused += 1
            continue
        other = None
        if name in OTHER:
            om = other_by_close.get(OTHER[name], {}).get(m["close"])
            if om is None:
                continue
            ok2, _w = guard(info, om["ticker"], om["close"])
            if not ok2 or not om["candles"]:
                continue
            other = {c[0]: c for c in om["candles"] if c[0] <= om["close"]}
        ent = v4_entry(mods, spec, m, other, cuts)
        if ent is None:
            continue
        core = D.to_core(m, ent)
        x1, x2, held = R.score_both(K, core, spec["exit"])
        if x1 is None or x2 is None:
            continue
        trades.append({"t": m["ticker"], "c": m["close"], "d": R.day_of(m["close"]), "x1": x1, "x2": x2, "w": 1 if m["result"] == ent["side"] else 0, "v": 1 if m["result"] == "void" else 0, "h": held})
    return trades, refused


def config_path(root, v):
    return os.path.join(root, "kalshi-scalper", "workers", "shadow", "SHADOW_RUNNER_%s_CONFIG.json" % v)


def load_config(root, v="V4"):
    with open(config_path(root, v), encoding="utf-8") as f:
        return json.load(f)


def verified_inputs(root, cfg):
    w = os.path.join(root, "kalshi-scalper", "workers")
    lp = os.path.join(w, cfg["list_file"])
    if R.sha_of(lp) != cfg["list_sha256"]:
        raise R.Refused("the shadow list is not the pinned one")
    cuts = None
    if cfg.get("vspike_cuts_file"):
        cp = os.path.join(w, cfg["vspike_cuts_file"])
        if R.sha_of(cp) != cfg["vspike_cuts_sha256"]:
            raise R.Refused("the vspike cuts file is not the pinned one")
        with open(cp, encoding="utf-8") as f:
            cuts = json.load(f)
    mods = R.load_modules(os.path.join(w, "desk_a_verify"), cfg["modules"])
    import shadow_holds as H
    table = H.load(os.path.join(w, "HOLDS.json"))
    with open(lp, encoding="utf-8") as f:
        lst = json.load(f)
    excluded = set(cfg.get("excluded_picks", {}))
    for item in lst["specs"]:
        name = R.parse_filter(item["spec"]["entry"]["filter"])[0]
        if name == "vspike" and cuts is None and item["spec"]["id"] not in excluded:
            raise R.Refused("pick %s needs vspike cuts and the config has none (list it in excluded_picks or add the pinned cuts file)" % item["spec"]["id"])
    return lst, mods, table, H, cuts


def cache_key(root, lists=LISTS):
    parts = []
    for v in lists:
        if os.path.exists(config_path(root, v)):
            parts.append(load_config(root, v).get("list_sha256", "")[:8])
    return "shadow-state-v234-%s-%s-%s" % ("-".join(parts), R.sha_of(os.path.abspath(__file__))[:12], R.sha_of(os.path.join(root, "kalshi-scalper", "workers", "HOLDS.json"))[:12])


def run_list(root, v, now, puller, state):
    """One daily run of ONE list. -> (results_doc, counts_doc, state)."""
    cfg = load_config(root, v)
    lst, mods, table, H, cuts = verified_inputs(root, cfg)
    start = cfg["start_utc"]
    excluded = set(cfg.get("excluded_picks", {}))
    specs = [i for i in lst["specs"] if i["spec"]["id"] not in excluded]
    own = sorted({s["spec"]["market"] for s in specs})
    others = sorted({OTHER[R.parse_filter(s["spec"]["entry"]["filter"])[0]] for s in specs if R.parse_filter(s["spec"]["entry"]["filter"])[0] in OTHER})
    series_all = sorted(set(own) | set(others))
    guard = lambda info, ticker, close: H.decide(table, info, ticker, close)
    st = json.loads(json.dumps(state)) if state else {}
    st.setdefault("pulled_until", {}); st.setdefault("trades", {})
    max_close = now - R.SETTLE_LAG_S
    fetched = {}
    for series in series_all:
        lo = max(start, st["pulled_until"].get(series, start))
        if max_close < lo:
            continue
        users = [(i["spec"], i["spec_sha256"]) for i in specs if i["spec"]["market"] == series or OTHER.get(R.parse_filter(i["spec"]["entry"]["filter"])[0]) == series]
        def keep(m, users=users):
            return any(m["close"] >= spec_start(sp, start) and guard({"sha256": sh, "series": series_all, "start_utc": spec_start(sp, start)}, m["ticker"], m["close"])[0] for sp, sh in users)
        fetched[series] = fetch_v4(puller, series, lo, max_close, keep)
    by_close = {s: {m["close"]: m for m in ms} for s, ms in fetched.items()}
    results, counts = {}, []
    for item in specs:
        spec, sha = item["spec"], item["spec_sha256"]
        mine = st["trades"].setdefault(spec["id"], {"seq": [], "n_days": 0, "last_day": ""})
        new, refused = score_spec_v4(mods, spec, fetched.get(spec["market"], []), by_close, start, guard, series_all, sha, cuts)
        for t in sorted(new, key=lambda t: (t["c"], t["t"])):
            mine["seq"].append([t["x1"], t["x2"], t["v"], t.get("h", 0)])
            if t["d"] != mine["last_day"]:
                mine["n_days"] += 1; mine["last_day"] = t["d"]
        sstart = spec_start(spec, start)
        a = R.aggregate(mods, mine["seq"], mine["n_days"], sstart, now)
        a["status"] = R.status_of(a); a["days_to_100"] = R.days_to_100(a)
        a["refused_by_guard"] = st.setdefault("refused", {}).get(spec["id"], 0) + refused
        st["refused"][spec["id"]] = a["refused_by_guard"]
        stamp0 = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(sstart))
        results[spec["id"]] = dict(a, admission=item.get("admission"), market=spec["market"], spec_sha256=sha, start_utc=stamp0)
        counts.append({"id": spec["id"], "signals": a["n"], "settled": a["n"], "wins": a["wins"], "voids": a["voids"], "scored_at_settlement": a["scored_at_settlement"], "target": 100, "status": a["status"], "expected_days_to_100": a["days_to_100"],
                       "start_utc": stamp0, "as_of_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))})
    for series in fetched:
        st["pulled_until"][series] = max_close + 1
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
    doc = {"list": lst["list"], "as_of_utc": stamp, "labels": {"forward": R.LABEL_FWD, "paper": R.LABEL_PAPER}, "excluded_picks": cfg.get("excluded_picks", {}), "specs": results}
    return doc, {"as_of_utc": stamp, "rebuilt_from_scratch": not state, "specs": counts}, st


def fetch_v4(puller, series, min_close, max_close, keep):
    """V1's fetch_markets with the V4 candle mapping (open interest fallback): the settled markets of one series, candles only for the ones the guard clears."""
    orig = R.candle_rows
    R.candle_rows = candle_rows_v4
    try:
        return R.fetch_markets(puller, series, min_close, max_close, keep)
    finally:
        R.candle_rows = orig


def main(argv):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--state", default="state")
    ap.add_argument("--out", default="out")
    ap.add_argument("--now", type=int, default=None)
    ap.add_argument("--lists", default=",".join(LISTS))
    ap.add_argument("--print-key", action="store_true")
    a = ap.parse_args(argv)
    root = os.path.abspath(a.root)
    lists = [x for x in a.lists.split(",") if x in LISTS]
    if a.print_key:
        print(cache_key(root, lists)); return 0
    now = a.now if a.now is not None else int(time.time())
    os.makedirs(a.state, exist_ok=True); os.makedirs(a.out, exist_ok=True)
    rc = 0
    for v in lists:
        if not os.path.exists(config_path(root, v)):
            print("skip %s: no config" % v); continue
        sp = os.path.join(a.state, "shadow_state_%s.json" % v.lower())
        state = json.load(open(sp)) if os.path.exists(sp) else {}
        try:
            res, cnt, st = run_list(root, v, now, R.Puller(), state)
        except R.Refused as e:
            print("REFUSED %s:" % v, e); rc = 1; continue
        rn, cn = out_names(v)
        for path, obj in ((sp, st), (os.path.join(a.out, rn), res), (os.path.join(a.out, cn), cnt)):
            with open(path + ".tmp", "w") as f:
                json.dump(obj, f, indent=1); f.write("\n")
            os.replace(path + ".tmp", path)
        print("ok %s: %d specs" % (v, len(res["specs"])))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
