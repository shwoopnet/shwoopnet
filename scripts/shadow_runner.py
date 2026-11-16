#!/usr/bin/env python3
"""The generic forward shadow runner (Nov 16, 2026, the owner's order, the Head of R&D's spec). LOG ONLY: it places no order, holds no key, writes no Firestore and touches nothing under functions/.
Once a day it pulls the public settled markets and one minute candles of the series named in a frozen list (SHADOW_LIST_V1.json), scores each spec with Desk A's audited ENGINE1 modules (copied byte for byte, pinned by sha256 here),
and writes per-spec AGGREGATES only (the clause S1 of HOLDS.json): forward n, wins, voids, net, profit factor at 1c and 2c, first-half and second-half PF, days, income, a status and the days to 100 signals.
Rules it keeps: the list, the spread cuts and every engine module must match their pinned sha256 or it refuses; a market is read only if the held-out guard (scripts/shadow_holds.py reading HOLDS.json) clears it for the spec;
the forward start is a written constant (start_utc), never the run date, and both the close and the entry decision must be at or after it; a void is scored as a trade at minus the entry fee (the engine core's rule); the spread cuts are read from the file, never recomputed.
Public GETs only to api.elections.kalshi.com, at most one a second, three 429s in a row stop the run, no redirects, no key. Per-trade state (needed for the halves) lives only in the private state directory the caller gives (the workflow keeps it in the Actions cache), never in a published file."""
import calendar, collections, hashlib, importlib.util, json, math, os, sys, time, urllib.error, urllib.request

HOST = "https://api.elections.kalshi.com/trade-api/v2"
GAP_S = 1.0
MAX_429_IN_A_ROW = 3
SETTLE_LAG_S = 7200            # a market is pulled only 2 hours after its close, so it has settled
BATCH = 20                     # consecutive markets per candle request (20 x about 305 minutes is under the 9,000 minute-ticker size the endpoint takes)
LEAD_S = 1200                  # candles from 20 minutes before the first close (features look back at most 360 s before the entry)
CONTRACTS = 10
INCOME_CONTRACTS = 5
UA = {"User-Agent": "shwoopnet-research-recorder"}
LABEL_PAPER = "validate-window income, upward biased, not a forecast"
LABEL_FWD = "forward income at 5 contracts a signal, 7 days a week; signals a day counts calendar days, weekends included; a forward development figure, not a forecast"


def sha_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class Refused(Exception):
    pass


def load_modules(engine_dir, pins):
    """Import the pinned ENGINE1 modules from engine_dir; refuse if any file's sha256 differs from its pin."""
    mods = {}
    sys.path.insert(0, engine_dir)
    for name, want in pins.items():
        path = os.path.join(engine_dir, name + ".py")
        got = sha_of(path)
        if got != want:
            raise Refused("module %s sha256 %s is not the pinned %s" % (name, got, want))
    for name in pins:
        spec = importlib.util.spec_from_file_location(name, os.path.join(engine_dir, name + ".py"))
        mods[name] = importlib.util.module_from_spec(spec)
        sys.modules[name] = mods[name]
        spec.loader.exec_module(mods[name])
    return mods


def parse_filter(f):
    if f in (None, "none"):
        return None
    a, b = f.split(":")
    return (a, b)


def iso_epoch(s):
    try:
        return calendar.timegm(time.strptime(str(s).replace("Z", "").split(".")[0], "%Y-%m-%dT%H:%M:%S"))
    except Exception:
        return None


def num(x):
    try:
        return float(x) if x not in ("", None) else None
    except (TypeError, ValueError):
        return None


def candle_rows(body, kept_close):
    """Desk A's mapping (engine1_heldout_load.py): the CLOSE fields of a Kalshi candlestick -> (end_ts, bid, ask, last, volume, oi); a candle without both bid and ask is skipped, a candle after the close is dropped.
    Returns {ticker: {end_ts: row}}."""
    out = collections.defaultdict(dict)
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
            out[tk].setdefault(e, (e, bid, ask, num((k.get("price") or {}).get("close_dollars")), num(k.get("volume_fp")), num(k.get("open_interest_fp"))))
    return out


class Puller:
    """GET only, one host, one request a second, no redirects, no key; three 429s in a row end the run."""
    def __init__(self, get=None, sleep=time.sleep):
        self.get, self.sleep, self.streak, self.requests = get or self._http, sleep, 0, 0

    @staticmethod
    def _http(url):
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k):
                return None
        op = urllib.request.build_opener(NoRedirect)
        try:
            with op.open(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, None
        except Exception:
            return 0, None

    def read(self, path, params):
        url = HOST + path + "?" + "&".join("%s=%s" % (k, v) for k, v in params.items())
        wait = 5.0
        while True:
            st, body = self.get(url)
            self.requests += 1
            self.sleep(GAP_S)
            if st == 429:
                self.streak += 1
                if self.streak >= MAX_429_IN_A_ROW:
                    raise Refused("three 429 answers in a row: the run stops")
                self.sleep(wait); wait = min(wait * 2, 60.0)
                continue
            self.streak = 0
            if st != 200 or not isinstance(body, dict):
                raise Refused("answer %s for %s" % (st, path))
            return body

    def settled(self, series, min_close, max_close):
        out, cursor = [], None
        while True:
            p = {"series_ticker": series, "status": "settled", "min_close_ts": min_close, "max_close_ts": max_close, "limit": 1000}
            if cursor:
                p["cursor"] = cursor
            b = self.read("/markets", p)
            out += [m for m in b.get("markets", []) if isinstance(m, dict)]
            cursor = b.get("cursor")
            if not cursor:
                return out

    def candles(self, tickers, start_ts, end_ts):
        return self.read("/markets/candlesticks", {"market_tickers": ",".join(tickers), "start_ts": start_ts, "end_ts": end_ts, "period_interval": 1})


def fetch_markets(puller, series, min_close, max_close):
    """-> [market] for the settled markets of one series closing in [min_close, max_close]: {series, ticker, close, result, candles}. result not yes or no is kept as 'void'."""
    ms = []
    for m in puller.settled(series, min_close, max_close):
        tk, cl = m.get("ticker"), iso_epoch(m.get("close_time"))
        if isinstance(tk, str) and tk.split("-")[0] == series and cl is not None:
            ms.append({"series": series, "ticker": tk, "close": cl, "result": m.get("result") if m.get("result") in ("yes", "no") else "void", "candles": []})
    ms = sorted({m["ticker"]: m for m in ms}.values(), key=lambda m: (m["close"], m["ticker"]))
    for i in range(0, len(ms), BATCH):
        grp = ms[i:i + BATCH]
        rows = candle_rows(puller.candles([m["ticker"] for m in grp], grp[0]["close"] - LEAD_S, grp[-1]["close"]), {m["ticker"]: m["close"] for m in grp})
        for m in grp:
            m["candles"] = sorted(rows.get(m["ticker"], {}).values())
    return ms


def cache_key(cfg, root):
    """The state's cache key: the list version, the runner's own sha256 and the HOLDS.json sha, so a changed runner, list or hold table never reuses an old sequence (Auditor B's condition 1)."""
    return "shadow-state-%s-%s-%s" % (cfg.get("list_sha256", "")[:12], sha_of(os.path.abspath(__file__))[:12], sha_of(os.path.join(root, "kalshi-scalper", "workers", "HOLDS.json"))[:12])


def day_of(ts):
    return time.strftime("%Y-%m-%d", time.gmtime(ts))


def score_spec(mods, spec, cut, markets, start_utc, guard, series_in_list, sha256):
    """-> (new trades [ {t: ticker, c: close, d: day, x1: net at 1c, x2: net at 2c, w: 1 if it won, v: 1 if void} ], refused count). The engine core scores every trade; a market is skipped unless the guard clears it."""
    N, K, D = mods["engine1_enum"], mods["engine1_core"], mods["engine1_driver"]
    e = spec["entry"]; filt = parse_filter(e.get("filter")); bucket, band, side = e["seconds_left"], e["price_band_5c"], e["side_rule"]
    info = {"sha256": sha256, "series": series_in_list, "start_utc": start_utc}
    trades, refused = [], 0
    for m in markets:
        if m["close"] < start_utc or m["close"] - bucket < start_utc:
            continue
        ok, _why = guard(info, m["ticker"], m["close"])
        if not ok:
            refused += 1
            continue
        ent, _r = N.entries(m["candles"], m["close"], bucket, band, side, filt, cut)
        if ent is None:
            continue
        core = D.to_core(m, ent)
        x1, r1 = K.score(core, spec["exit"], 0.01, CONTRACTS); x2, _r2 = K.score(core, spec["exit"], 0.02, CONTRACTS)
        if x1 is None or x2 is None:
            continue
        trades.append({"t": m["ticker"], "c": m["close"], "d": day_of(m["close"]), "x1": x1, "x2": x2, "w": 1 if m["result"] == ent["side"] else 0, "v": 1 if m["result"] == "void" else 0})
    return trades, refused


def aggregate(mods, seq, n_days, start_utc, now):
    """Per-spec aggregates from the private ordered sequence [[net at 1c, net at 2c, void flag], ...] (order = (close, ticker), the engine's own), with the engine core's pf. PF is None (with no_losses true) when there are no losses."""
    K = mods["engine1_core"]
    n = len(seq); half = n // 2
    out = {"n": n, "wins": sum(1 for t in seq if t[0] > 0), "voids": sum(t[2] for t in seq)}
    for tag, i in (("1c", 0), ("2c", 1)):
        xs = [t[i] for t in seq]
        v = K.pf(xs); out["net_" + tag] = round(sum(xs), 4)
        out["pf_" + tag] = None if (v != v or v == float("inf")) else round(v, 3); out["no_losses_" + tag] = bool(xs) and v == float("inf")
    xs = [t[0] for t in seq]
    for name, part in (("half1", xs[:half]), ("half2", xs[half:])):
        v = K.pf(part); out["pf_%s_1c" % name] = None if (v != v or v == float("inf")) else round(v, 3); out["no_losses_%s_1c" % name] = bool(part) and v == float("inf")
    out["trade_days"] = n_days
    days = max(1.0, (now - start_utc) / 86400.0)
    out["days"] = round(days, 2)
    out["signals_per_day"] = round(n / days, 3)
    per = (out["net_1c"] / (n * CONTRACTS)) if n else 0.0
    out["edge_cents_per_contract_1c"] = round(per * 100, 3)
    out["dollars_week_5c_1c"] = round((n / days) * per * INCOME_CONTRACTS * 7, 2)
    return out


def status_of(a):
    """The Head's rules: CANDIDATE at 100 or more signals, PF 1.3 or better at 1c and 1.0 or better at 2c, both halves 1.0 or better at 1c; DROPPED when PF is under 1.0 at 1c after 60; else collecting.
    An undefined PF (no losses) counts as passing the bar it is compared with."""
    ge = lambda v, line, nl: nl or (v is not None and v >= line)
    if a["n"] >= 100 and ge(a["pf_1c"], 1.3, a["no_losses_1c"]) and ge(a["pf_2c"], 1.0, a["no_losses_2c"]) and ge(a["pf_half1_1c"], 1.0, a["no_losses_half1_1c"]) and ge(a["pf_half2_1c"], 1.0, a["no_losses_half2_1c"]):
        return "CANDIDATE"
    if a["n"] >= 60 and a["pf_1c"] is not None and a["pf_1c"] < 1.0:
        return "DROPPED"
    return "collecting"


def days_to_100(a):
    """Expected days until 100 signals at the observed rate; None until there are 5 signals (a rate from fewer is noise), 0 once 100 is reached."""
    if a["n"] >= 100:
        return 0
    if a["n"] < 5:
        return None
    return int(math.ceil((100 - a["n"]) / (a["n"] / a["days"])))


def load_config(root):
    p = os.path.join(root, "kalshi-scalper", "workers", "shadow", "SHADOW_RUNNER_CONFIG.json")
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def verified_inputs(root, cfg):
    """Check every pinned file and return (list, cuts, modules, holds table). Anything that differs from its pin stops the run."""
    w = os.path.join(root, "kalshi-scalper", "workers")
    lp, cp = os.path.join(w, cfg["list_file"]), os.path.join(w, cfg["cuts_file"])
    if sha_of(lp) != cfg["list_sha256"]:
        raise Refused("the shadow list is not the pinned one")
    if sha_of(cp) != cfg["cuts_sha256"]:
        raise Refused("the spread cuts file is not the pinned one")
    mods = load_modules(os.path.join(w, "desk_a_verify"), cfg["modules"])
    import shadow_holds as H
    table = H.load(os.path.join(w, "HOLDS.json"))
    with open(lp, encoding="utf-8") as f:
        lst = json.load(f)
    with open(cp, encoding="utf-8") as f:
        cuts = json.load(f)
    return lst, cuts, mods, table, H


def cut_for(cuts, spec):
    if parse_filter(spec["entry"].get("filter")) is None or parse_filter(spec["entry"]["filter"])[0] != "spread":
        return None
    c = cuts["all_series_buckets"][spec["market"]][str(spec["entry"]["seconds_left"])]
    return (c["c1"], c["c2"])


def run_once(root, now, puller, state, cfg=None):
    """One daily run. `state` is {pulled_until: {series: epoch}, trades: {spec_id: {seq: [[x1, x2, void]], n_days, last_day}}, refused} (private: net amounts in close order and a day counter, no ticker, price or feature; the caller loads and saves it). Returns (results, counts, state). Any refusal leaves the state as it was."""
    cfg = cfg or load_config(root)
    lst, cuts, mods, table, H = verified_inputs(root, cfg)
    start = cfg["start_utc"]
    series_in_list = sorted({s["spec"]["market"] for s in lst["specs"]})
    guard = lambda info, ticker, close: H.decide(table, info, ticker, close)
    st = json.loads(json.dumps(state)) if state else {}
    st.setdefault("pulled_until", {}); st.setdefault("trades", {})
    max_close = now - SETTLE_LAG_S
    fetched = {}
    for series in series_in_list:
        lo = max(start, st["pulled_until"].get(series, start))
        if max_close >= lo:
            fetched[series] = fetch_markets(puller, series, lo, max_close)
    results, counts = {}, []
    for item in lst["specs"]:
        spec, sha = item["spec"], item["spec_sha256"]
        mine = st["trades"].setdefault(spec["id"], {"seq": [], "n_days": 0, "last_day": ""})
        new, refused = score_spec(mods, spec, cut_for(cuts, spec), fetched.get(spec["market"], []), start, guard, series_in_list, sha)
        for t in sorted(new, key=lambda t: (t["c"], t["t"])):
            mine["seq"].append([t["x1"], t["x2"], t["v"]])
            if t["d"] != mine["last_day"]:
                mine["n_days"] += 1; mine["last_day"] = t["d"]
        a = aggregate(mods, mine["seq"], mine["n_days"], start, now)
        a["status"] = status_of(a); a["days_to_100"] = days_to_100(a)
        a["refused_by_guard"] = st.setdefault("refused", {}).get(spec["id"], 0) + refused
        st["refused"][spec["id"]] = a["refused_by_guard"]
        results[spec["id"]] = dict(a, admission=item.get("admission"), market=spec["market"], spec_sha256=sha)
        counts.append({"id": spec["id"], "signals": a["n"], "settled": a["n"], "wins": a["wins"], "voids": a["voids"], "target": 100, "status": a["status"], "expected_days_to_100": a["days_to_100"],
                       "start_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start)), "as_of_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))})
    for series in fetched:
        st["pulled_until"][series] = max_close + 1
    results_doc = {"list": lst["list"], "as_of_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)), "labels": {"forward": LABEL_FWD, "paper": LABEL_PAPER}, "specs": results}
    return results_doc, {"as_of_utc": results_doc["as_of_utc"], "specs": counts}, st


def main(argv):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--state", default="state", help="state directory (kept in the Actions cache, never published)")
    ap.add_argument("--out", default="out", help="where shadow_results.json and shadow_counts.json are written (the data branch checkout)")
    ap.add_argument("--now", type=int, default=None)
    ap.add_argument("--print-key", action="store_true", help="print the state cache key (list, runner and holds shas) and stop; reads no network")
    a = ap.parse_args(argv)
    if a.print_key:
        print(cache_key(load_config(os.path.abspath(a.root)), os.path.abspath(a.root))); return 0
    now = a.now if a.now is not None else int(time.time())
    sp = os.path.join(a.state, "shadow_state.json")
    state = json.load(open(sp)) if os.path.exists(sp) else {}
    try:
        res, cnt, st = run_once(os.path.abspath(a.root), now, Puller(), state)
    except Refused as e:
        print("REFUSED:", e); return 1
    os.makedirs(a.state, exist_ok=True); os.makedirs(a.out, exist_ok=True)
    for path, obj in ((sp, st), (os.path.join(a.out, "shadow_results.json"), res), (os.path.join(a.out, "shadow_counts.json"), cnt)):
        with open(path + ".tmp", "w") as f:
            json.dump(obj, f, indent=1); f.write("\n")
        os.replace(path + ".tmp", path)
    print("ok: %d specs, %d requests" % (len(res["specs"]), 0))
    return 0


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main(sys.argv[1:]))
